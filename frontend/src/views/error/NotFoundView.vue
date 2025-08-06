<template>
  <div class="not-found-page">
    <div class="error-container">
      <div class="error-icon">
        <el-icon :size="80" color="#6b7280">
          <Warning />
        </el-icon>
      </div>
      
      <h1 class="error-title">404</h1>
      <h2 class="error-subtitle">頁面不存在</h2>
      <p class="error-description">
        抱歉，您訪問的頁面不存在或已被移除。
      </p>
      
      <div class="error-actions">
        <el-button type="primary" @click="goHome">
          返回首頁
        </el-button>
        <el-button @click="goBack">
          返回上頁
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Warning } from '@element-plus/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.not-found-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.error-container {
  text-align: center;
  background: white;
  padding: 60px 40px;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 100%;
  margin: 20px;
}

.error-icon {
  margin-bottom: 24px;
}

.error-title {
  font-size: 48px;
  font-weight: 700;
  color: #374151;
  margin: 0 0 8px;
}

.error-subtitle {
  font-size: 24px;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 16px;
}

.error-description {
  color: #9ca3af;
  margin-bottom: 32px;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

@media (max-width: 480px) {
  .error-container {
    padding: 40px 24px;
  }
  
  .error-title {
    font-size: 36px;
  }
  
  .error-subtitle {
    font-size: 20px;
  }
  
  .error-actions {
    flex-direction: column;
  }
}
</style>