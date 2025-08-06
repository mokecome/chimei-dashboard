<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="wave"></div>
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
      </div>
    </div>

    <!-- 登录表单 -->
    <div class="login-container">
      <!-- Logo 和标题 -->
      <div class="login-header">
        <div class="logo">
          <el-icon :size="40" color="#fff">
            <TrendCharts />
          </el-icon>
        </div>
        <h1>歡迎回來</h1>
        <p>登入奇美食品智能分析系統</p>
      </div>

      <!-- 错误消息 -->
      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        class="error-alert"
      />

      <!-- 登录表单 -->
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <!-- 账号输入 -->
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="請輸入帳號"
            size="large"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <!-- 密码输入 -->
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="請輸入密碼"
            size="large"
            :prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <!-- 记住我和忘记密码 -->
        <div class="login-options">
          <el-checkbox v-model="loginForm.rememberMe">
            記住我的帳號
          </el-checkbox>
          <el-button type="primary" link>
            忘記密碼？
          </el-button>
        </div>

        <!-- 登录按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="authStore.loading"
            @click="handleLogin"
          >
            <span v-if="!authStore.loading">登入系統</span>
            <span v-else>登入中...</span>
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 页脚 -->
      <div class="login-footer">
        <p>© 2025 奇美食品股份有限公司</p>
        <p>需要協助？請聯繫 <el-button type="primary" link>support@chimei.com</el-button></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, TrendCharts } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import type { LoginRequest } from '@/types/auth'

const router = useRouter()
const authStore = useAuthStore()

// 表单引用
const loginFormRef = ref<FormInstance>()

// 错误消息
const errorMessage = ref('')

// 登录表单数据
const loginForm = reactive<LoginRequest>({
  username: '',
  password: '',
  rememberMe: false
})

// 表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '請輸入帳號', trigger: 'blur' },
    { min: 3, max: 50, message: '帳號長度應在 3-50 個字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '請輸入密碼', trigger: 'blur' },
    { min: 6, message: '密碼長度不能少於 6 個字符', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    errorMessage.value = ''
    
    await authStore.login(loginForm)
    
    // 登录成功后跳转
    const redirect = (router.currentRoute.value.query.redirect as string) || '/dashboard'
    router.push(redirect)
  } catch (error: any) {
    console.error('Login error:', error)
    if (error.response?.data?.message) {
      errorMessage.value = error.response.data.message
    } else {
      errorMessage.value = '登入失敗，請檢查帳號密碼'
    }
  }
}


// 组件挂载时的操作
onMounted(() => {
  // 如果已经登录，直接跳转到首页
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
    return
  }

  // 读取记住的用户名
  const rememberedUsername = localStorage.getItem('remembered_username')
  if (rememberedUsername) {
    loginForm.username = rememberedUsername
    loginForm.rememberMe = true
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
}

.wave {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 100px;
  background: url('data:image/svg+xml;utf8,<svg viewBox="0 0 1200 120" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg"><path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z" style="fill:white;opacity:0.3"></path></svg>');
  background-size: cover;
}

.floating-shapes {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.shape {
  position: absolute;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  top: 10%;
  left: 10%;
  width: 80px;
  height: 80px;
  animation-delay: 0s;
}

.shape-2 {
  bottom: 10%;
  right: 10%;
  width: 128px;
  height: 128px;
  animation-delay: 2s;
}

.shape-3 {
  top: 50%;
  right: 20%;
  width: 64px;
  height: 64px;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
    opacity: 0.7;
  }
  50% {
    transform: translateY(-20px);
    opacity: 1;
  }
}

.login-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  margin: 20px;
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
  border-radius: 50%;
  margin-bottom: 16px;
}

.login-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 8px;
}

.login-header p {
  color: #6b7280;
  font-size: 14px;
}

.error-alert {
  margin-bottom: 20px;
}

.login-form {
  margin-bottom: 24px;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
  border: none;
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -5px rgba(139, 92, 246, 0.5);
}


.login-footer {
  text-align: center;
  margin-top: 32px;
  font-size: 12px;
  color: #6b7280;
}

.login-footer p {
  margin-bottom: 4px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-container {
    margin: 10px;
    padding: 24px;
  }
  
  .login-header h1 {
    font-size: 24px;
  }
}
</style>