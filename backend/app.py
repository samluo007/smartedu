"""
SmartEdu 后端主应用（安全增强版）
支持多版本：九年义务教育、高中、高校
包含：速率限制、审计日志、缓存优化、分页支持、所有 API 路由
"""
from flask import Flask, request, jsonify, g, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import db, EducationStage, Subject, User, AuditLog
import os
from datetime import datetime
import time
import json

# ==================== 初始化应用 ====================

app = Flask(__name__)
CORS(app)

# 配置数据库（优化：连接池配置）
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'smartedu_unified.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'smartedu-secret-key-2026'

# 数据库连接池配置（为 PostgreSQL 生产环境准备）
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20,
    'pool_timeout': 30,
}

# 初始化数据库
db.init_app(app)

# 导入安全模块和缓存工具
from security import (
    rate_limit, audit_action, security_headers,
    create_audit_log, sanitize_input, validate_education_stage,
    CacheStats, cached_with_stats
)
from cache_utils import clear_cache, _cache


# ==================== 全局请求钩子 ====================

@app.before_request
def before_request():
    """请求前处理"""
    # 记录请求开始时间
    g.start_time = time.time()

    # 输入清理 - 对 GET 参数进行基本验证
    if request.method == 'GET':
        for key in list(request.args.keys()):
            value = request.args.get(key)
            if value and len(str(value)) > 10000:
                return jsonify({
                    'error': 'Invalid parameter',
                    'message': f'Parameter {key} exceeds maximum length',
                    'code': 400
                }), 400


@app.after_request
def after_request(response):
    """请求后处理 - 提交审计日志 + 安全头"""

    # 添加安全响应头
    response = security_headers(response)

    # 提交待处理的审计日志
    try:
        if hasattr(g, 'audit_logs') and g.audit_logs:
            for log_entry in g.audit_logs:
                # 更新响应状态码
                if not log_entry.response_status or log_entry.response_status == 'pending':
                    log_entry.response_status = str(response.status_code)

                    # 根据状态码更新状态
                    status_code = response.status_code
                    if status_code >= 200 and status_code < 300:
                        if log_entry.status == 'pending' or not log_entry.status:
                            log_entry.status = 'success'
                    elif status_code == 401:
                        log_entry.status = 'unauthorized'
                    elif status_code == 403:
                        log_entry.status = 'forbidden'
                    elif status_code == 429:
                        log_entry.status = 'rate_limited'
                    elif status_code >= 400:
                        log_entry.status = 'failure'

                # 更新执行耗时
                if hasattr(g, 'start_time') and not log_entry.duration_ms:
                    log_entry.duration_ms = int((time.time() - g.start_time) * 1000)

            # 批量提交审计日志
            db.session.commit()
    except Exception as e:
        print(f"⚠️ 审计日志提交失败: {e}")
        db.session.rollback()

    return response


# ==================== 健康检查 API ====================

@app.route('/api/health', methods=['GET'])
@rate_limit('/api/health')
def health_check():
    """
    健康检查
    包含系统状态、缓存统计、版本信息
    """
    return jsonify({
        'status': 'ok',
        'message': 'SmartEdu Unified System Running (Security Enhanced)',
        'supported_versions': ['9-year', 'high-school', 'university'],
        'cache_size': len(_cache),
        'cache_stats': CacheStats.get_stats(),
        'timestamp': datetime.utcnow().isoformat(),
        'security_features': {
            'rate_limiting': True,
            'audit_logging': True,
            'caching': True,
            'security_headers': True
        }
    })


# ==================== 教育阶段 API ====================

@app.route('/api/education-stages', methods=['GET'])
@rate_limit('/api/education-stages')
@cached_with_stats('education_stages')
@audit_action('read', resource_type='education_stage')
def get_education_stages():
    """获取所有教育阶段"""
    stages = EducationStage.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': s.id,
        'code': s.code,
        'name': s.name,
        'name_en': s.name_en,
        'description': s.description,
        'grade_range': s.grade_range
    } for s in stages])


