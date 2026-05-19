# SmartEdu 统一教育系统 - 数据库初始化脚本
# 支持版本：九年义务教育、高中、高校

import sqlite3
import json
from datetime import datetime

def init_unified_database(db_path='smartedu_unified.db'):
    """
    初始化统一数据库
    包含三个教育阶段的基础数据
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"🚀 开始初始化 SmartEdu 统一数据库: {db_path}")
    
    # 创建教育阶段表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS education_stages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        name_en TEXT,
        description TEXT,
        grade_range TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 插入教育阶段数据
    education_stages = [
        ('9-year', '九年义务教育', '9-Year Compulsory Education', 
         '小学一年级至初中九年级（Grade 1-9）', '1-9', 1),
        ('high-school', '高中版', 'High School',
         '高中一年级至三年级（Grade 10-12）', '10-12', 1),
        ('university', '高校版', 'University',
         '大学本科及研究生教育（Grade 13+）', '13+', 1)
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO education_stages 
    (code, name, name_en, description, grade_range, is_active)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', education_stages)
    
    print("✅ 教育阶段数据初始化完成")
    
    # 创建科目表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        education_stage_code TEXT NOT NULL,
        name TEXT NOT NULL,
        name_en TEXT,
        grade_applicable TEXT,
        icon TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (education_stage_code) REFERENCES education_stages(code)
    )
    ''')
    
    # 插入科目数据
    subjects_data = [
        # 九年义务教育阶段
        ('9-year', '语文', 'Chinese', '1,2,3,4,5,6,7,8,9', '📖'),
        ('9-year', '数学', 'Mathematics', '1,2,3,4,5,6,7,8,9', '📐'),
        ('9-year', '英语', 'English', '3,4,5,6,7,8,9', '🔤'),
        ('9-year', '物理', 'Physics', '8,9', '⚛️'),
        ('9-year', '化学', 'Chemistry', '9', '🧪'),
        ('9-year', '生物', 'Biology', '7,8,9', '🧬'),
        ('9-year', '历史', 'History', '7,8,9', '📜'),
        ('9-year', '地理', 'Geography', '7,8,9', '🌍'),
        ('9-year', '道德与法治', 'Morality & Law', '1,2,3,4,5,6,7,8,9', '⚖️'),
        
        # 高中阶段
        ('high-school', '语文', 'Chinese', '10,11,12', '📖'),
        ('high-school', '数学', 'Mathematics', '10,11,12', '📐'),
        ('high-school', '英语', 'English', '10,11,12', '🔤'),
        ('high-school', '物理', 'Physics', '10,11,12', '⚛️'),
        ('high-school', '化学', 'Chemistry', '10,11,12', '🧪'),
        ('high-school', '生物', 'Biology', '10,11,12', '🧬'),
        ('high-school', '历史', 'History', '10,11,12', '📜'),
        ('high-school', '地理', 'Geography', '10,11,12', '🌍'),
        ('high-school', '政治', 'Politics', '10,11,12', '⚖️'),
        
        # 高校阶段
        ('university', '高等数学', 'Advanced Mathematics', '13,14,15,16', '📐'),
        ('university', '大学英语', 'College English', '13,14,15,16', '🔤'),
        ('university', '计算机科学', 'Computer Science', '13,14,15,16', '💻'),
        ('university', '物理学', 'Physics', '13,14,15,16', '⚛️'),
        ('university', '化学', 'Chemistry', '13,14,15,16', '🧪'),
        ('university', '生物学', 'Biology', '13,14,15,16', '🧬'),
        ('university', '经济学', 'Economics', '13,14,15,16', '💰'),
        ('university', '管理学', 'Management', '13,14,15,16', '📊')
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO subjects
    (education_stage_code, name, name_en, grade_applicable, icon, is_active)
    VALUES (?, ?, ?, ?, ?, 1)
    ''', subjects_data)
    
    print("✅ 科目数据初始化完成")
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        role TEXT NOT NULL,
        education_stage TEXT DEFAULT '9-year',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建教材表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS textbooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        education_stage_code TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        publisher TEXT,
        edition TEXT,
        grade TEXT,
        isbn TEXT,
        cover_image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    )
    ''')
    
    # 创建知识点表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge_points_enhanced (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        education_stage_code TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        textbook_id INTEGER,
        chapter_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        difficulty_level INTEGER DEFAULT 1,
        bloom_level INTEGER,
        prerequisites TEXT,
        dependents TEXT,
        interdisciplinary_links TEXT,
        multimedia_resources TEXT,
        real_life_examples TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    )
    ''')
    
    # 创建备课表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lesson_preparations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER NOT NULL,
        education_stage_code TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        grade TEXT,
        duration_minutes INTEGER,
        knowledge_graph_data TEXT,
        multimedia_suggestions TEXT,
        life_examples TEXT,
        interdisciplinary_design TEXT,
        objectives TEXT,
        teaching_process TEXT,
        homework TEXT,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (teacher_id) REFERENCES users(id),
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    )
    ''')
    
    # 创建题库表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question_bank_enhanced (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        education_stage_code TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        knowledge_point_id INTEGER,
        question_type TEXT NOT NULL,
        difficulty_level INTEGER DEFAULT 1,
        bloom_level INTEGER,
        content TEXT NOT NULL,
        options TEXT,
        correct_answer TEXT,
        explanation TEXT,
        tags TEXT,
        interdisciplinary BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print("🎉 数据库初始化完成！")
    print(f"📊 数据统计：")
    print(f"   - 教育阶段：{len(education_stages)} 个")
    print(f"   - 科目：{len(subjects_data)} 个")
    print(f"   - 数据表：已创建教育阶段、科目、用户、教材、知识点、备课、题库等表")
    print(f"\n✨ 系统支持：九年义务教育、高中、高校 三个版本")

if __name__ == '__main__':
    init_unified_database()
