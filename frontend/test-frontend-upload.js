/**
 * 測試前端上傳功能的腳本
 * 使用 Node.js 執行
 */
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

// API 設定
const API_BASE_URL = 'http://localhost:3000/api';
const TEST_EMAIL = 'admin@chimei.com';
const TEST_PASSWORD = 'admin123';

// 顏色輸出
const colors = {
  success: '\x1b[32m',
  error: '\x1b[31m',
  info: '\x1b[34m',
  warning: '\x1b[33m',
  reset: '\x1b[0m'
};

function log(message, type = 'info') {
  const color = colors[type] || colors.info;
  console.log(`${color}[${type.toUpperCase()}]${colors.reset} ${message}`);
}

// 登入函數
async function login() {
  log('正在登入...', 'info');
  
  try {
    const response = await axios.post(`${API_BASE_URL}/auth/login`, {
      email: TEST_EMAIL,
      password: TEST_PASSWORD
    });
    
    if (response.data && response.data.data && response.data.data.token) {
      log('登入成功', 'success');
      return response.data.data.token;
    } else {
      throw new Error('無法獲取 token');
    }
  } catch (error) {
    log(`登入失敗: ${error.response?.data?.detail || error.message}`, 'error');
    process.exit(1);
  }
}

// 建立測試檔案
function createTestFiles() {
  const testDir = '/tmp/frontend_test_uploads';
  if (!fs.existsSync(testDir)) {
    fs.mkdirSync(testDir, { recursive: true });
  }
  
  const files = [];
  
  // 建立測試檔案 1
  const file1 = path.join(testDir, 'frontend_test_1.txt');
  fs.writeFileSync(file1, `前端測試檔案 1
時間: ${new Date().toISOString()}
內容: 客戶反映鳳梨酥口感很好，但希望能有更多口味選擇。`, 'utf-8');
  files.push(file1);
  
  // 建立測試檔案 2
  const file2 = path.join(testDir, 'frontend_test_2.txt');
  fs.writeFileSync(file2, `前端測試檔案 2
時間: ${new Date().toISOString()}
內容: 綠豆椪的包裝很精美，送禮很合適。`, 'utf-8');
  files.push(file2);
  
  log(`建立了 ${files.length} 個測試檔案`, 'success');
  return files;
}

// 測試單檔案上傳
async function testSingleUpload(token, filePath) {
  log('\n=== 測試單檔案上傳（透過前端 API） ===', 'info');
  
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));
  formData.append('autoAnalyze', 'true');
  formData.append('notifyOnComplete', 'true');
  
  try {
    log(`上傳檔案: ${path.basename(filePath)}`, 'info');
    
    const response = await axios.post(`${API_BASE_URL}/files/upload`, formData, {
      headers: {
        ...formData.getHeaders(),
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.status === 200) {
      log('單檔案上傳成功', 'success');
      log(`  檔案 ID: ${response.data.file_id || response.data.id}`);
      log(`  訊息: ${response.data.message}`);
      return true;
    }
  } catch (error) {
    log('單檔案上傳失敗', 'error');
    log(`  錯誤: ${error.response?.data?.detail || error.message}`, 'error');
    return false;
  }
}

// 測試批量上傳
async function testBatchUpload(token, files) {
  log('\n=== 測試批量上傳（透過前端 API） ===', 'info');
  
  const formData = new FormData();
  
  // 添加多個檔案
  files.forEach(file => {
    formData.append('files', fs.createReadStream(file));
  });
  
  formData.append('autoAnalyze', 'true');
  formData.append('notifyOnComplete', 'true');
  
  try {
    log(`批量上傳 ${files.length} 個檔案`, 'info');
    
    const response = await axios.post(`${API_BASE_URL}/files/batch-upload`, formData, {
      headers: {
        ...formData.getHeaders(),
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.status === 200) {
      const data = response.data;
      log('批量上傳完成', 'success');
      log(`  總檔案數: ${data.total_files}`);
      log(`  成功數量: ${data.successful_count}`);
      log(`  失敗數量: ${data.failed_count}`);
      
      if (data.successful_uploads?.length > 0) {
        log('\n  成功上傳的檔案:');
        data.successful_uploads.forEach(upload => {
          log(`    - ${upload.filename} (ID: ${upload.file_id})`);
        });
      }
      
      return true;
    }
  } catch (error) {
    log('批量上傳失敗', 'error');
    log(`  錯誤: ${error.response?.data?.detail || error.message}`, 'error');
    return false;
  }
}

// 檢查前端 API 代理設定
async function checkProxyConfig() {
  log('\n=== 檢查前端代理設定 ===', 'info');
  
  try {
    // 嘗試直接訪問前端的 API 路徑
    const response = await axios.get('http://localhost:3000/api/auth/check', {
      validateStatus: () => true // 接受所有狀態碼
    });
    
    if (response.status === 401) {
      log('前端 API 代理正常運作（收到 401 未授權回應）', 'success');
      return true;
    } else if (response.status === 404) {
      log('前端 API 代理可能未正確設定', 'warning');
      return false;
    }
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      log('前端服務未啟動', 'error');
      log('請先執行: cd frontend && npm run dev', 'info');
      return false;
    }
    log(`檢查失敗: ${error.message}`, 'error');
    return false;
  }
}

// 主函數
async function main() {
  log('開始測試前端上傳功能', 'info');
  
  // 1. 檢查前端代理
  const proxyOk = await checkProxyConfig();
  if (!proxyOk) {
    log('\n請確保前端開發服務器正在運行', 'error');
    log('執行: cd frontend && npm run dev', 'info');
    process.exit(1);
  }
  
  // 2. 登入
  const token = await login();
  
  // 3. 建立測試檔案
  const testFiles = createTestFiles();
  
  // 4. 測試單檔案上傳
  const singleSuccess = await testSingleUpload(token, testFiles[0]);
  
  // 5. 測試批量上傳
  const batchSuccess = await testBatchUpload(token, testFiles);
  
  // 6. 清理
  log('\n清理測試檔案...', 'info');
  testFiles.forEach(file => fs.unlinkSync(file));
  
  // 7. 總結
  log('\n=== 測試總結 ===', 'info');
  if (singleSuccess) {
    log('✓ 前端單檔案上傳功能正常', 'success');
  } else {
    log('✗ 前端單檔案上傳功能異常', 'error');
  }
  
  if (batchSuccess) {
    log('✓ 前端批量上傳功能正常', 'success');
  } else {
    log('✗ 前端批量上傳功能異常', 'error');
  }
}

// 執行測試
main().catch(error => {
  log(`測試過程發生錯誤: ${error.message}`, 'error');
  process.exit(1);
});