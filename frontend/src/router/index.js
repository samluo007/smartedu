import { createRouter, createWebHistory } from 'vue-router'

// ==================== 路由懒加载（代码分割）====================
// 使用动态 import() 实现，Vite 自动生成独立 chunk
// 首屏只加载 VersionSelectionView，其他页面按需加载
const VersionSelectionView = () => import('@/views/VersionSelectionView.vue')
const DashboardView = () => import('@/views/DashboardView.vue')
const LessonPreparationView = () => import('@/views/LessonPreparationView.vue')

// 预加载常驻页面（浏览器空闲时静默下载）
const preloadableViews = {
  Dashboard: () => import('@/views/DashboardView.vue'),
  LessonPreparation: () => import('@/views/LessonPreparationView.vue'),
}

const routes = [
  {
    path: '/',
    redirect: '/version-selection'
  },
  {
    path: '/version-selection',
    name: 'VersionSelection',
    component: VersionSelectionView,
    meta: {
      title: '选择教育版本 - SmartEdu',
      requiresVersion: false,
      // 入口页不缓存
      keepAlive: false
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: {
      title: '控制台 - SmartEdu',
      requiresVersion: true,
      keepAlive: true,
      // 预加载权重：用户选择版本后最可能进入此页
      preload: true
    }
  },
  {
    path: '/lesson-preparation',
    name: 'LessonPreparation',
    component: LessonPreparationView,
    meta: {
      title: '智能备课 - SmartEdu',
      requiresVersion: true,
      keepAlive: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/version-selection'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,

  // 滚动行为：路由切换时恢复滚动位置
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    } else {
      return { top: 0 }
    }
  }
})

// 全局路由守卫 - 检查是否已选择教育版本 + 触发预加载
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title || 'SmartEdu 智慧教育系统'

  // 检查是否需要版本选择
  if (to.meta.requiresVersion) {
    const savedStage = localStorage.getItem('selectedEducationStage')
    if (!savedStage) {
      ElMessage.warning('请先选择教育版本')
      next('/version-selection')
      return
    }
  }

  next()
})

// 路由切换后触发预加载（利用 requestIdleCallback 空闲时间）
router.afterEach((to) => {
  if (to.meta.preload || process.env.NODE_ENV === 'production') {
    // 浏览器空闲时预加载其他常驻页面
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        Object.entries(preloadableViews).forEach(([name, loader]) => {
          if (name !== to.name) {
            loader() // 触发 chunk 下载但不渲染
          }
        })
      })
    }
  }
})

export default router
