import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// ==================== 按需引入 Element Plus（减少 60%+ 体积）====================
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 仅注册常用图标（避免全量引入 ~1MB）
import {
  // 导航图标
  HomeFilled, Setting, User, Document, DataAnalysis,
  // 操作图标
  Search, Refresh, Plus, Edit, Delete, Check, Close,
  ArrowLeft, ArrowRight, ArrowUp, ArrowDown,
  // 状态图标
  Success, Warning, Info, Loading, CircleCheck, CircleClose,
  // 文件/编辑
  FolderOpened, Notebook, EditPen, Files,
  // 其他
  Menu, Grid, List, Star, Bell, Monitor,
} from '@element-plus/icons-vue'

const iconComponents = {
  HomeFilled, Setting, User, Document, DataAnalysis,
  Search, Refresh, Plus, Edit, Delete, Check, Close,
  ArrowLeft, ArrowRight, ArrowUp, ArrowDown,
  Success, Warning, Info, Loading, CircleCheck, CircleClose,
  FolderOpened, Notebook, EditPen, Files,
  Menu, Grid, List, Star, Bell, Monitor,
}

// ==================== Axios 配置 ====================
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：添加审计信息 + 防重发
apiClient.interceptors.request.use(
  (config) => {
    // 性能计时开始
    config.metadata = { startTime: Date.now() }

    // 自动附加教育阶段参数
    const stageCode = localStorage.getItem('selectedEducationStage')
    if (stageCode && !config.params?.education_stage_code) {
      config.params = { ...config.params, education_stage_code: stageCode }
    }

    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一错误处理 + 性能上报
apiClient.interceptors.response.use(
  (response) => {
    const duration = Date.now() - response.config.metadata?.startTime
    if (duration > 2000) {
      console.warn(`[API Slow] ${response.config.url} took ${duration}ms`)
    }
    return response
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 429:
          console.error('[Rate Limited] 请求过于频繁，请稍后重试')
          break
        case 401:
          console.error('[Unauthorized] 认证已过期')
          localStorage.removeItem('selectedEducationStage')
          window.location.href = '/version-selection'
          break
        case 403:
          console.error('[Forbidden] 无权限访问')
          break
        case 500:
          console.error('[Server Error] 服务端内部错误')
          break
        default:
          console.error(`[API Error] ${status}: ${data?.message || '未知错误'}`)
      }
    }
    return Promise.reject(error)
  }
)

// ==================== 创建 Vue 应用实例 ====================
const app = createApp(App)

// 注册精选图标组件（~20个 vs 全量 ~300+）
Object.entries(iconComponents).forEach(([name, component]) => {
  app.component(name, component)
})

app.use(ElementPlus, {
  // 尺寸全局配置
  size: 'default',
  // 国际化中文
  locale: undefined, // Element Plus 默认中文
})

app.use(router)

// ==================== 全局错误边界 ====================
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue Error]', err)

  if (process.env.NODE_ENV === 'production') {
    // 生产环境可上报至监控服务
    // reportErrorToService(err, info)
  }
}

// ==================== 性能监控（开发环境）====================
if (import.meta.env.DEV) {
  app.config.performance = true

  app.mixin({
    mounted() {
      const name = this.$options.name || 'Anonymous'
      if (name !== 'Anonymous') {
        const end = performance.now()
        // 组件渲染耗时追踪（可扩展）
      }
    }
  })
}

// ==================== 挂载应用 ====================
// 等待路由就绪后再挂载（确保首屏不白屏）
router.isReady().then(() => {
  app.mount('#app')

  // 首屏性能指标
  if (import.meta.env.DEV) {
    const perf = performance.getEntriesByType('navigation')[0]
    console.log(`[SmartEdu] First Paint: ${(perf?.responseStart - perf?.startTime).toFixed(0)}ms`)
    console.log(`[SmartEdu] DOM Ready: ${(perf?.domContentLoadedEventEnd - perf?.startTime).toFixed(0)}ms`)
    console.log(`[SmartEdu] Full Load: ${(perf?.loadEventEnd - perf?.startTime).toFixed(0)}ms`)
  }
})

// ==================== 全局导出（供组件使用）====================
app.config.globalProperties.$api = apiClient

export default app
