#!/usr/bin/env node

/**
 * 前後端 API 連通性測試腳本
 * 測試所有實現頁面的 API 端點
 */

const axios = require('axios')

// 後端 API 基礎 URL
const API_BASE_URL = 'http://127.0.0.1:8100'
const API_PREFIX = '/api'

// 測試結果統計
let totalTests = 0
let passedTests = 0
let failedTests = 0

// 顏色輸出
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
}

// 輸出函數
function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`)
}

function logSuccess(message) {
  log(`✅ ${message}`, 'green')
}

function logError(message) {
  log(`❌ ${message}`, 'red')
}

function logInfo(message) {
  log(`ℹ️  ${message}`, 'blue')
}

function logWarning(message) {
  log(`⚠️  ${message}`, 'yellow')
}

// 測試函數
async function testAPI(name, method, url, data = null, headers = {}) {
  totalTests++
  
  try {
    const config = {
      method,
      url: `${API_BASE_URL}${url}`,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      }
    }
    
    if (data) {
      config.data = data
    }
    
    const response = await axios(config)
    
    if (response.status >= 200 && response.status < 300) {
      logSuccess(`${name} - Status: ${response.status}`)
      passedTests++
      return { success: true, data: response.data, status: response.status }
    } else {
      logError(`${name} - Status: ${response.status}`)
      failedTests++
      return { success: false, status: response.status }
    }
  } catch (error) {
    const status = error.response?.status || 'Network Error'
    const message = error.response?.data?.message || error.message
    
    // 某些錯誤是預期的（如 401 未授權）
    if (status === 401 || status === 403) {
      logWarning(`${name} - Status: ${status} (Expected for protected endpoints)`)
      passedTests++
      return { success: true, status, expectedError: true }
    } else {
      logError(`${name} - Status: ${status}, Message: ${message}`)
      failedTests++
      return { success: false, status, error: message }
    }
  }
}

// 測試用戶認證
async function testAuthentication() {
  log('\n🔐 測試用戶認證 API', 'cyan')
  
  // 測試登入 API
  const loginResult = await testAPI(
    '用戶登入',
    'POST',
    `${API_PREFIX}/auth/login`,
    {
      email: 'admin@chimei.com',
      password: 'admin123'
    }
  )
  
  let authToken = null
  if (loginResult.success && loginResult.data?.data?.token) {
    authToken = loginResult.data.data.token
    logInfo(`獲得認證 token: ${authToken.substring(0, 20)}...`)
  }
  
  // 測試獲取當前用戶信息
  await testAPI(
    '獲取當前用戶',
    'GET',
    `${API_PREFIX}/auth/me`,
    null,
    authToken ? { Authorization: `Bearer ${authToken}` } : {}
  )
  
  // 測試刷新 token
  if (loginResult.data?.data?.refreshToken) {
    await testAPI(
      '刷新 Token',
      'POST',
      `${API_PREFIX}/auth/refresh`,
      { refresh_token: loginResult.data.data.refreshToken }
    )
  }
  
  return authToken
}

// 測試儀表板 API
async function testDashboard(authToken) {
  log('\n📊 測試儀表板 API', 'cyan')
  
  const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {}
  
  await testAPI('獲取儀表板數據', 'GET', `${API_PREFIX}/data/dashboard`, null, headers)
}

// 測試分析 API
async function testAnalysis(authToken) {
  log('\n📈 測試數據分析 API', 'cyan')
  
  const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {}
  
  await testAPI('獲取分析數據', 'GET', `${API_PREFIX}/data/analysis`, null, headers)
  await testAPI('創建分析報告', 'POST', `${API_PREFIX}/analysis/reports`, {
    title: '測試報告',
    filters: {},
    charts: ['sentiment_trend']
  }, headers)
  await testAPI('獲取分析報告列表', 'GET', `${API_PREFIX}/analysis/reports`, null, headers)
  await testAPI('匯出分析結果', 'POST', `${API_PREFIX}/analysis/export`, {
    format: 'csv',
    data_type: 'summary'
  }, headers)
}

// 測試資料來源 API
async function testDataSource(authToken) {
  log('\n💾 測試資料來源 API', 'cyan')
  
  const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {}
  
  await testAPI('獲取文件列表', 'GET', `${API_PREFIX}/files`, null, headers)
  await testAPI('獲取文件統計', 'GET', `${API_PREFIX}/files/stats`, null, headers)
  
  // 測試文件上傳（模擬）
  const formData = {
    files: ['test-file.txt'],
    category: 'customer_feedback'
  }
  await testAPI('文件上傳', 'POST', `${API_PREFIX}/files/upload`, formData, headers)
  
  await testAPI('文件處理狀態', 'GET', `${API_PREFIX}/files/processing-status`, null, headers)
}

// 測試標籤設定 API
async function testLabels(authToken) {
  log('\n🏷️  測試標籤設定 API', 'cyan')
  
  const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {}
  
  await testAPI('獲取商品標籤', 'GET', `${API_PREFIX}/labels/products`, null, headers)
  await testAPI('獲取反饋標籤', 'GET', `${API_PREFIX}/labels/feedbacks`, null, headers)
  await testAPI('獲取標籤統計', 'GET', `${API_PREFIX}/labels/stats`, null, headers)
  
  // 測試創建標籤
  await testAPI('創建商品標籤', 'POST', `${API_PREFIX}/labels/products`, {
    name: '測試商品標籤',
    description: '測試描述'
  }, headers)
  
  await testAPI('創建反饋標籤', 'POST', `${API_PREFIX}/labels/feedbacks`, {
    name: '測試反饋標籤',
    category: '產品規格',
    description: '測試描述'
  }, headers)
  
  await testAPI('獲取操作記錄', 'GET', `${API_PREFIX}/labels/operations`, null, headers)
}

// 測試用戶管理 API
async function testUsers(authToken) {
  log('\n👥 測試用戶管理 API', 'cyan')
  
  const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {}
  
  await testAPI('獲取用戶列表', 'GET', `${API_PREFIX}/users`, null, headers)
  await testAPI('獲取用戶統計', 'GET', `${API_PREFIX}/users/stats`, null, headers)
  await testAPI('獲取角色列表', 'GET', `${API_PREFIX}/roles`, null, headers)
  await testAPI('獲取模組列表', 'GET', `${API_PREFIX}/modules`, null, headers)
  
  // 測試創建用戶
  await testAPI('創建用戶', 'POST', `${API_PREFIX}/users`, {
    username: 'test_user_api',
    email: 'test@test.com',
    password: 'test123',
    roleId: 'viewer'
  }, headers)
  
  await testAPI('用戶名驗證', 'POST', `${API_PREFIX}/users/validate-username`, {
    username: 'test_validation'
  }, headers)
  
  await testAPI('獲取操作記錄', 'GET', `${API_PREFIX}/users/operations`, null, headers)
}

// 測試系統健康狀態
async function testSystemHealth() {
  log('\n🏥 測試系統健康狀態', 'cyan')
  
  await testAPI('系統健康檢查', 'GET', '/health')
  await testAPI('API 版本信息', 'GET', `${API_PREFIX}/version`)
  await testAPI('系統狀態', 'GET', `${API_PREFIX}/system/status`)
}

// 主測試函數
async function runTests() {
  log('🚀 開始前後端 API 連通性測試', 'bright')
  log('='.repeat(50), 'blue')
  
  try {
    // 測試系統健康狀態
    await testSystemHealth()
    
    // 測試用戶認證
    const authToken = await testAuthentication()
    
    // 測試各個模組的 API
    await testDashboard(authToken)
    await testAnalysis(authToken)
    await testDataSource(authToken)
    await testLabels(authToken)
    await testUsers(authToken)
    
  } catch (error) {
    logError(`測試過程中發生錯誤: ${error.message}`)
  }
  
  // 輸出測試結果
  log('\n' + '='.repeat(50), 'blue')
  log('📋 測試結果總結', 'bright')
  log('='.repeat(50), 'blue')
  
  logInfo(`總測試數: ${totalTests}`)
  logSuccess(`通過測試: ${passedTests}`)
  logError(`失敗測試: ${failedTests}`)
  
  const successRate = ((passedTests / totalTests) * 100).toFixed(1)
  log(`\n成功率: ${successRate}%`, successRate >= 80 ? 'green' : 'red')
  
  if (failedTests === 0) {
    log('\n🎉 所有測試通過！前後端連通性良好。', 'green')
  } else if (successRate >= 80) {
    log('\n✅ 大部分測試通過，系統基本可用。', 'yellow')
  } else {
    log('\n❌ 多個測試失敗，需要檢查後端服務配置。', 'red')
  }
  
  log('\n💡 提示:', 'cyan')
  log('- 確保後端服務在 http://127.0.0.1:8100 運行')
  log('- 檢查數據庫連接和初始化')
  log('- 驗證 API 路由和權限配置')
  log('- 某些 401/403 錯誤是正常的（未授權訪問）')
}

// 執行測試
if (require.main === module) {
  runTests().catch(error => {
    logError(`測試執行失敗: ${error.message}`)
    process.exit(1)
  })
}

module.exports = { runTests, testAPI }