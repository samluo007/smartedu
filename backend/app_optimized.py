"""
SmartEdu 后端主应用（优化版）
支持多版本：九年义务教育、高中、高校
包含：数据库连接池、缓存、分页支持
"""
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import db, EducationStage, Subject, User
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 配置数据库（优化：连接池配置）
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'smartedu_unified.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'smartedu-secret-key-2026'

# 数据库连接池配置（为 PostgreSQL 生产环境准备）
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,  # 连接池大小
    'pool_recycle': 3600,  # 连接回收时间（秒）
    'pool_pre_ping': True,  # 连接前 ping，确保连接有效
    'max_overflow': 20,  # 超出 pool_size 后的最大溢出连接数
    'pool_timeout': 30,  # 获取连接的超时时间（秒）
}

# 初始化数据库
db.init_app(app)

# 导入缓存工具
from cache_utils import clear_cache

# 导入并注册优化后的 API 蓝图
from api.unified_api import *
import api.unified_api as unified_api_module
# 注册路由（unified_api.py 直接使用 @app.route 装饰器）
# 无需额外注册，因为路由已直接绑定到 app

# ==================== 优化后的路由 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查（增强版）"""
    from cache_utils import _cache
    return jsonify({
        'status': 'ok',
        'message': 'SmartEdu Unified System Running (Optimized)',
        'supported_versions': ['9-year', 'high-school', 'university'],
        'cache_size': len(_cache),
        'timestamp': datetime.utcnow().isoformat()
    })

# ==================== 数据库初始化 ====================

def init_database():
    """初始化数据库"""
    print("🚀 开始初始化 SmartEdu 统一数据库...")
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✅ 数据库表创建完成")
        
        # 初始化教育阶段
        init_education_stages()
        
        # 初始化科目
        init_subjects()
        
        print("\n🎉 数据库初始化完成！")
        print("\n📊 数据统计：")
        print(f"   - 教育阶段：{EducationStage.query.count()} 个")
        print(f"   - 科目：{Subject.query.count()} 个")
        print("\n🚀 启动后端服务：")
        print("   python app.py")

def init_education_stages():
    """初始化教育阶段数据"""
    stages = [
        {
            'code': '9-year',
            'name': '九年义务教育',
            'name_en': '9-Year Compulsory Education',
            'description': '小学一年级至初中九年级（Grade 1-9）',
            'grade_range': '1-9',
            'is_active': True
        },
        {
            'code': 'high-school',
            'name': '高中版',
            'name_en': 'High School',
            'description': '高中一年级至三年级（Grade 10-12）',
            'grade_range': '10-12',
            'is_active': True
        },
        {
            'code': 'university',
            'name': '高校版',
            'name_en': 'University',
            'description': '大学本科及研究生教育（Grade 13+）',
            'grade_range': '13+',
            'is_active': True
        }
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
        # 九年义务教育阶段
        {'education_stage_code': '9-year', 'name': '语文', 'name_en': 'Chinese', 'grade_applicable': '1,2,3,4,5,6,7,8,9', 'is_active': True},
        {'education_stage_code': '9-year', 'name': '数学', 'name_en': 'Mathematics', 'grade_applicable': '1,2,3,4,5,6,7,8,9', 'is_active': True},
        {'education_stage_code': '9-year', 'name': '英语', 'name_en': 'English', 'grade_applicable': '3,4,5,6,7,8,9', 'is_active': True},
        {'education_stage_code': '9-year', 'name': '物理', 'name_en': 'Physics', 'grade_applicable': '8,9', 'is_active': True},
        {'education_stage_code': '9-year', 'name': '化学', 'name_en': 'Chemistry', 'grade_applicable': '9', 'is_active': True},
        {'education_stage_code': '9-year', 'name': '生物', 'name_en': 'Biology', 'grade_applicable': '7,8,9', 'is_active': True},
        {'education_stage_code': '9-year', 'name': '历史', 'name_en': 'History', 'grade_applicable': '7,8,9', 'is_active': True},
        {'education_stage_code': '9-year', 'name': '地理', 'name_en': 'Geography', 'grade_applicable': '7,8,9', 'is_active': True},
        {'education_stage_code': '9-year', 'name': '道德与法治', 'name_en': 'Morality & Law', 'grade_applicable': '1,2,3,4,5,6,7,8,9', 'is_active': True},
        
        # 高中阶段
        {'education_stage_code': 'high-school', 'name': '语文', 'name_en': 'Chinese', 'grade_applicable': '10,11,12', 'is_active': True},
        {'education_stage_code': 'high-school', 'name': '数学', 'name_en': 'Mathematics', 'grade_applicable': '10,11,12', 'is_active': True},
        {'education_stage_code': 'high-school', 'name': '英语', 'name_en': 'English', 'grade_applicable': '10,11,12', 'is_active': True},
        {'education_stage_code': 'high-school', 'name': '物理', 'name_en': 'Physics', 'grade_applicable': '10,11,12', 'is_active': True},
        {'education_stage_code': 'high-school', 'name': '化学', 'name_en': 'Chemistry', 'grade_applicable': '10,11,12', 'is_active': True},
        {'education_stage_code': 'high-school', 'name': '生物', 'name_en': 'Biology', 'grade_applicable': '10,11,12', 'is_active': True},
        {'education_stage_code': 'high-school', 'name': '历史', 'name_en': 'History', 'grade_applicable': '10,11,12', 'is_active': True},
        {'education_stage_code': 'high-school', 'name': '地理', 'name_en': 'Geography', 'grade_applicable': '10,11,12', 'is_active': True},
        {'education_stage_code': 'high-school', 'name': '政治', 'name_en': 'Politics', 'grade_applicable': '10,11,12', 'is_active': True},
        
        # 高校阶段
        {'education_stage_code': 'university', 'name': '高等数学', 'name_en': 'Advanced Mathematics', 'grade_applicable': '13,14,15,16', 'is_active': True},
        {'education_stage_code': 'university', 'name': '大学英语', 'name_en': 'College English', 'grade_applicable': '13,14,15,16', 'is_active': True},
        {'education_stage_code': 'university', 'name': '计算机科学', 'name_en': 'Computer Science', 'grade_applicable': '13,14,15,16', 'is_active': True},
        {'education_stage_code': 'university', 'name': '物理学', 'name_en': 'Physics', 'grade_applicable': '13,14,15,16', 'is_active': True},
        {'education_stage_code': 'university', 'name': '化学', 'name_en': 'Chemistry', 'grade_applicable': '13,14,15,16', 'is_active': True},
        {'education_stage_code': 'university', 'name': '生物学', 'name_en': 'Biology', 'grade_applicable': '13,14,15,16', 'is_active': True},
        {'education_stage_code': 'university', 'name': '经济学', 'name_en': 'Economics', 'grade_applicable': '13,14,15,16', 'is_active': True},
        {'education_stage_code': 'university', 'name': '管理学', 'name_en': 'Management', 'grade_applicable': '13,14,15,16', 'is_active': True}
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
        # 检查是否需要初始化数据
        if EducationStage.query.count() == 0:
            init_database()
    
    # 启动应用（优化：禁用 auto-reload 以提升性能）
    app.run(
        debug=False,  # 生产环境应设为 False
        host='0.0.0.0',
        port=5000,
        threaded=True  # 启用多线程处理并发请求
    )
