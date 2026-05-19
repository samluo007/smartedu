<template>
  <div id="app" class="app-container">
    <!-- 路由过渡动画 + Keep-Alive 缓存 -->
    <router-view v-slot="{ Component, route }">
      <transition :name="transitionName" mode="out-in" @after-leave="onTransitionEnd">
        <keep-alive :include="cachedViews" :max="5">
          <component
            :is="Component"
            :key="route.meta.keepAlive ? route.name : route.fullPath"
            v-if="!route.meta.keepAlive || isRouterAlive"
          />
        </keep-alive>
      </transition>
      <!-- 非 Keep-Alive 的路由（如版本选择页） -->
      <component
        :is="Component"
        v-if="!route.meta.keepAlive"
        :key="route.fullPath"
      />
    </router-view>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, provide } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// ==================== 页面切换过渡动画 ====================
// 根据路由深度判断动画方向
const transitionName = ref('fade')

watch(
  () => route.path,
  (to, from) => {
    // 深度比较：前进 slide-left，后退 slide-right，其他 fade
    const toDepth = to.split('/').length
    const fromDepth = from?.split('/').length || 0

    if (!from) {
      transitionName.value = 'fade'
    } else if (toDepth > fromDepth) {
      transitionName.value = 'slide-left'   // 进入子页面 → 左滑
    } else if (toDepth < fromDepth) {
      transitionName.value = 'slide-right'  // 返回上级 → 右滑
    } else {
      transitionName.value = 'fade'         // 同级切换 → 淡入淡出
    }
  }
)

// ==================== Keep-Alive 缓存管理 ====================
const cachedViews = computed(() => {
  // 从已访问的路由中筛选需要缓存的页面名
  return []
  // 实际使用时可通过全局状态管理缓存列表：
  // return store.state.cachedViews
})

const isRouterAlive = ref(true)
provide('reload', async () => {
  // 提供子组件调用 this.reload() 刷新当前页面（清除 Keep-Alive）
  isRouterAlive.value = false
  await nextTick()
  isRouterAlive.value = true
})

function onTransitionEnd() {
  // 动画结束后的清理工作（可扩展）
}

// ==================== 性能监控 ====================
if (process.env.NODE_ENV === 'development') {
  watch(
    () => route.name,
    (name) => {
      if (name) {
        const perf = performance.getEntriesByType('navigation')[0]
        console.log(`[SmartEdu] Route: ${name}, Load: ${(perf?.loadEventEnd - perf?.startTime).toFixed(0)}ms`)
      }
    }
  )
}
</script>

<style>
/* ==================== 全局样式重置 ==================== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, 'Noto Sans SC', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100%;
}

.app-container {
  height: 100%;
  width: 100%;
  overflow-x: hidden;
}

/* ==================== 过渡动画样式 ==================== */

/* 淡入淡出（默认） */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 左滑进入 */
.slide-left-enter-active {
  transition: all 0.3s ease-out;
}
.slide-left-leave-active {
  transition: all 0.2s ease-in;
}
.slide-left-enter-from {
  transform: translateX(30px);
  opacity: 0;
}
.slide-left-leave-to {
  transform: translateX(-20px);
  opacity: 0;
}

/* 右滑返回 */
.slide-right-enter-active {
  transition: all 0.3s ease-out;
}
.slide-right-leave-active {
  transition: all 0.2s ease-in;
}
.slide-right-enter-from {
  transform: translateX(-30px);
  opacity: 0;
}
.slide-right-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
