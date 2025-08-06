<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <AppSidebar />
    
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 页面内容 -->
      <main class="page-content">
        <router-view v-slot="{ Component, route }">
          <transition name="page" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- 移动端遮罩 -->
    <div 
      v-if="showMobileMask"
      class="mobile-mask"
      @click="closeMobileSidebar"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import AppSidebar from './AppSidebar.vue'

// 移动端相关状态
const showMobileMask = ref(false)
const isMobile = ref(false)

// 检查是否为移动端
const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
}

// 关闭移动端侧边栏
const closeMobileSidebar = () => {
  showMobileMask.value = false
}

// 生命周期
onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  background-color: var(--light-bg);
}

.main-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.page-content {
  height: 100vh;
  overflow-y: auto;
  background-color: var(--light-bg);
}

.mobile-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: none;
}

/* 页面切换动画 */
.page-enter-active,
.page-leave-active {
  transition: all 0.3s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .mobile-mask {
    display: block;
  }
}

/* 自定义滚动条 */
.page-content::-webkit-scrollbar {
  width: 6px;
}

.page-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.page-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.page-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>