"""
SmartEdu 统一 API - 支持多版本（九年义务教育/高中/高校）
优化版：添加缓存和分页支持
"""
from flask import jsonify, request
from models import db, EducationStage, Subject, Textbook, KnowledgePointEnhanced
from models import LessonPreparation, QuestionBankEnhanced, MultimediaResource
from app import app
from datetime import datetime
from cache_utils import cached, clear_cache, CACHE_PREFIX_SUBJECTS, CACHE_PREFIX_TEXTBOOKS
from cache_utils import CACHE_PREFIX_KNOWLEDGE_POINTS, CACHE_PREFIX_STATISTICS

# ==================== 教育阶段 API ====================

@app.route('/api/education-stages', methods=['GET'])
@cached('education_stages', ttl=600)  # 缓存10分钟
def get_education_stages():
    """获取所有教育阶段（带缓存）"""
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
@cached('education_stage_detail', ttl=600)
def get_education_stage_detail(code):
    """获取单个教育阶段详情（带缓存）"""
    stage = EducationStage.query.filter_by(code=code, is_active=True).first()
    if not stage:
        return jsonify({'error': 'Education stage not found'}), 404
    
    # 获取该阶段的科目统计
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

# ==================== 科目 API（支持版本过滤 + 缓存 + 分页）====================

@app.route('/api/subjects', methods=['GET'])
@cached(CACHE_PREFIX_SUBJECTS, ttl=300)
def get_all_subjects():
    """获取所有科目（可按教育阶段过滤，带缓存）"""
    stage_code = request.args.get('education_stage')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = Subject.query.filter_by(is_active=True)
    if stage_code:
        query = query.filter_by(education_stage_code=stage_code)
    
    # 分页
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

# ==================== 教材 API（支持版本过滤 + 分页）====================

@app.route('/api/textbooks', methods=['GET'])
def get_textbooks():
    """获取教材列表（支持多条件过滤 + 分页）"""
    stage_code = request.args.get('education_stage')
    subject_id = request.args.get('subject_id', type=int)
    grade = request.args.get('grade')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Textbook.query
    
    if stage_code:
        query = query.filter_by(education_stage_code=stage_code)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if grade:
        query = query.filter_by(grade=grade)
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'textbooks': [{
            'id': t.id,
            'education_stage_code': t.education_stage_code,
            'subject_id': t.subject_id,
            'title': t.title,
            'publisher': t.publisher,
            'edition': t.edition,
            'grade': t.grade,
            'isbn': t.isbn
        } for t in paginated.items],
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })

@app.route('/api/textbooks/<int:textbook_id>/chapters', methods=['GET'])
@cached('textbook_chapters', ttl=600)
def get_textbook_chapters(textbook_id):
    """获取教材的章节树（带缓存）"""
    from models import TextbookChapter
    
    chapters = TextbookChapter.query.filter_by(
        textbook_id=textbook_id,
        parent_id=None
    ).order_by(TextbookChapter.order_index).all()
    
    def serialize_chapter(chapter):
        return {
            'id': chapter.id,
            'chapter_number': chapter.chapter_number,
            'title': chapter.title,
            'level': chapter.level,
            'children': [serialize_chapter(child) for child in chapter.children]
        }
    
    return jsonify([serialize_chapter(ch) for ch in chapters])

# ==================== 知识点 API（支持版本过滤 + 分页）====================

@app.route('/api/knowledge-points', methods=['GET'])
def get_knowledge_points():
    """获取知识点列表（支持版本和多条件过滤 + 分页）"""
    stage_code = request.args.get('education_stage')
    subject_id = request.args.get('subject_id', type=int)
    difficulty = request.args.get('difficulty', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    query = KnowledgePointEnhanced.query
    
    if stage_code:
        query = query.filter_by(education_stage_code=stage_code)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if difficulty:
        query = query.filter_by(difficulty_level=difficulty)
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'knowledge_points': [{
            'id': p.id,
            'education_stage_code': p.education_stage_code,
            'subject_id': p.subject_id,
            'name': p.name,
            'difficulty_level': p.difficulty_level,
            'bloom_level': p.bloom_level
        } for p in paginated.items],
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })

@app.route('/api/knowledge-graph/<int:subject_id>', methods=['GET'])
@cached(CACHE_PREFIX_KNOWLEDGE_POINTS, ttl=300)
def get_knowledge_graph(subject_id):
    """获取学科知识图谱数据（用于可视化，带缓存）"""
    from models import KnowledgeRelationship
    
    # 获取该科目的所有知识点
    points = KnowledgePointEnhanced.query.filter_by(subject_id=subject_id).all()
    
    # 获取知识点之间的关系
    relationships = KnowledgeRelationship.query.filter(
        KnowledgeRelationship.source_id.in_([p.id for p in points]) |
        KnowledgeRelationship.target_id.in_([p.id for p in points])
    ).all()
    
    # 构建可视化数据（ECharts D3.js 格式）
    nodes = [{
        'id': str(p.id),
        'name': p.name,
        'difficulty': p.difficulty_level,
        'bloom_level': p.bloom_level
    } for p in points]
    
    links = [{
        'source': str(r.source_id),
        'target': str(r.target_id),
        'type': r.relation_type,
        'strength': r.strength
    } for r in relationships]
    
    return jsonify({
        'nodes': nodes,
        'links': links,
        'total_nodes': len(nodes),
        'total_links': len(links)
    })

