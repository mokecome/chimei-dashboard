# 奇美食品客服語音分析系統 PRD

## 1. 項目概述

### 1.1 項目背景

奇美食品作為知名食品製造品牌，日常接收大量來自消費者的客服語音或文字回饋，涵蓋商品問題、保存方式、品質意見等。現有客服需耗費大量人力處理、歸類、回報。為提升處理效率與數據價值，我方軟體公司提供一套基於大型語言模型（LLM）的智能分析系統，實現語音轉文字、關鍵資訊擷取、自動標籤與情緒分析，最終以儀表板呈現整體客服趨勢與商品反饋。

### 1.2 核心目標

* **語音資料來源上傳(Data Source)** - 自動化上傳語音轉文字或文字分析處理
* **標籤設定(LabelSetting)** - 使用者自定義商品類型及反饋類型標籤
* **數據分析(Analysis)** - 擷取客服內容中的商品類型標籤、反饋類型及判斷正負評價傾向
* **儀表板(Dashboard)** - 提供可視化儀表板以輔助管理決策
* **帳號權限(Account)** - 支援多模組功能權限管理機制

### 1.3 系統架構概覽

* **前端技術**: Vue 3 + TypeScript + Element Plus + ECharts
* **後端技術**: FastAPI + MySQL + Ollama/Qwen LLM + Whisper ASR
* **部署方式**: Docker Compose 容器化部署

## 2. 用戶分析

### 2.1 目標用戶畫像

* **系統管理員(Admin)**：擁有系統所有權限，管理用戶帳號、系統設定
* **主管(Manager)**：查看所有數據、管理標籤設定、匯出報表
* **操作員(Operator)**：上傳語音檔案、查看分析結果、使用儀表板
* **檢視者(Viewer)**：僅能查看儀表板與分析結果，無操作權限

### 2.2 用戶場景分析

* 客服人員上傳每日客服錄音檔案，系統自動轉文字並分析
* 品管主管查看特定產品的負評趨勢，找出品質問題
* 行銷人員分析消費者對新產品的反饋情緒分布
* 高階主管透過儀表板掌握整體客戶滿意度變化

### 2.3 用戶旅程地圖

1. **登入系統** → 輸入帳號密碼 → 進入系統首頁
2. **上傳語音** → 選擇檔案 → 等待處理 → 查看分析結果
3. **查看儀表板** → 選擇時間範圍 → 查看圖表 → 點擊深入分析
4. **數據分析** → 設定篩選條件 → 查看列表 → 匯出報表
5. **標籤管理** → 新增/編輯標籤 → 設定關鍵字 → 保存設定

## 3. 功能需求

### 3.1 核心功能模組

| 模塊名稱 | 功能說明 | 權限要求 |
| :---- | :---- | :---- |
| 語音資料來源上傳 | 支援上傳 .wav、.mp3 語音檔案及 .txt 文字檔，提供檔案的新增、查看、刪除操作。系統自動進行語音轉文字(ASR)與AI分析處理。 | Operator以上 |
| 標籤設定 | 管理商品標籤與反饋類型標籤，支援新增、編輯、刪除、設定關鍵字。系統根據標籤關鍵字自動分類分析結果。 | Manager以上 |
| 數據分析 | 多維度查看AI分析結果，支援時間範圍、商品類型、情感傾向等篩選條件。提供列表展示、詳細內容查看、數據匯出功能。 | Viewer以上 |
| 儀表板 | 視覺化展示關鍵指標：檔案處理統計、商品提及排行、情感分析分布、反饋類型統計、每日趨勢圖表等。支援圖表交互跳轉至詳細分析。 | Viewer以上 |
| 帳號權限 | 管理系統用戶，支援新增、編輯、停用帳號。設定四級權限角色：Admin、Manager、Operator、Viewer。 | Admin專屬 |

### 3.2 功能詳細規格

#### 3.2.1 用戶認證系統

**登入功能**
- 支援 Email 或使用者名稱登入
- 密碼採用 bcrypt 加密儲存
- 實作 JWT Token 認證機制
- Access Token 有效期：30分鐘
- Refresh Token 有效期：7天
- 支援 Token 自動刷新

**權限角色定義**
```python
class UserRole(Enum):
    ADMIN = "admin"       # 系統管理員
    MANAGER = "manager"   # 主管
    OPERATOR = "operator" # 操作員
    VIEWER = "viewer"     # 檢視者
```

**權限矩陣**
| 功能 | Admin | Manager | Operator | Viewer |
|-----|-------|---------|----------|---------|
| 用戶管理 | ✓ | ✗ | ✗ | ✗ |
| 標籤管理 | ✓ | ✓ | ✗ | ✗ |
| 檔案上傳 | ✓ | ✓ | ✓ | ✗ |
| 檔案刪除 | ✓ | ✓ | ✗ | ✗ |
| 數據查看 | ✓ | ✓ | ✓ | ✓ |
| 數據匯出 | ✓ | ✓ | ✗ | ✗ |

