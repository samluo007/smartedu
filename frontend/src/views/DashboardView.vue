<template>
  <div class="dashboard-container">
    <!-- 顶部导航栏 -->
    <el-header class="header">
      <div class="header-left">
        <h1 class="logo">🎓 SmartEdu</h1>
        <el-tag type="success" size="small">{{ educationStage?.name || '未选择版本' }}</el-tag>
      </div>
      
      <div class="header-right">
        <el-button text @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          切换版本
        </el-button>
        <el-avatar :size="32">{{ userInitials }}</el-avatar>
      </div>
    </el-header>

    <!-- 侧边栏 -->
    <el-container class="main-container">
      <el-aside width="250px" class="sidebar">
        <el-menu
          :default-active="activeMenu"
          router
          background-color="#2c3e50"
          text-color="#ecf0f1"
          active-text-color="#3498db"
        >
          <el-menu-item index="/dashboard">
            <el-icon><DataLine /></el-icon>
            <span>控制台首页</span>
          </el-menu-item>
          
          <el-menu-item index="/lesson-preparation">
            <el-icon><EditPen /></el-icon>
            <span>智能备课</span>
          </el-menu-item>
          
          <el-sub-menu index="teaching">
            <template #title>
              <el-icon><Reading /></el-icon>
              <span>教学管理</span>
            </template>
            <el-menu-item index="/teaching/subjects">科目管理</el-menu-item>
            <el-menu-item index="/teaching/textbooks">教材管理</el-menu-item>
            <el-menu-item index="/teaching/knowledge-graph">知识图谱</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="assessment">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>测评系统</span>
            </template>
            <el-menu-item index="/assessment/question-bank">题库管理</el-menu-item>
            <el-menu-item index="/assessment/exams">考试管理</el-menu-item>
            <el-menu-item index="/assessment/grades">成绩管理</el-menu-item>
          </el-sub-menu>
          
          <el-menu-item index="/students">
            <el-icon><User /></el-icon>
            <span>学生管理</span>
          </el-menu-item>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <div class="welcome-section" v-if="route.path === '/dashboard'">
          <el-card class="welcome-card">
            <template #header>
              <div class="card-header">
                <h2>👋 欢迎使用 SmartEdu {{ educationStage?.name }}</h2>
              </div>
            </template>
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-card shadow="hover" class="stat-card">
                  <template #header>
                    <div class="stat-header">
                      <el-icon :size="24" color="#409EFF"><Reading /></el-icon>
                      <span>科目数量</span>
                    </div>
                  </template>
                  <div class="stat-content">
                    <span class="stat-number">{{ stats.subjects }}</span>
                    <span class="stat-label">个科目</span>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="8">
                <el-card shadow="hover" class="stat-card">
                  <template #header>
                    <div class="stat-header">
                      <el-icon :size="24" color="#67C23A"><User /></el-icon>
                      <span>学生数量</span>
                    </div>
                  </template>
                  <div class="stat-content">
                    <span class="stat-number">{{ stats.students }}</span>
                    <span class="stat-label">名学生</span>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="8">
                <el-card shadow="hover" class="stat-card">
                  <template #header>
                    <div class="stat-header">
                      <el-icon :size="24" color="#E6A23C"><Document /></el-icon>
                      <span>备课数量</span>
                    </div>
                  </template>
                  <div class="stat-content">
                    <span class="stat-number">{{ stats.lessonPlans }}</span>
                    <span class="stat-label">个教案</span>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            
            <el-divider />
            
            <div class="quick-actions">
              <h3>🚀 快速操作</h3>
              <el-row :gutter="15" class="action-buttons">
                <el-col :span="6" v-for="action in quickActions" :key="action.path">
                  <el-button 
                    class="action-btn"
                    @click="router.push(action.path)"
                    :color="action.color"
                    plain
                  >
                    <el-icon><component :is="action.icon" /></el-icon>
                    {{ action.name }}
                  </el-button>
                </el-col>
              </el-row>
            </div>
          </el-card>
        </div>
        
        <router-view v-else />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

const educationStage = ref(null)
const activeMenu = ref(route.path)
const stats = ref({
  subjects: 0,
  students: 0,
  lessonPlans: 0
})

const quickActions = ref([
  { name: '智能备课', path: '/lesson-preparation', icon: 'EditPen', color: '#409EFF' },
  { name: '知识图谱', path: '/teaching/knowledge-graph', icon: 'Share', color: '#67C23A' },
  { name: '题库管理', path: '/assessment/question-bank', icon: 'Document', color: '#E6A23C' },
  { name: '学生管理', path: '/students', icon: 'User', color: '#F56C6C' }
])

const userInitials = computed(() => {
  return '教师'  // 可以从 user 对象获取
})

const handleLogout = () => {
  localStorage.removeItem('selectedEducationStage')
  ElMessage.success('已退出当前版本')
  router.push('/version-selection')
}

const loadDashboardData = async () => {
  try {
    // 加载教育阶段信息
    const stageData = localStorage.getItem('selectedEducationStage')
    if (stageData) {
      educationStage.value = JSON.parse(stageData)
    }
    
    // 加载统计数据
    const stageCode = educationStage.value?.code
    if (stageCode) {
      const subjectsRes = await axios.get(`/api/subjects/${stageCode}`)
      stats.value.subjects = subjectsRes.data?.length || 0
    }
    
    // TODO: 加载其他统计数据
    stats.value.students = 128  // 模拟数据
    stats.value.lessonPlans = 24  // 模拟数据
    
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.logo {
  color: white;
  font-size: 1.5rem;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
  color: white;
}

.sidebar {
  background-color: #2c3e50;
  min-height: calc(100vh - 60px);
}

.sidebar .el-menu {
  border-right: none;
}

.main-container {
  min-height: calc(100vh - 60px);
}

.main-content {
  padding: 20px;
  background: #f5f7fa;
}

.welcome-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.card-header h2 {
  margin: 0;
  color: #303133;
}

.stat-card {
  border-radius: 10px;
  transition: all 0.3s ease;
  margin-bottom: 15px;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.stat-content {
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 0.9rem;
  color: #909399;
}

.quick-actions h3 {
  margin-bottom: 20px;
  color: #303133;
}

.action-buttons {
  margin-top: 15px;
}

.action-btn {
  width: 100%;
  height: 60px;
  font-size: 1rem;
}
</style>
