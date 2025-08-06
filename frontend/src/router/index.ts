import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Permission } from '@/utils/constants'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 登录页面
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: {
        layout: 'auth',
        requiresAuth: false
      }
    },
    
    // 主要应用路由
    {
      path: '/',
      redirect: '/dashboard',
      component: () => import('@/components/layout/MainLayout.vue'),
      meta: {
        requiresAuth: true
      },
      children: [
        // 仪表板
        {
          path: '/dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
          meta: {
            title: '營運洞察',
            permission: Permission.DASHBOARD_VIEW
          }
        },
        
        // 数据分析
        {
          path: '/analysis',
          name: 'Analysis',
          component: () => import('@/views/analysis/AnalysisView.vue'),
          meta: {
            title: '數據分析',
            permission: Permission.ANALYSIS_VIEW
          }
        },
        
        
        // 分析详情
        {
          path: '/analysis/detail/:id',
          name: 'AnalysisDetail',
          component: () => import('@/views/analysis/AnalysisDetailView.vue'),
          meta: {
            title: '分析詳細',
            permission: Permission.ANALYSIS_VIEW
          }
        },
        
        // 资料来源管理
        {
          path: '/datasource',
          name: 'DataSource',
          component: () => import('@/views/datasource/DataSourceView.vue'),
          meta: {
            title: '資料來源管理',
            permission: Permission.DATASOURCE_VIEW
          }
        },
        
        // 资料来源详情
        {
          path: '/datasource/detail/:id',
          name: 'DataSourceDetail',
          component: () => import('@/views/datasource/DataSourceDetailView.vue'),
          meta: {
            title: '檔案詳細',
            permission: Permission.DATASOURCE_VIEW
          }
        },
        
        // 分类设定
        {
          path: '/labelsetting',
          name: 'LabelSetting',
          component: () => import('@/views/label/LabelSettingView.vue'),
          meta: {
            title: '分類設定',
            permission: Permission.LABELS_VIEW
          }
        },
        
        // 账号管理
        {
          path: '/account',
          name: 'Account',
          component: () => import('@/views/account/AccountManagementView.vue'),
          meta: {
            title: '帳號權限管理',
            permission: Permission.ACCOUNT_MANAGE
          }
        },
        
      ]
    },
    
    // 404 页面
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/error/NotFoundView.vue'),
      meta: {
        layout: 'error'
      }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 初始化认证状态
  if (!authStore.isAuthenticated && localStorage.getItem('auth_token')) {
    await authStore.initializeAuth()
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
    return
  }
  
  // 如果已登录且访问登录页，重定向到首页
  if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
    return
  }
  
  // 检查权限
  if (to.meta.permission && !authStore.hasPermission(to.meta.permission as string)) {
    // 可以跳转到无权限页面或返回首页
    next('/dashboard')
    return
  }
  
  next()
})

// 路由后置守卫 - 更新页面标题
router.afterEach((to) => {
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - 奇美食品智能分析系統`
  } else {
    document.title = '奇美食品智能分析系統'
  }
})

export default router