#### 3.2.2 檔案處理流程

**支援格式**
- 音訊格式：.wav, .mp3
- 文字格式：.txt
- 檔案大小限制：100MB

**處理流程**
1. 檔案上傳至 `/storage/uploads/` 目錄
2. 建立檔案記錄於資料庫
3. 觸發非同步處理任務：
   - 音訊檔案 → Whisper ASR 轉文字
   - 文字內容 → Ollama/Qwen LLM 分析
4. 分析結果儲存至資料庫
5. 更新檔案處理狀態

**處理狀態**
```python
class ProcessingStatus(Enum):
    PENDING = "pending"       # 待處理
    PROCESSING = "processing" # 處理中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 處理失敗
```

#### 3.2.3 AI 分析功能

**分析維度**
- **商品識別**：根據商品標籤關鍵字匹配
- **情感分析**：正面(positive)、負面(negative)、中性(neutral)
- **反饋類型**：根據反饋標籤分類
- **關鍵詞提取**：提取重要關鍵詞
- **摘要生成**：生成內容摘要

**LLM 提示詞模板**
```python
ANALYSIS_PROMPT = """
分析以下客服對話內容，提取關鍵信息：

對話內容：
{content}

請提供以下分析結果：
1. 提及的產品（從以下列表選擇）：{products}
2. 情感傾向（positive/negative/neutral）
3. 反饋類型（從以下列表選擇）：{feedback_types}
4. 關鍵詞（最多5個）
5. 內容摘要（50字以內）

以JSON格式返回結果。
"""
```

#### 3.2.4 數據視覺化

**儀表板圖表組件**
1. **處理統計卡片**
   - 總檔案數
   - 今日新增
   - 處理中數量
   - 失敗數量

2. **商品提及排行榜**
   - 橫向柱狀圖
   - 顯示前10名商品
   - 支援點擊跳轉

3. **情感分析圓餅圖**
   - 正面/負面/中性分布
   - 顯示百分比
   - 支援圖例交互

4. **反饋類型分布**
   - 垂直柱狀圖
   - 顯示各類型數量
   - 支援數據篩選

5. **每日趨勢折線圖**
   - 顯示7天/30天趨勢
   - 多指標對比
   - 支援時間範圍選擇

**圖表技術實現**
- 使用 ECharts 5.x
- 響應式設計適配
- 支援數據自動更新
- 提供載入動畫

### 3.3 非功能需求

#### 3.3.1 性能需求
- API 響應時間 < 500ms（不含AI處理）
- 支援同時 100 個並發用戶
- 檔案上傳速度 > 1MB/s
- AI 處理佇列並發數：3

#### 3.3.2 安全需求
- HTTPS 加密傳輸
- SQL 注入防護（使用 ORM）
- XSS 防護（前端框架內建）
- 敏感資料加密存儲
- 定期安全漏洞掃描

#### 3.3.3 可用性需求
- 系統可用性 > 99%
- 支援瀏覽器：Chrome、Firefox、Safari、Edge
- 響應式設計支援平板瀏覽
- 提供操作錯誤提示
- 支援中文繁體介面

#### 3.3.4 可擴展性需求
- 微服務架構設計
- 支援水平擴展
- 資料庫讀寫分離
- 快取機制（Redis）
- 訊息佇列（計劃中）

## 4. 資料庫設計

### 4.1 核心資料表

**users（用戶表）**
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','manager','operator','viewer') DEFAULT 'viewer',
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**voice_files（語音檔案表）**
```sql
CREATE TABLE voice_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_type ENUM('audio','text') NOT NULL,
    file_size INT,
    status ENUM('pending','processing','completed','failed') DEFAULT 'pending',
    upload_user_id INT,
    transcribed_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_user_id) REFERENCES users(id)
);
```

**voice_analysis（分析結果表）**
```sql
CREATE TABLE voice_analysis (
    id INT PRIMARY KEY AUTO_INCREMENT,
    file_id INT NOT NULL,
    sentiment ENUM('positive','negative','neutral'),
    summary TEXT,
    keywords JSON,
    analysis_result JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES voice_files(id) ON DELETE CASCADE
);
```

**product_labels（商品標籤表）**
```sql
CREATE TABLE product_labels (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    keywords JSON,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

**feedback_categories（反饋類型表）**
```sql
CREATE TABLE feedback_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    keywords JSON,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

### 4.2 關聯關係

- User (1) → (N) VoiceFile
- VoiceFile (1) → (1) VoiceAnalysis  
- User (1) → (N) ProductLabel
- User (1) → (N) FeedbackCategory
- VoiceAnalysis (N) ← → (N) ProductLabel
- VoiceAnalysis (N) ← → (N) FeedbackCategory

## 5. API 設計規範

### 5.1 API 基本規範