@app.route('/api/education-stages/<code>', methods=['GET'])
@rate_limit('/api/education-stages/<code>')
@audit_action('read', resource_type='education_stage')
def get_education_stage_detail(code):
    """获取单个教育阶段详情"""

    # 验证输入
    code = sanitize_input(code)

    stage = EducationStage.query.filter_by(code=code, is_active=True).first()
    if not stage:
        return jsonify({'error': 'Education stage not found'}), 404

    subjects_count = Subject.query.filter_by(education_stage_code=code).count()

    return jsonify({
        'code': stage.code,
        'name': stage.name,
        'name_en': stage.name_en,
        'description': stage.description,
        'grade_range': stage.grade_range,
        'subjects_count': subjects_count,
        'is_active': stage.is_active
    })


# ==================== 科目 API（支持版本过滤 + 分页）====================

@app.route('/api/subjects', methods=['GET'])
@rate_limit('/api/subjects')
@cached_with_stats('subjects')
@audit_action('read', resource_type='subject')
def get_all_subjects():
    """获取所有科目（可按教育阶段过滤，支持分页）"""

    stage_code = request.args.get('education_stage')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # 参数验证
    per_page = min(per_page, 100)  # 最大每页 100 条
    page = max(page, 1)  # 最小页码为 1

    query = Subject.query.filter_by(is_active=True)

    if stage_code:
        # 验证教育阶段代码
        is_valid, code = validate_education_stage(stage_code)
        if not is_valid:
            return jsonify({
                'error': 'Invalid education stage code',
                'valid_codes': ['9-year', 'high-school', 'university']
            }), 400
        query = query.filter_by(education_stage_code=stage_code)

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'subjects': [{
            'id': s.id,
            'education_stage_code': s.education_stage_code,
            'name': s.name,
            'name_en': s.name_en,
            'grade_applicable': s.grade_applicable,
            'icon': s.icon
        } for s in paginated.items],
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })


# ==================== 统计 API ====================

@app.route('/api/statistics/<stage_code>', methods=['GET'])
@rate_limit('/api/statistics/<stage_code>')
@cached_with_stats('statistics')
@audit_action('read', resource_type='statistics')
def get_statistics(stage_code):
    """获取指定教育阶段的统计数据"""

    # 验证输入
    stage_code = sanitize_input(stage_code)
    is_valid, _ = validate_education_stage(stage_code)

    if not is_valid:
        return jsonify({
            'error': 'Invalid education stage code',
            'valid_codes': ['9-year', 'high-school', 'university']
        }), 400

    stats = {
        'education_stage': stage_code,
        'subjects_count': Subject.query.filter_by(education_stage_code=stage_code).count(),
        'students_count': User.query.filter_by(
            education_stage=stage_code, role='student'
        ).count() if hasattr(User, 'education_stage') else 0,
        'teachers_count': User.query.filter_by(
            education_stage=stage_code, role='teacher'
        ).count() if hasattr(User, 'education_stage') else 0,
        'classes_count': 0,
        'lesson_plans_count': 0,
        'questions_count': 0,
        'knowledge_points_count': 0
    }

    return jsonify(stats)


# ==================== 版本选择 API ====================

@app.route('/api/version/select', methods=['POST'])
@rate_limit('/api/version/select')  # 更严格的限制
@audit_action('select_version', resource_type='version')
def select_version():
    """选择教育版本"""

    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body required'}), 400

    stage_code = data.get('education_stage')

    # 验证输入
    stage_code = sanitize_input(stage_code)
    is_valid, _ = validate_education_stage(stage_code)

    if not is_valid:
        return jsonify({
            'error': 'Invalid education stage code',
            'valid_codes': ['9-year', 'high-school', 'university']
        }), 400

    stage = EducationStage.query.filter_by(code=stage_code).first()

    if not stage:
        return jsonify({'error': 'Education stage not found'}), 404

    # 创建详细的审计日志
    create_audit_log(
        action_type='version_selection',
        resource_type='version',
        details={
            'selected_version': stage_code,
            'version_name': stage.name,
            'user_agent': request.headers.get('User-Agent', '')[:200]
        },
        status='success'
    )

    return jsonify({
        'message': f'Successfully selected {stage.name}',
        'education_stage': {
            'code': stage.code,
            'name': stage.name,
            'grade_range': stage.grade_range
        }
    })


