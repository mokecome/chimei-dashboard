<template>
  <header class="app-header">
    <div class="header-content">
      <!-- 左侧标题和面包屑 -->
      <div class="header-left">
        <h1 class="page-title">{{ pageTitle }}</h1>
        <el-breadcrumb separator="/" class="breadcrumb">
          <el-breadcrumb-item 
            v-for="item in breadcrumbs" 
            :key="item.path"
            :to="item.path"
          >
            {{ item.name }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>

      <!-- 右侧操作区域 -->
      <div class="header-right">
        <!-- 筛选按钮 -->
        <el-button v-if="showFilter" @click="$emit('openFilter')">
          <el-icon><Filter /></el-icon>
          篩選
        </el-button>

        <!-- 导出按钮 -->
        <el-button v-if="showExport" type="primary" @click="$emit('export')">
          <el-icon><Download /></el-icon>
          匯出報表
        </el-button>

        <!-- 刷新按钮 -->
        <el-button v-if="showRefresh" circle @click="$emit('refresh')">
          <el-icon><Refresh /></el-icon>
        </el-button>

        <!-- 通知 -->
        <el-badge :value="notificationCount" :max="99" class="notification-badge">
          <el-button circle>
            <el-icon><Bell /></el-icon>
          </el-button>
        </el-badge>

        <!-- 用户菜单 -->
        <el-dropdown class="user-dropdown" @command="handleUserCommand">
          <div class="user-info">
            <el-avatar :size="32" :src="userAvatar" class="user-avatar">
              {{ userInitials }}
            </el-avatar>
            <div class="user-details">
              <span class="user-name">{{ authStore.user?.name }}</span>
              <span class="user-role">{{ getRoleName(authStore.user?.role) }}</span>
            </div>
            <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
          </div>
          
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>
                個人設定
              </el-dropdown-item>
              <el-dropdown-item command="settings" :disabled="!authStore.hasPermission('system:settings')">
                <el-icon><Setting /></el-icon>
                系統設定
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                登出
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Filter, 
  Download, 
  Refresh, 
  Bell, 
  User, 
  Setting, 
  SwitchButton,
  ArrowDown 
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { UserRole } from '@/utils/constants'

interface Props {
  pageTitle?: string
  showFilter?: boolean
  showExport?: boolean
  showRefresh?: boolean
  notificationCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  pageTitle: '',
  showFilter: false,
  showExport: false,
  showRefresh: true,
  notificationCount: 0
})

const emit = defineEmits<{
  openFilter: []
  export: []
  refresh: []
}>()

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 面包屑导航
const breadcrumbs = computed(() => {
  const pathSegments = route.path.split('/').filter(Boolean)
  const breadcrumbItems = []
  
  // 总是从首页开始
  breadcrumbItems.push({ name: '首頁', path: '/dashboard' })
  
  // 根据当前路径生成面包屑
  if (route.path !== '/dashboard') {
    const routeNames = {
      'analysis': '數據分析',
      'datasource': '資料來源',
      'labelsetting': '分類設定',
      'account': '帳號管理',
      'profile': '個人設定',
      'settings': '系統設定',
      'logs': '操作記錄',
      'export': '匯出報表'
    }
    
    pathSegments.forEach((segment, index) => {
      const routeName = routeNames[segment as keyof typeof routeNames]
      if (routeName) {
        const path = '/' + pathSegments.slice(0, index + 1).join('/')
        breadcrumbItems.push({ name: routeName, path })
      }
    })
  }
  
  return breadcrumbItems
})

// 用户头像和姓名首字母
const userAvatar = computed(() => {
  // 如果有头像URL，返回URL，否则返回undefined使用姓名首字母
  return undefined
})

const userInitials = computed(() => {
  const name = authStore.user?.name
  if (!name) return 'U'
  
  // 提取中文名字的第一个字符，或英文名字的首字母
  const chars = name.trim().split('')
  if (chars.length >= 2 && /[\u4e00-\u9fa5]/.test(chars[0])) {
    // 中文名取前两个字符
    return chars.slice(0, 2).join('')
  } else {
    // 英文名取首字母
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

// 处理用户菜单命令
const handleUserCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      await authStore.logout()
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.app-header {
  background: white;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
}

.header-left {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
  line-height: 1.2;
}

.breadcrumb {
  font-size: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.notification-badge {
  position: relative;
}

.user-dropdown {
  margin-left: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.user-info:hover {
  background-color: #f3f4f6;
}

.user-avatar {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
  color: white;
  font-size: 12px;
  font-weight: 500;
}

.user-details {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.2;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.user-role {
  font-size: 12px;
  color: #6b7280;
}

.dropdown-icon {
  color: #9ca3af;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .user-details {
    display: none;
  }
  
  .header-right {
    gap: 8px;
  }
}
</style>