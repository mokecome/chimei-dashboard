<template>
  <aside class="app-sidebar" :class="{ 'collapsed': collapsed }">
    <!-- Logo区域 -->
    <div class="sidebar-header">
      <div class="logo-container">
        <div class="logo">
          <el-icon :size="collapsed ? 24 : 28" color="#fff">
            <TrendCharts />
          </el-icon>
        </div>
        <transition name="fade">
          <div v-show="!collapsed" class="logo-text">
            <h2>奇美食品</h2>
            <p>智能分析系統</p>
          </div>
        </transition>
      </div>
      
      <!-- 折叠按钮 -->
      <el-button 
        class="collapse-btn"
        circle 
        size="small"
        @click="toggleCollapse"
      >
        <el-icon>
          <Expand v-if="collapsed" />
          <Fold v-else />
        </el-icon>
      </el-button>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar-nav">
      <!-- 主要功能组 -->
      <div class="nav-group">
        <div v-show="!collapsed" class="nav-group-title">主要功能</div>
        
        <router-link 
          v-for="item in mainMenuItems" 
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ 'active': isActive(item.path) }"
          v-show="hasPermission(item.permission)"
        >
          <el-icon class="nav-icon">
            <component :is="item.icon" />
          </el-icon>
          <transition name="fade">
            <span v-show="!collapsed" class="nav-text">{{ item.name }}</span>
          </transition>
          <div v-if="item.badge && !collapsed" class="nav-badge">
            {{ item.badge }}
          </div>
        </router-link>
      </div>

      <!-- 设定管理组 -->
      <div class="nav-group">
        <div v-show="!collapsed" class="nav-group-title">數據管理</div>
        
        <router-link 
          v-for="item in settingMenuItems" 
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ 'active': isActive(item.path) }"
          v-show="hasPermission(item.permission)"
        >
          <el-icon class="nav-icon">
            <component :is="item.icon" />
          </el-icon>
          <transition name="fade">
            <span v-show="!collapsed" class="nav-text">{{ item.name }}</span>
          </transition>
        </router-link>
      </div>
    </nav>

    <!-- 底部用户信息 -->
    <div class="sidebar-footer">
      <div class="user-card" :class="{ 'collapsed': collapsed }">
        <el-avatar :size="collapsed ? 32 : 36" class="user-avatar">
          {{ userInitials }}
        </el-avatar>
        <transition name="fade">
          <div v-show="!collapsed" class="user-info">
            <div class="user-name">{{ authStore.user?.name }}</div>
            <div class="user-role">{{ getRoleName(authStore.user?.role) }}</div>
          </div>
        </transition>
        <transition name="fade">
          <el-icon v-show="!collapsed" class="dropdown-icon">
            <ArrowDown />
          </el-icon>
        </transition>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  TrendCharts,
  Expand,
  Fold,
  House,
  DataAnalysis,
  DataBoard,
  PriceTag,
  UserFilled,
  Setting,
  Document,
  ArrowDown
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { Permission, UserRole } from '@/utils/constants'

const route = useRoute()
const authStore = useAuthStore()

// 侧边栏折叠状态
const collapsed = ref(false)

// 主要功能菜单项
const mainMenuItems = [
  {
    path: '/dashboard',
    name: '營運洞察',
    icon: 'House',
    permission: Permission.DASHBOARD_VIEW,
    badge: null
  },
  {
    path: '/analysis',
    name: '數據分析',
    icon: 'DataAnalysis',
    permission: Permission.ANALYSIS_VIEW,
    badge: null
  }
]

// 数据管理菜单项
const settingMenuItems = [
  {
    path: '/datasource',
    name: '資料來源',
    icon: 'DataBoard',
    permission: Permission.DATASOURCE_VIEW
  },
  {
    path: '/labelsetting',
    name: '分類設定',
    icon: 'PriceTag',
    permission: Permission.LABELS_VIEW
  },
  {
    path: '/account',
    name: '帳號管理',
    icon: 'UserFilled',
    permission: Permission.ACCOUNT_MANAGE
  }
]

// 用户姓名首字母
const userInitials = computed(() => {
  const name = authStore.user?.name
  if (!name) return 'U'
  
  const chars = name.trim().split('')
  if (chars.length >= 2 && /[\u4e00-\u9fa5]/.test(chars[0])) {
    return chars.slice(0, 2).join('')
  } else {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
  }
})

// 角色名称映射
const getRoleName = (role?: string) => {
  const roleNames = {
    [UserRole.ADMIN]: '系統管理員',
    [UserRole.MANAGER]: '經理',
    [UserRole.OPERATOR]: '操作員',
    [UserRole.VIEWER]: '檢視員'
  }
  return roleNames[role as UserRole] || '用戶'
}

// 切换折叠状态
const toggleCollapse = () => {
  collapsed.value = !collapsed.value
}

// 检查菜单项是否激活
const isActive = (path: string) => {
  return route.path === path || route.path.startsWith(path + '/')
}

// 检查权限
const hasPermission = (permission?: string) => {
  if (!permission) return true
  return authStore.hasPermission(permission)
}
</script>

<style scoped>
.app-sidebar {
  width: 256px;
  min-height: 100vh;
  background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
  color: white;
  transition: width 0.3s ease;
  position: relative;
  display: flex;
  flex-direction: column;
}

.app-sidebar.collapsed {
  width: 80px;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo-text h2 {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  line-height: 1.2;
}

.logo-text p {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  line-height: 1.2;
}

.collapse-btn {
  position: absolute;
  top: 50%;
  right: -12px;
  transform: translateY(-50%);
  background: var(--primary-color);
  border: 2px solid white;
  z-index: 10;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}

.nav-group {
  margin-bottom: 24px;
}

.nav-group-title {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 0 20px 8px;
  font-weight: 500;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  transition: all 0.3s ease;
  position: relative;
  gap: 12px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  padding-left: 24px;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  font-weight: 500;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--secondary-color);
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.nav-text {
  flex: 1;
  font-size: 14px;
}

.nav-badge {
  background: var(--danger-color);
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.user-card:hover {
  background: rgba(255, 255, 255, 0.1);
}

.user-card.collapsed {
  justify-content: center;
}

.user-avatar {
  background: linear-gradient(135deg, var(--secondary-color) 0%, var(--accent-color) 100%);
  color: white;
  font-size: 14px;
  font-weight: 500;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: white;
  line-height: 1.2;
  margin-bottom: 2px;
}

.user-role {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.2;
}

.dropdown-icon {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 滚动条样式 */
.sidebar-nav::-webkit-scrollbar {
  width: 4px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 1000;
    height: 100vh;
    transform: translateX(-100%);
  }
  
  .app-sidebar.mobile-open {
    transform: translateX(0);
  }
}
</style>