# ==================== 审计日志管理 API ====================

@app.route('/api/admin/audit-logs', methods=['GET'])
@rate_limit('/api/admin/audit-logs')
def get_audit_logs():
    """
    获取审计日志列表（管理员功能）
    支持按时间范围、操作类型、用户等筛选
    """

    # 基础参数
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    # 筛选参数
    action_type = request.args.get('action_type')
    resource_type = request.args.get('resource_type')
    user_id = request.args.get('user_id', type=int)
    status = request.args.get('status')

    # 时间范围
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # 构建查询
    query = AuditLog.query

    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if status:
        query = query.filter(AuditLog.status == status)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(AuditLog.created_at <= end_dt)
        except ValueError:
            pass

    # 排序：最新优先
    query = query.order_by(AuditLog.created_at.desc())

    # 分页
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'audit_logs': [{
            'id': log.id,
            'action_type': log.action_type,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'user_id': log.user_id,
            'ip_address': log.ip_address[:20] + '...' if log.ip_address and len(log.ip_address) > 20 else log.ip_address,
            'request_method': log.request_method,
            'request_path': log.request_path,
            'response_status': log.response_status,
            'status': log.status,
            'duration_ms': log.duration_ms,
            'created_at': log.created_at.isoformat() if log.created_at else None
        } for log in paginated.items],
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })


@app.route('/api/admin/audit-stats', methods=['GET'])
@rate_limit('/api/admin/audit-stats')
@cached_with_stats('audit_stats', ttl=60)  # 统计数据缓存1分钟
def get_audit_statistics():
    """获取审计统计概览"""

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    stats = {
        'total_requests': AuditLog.query.count(),
        'today_requests': AuditLog.query.filter(AuditLog.created_at >= today).count(),

        # 按操作类型分组
        'by_action': dict(db.session.query(
            AuditLog.action_type,
            db.func.count(AuditLog.id)
        ).group_by(AuditLog.action_type).all()),

        # 按状态分组
        'by_status': dict(db.session.query(
            AuditLog.status,
            db.func.count(AuditLog.id)
        ).group_by(AuditLog.status).all()),

        # 平均响应时间（毫秒）
        'avg_duration_ms': db.session.query(
            db.func.avg(AuditLog.duration_ms)
        ).scalar() or 0,

        # 错误率
        'error_rate': (db.session.query(AuditLog.id).filter(
            AuditLog.status.in_(['failure', 'error', 'unauthorized', 'forbidden', 'rate_limited'])
        ).count() / max(db.session.query(AuditLog.id).count(), 1)) * 100,

        # 缓存统计
        'cache_stats': CacheStats.get_stats()
    }

    return jsonify(stats)


# ==================== 缓存管理 API ====================

@app.route('/api/admin/cache/stats', methods=['GET'])
@rate_limit('/api/admin/cache/stats')
def get_cache_statistics():
    """获取缓存统计信息"""
    return jsonify({
        'cache_size': len(_cache),
        'stats': CacheStats.get_stats()
    })


@app.route('/api/admin/cache/clear', methods=['POST'])
@rate_limit('/api/admin/cache/clear')
def clear_cache_api():
    """清除缓存（管理员功能）"""
    prefix = (request.get_json() or {}).get('prefix')

    before_size = len(_cache)
    clear_cache(prefix)
    after_size = len(_cache)

    create_audit_log(
        action_type='cache_clear',
        resource_type='cache',
        details={
            'prefix': prefix,
            'before_size': before_size,
            'after_size': after_size
        },
        status='success'
    )

    return jsonify({
        'message': 'Cache cleared successfully',
        'entries_removed': before_size - after_size,
        'current_size': after_size
    })


