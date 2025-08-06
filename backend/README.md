# Chime Dashboard Backend

奇美食品客服語音分析系統後端 API

## 技術棧

- **框架**: FastAPI 0.104+
- **語言**: Python 3.11+
- **數據庫**: MySQL 8.0
- **ORM**: SQLAlchemy 2.0
- **認證**: JWT Token
- **AI處理**: Whisper + Ollama/Qwen3:8b 模型

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 環境配置

複製環境變量文件並配置：

```bash
cp .env.example .env
```

編輯 `.env` 文件，配置數據庫連接等信息：

```env
DATABASE_URL=mysql://root:123456@127.0.0.1:3306/chime_dashboard
SECRET_KEY=your-secret-key-here
LLM_API_URL=http://192.168.50.123:11434/api/generate
```

### 3. 初始化數據庫

```bash
python scripts/init_db.py
```

### 4. 啟動服務器

```bash
python run_server.py
```

服務器將在 http://localhost:8100 啟動

## API 文檔

啟動服務器後，可以訪問以下地址查看 API 文檔：

- Swagger UI: http://localhost:8100/docs
- ReDoc: http://localhost:8100/redoc

## API 端點

### 認證 (/api/auth)
- `POST /api/auth/login` - 用戶登錄
- `POST /api/auth/logout` - 用戶登出
- `POST /api/auth/refresh` - 刷新令牌
- `GET /api/auth/me` - 獲取當前用戶信息

### 用戶管理 (/api/users)
- `GET /api/users/` - 獲取用戶列表
- `POST /api/users/` - 創建用戶
- `GET /api/users/{user_id}` - 獲取用戶詳情
- `PUT /api/users/{user_id}` - 更新用戶
- `DELETE /api/users/{user_id}` - 刪除用戶

### 文件管理 (/api/files)
- `POST /api/files/upload` - 上傳文件
- `POST /api/files/batch-upload` - 批量上傳
- `GET /api/files/` - 獲取文件列表
- `GET /api/files/{file_id}` - 獲取文件詳情
- `DELETE /api/files/{file_id}` - 刪除文件

### AI 分析 (/api/analysis)
- `POST /api/analysis/start/{file_id}` - 啟動分析
- `GET /api/analysis/status/{file_id}` - 獲取分析狀態
- `GET /api/analysis/result/{file_id}` - 獲取分析結果
- `POST /api/analysis/batch` - 批量分析

### 數據查詢 (/api/data)
- `GET /api/data/analysis` - 分頁查詢分析結果
- `GET /api/data/dashboard` - 獲取儀表盤數據
- `GET /api/data/export` - 數據導出
- `POST /api/data/search` - 高級搜索

### 標籤管理 (/api/labels)
- `GET /api/labels/products` - 獲取產品標籤
- `POST /api/labels/products` - 創建產品標籤
- `PUT /api/labels/products/{id}` - 更新產品標籤
- `DELETE /api/labels/products/{id}` - 刪除產品標籤
- `GET /api/labels/categories` - 獲取反饋分類
- `POST /api/labels/categories` - 創建反饋分類

## 權限系統

系統支持基於角色的權限控制 (RBAC)：

### 用戶角色
- **admin**: 系統管理員，擁有所有權限
- **manager**: 管理者，可以管理數據和標籤
- **operator**: 操作員，可以上傳文件和查看數據
- **viewer**: 查看者，只能查看數據

### 權限矩陣
| 功能模塊 | Admin | Manager | Operator | Viewer |
|----------|-------|---------|----------|--------|
| 儀表盤查看 | ✅ | ✅ | ✅ | ✅ |
| 文件上傳 | ✅ | ✅ | ✅ | ❌ |
| 文件刪除 | ✅ | ✅ | ❌ | ❌ |
| 數據分析 | ✅ | ✅ | ❌ | ✅ |
| 數據導出 | ✅ | ✅ | ❌ | ❌ |
| 標籤管理 | ✅ | ✅ | ❌ | ❌ |
| 用戶管理 | ✅ | ❌ | ❌ | ❌ |

## 默認用戶

系統初始化後會創建默認管理員用戶：

- 郵箱: admin@chimei.com
- 密碼: admin123

## 測試

運行 API 測試：

```bash
python app/tests/test_api.py
```

或測試特定功能：

```bash
python app/tests/test_api.py --test login
```

## 開發

### 項目結構

```
backend/
├── app/
│   ├── api/v1/          # API 路由
│   ├── core/            # 核心功能
│   ├── models/          # 數據模型
│   ├── schemas/         # Pydantic 模式
│   ├── repositories/    # 數據訪問層
│   ├── services/        # 業務邏輯層
│   ├── ai/              # AI 處理模塊
│   └── tests/           # 測試代碼
├── scripts/             # 部署腳本
├── storage/             # 文件存儲
└── requirements.txt     # 依賴包
```

### 添加新功能

1. 在 `models/` 中定義數據模型
2. 在 `schemas/` 中定義 Pydantic 模式
3. 在 `repositories/` 中實現數據訪問
4. 在 `services/` 中實現業務邏輯
5. 在 `api/v1/` 中實現 API 端點
6. 在 `tests/` 中添加測試

## 部署

### Docker 部署

```bash
# 構建鏡像
docker build -t chime-dashboard-backend .

# 運行容器
docker run -p 8000:8000 chime-dashboard-backend
```

### 生產環境

1. 設置環境變量
2. 配置數據庫
3. 運行數據庫初始化
4. 啟動服務器

```bash
# 生產環境啟動
uvicorn app.main:app --host 0.0.0.0 --port 8100 --workers 4
```

## 故障排除

### 常見問題

1. **數據庫連接失敗**
   - 檢查數據庫配置
   - 確保 MySQL 服務運行
   - 驗證用戶名和密碼

2. **LLM API 連接失敗**
   - 檢查 LLM 服務是否運行
   - 驗證 API URL 配置
   - 檢查網絡連接

3. **文件上傳失敗**
   - 檢查存儲目錄權限
   - 驗證文件大小限制
   - 確認文件格式支持

### 日誌查看

應用日誌會輸出到控制台和文件，可以通過以下方式查看：

```bash
# 查看服務器日誌
tail -f logs/app.log
```

## 貢獻

1. Fork 項目
2. 創建功能分支
3. 提交更改
4. 推送到分支
5. 創建 Pull Request

## 許可證

本項目使用 MIT 許可證。