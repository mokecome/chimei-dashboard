import axios from 'axios'
import type { AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { API_BASE_URL, AUTH_TOKEN_KEY } from '@/utils/constants'

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          localStorage.removeItem(AUTH_TOKEN_KEY)
          localStorage.removeItem('user_info')
          window.location.href = '/login'
          ElMessage.error('登入已過期，請重新登入')
          break
        case 403:
          ElMessage.error('權限不足')
          break
        case 404:
          // 對於 insights API 和 analysis result 的 404 錯誤，不顯示錯誤消息（因為有備用方案）
          if (!error.config.url?.includes('/analysis/insights') && 
              !error.config.url?.includes('/analysis/result/')) {
            ElMessage.error('請求的資源不存在')
          }
          break
        case 422:
          // 驗證錯誤，顯示詳細錯誤訊息
          const errorDetail = data?.detail
          if (Array.isArray(errorDetail)) {
            const messages = errorDetail.map(err => err.msg || err.message).join(', ')
            ElMessage.error(`驗證錯誤: ${messages}`)
          } else if (typeof errorDetail === 'string') {
            ElMessage.error(`驗證錯誤: ${errorDetail}`)
          } else {
            ElMessage.error(data?.message || '請求資料格式錯誤')
          }
          break
        case 500:
          ElMessage.error('伺服器內部錯誤')
          break
        default:
          ElMessage.error(data?.message || '請求失敗')
      }
    } else {
      ElMessage.error('網路連線錯誤')
    }
    
    return Promise.reject(error)
  }
)

export default api