# ==================== 数据库初始化 ====================

def init_database():
    """初始化数据库"""
    print("🚀 开始初始化 SmartEdu 统一数据库（含审计表）...")

    with app.app_context():
        db.create_all()
        print("✅ 数据库表创建完成（含审计日志表）")

        init_education_stages()
        init_subjects()

        # 初始审计日志
        create_audit_log(
            action_type='system_init',
            resource_type='system',
            details={'message': 'System initialized with security enhancements'},
            status='success'
        )
        db.session.commit()

        print("\n🎉 数据库初始化完成！")
        print(f"\n📊 数据统计：")
        print(f"   - 教育阶段：{EducationStage.query.count()} 个")
        print(f"   - 科目：{Subject.query.count()} 个")
        print(f"   - 审计表已就绪 ✅")


def init_education_stages():
    """初始化教育阶段数据"""
    stages = [
        {'code': '9-year', 'name': '九年义务教育', 'name_en': '9-Year Compulsory Education', 'description': '小学一年级至初中九年级（Grade 1-9）', 'grade_range': '1-9', 'is_active': True},
        {'code': 'high-school', 'name': '高中版', 'name_en': 'High School', 'description': '高中一年级至三年级（Grade 10-12）', 'grade_range': '10-12', 'is_active': True},
        {'code': 'university', 'name': '高校版', 'name_en': 'University', 'description': '大学本科及研究生教育（Grade 13+）', 'grade_range': '13+', 'is_active': True}
    ]

    for stage_data in stages:
        if not EducationStage.query.filter_by(code=stage_data['code']).first():
            stage = EducationStage(**stage_data)
            db.session.add(stage)

    db.session.commit()
    print("✅ 教育阶段数据初始化完成")


def init_subjects():
    """初始化科目数据"""
    subjects_data = [
        {'education_stage_code': '9-year', 'name': '语文', 'name_en': 'Chinese', 'grade_applicable': '1,2,3,4,5,6,7,8,9', 'is_active': True},
        {'education_stage_code': '9-year', 'name': '数学', 'name_en': 'Mathematics', 'grade_applicable': '1,2,3,4,5,6,7,8,9', 'is_active': True},
        {'education_stage_code': 'high-school', 'name': '语文', 'name_en': 'Chinese', 'grade_applicable': '10,11,12', 'is_active': True},
        {'education_stage_code': 'high-school', 'name': '数学', 'name_en': 'Mathematics', 'grade_applicable': '10,11,12', 'is_active': True},
        {'education_stage_code': 'university', 'name': '高等数学', 'name_en': 'Advanced Mathematics', 'grade_applicable': '13,14,15,16', 'is_active': True},
        {'education_stage_code': 'university', 'name': '大学英语', 'name_en': 'College English', 'grade_applicable': '13,14,15,16', 'is_active': True}
    ]

    for sub_data in subjects_data:
        if not Subject.query.filter_by(
            education_stage_code=sub_data['education_stage_code'],
            name=sub_data['name']
        ).first():
            subject = Subject(**sub_data)
            db.session.add(subject)

    db.session.commit()
    print("✅ 科目数据初始化完成")


# ==================== 主程序入口 ====================

if __name__ == '__main__':
    with app.app_context():
        # 检查是否需要初始化
        table_exists = db.engine.dialect.has_table(db.engine.connect(), 'users')

        if not table_exists:
            init_database()
        else:
            # 检查审计表是否存在
            if not db.engine.dialect.has_table(db.engine.connect(), 'audit_logs'):
                print("🔄 检测到旧表结构，添加审计表...")
                db.create_all()
                print("✅ 审计表创建完成")
            else:
                print("✅ 数据库已是最新结构（含安全增强）")

    print("\n🔒 安全增强功能已启用：")
    print("   ✓ 速率限制 (Rate Limiting)")
    print("   ✓ 审计日志 (Audit Logging)")
    print("   ✓ 智能缓存 (Intelligent Caching)")
    print("   ✓ 安全响应头 (Security Headers)")

    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