- RESTful 設計風格
- 統一使用 `/api/v1` 前綴
- 使用 HTTP 狀態碼表示結果
- 統一錯誤回應格式
- 支援分頁、排序、篩選

### 5.2 主要 API 端點

**認證相關**
- `POST /api/v1/auth/login` - 用戶登入
- `POST /api/v1/auth/refresh` - 刷新 Token
- `POST /api/v1/auth/logout` - 用戶登出
- `POST /api/v1/auth/change-password` - 修改密碼

**用戶管理**
- `GET /api/v1/users` - 獲取用戶列表
- `POST /api/v1/users` - 創建用戶
- `PUT /api/v1/users/{id}` - 更新用戶
- `DELETE /api/v1/users/{id}` - 刪除用戶

**檔案管理**
- `GET /api/v1/files` - 獲取檔案列表
- `POST /api/v1/files/upload` - 上傳檔案
- `GET /api/v1/files/{id}` - 獲取檔案詳情
- `DELETE /api/v1/files/{id}` - 刪除檔案

**分析結果**
- `GET /api/v1/analysis` - 獲取分析列表
- `GET /api/v1/analysis/{id}` - 獲取分析詳情
- `GET /api/v1/analysis/export` - 匯出分析數據

**標籤管理**
- `GET /api/v1/labels/products` - 獲取商品標籤
- `POST /api/v1/labels/products` - 創建商品標籤
- `PUT /api/v1/labels/products/{id}` - 更新商品標籤
- `DELETE /api/v1/labels/products/{id}` - 刪除商品標籤

**儀表板**
- `GET /api/v1/dashboard/stats` - 獲取統計數據
- `GET /api/v1/dashboard/charts` - 獲取圖表數據

### 5.3 統一回應格式

**成功回應**
```json
{
    "code": 0,
    "message": "success",
    "data": {
        // 實際數據
    }
}
```

**錯誤回應**
```json
{
    "code": 40001,
    "message": "未授權訪問",
    "detail": "Token 已過期"
}
```

**分頁回應**
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "items": [],
        "total": 100,
        "page": 1,
        "pageSize": 20,
        "pages": 5
    }
}
```

## 6. 部署架構

### 6.1 容器化部署

**Docker Compose 配置**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8100:8100"
    environment:
      - DATABASE_URL=mysql://root:123456@db:3306/chime_dashboard
      - JWT_SECRET_KEY=your-secret-key
      - LLM_API_URL=http://ollama:11434
    depends_on:
      - db
      - ollama

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_BASE_URL=http://backend:8100

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=123456
      - MYSQL_DATABASE=chime_dashboard
    volumes:
      - mysql_data:/var/lib/mysql

  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
```

### 6.2 生產環境建議

1. **負載均衡**：使用 Nginx 反向代理
2. **資料庫**：MySQL 主從複製
3. **檔案儲存**：使用物件儲存服務（如 S3）
4. **快取**：Redis 快取熱點數據
5. **監控**：Prometheus + Grafana
6. **日誌**：ELK Stack 集中式日誌

## 7. 專案里程碑

### Phase 1：基礎功能（已完成）
- ✓ 用戶認證系統
- ✓ 檔案上傳功能
- ✓ AI 分析整合
- ✓ 基礎儀表板

### Phase 2：進階功能（進行中）
- □ 批量檔案處理
- □ 自定義分析規則
- □ 進階數據視覺化
- □ 匯出報表優化

### Phase 3：企業功能（規劃中）
- □ 多租戶支援
- □ API 開放平台
- □ 即時分析功能
- □ 智能預警系統

## 8. 風險評估

### 8.1 技術風險
- **AI 模型準確度**：需持續優化提示詞與模型選擇
- **大量資料處理**：需要實作佇列機制避免阻塞
- **系統擴展性**：架構需支援未來功能擴充

### 8.2 業務風險
- **資料隱私**：需確保客戶資料安全
- **系統可用性**：需要備援機制
- **使用者採用度**：需要完善的教育訓練

## 9. 成功指標

### 9.1 技術指標
- 系統可用率 > 99.5%
- API 平均響應時間 < 300ms
- AI 分析準確率 > 85%
- 並發處理能力 > 100 用戶

### 9.2 業務指標
- 客服處理效率提升 50%
- 問題發現時間縮短 70%
- 用戶滿意度提升 30%
- 資料分析覆蓋率 > 95%

## 10. 附錄

### 10.1 術語表
- **ASR**：Automatic Speech Recognition，自動語音識別
- **LLM**：Large Language Model，大型語言模型
- **JWT**：JSON Web Token，用於身份驗證
- **RBAC**：Role-Based Access Control，基於角色的訪問控制

### 10.2 參考資料
- FastAPI 官方文檔：https://fastapi.tiangolo.com/
- Vue 3 官方文檔：https://vuejs.org/
- Ollama 文檔：https://ollama.ai/
- Whisper 模型：https://github.com/openai/whisper