<template>
  <div class="version-selection-container">
    <div class="hero-section">
      <h1 class="main-title">🎓 SmartEdu 智慧教育系统</h1>
      <p class="subtitle">请选择您要使用的教育版本</p>
    </div>

    <div class="version-cards">
      <el-card 
        v-for="version in versions" 
        :key="version.code"
        class="version-card"
        :class="{ 'selected': selectedVersion === version.code }"
        @click="selectVersion(version)"
        shadow="hover"
      >
        <div class="card-content">
          <div class="icon-wrapper" :style="{ backgroundColor: version.color + '20' }">
            <span class="icon" :style="{ color: version.color }">{{ version.icon }}</span>
          </div>
          
          <h2 class="version-name">{{ version.name }}</h2>
          <p class="version-name-en">{{ version.nameEn }}</p>
          
          <div class="grade-range">
            <el-tag size="small" type="info">{{ version.gradeRange }}</el-tag>
          </div>
          
          <p class="description">{{ version.description }}</p>
          
          <div class="subjects-preview">
            <h4>主要科目：</h4>
            <div class="subject-tags">
              <el-tag 
                v-for="subject in version.subjects" 
                :key="subject"
                size="small"
                class="subject-tag"
              >
                {{ subject }}
              </el-tag>
            </div>
          </div>
          
          <el-button 
            type="primary" 
            class="select-btn"
            @click.stop="confirmSelection(version)"
            :style="{ backgroundColor: version.color, borderColor: version.color }"
          >
            选择此版本
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 确认对话框 -->
    <el-dialog
      v-model="showConfirmDialog"
      :title="`确认选择 - ${pendingSelection?.name}`"
      width="500px"
    >
      <div class="confirm-content">
        <el-result
          :icon="pendingSelection?.icon"
          :title="`即将进入 ${pendingSelection?.name}`"
          :sub-title="`适用年级：${pendingSelection?.gradeRange}`"
        >
          <template #extra>
            <p>系统将根据您选择的版本加载相应的：</p>
            <ul>
              <li>✅ 科目和课程</li>
              <li>✅ 教材和知识点</li>
              <li>✅ 题库和测试</li>
              <li>✅ AI 教学辅助功能</li>
            </ul>
          </template>
        </el-result>
      </div>
      
      <template #footer>
        <el-button @click="showConfirmDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleConfirmSelection"
          :loading="isLoading"
        >
          确认进入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const selectedVersion = ref('')
const showConfirmDialog = ref(false)
const isLoading = ref(false)
const pendingSelection = ref(null)

const versions = ref([
  {
    code: '9-year',
    name: '九年义务教育版',
    nameEn: '9-Year Compulsory Education',
    icon: '📚',
    color: '#409EFF',
    gradeRange: '小学1年级 - 初中9年级',
    description: '涵盖小学至初中全部课程，注重基础知识和综合素质培养',
    subjects: ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '道德与法治']
  },
  {
    code: 'high-school',
    name: '高中版',
    nameEn: 'High School Edition',
    icon: '🎯',
    color: '#67C23A',
    gradeRange: '高中1年级 - 高中3年级',
    description: '聚焦高考科目，强化知识点体系和应试能力培养',
    subjects: ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治']
  },
  {
    code: 'university',
    name: '高校版',
    nameEn: 'University Edition',
    icon: '🎓',
    color: '#E6A23C',
    gradeRange: '大学本科 - 研究生',
    description: '专业课程教育，支持跨学科教学和科研辅助',
    subjects: ['高等数学', '大学英语', '计算机科学', '物理学', '化学', '经济学', '管理学']
  }
])

const selectVersion = (version) => {
  selectedVersion.value = version.code
}

const confirmSelection = (version) => {
  pendingSelection.value = version
  showConfirmDialog.value = true
}

const handleConfirmSelection = async () => {
  if (!pendingSelection.value) return
  
  isLoading.value = true
  try {
    // 调用后端 API 设置版本
    const response = await axios.post('/api/version/select', {
      education_stage: pendingSelection.value.code
    })
    
    if (response.data) {
      ElMessage.success(`成功选择 ${pendingSelection.value.name}`)
      
      // 保存选择到 localStorage
      localStorage.setItem('selectedEducationStage', JSON.stringify({
        code: pendingSelection.value.code,
        name: pendingSelection.value.name,
        gradeRange: pendingSelection.value.gradeRange,
        selectedAt: new Date().toISOString()
      }))
      
      // 跳转到主界面
      setTimeout(() => {
        router.push('/dashboard')
      }, 1000)
    }
  } catch (error) {
    ElMessage.error('选择版本失败，请重试')
    console.error('Version selection error:', error)
  } finally {
    isLoading.value = false
    showConfirmDialog.value = false
  }
}

onMounted(() => {
  // 检查是否已经选择过版本
  const savedStage = localStorage.getItem('selectedEducationStage')
  if (savedStage) {
    const stageData = JSON.parse(savedStage)
    ElMessage.info(`当前已选择：${stageData.name}，正在跳转...`)
    setTimeout(() => {
      router.push('/dashboard')
    }, 1500)
  }
})
</script>

<style scoped>
.version-selection-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

.hero-section {
  text-align: center;
  margin-bottom: 50px;
  color: white;
}

.main-title {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
}

.version-cards {
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
  max-width: 1400px;
  margin: 0 auto;
}

.version-card {
  width: 380px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 15px;
  overflow: hidden;
}

.version-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 35px rgba(0,0,0,0.2);
}

.version-card.selected {
  border: 3px solid #409EFF;
}

.card-content {
  padding: 30px;
  text-align: center;
}

.icon-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.icon {
  font-size: 2.5rem;
}

.version-name {
  font-size: 1.8rem;
  font-weight: bold;
  margin-bottom: 5px;
  color: #303133;
}

.version-name-en {
  font-size: 0.9rem;
  color: #909399;
  margin-bottom: 15px;
}

.grade-range {
  margin-bottom: 15px;
}

.description {
  font-size: 0.95rem;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 20px;
}

.subjects-preview {
  text-align: left;
  margin-bottom: 20px;
}

.subjects-preview h4 {
  font-size: 0.9rem;
  color: #909399;
  margin-bottom: 10px;
}

.subject-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.subject-tag {
  margin: 2px;
}

.select-btn {
  width: 100%;
  height: 45px;
  font-size: 1.1rem;
  border-radius: 8px;
}

.confirm-content {
  text-align: center;
}

.confirm-content ul {
  text-align: left;
  margin-top: 20px;
  list-style: none;
  padding-left: 0;
}

.confirm-content li {
  margin-bottom: 10px;
  font-size: 1rem;
}

@media (max-width: 768px) {
  .version-cards {
    flex-direction: column;
    align-items: center;
  }
  
  .version-card {
    width: 90%;
  }
  
  .main-title {
    font-size: 2rem;
  }
}
</style>
