# SmartEdu 统一智慧教育系统

支持版本：九年义务教育 | 高中版 | 高校版

## 📋 项目介绍

SmartEdu 是一个面向多教育阶段的智能教学管理系统，支持：
- 🏫 九年义务教育阶段（小学1年级 - 初中9年级）
- 🎯 高中版（高中1年级 - 高中3年级）
- 🎓 高校版（大学本科 - 研究生）

## ✨ 核心功能

### 1. 多版本支持
- 统一数据库设计，支持三个教育阶段
- 用户登录后选择对应版本
- 数据和功能按版本隔离

### 2. 智能备课系统
- AI 驱动的知识图谱生成
- 跨学科教学建议
- 多媒体资源推荐
- 现实生活案例库

### 3. 知识图谱
- 可视化知识点关联
- 前置知识点分析
- 跨学科知识链接

### 4. 增强题库
- 支持 Bloom 认知层次标注
- 知识点关联
- 跨学科题目标记

## 🚀 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python init_db.py
python app.py
```

后端运行在：http://localhost:5000

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端运行在：http://localhost:3000

## 📁 项目结构

```
SmartEdu/
├── backend/
│   ├── models.py              # 数据库模型
│   ├── app.py                # 主应用
│   ├── api/
│   │   └── unified_api.py   # 统一 API
│   └── ai_services/         # AI 服务
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── VersionSelectionView.vue  # 版本选择页
│   │   │   └── DashboardView.vue        # 控制台
│   │   ├── router/
│   │   │   └── index.js      # 路由配置
│   │   └── main.js           # 入口文件
│   └── package.json
├── docs/
│   ├── init_unified_db.py   # 数据库初始化脚本
│   └── API文档.md
└── README.md
```

## 🎯 使用流程

1. **启动系统** → 访问 http://localhost:3000
2. **选择版本** → 九年义务教育 / 高中版 / 高校版
3. **进入控制台** → 查看统计数据和快速操作
4. **使用功能** → 智能备课、知识图谱、题库管理等

## 📊 数据库设计

### 核心表结构

- `education_stages` - 教育阶段配置
- `subjects` - 科目表（按教育阶段分类）
- `textbooks` - 教材表
- `knowledge_points_enhanced` - 增强版知识点
- `lesson_preparations` - 备课表
- `question_bank_enhanced` - 增强题库

所有核心表都包含 `education_stage_code` 字段，实现数据按版本隔离。

## 🔧 API 端点

### 教育阶段
- `GET /api/education-stages` - 获取所有教育阶段
- `GET /api/education-stages/<code>` - 获取阶段详情
- `POST /api/version/select` - 选择教育版本

### 科目
- `GET /api/subjects?education_stage=9-year` - 按版本获取科目

### 备课
- `POST /api/lesson-plan/generate-enhanced` - 生成 AI 教案
- `GET /api/lesson-plans?education_stage=9-year` - 获取备课列表

### 知识图谱
- `GET /api/knowledge-graph/<subject_id>` - 获取知识图谱数据

## 🛠️ 技术栈

### 后端
- Flask 2.3+
- SQLAlchemy 2.0+
- SQLite（开发）/ PostgreSQL（生产）

### 前端
- Vue 3
- TypeScript
- Element Plus
- Vue Router

### AI 集成
- DeepSeek API（知识图谱生成）
- 支持自定义 AI 模型接入

## 📝 开发计划

- [x] 多版本支持（九年义务教育/高中/高校）
- [x] 版本选择入口
- [x] 统一数据库设计
- [x] 智能备课系统
- [ ] 知识图谱可视化（D3.js / ECharts）
- [ ] AI 教案生成优化
- [ ] 多媒体资源管理
- [ ] 学生成绩分析
- [ ] 移动端适配

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**开发者**：SmartEdu Team  
**最后更新**：2026-05-19