# ==================== 备课 API（支持版本 + 分页）====================

@app.route('/api/lesson-plan/generate-enhanced', methods=['POST'])
def generate_enhanced_lesson_plan():
    """生成增强版教案（AI驱动）"""
    data = request.get_json()
    
    required_fields = ['education_stage', 'subject_id', 'topic']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # TODO: 调用 AI 服务生成教案
    # 这里返回模拟数据作为示例
    
    lesson_plan = {
        'id': 1,
        'education_stage': data['education_stage'],
        'subject_id': data['subject_id'],
        'topic': data['topic'],
        'title': f"{data['topic']} - 智能教案",
        'duration_minutes': data.get('duration', 45),
        'knowledge_graph': {
            'nodes': [
                {'id': '1', 'name': '知识点1', 'type': 'core'},
                {'id': '2', 'name': '知识点2', 'type': 'sub'}
            ],
            'links': [
                {'source': '1', 'target': '2', 'relation': 'prerequisite'}
            ]
        },
        'multimedia_suggestions': [
            {'type': 'video', 'title': '相关教学视频', 'duration': 300},
            {'type': 'interactive', 'title': '互动练习', 'url': '#'}
        ],
        'real_life_examples': [
            {'scenario': '日常生活中的应用', 'description': '举例说明...'},
            {'scenario': '跨学科关联', 'description': '与物理知识的关联...'}
        ],
        'interdisciplinary_design': {
            'related_subjects': ['物理', '生物'],
            'integration_points': ['知识点融合', '综合实践']
        },
        'generated_at': datetime.utcnow().isoformat()
    }
    
    return jsonify(lesson_plan)

@app.route('/api/lesson-plans', methods=['GET'])
def get_lesson_plans():
    """获取备课列表（支持版本过滤 + 分页）"""
    stage_code = request.args.get('education_stage')
    teacher_id = request.args.get('teacher_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = LessonPreparation.query
    
    if stage_code:
        query = query.filter_by(education_stage_code=stage_code)
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    
    paginated = query.order_by(LessonPreparation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'lesson_plans': [{
            'id': p.id,
            'title': p.title,
            'education_stage_code': p.education_stage_code,
            'subject_id': p.subject_id,
            'grade': p.grade,
            'duration_minutes': p.duration_minutes,
            'status': p.status,
            'created_at': p.created_at.isoformat()
        } for p in paginated.items],
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })

# ==================== 题库 API（支持版本过滤 + 分页）====================

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """获取题目列表（支持版本和多条件过滤 + 分页）"""
    stage_code = request.args.get('education_stage')
    subject_id = request.args.get('subject_id', type=int)
    question_type = request.args.get('type')
    difficulty = request.args.get('difficulty', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = QuestionBankEnhanced.query
    
    if stage_code:
        query = query.filter_by(education_stage_code=stage_code)
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    if question_type:
        query = query.filter_by(question_type=question_type)
    if difficulty:
        query = query.filter_by(difficulty_level=difficulty)
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'questions': [{
            'id': q.id,
            'education_stage_code': q.education_stage_code,
            'subject_id': q.subject_id,
            'question_type': q.question_type,
            'difficulty_level': q.difficulty_level,
            'content': q.content[:100] + '...' if len(q.content) > 100 else q.content,
            'bloom_level': q.bloom_level,
            'interdisciplinary': q.interdisciplinary
        } for q in paginated.items],
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })

# ==================== 统计 API（带缓存）====================

@app.route('/api/statistics/<stage_code>', methods=['GET'])
@cached(CACHE_PREFIX_STATISTICS, ttl=300)
def get_statistics(stage_code):
    """获取指定教育阶段的统计数据（带缓存）"""
    from models import User, Class
    
    stats = {
        'education_stage': stage_code,
        'subjects_count': Subject.query.filter_by(education_stage_code=stage_code).count(),
        'students_count': User.query.filter_by(education_stage=stage_code, role='student').count(),
        'teachers_count': User.query.filter_by(education_stage=stage_code, role='teacher').count(),
        'classes_count': Class.query.filter_by(education_stage_code=stage_code).count(),
        'lesson_plans_count': LessonPreparation.query.filter_by(education_stage_code=stage_code).count(),
        'questions_count': QuestionBankEnhanced.query.filter_by(education_stage_code=stage_code).count(),
        'knowledge_points_count': KnowledgePointEnhanced.query.filter_by(education_stage_code=stage_code).count()
    }
    
    return jsonify(stats)

# ==================== 缓存管理 API ====================

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache_endpoint():
    """清除缓存（管理员功能）"""
    prefix = request.args.get('prefix')
    clear_cache(prefix)
    return jsonify({
        'message': f'Cache cleared' + (f' for prefix: {prefix}' if prefix else '')
    })
