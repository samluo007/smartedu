"""
SmartEdu 统一数据库模型
支持多版本：九年义务教育、高中、高校
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """用户基础模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), nullable=False)  # student, teacher, parent, admin
    education_stage = db.Column(db.String(20), default='9-year')  # 9-year, high-school, university
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class EducationStage(db.Model):
    """教育阶段配置表"""
    __tablename__ = 'education_stages'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # 9-year, high-school, university
    name = db.Column(db.String(50), nullable=False)  # 九年义务教育, 高中, 高校
    name_en = db.Column(db.String(50))
    description = db.Column(db.Text)
    grade_range = db.Column(db.String(50))  # 1-9, 10-12, 13+
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    subjects = db.relationship('Subject', backref='education_stage', lazy=True)

class Subject(db.Model):
    """科目表 - 按教育阶段分类"""
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    education_stage_code = db.Column(db.String(20), db.ForeignKey('education_stages.code'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    name_en = db.Column(db.String(50))
    grade_applicable = db.Column(db.String(50))  # 适用年级，如 "1,2,3" 或 "10,11,12"
    icon = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    knowledge_points = db.relationship('KnowledgePointEnhanced', backref='subject', lazy=True)
    lesson_plans = db.relationship('LessonPreparation', backref='subject', lazy=True)

class Textbook(db.Model):
    """教材表"""
    __tablename__ = 'textbooks'
    
    id = db.Column(db.Integer, primary_key=True)
    education_stage_code = db.Column(db.String(20), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    publisher = db.Column(db.String(100))  # 出版社
    edition = db.Column(db.String(50))  # 版本（如：人教版2019）
    grade = db.Column(db.String(20))  # 适用年级
    isbn = db.Column(db.String(20))
    cover_image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    chapters = db.relationship('TextbookChapter', backref='textbook', lazy=True, cascade='all, delete-orphan')

class TextbookChapter(db.Model):
    """教材章节表"""
    __tablename__ = 'textbook_chapters'
    
    id = db.Column(db.Integer, primary_key=True)
    textbook_id = db.Column(db.Integer, db.ForeignKey('textbooks.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('textbook_chapters.id'))  # 支持多级章节
    chapter_number = db.Column(db.String(20))  # 章节编号，如 "1.1", "2.3.1"
    title = db.Column(db.String(200), nullable=False)
    level = db.Column(db.Integer, default=1)  # 层级深度
    order_index = db.Column(db.Integer, default=0)
    knowledge_points = db.Column(db.Text)  # JSON格式的知识点列表
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 自引用关系
    children = db.relationship('TextbookChapter', backref=db.backref('parent', remote_side=[id]))

class KnowledgePointEnhanced(db.Model):
    """增强版知识点模型 - 支持知识图谱"""
    __tablename__ = 'knowledge_points_enhanced'
    
    id = db.Column(db.Integer, primary_key=True)
    education_stage_code = db.Column(db.String(20), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    textbook_id = db.Column(db.Integer, db.ForeignKey('textbooks.id'))
    chapter_id = db.Column(db.Integer, db.ForeignKey('textbook_chapters.id'))
    
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5难度等级
    bloom_level = db.Column(db.Integer)  # Bloom认知层次 1-6
    
    # 知识图谱关系
    prerequisites = db.Column(db.Text)  # JSON: 前置知识点ID列表
    dependents = db.Column(db.Text)  # JSON: 后续知识点ID列表
    interdisciplinary_links = db.Column(db.Text)  # JSON: 跨学科关联知识点
    
    # 多模态资源
    multimedia_resources = db.Column(db.Text)  # JSON: 多媒体资源ID列表
    real_life_examples = db.Column(db.Text)  # JSON: 现实生活案例ID列表
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class KnowledgeRelationship(db.Model):
    """知识点关系表 - 用于知识图谱"""
    __tablename__ = 'knowledge_relationships'
    
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('knowledge_points_enhanced.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('knowledge_points_enhanced.id'), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False)  # prerequisite, related, interdisciplinary
    strength = db.Column(db.Float, default=1.0)  # 关系强度 0-1
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('source_id', 'target_id', 'relation_type', name='uix_kr_source_target_type'),
    )

class MultimediaResource(db.Model):
    """多媒体资源表"""
    __tablename__ = 'multimedia_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    education_stage_code = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    resource_type = db.Column(db.String(20), nullable=False)  # video, audio, image, interactive, document
    url = db.Column(db.String(500))
    file_path = db.Column(db.String(500))
    thumbnail = db.Column(db.String(500))
    duration = db.Column(db.Integer)  # 视频/音频时长（秒）
    file_size = db.Column(db.Integer)  # 文件大小（字节）
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LifeExample(db.Model):
    """现实生活案例表"""
    __tablename__ = 'life_examples'
    
    id = db.Column(db.Integer, primary_key=True)
    education_stage_code = db.Column(db.String(20), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    knowledge_point_id = db.Column(db.Integer, db.ForeignKey('knowledge_points_enhanced.id'))
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    scenario = db.Column(db.Text)  # 应用场景描述
    difficulty_level = db.Column(db.Integer, default=1)
    multimedia_resources = db.Column(db.Text)  # JSON: 相关多媒体资源ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuestionBankEnhanced(db.Model):
    """增强版题库 - 支持知识体系化"""
    __tablename__ = 'question_bank_enhanced'
    
    id = db.Column(db.Integer, primary_key=True)
    education_stage_code = db.Column(db.String(20), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    knowledge_point_id = db.Column(db.Integer, db.ForeignKey('knowledge_points_enhanced.id'))
    
    question_type = db.Column(db.String(20), nullable=False)  # choice, fill-blank, essay, calculation
    difficulty_level = db.Column(db.Integer, default=1)
    bloom_level = db.Column(db.Integer)  # Bloom认知层次
    
    content = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)  # JSON: 选择题选项
    correct_answer = db.Column(db.Text)
    explanation = db.Column(db.Text)
    
    tags = db.Column(db.Text)  # JSON: 标签列表
    interdisciplinary = db.Column(db.Boolean, default=False)  # 是否跨学科
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LessonPreparation(db.Model):
    """备课表 - AI增强版"""
    __tablename__ = 'lesson_preparations'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    education_stage_code = db.Column(db.String(20), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    grade = db.Column(db.String(20))
    duration_minutes = db.Column(db.Integer)
    
    # AI生成的内容
    knowledge_graph_data = db.Column(db.Text)  # JSON: 知识图谱数据
    multimedia_suggestions = db.Column(db.Text)  # JSON: 多媒体建议
    life_examples = db.Column(db.Text)  # JSON: 生活案例
    interdisciplinary_design = db.Column(db.Text)  # JSON: 跨学科设计
    
    # 教案内容
    objectives = db.Column(db.Text)  # 教学目标
    teaching_process = db.Column(db.Text)  # 教学过程
    homework = db.Column(db.Text)  # 作业布置
    
    status = db.Column(db.String(20), default='draft')  # draft, reviewed, published
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Class(db.Model):
    """班级表"""
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    education_stage_code = db.Column(db.String(20), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    academic_year = db.Column(db.String(20))  # 学年，如 "2025-2026"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentProfile(db.Model):
    """学生档案表"""
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    education_stage_code = db.Column(db.String(20), nullable=False)
    grade = db.Column(db.String(20))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    
    student_number = db.Column(db.String(50))
    enrollment_date = db.Column(db.Date)
    guardian_name = db.Column(db.String(100))
    guardian_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeacherProfile(db.Model):
    """教师档案表"""
    __tablename__ = 'teacher_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    education_stage_code = db.Column(db.String(20), nullable=False)
    subjects = db.Column(db.Text)  # JSON: 教授科目ID列表
    qualifications = db.Column(db.Text)  # JSON: 资质证书
    biography = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GradeRecord(db.Model):
    """成绩记录表"""
    __tablename__ = 'grade_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exam_name = db.Column(db.String(200))
    score = db.Column(db.Float)
    max_score = db.Column(db.Float, default=100.0)
    grade_type = db.Column(db.String(20))  # midterm, final, quiz, assignment
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.Column(db.Text)

class AttendanceRecord(db.Model):
    """考勤记录表"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late, excused
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', 'date', name='uix_attendance_student_class_date'),
    )

class Notification(db.Model):
    """通知公告表"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    education_stage_code = db.Column(db.String(20))
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    notification_type = db.Column(db.String(50))  # announcement, homework, exam, event
    target_role = db.Column(db.String(20))  # student, teacher, parent, all
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_urgent = db.Column(db.Boolean, default=False)
    publish_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)

class SystemConfig(db.Model):
    """系统配置表"""
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(50), unique=True, nullable=False)
    config_value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==================== 安全增强模型 ====================

class AuditLog(db.Model):
    """审计日志表 - 记录所有关键操作"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)

    # 操作信息
    action_type = db.Column(db.String(50), nullable=False)  # login, logout, read, create, update, delete
    resource_type = db.Column(db.String(50))  # user, subject, lesson_plan 等
    resource_id = db.Column(db.Integer)  # 资源 ID

    # 用户信息
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 请求信息
    ip_address = db.Column(db.String(45))  # 支持 IPv6
    user_agent = db.Column(db.String(500))
    request_method = db.Column(db.String(10))
    request_path = db.Column(db.String(500))
    query_string = db.Column(db.Text)
    request_body = db.Column(db.Text)  # 仅记录非敏感数据

    # 响应信息
    response_status = db.Column(db.String(10))  # HTTP 状态码

    # 详细信息和状态
    details = db.Column(db.Text)  # JSON 格式的详细信息
    status = db.Column(db.String(20), default='success')  # success, failure, error, unauthorized
    duration_ms = db.Column(db.Integer)  # 执行耗时（毫秒）

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 性能优化索引
    __table_args__ = (
        db.Index('idx_audit_action', 'action_type'),
        db.Index('audit_user_idx', 'user_id'),
        db.Index('audit_resource', 'resource_type', 'resource_id'),
        db.Index('audit_created', 'created_at'),
        db.Index('audit_status', 'status'),
    )
