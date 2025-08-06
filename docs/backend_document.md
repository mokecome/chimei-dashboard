# 奇美食品客服語音分析系統 - 後端架構文檔

## 1. 專案概述

### 1.1 系統簡介
本系統為奇美食品開發的客服語音分析平台，基於 FastAPI + MySQL 架構，通過 AI 技術對客服語音檔案進行智能分析，提取客戶反饋的關鍵資訊，包括情感分析、產品識別、問題分類等，為企業決策提供數據支援。

### 1.2 技術棧
- **框架**: FastAPI 0.104+
- **語言**: Python 3.9+
- **資料庫**: MySQL 8.0
- **ORM**: SQLAlchemy 2.0
- **認證**: JWT Token (PyJWT)
- **AI 處理**: Whisper ASR + Ollama/Qwen
- **檔案儲存**: 本地檔案系統 + 資料庫記錄
- **異步處理**: asyncio + Background Tasks
- **部署**: Docker + Uvicorn

### 1.3 專案結構
```
backend/
├── app/
│   ├── main.py                 # 應用入口點
│   ├── config.py              # 配置管理
│   ├── database.py            # 資料庫連接配置
│   ├── api/                   # API 路由層
│   │   └── v1/
│   │       ├── auth.py        # 認證相關路由
│   │       ├── users.py       # 用戶管理路由
│   │       ├── files.py       # 檔案管理路由
│   │       ├── analysis.py    # 分析結果路由
│   │       ├── labels.py      # 標籤管理路由
│   │       └── dashboard.py   # 儀表板路由
│   ├── core/                  # 核心功能
│   │   ├── dependencies.py    # 依賴注入
│   │   ├── permissions.py     # 權限管理
│   │   └── security.py        # 安全相關
│   ├── models/                # 資料模型
│   │   ├── user.py           # 用戶模型
│   │   ├── voice_file.py     # 檔案模型
│   │   ├── voice_analysis.py # 分析結果模型
│   │   ├── product_label.py  # 商品標籤模型
│   │   └── feedback_category.py # 反饋分類模型
│   ├── schemas/               # Pydantic 模式
│   │   ├── user.py           # 用戶模式
│   │   ├── file.py           # 檔案模式
│   │   ├── analysis.py       # 分析模式
│   │   ├── label.py          # 標籤模式
│   │   └── common.py         # 通用模式
│   ├── services/              # 業務邏輯層
│   │   ├── auth_service.py   # 認證服務
│   │   ├── user_service.py   # 用戶服務
│   │   ├── file_service.py   # 檔案服務
│   │   ├── analysis_service.py # 分析服務
│   │   ├── label_service.py  # 標籤服務
│   │   └── ai_service.py     # AI 處理服務
│   ├── repositories/          # 資料訪問層
│   │   ├── user.py           # 用戶倉庫
│   │   ├── file.py           # 檔案倉庫
│   │   ├── analysis.py       # 分析倉庫
│   │   └── label.py          # 標籤倉庫
│   └── tests/                 # 測試檔案
│       ├── test_auth.py      # 認證測試
│       ├── test_files.py     # 檔案測試
│       └── test_api.py       # API 測試
├── storage/                   # 檔案儲存目錄
│   └── uploads/              # 上傳檔案目錄
├── scripts/                   # 工具腳本
│   ├── init_db.py            # 資料庫初始化
│   └── create_user.py        # 建立用戶腳本
├── requirements.txt           # Python 依賴
├── Dockerfile                # Docker 配置
└── run_server.py             # 開發伺服器啟動腳本
```

## 2. 系統架構設計

### 2.1 整體架構
```mermaid
graph TB
    A[Vue 3 Frontend] --> B[FastAPI Backend]
    B --> C[MySQL 8.0]
    B --> D[Whisper ASR]
    B --> E[Ollama/Qwen LLM]
    B --> F[Local File Storage]
    
    subgraph "Backend Architecture"
        G[API Routes] --> H[Services]
        H --> I[Repositories]
        I --> J[Models]
        H --> K[AI Service]
    end
```

### 2.2 分層架構設計

#### 2.2.1 API 路由層 (Routes)
負責 HTTP 請求處理、參數驗證、權限檢查和回應格式化。

**主要路由模組**：
- `/api/v1/auth/*` - 認證相關 API
- `/api/v1/users/*` - 用戶管理 API
- `/api/v1/files/*` - 檔案管理 API
- `/api/v1/analysis/*` - 分析結果 API
- `/api/v1/labels/*` - 標籤管理 API
- `/api/v1/dashboard/*` - 儀表板數據 API

#### 2.2.2 業務邏輯層 (Services)
封裝複雜的業務邏輯、資料處理和外部服務整合。

**核心服務模組**：
- `AuthService` - 認證和授權邏輯
- `UserService` - 用戶管理業務邏輯
- `FileService` - 檔案處理業務邏輯
- `AnalysisService` - 分析結果業務邏輯
- `LabelService` - 標籤管理業務邏輯
- `AIService` - AI 處理整合服務

#### 2.2.3 資料訪問層 (Repositories)
封裝資料庫操作，提供統一的資料訪問介面。

#### 2.2.4 資料模型層 (Models)
使用 SQLAlchemy 定義資料庫表結構和關聯關係。

## 3. 資料庫設計

### 3.1 核心資料表

#### 3.1.1 users（用戶表）
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  -- bcrypt 哈希
    role ENUM('admin','manager','operator','viewer') DEFAULT 'viewer',
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
);
```

#### 3.1.2 voice_files（語音檔案表）
```sql
CREATE TABLE voice_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type ENUM('audio','text') NOT NULL,
    file_size INT,
    upload_user_id INT,
    status ENUM('pending','processing','completed','failed') DEFAULT 'pending',
    transcribed_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_user_id) REFERENCES users(id),
    INDEX idx_status (status),
    INDEX idx_upload_user (upload_user_id),
    INDEX idx_created_at (created_at)
);
```

#### 3.1.3 voice_analysis（分析結果表）
```sql
CREATE TABLE voice_analysis (
    id INT PRIMARY KEY AUTO_INCREMENT,
    file_id INT NOT NULL,
    sentiment ENUM('positive','negative','neutral'),
    summary TEXT,
    keywords JSON,
    confidence_score DECIMAL(3,2),
    analysis_result JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES voice_files(id) ON DELETE CASCADE,
    INDEX idx_file_id (file_id),
    INDEX idx_sentiment (sentiment),
    INDEX idx_created_at (created_at)
);
```

#### 3.1.4 product_labels（商品標籤表）
```sql
CREATE TABLE product_labels (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    keywords JSON,
    created_by INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_name (name),
    INDEX idx_is_active (is_active)
);
```

#### 3.1.5 feedback_categories（反饋分類表）
```sql
CREATE TABLE feedback_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    keywords JSON,
    created_by INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_name (name),
    INDEX idx_is_active (is_active)
);
```

### 3.2 關聯關係
- User (1) → (N) VoiceFile：用戶可上傳多個檔案
- VoiceFile (1) → (1) VoiceAnalysis：每個檔案對應一個分析結果
- User (1) → (N) ProductLabel：用戶可創建多個商品標籤
- User (1) → (N) FeedbackCategory：用戶可創建多個反饋分類
- VoiceAnalysis (N) ← → (N) ProductLabel：多對多關聯（通過分析結果 JSON）
- VoiceAnalysis (N) ← → (N) FeedbackCategory：多對多關聯（通過分析結果 JSON）

## 4. API 設計規範

### 4.1 RESTful API 設計原則
- 使用標準 HTTP 方法（GET、POST、PUT、DELETE）
- 統一 URL 結構：`/api/v1/{resource}`
- 使用 HTTP 狀態碼表示操作結果
- 統一的 JSON 回應格式

### 4.2 統一回應格式

#### 4.2.1 成功回應
```json
{
    "code": 0,
    "message": "success",
    "data": {
        // 具體數據
    }
}
```

#### 4.2.2 錯誤回應
```json
{
    "code": 40001,
    "message": "驗證失敗",
    "detail": "電子郵件格式不正確"
}
```

#### 4.2.3 分頁回應
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "items": [],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "pages": 5
    }
}
```

### 4.3 主要 API 端點

#### 4.3.1 認證相關 API
```python
# app/api/v1/auth.py

@router.post("/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """用戶登入，返回 JWT Token"""
    
@router.post("/refresh")
async def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """刷新訪問 Token"""
    
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """用戶登出"""
    
@router.post("/change-password")  
async def change_password(password_data: ChangePasswordRequest, 
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """修改密碼"""
```

#### 4.3.2 用戶管理 API
```python
# app/api/v1/users.py

@router.get("/")
async def get_users(page: int = 1, page_size: int = 20,
                   current_user: User = Depends(require_admin),
                   db: Session = Depends(get_db)):
    """獲取用戶列表"""

@router.post("/")
async def create_user(user_data: UserCreateRequest,
                     current_user: User = Depends(require_admin),
                     db: Session = Depends(get_db)):
    """創建新用戶"""

@router.put("/{user_id}")
async def update_user(user_id: int, user_data: UserUpdateRequest,
                     current_user: User = Depends(require_admin),
                     db: Session = Depends(get_db)):
    """更新用戶資訊"""

@router.delete("/{user_id}")
async def delete_user(user_id: int,
                     current_user: User = Depends(require_admin),
                     db: Session = Depends(get_db)):
    """刪除用戶"""
```

#### 4.3.3 檔案管理 API
```python
# app/api/v1/files.py

@router.get("/")
async def get_files(page: int = 1, page_size: int = 20,
                   search: Optional[str] = None,
                   status: Optional[str] = None,
                   current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """獲取檔案列表"""

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...),
                      current_user: User = Depends(require_operator),
                      db: Session = Depends(get_db)):
    """上傳檔案"""

@router.get("/{file_id}")
async def get_file_detail(file_id: int,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """獲取檔案詳情"""

@router.delete("/{file_id}")
async def delete_file(file_id: int,
                     current_user: User = Depends(require_manager),
                     db: Session = Depends(get_db)):
    """刪除檔案"""
```

#### 4.3.4 分析結果 API
```python
# app/api/v1/analysis.py

@router.get("/")
async def get_analysis_results(page: int = 1, page_size: int = 20,
                              product_labels: Optional[List[str]] = Query(None),
                              feedback_types: Optional[List[str]] = Query(None),
                              sentiment: Optional[str] = None,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None,
                              current_user: User = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    """獲取分析結果列表"""

@router.get("/{analysis_id}")
async def get_analysis_detail(analysis_id: int,
                             current_user: User = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    """獲取分析詳情"""

@router.get("/export")
async def export_analysis_results(product_labels: Optional[List[str]] = Query(None),
                                 feedback_types: Optional[List[str]] = Query(None),
                                 sentiment: Optional[str] = None,
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None,
                                 current_user: User = Depends(require_manager),
                                 db: Session = Depends(get_db)):
    """匯出分析結果"""
```

#### 4.3.5 標籤管理 API
```python
# app/api/v1/labels.py

# 商品標籤
@router.get("/products")
async def get_product_labels(current_user: User = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    """獲取商品標籤列表"""

@router.post("/products")
async def create_product_label(label_data: ProductLabelCreateRequest,
                              current_user: User = Depends(require_manager),
                              db: Session = Depends(get_db)):
    """創建商品標籤"""

# 反饋分類
@router.get("/feedback")
async def get_feedback_categories(current_user: User = Depends(get_current_user),
                                 db: Session = Depends(get_db)):
    """獲取反饋分類列表"""

@router.post("/feedback")
async def create_feedback_category(category_data: FeedbackCategoryCreateRequest,
                                  current_user: User = Depends(require_manager),
                                  db: Session = Depends(get_db)):
    """創建反饋分類"""
```

#### 4.3.6 儀表板 API
```python
# app/api/v1/dashboard.py

@router.get("/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    """獲取儀表板統計數據"""

@router.get("/charts/product-mentions")
async def get_product_mentions_chart(days: int = 7,
                                    current_user: User = Depends(get_current_user),
                                    db: Session = Depends(get_db)):
    """獲取產品提及次數圖表數據"""

@router.get("/charts/sentiment-distribution")
async def get_sentiment_distribution_chart(days: int = 7,
                                          current_user: User = Depends(get_current_user),
                                          db: Session = Depends(get_db)):
    """獲取情感分析分布圖表數據"""

@router.get("/charts/feedback-types")
async def get_feedback_types_chart(days: int = 7,
                                  current_user: User = Depends(get_current_user),
                                  db: Session = Depends(get_db)):
    """獲取反饋類型分布圖表數據"""

@router.get("/charts/daily-trend")
async def get_daily_trend_chart(days: int = 7,
                               current_user: User = Depends(get_current_user),
                               db: Session = Depends(get_db)):
    """獲取每日趨勢圖表數據"""
```

## 5. 認證與權限系統

### 5.1 JWT Token 認證機制

#### 5.1.1 Token 結構
```python
# app/core/security.py

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """創建訪問 Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """創建刷新 Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

#### 5.1.2 Token 驗證
```python
# app/core/dependencies.py

async def get_current_user(token: str = Depends(oauth2_scheme), 
                          db: Session = Depends(get_db)) -> User:
    """獲取當前用戶"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise credentials_exception
    return user
```

### 5.2 角色權限系統

#### 5.2.1 角色定義
```python
# app/models/user.py

class UserRole(str, enum.Enum):
    ADMIN = "admin"       # 系統管理員 - 所有權限
    MANAGER = "manager"   # 主管 - 管理權限（不含用戶管理）
    OPERATOR = "operator" # 操作員 - 操作權限（上傳、查看）
    VIEWER = "viewer"     # 檢視員 - 僅查看權限
```

#### 5.2.2 權限檢查器
```python
# app/core/permissions.py

class PermissionChecker:
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: ["*"],  # 所有權限
        UserRole.MANAGER: ["read:*", "write:data", "write:labels", "write:analysis", "delete:files"],
        UserRole.OPERATOR: ["read:*", "write:files", "write:analysis"],
        UserRole.VIEWER: ["read:*"]
    }
    
    @classmethod
    def check_permission(cls, user_role: UserRole, action: str, resource: str) -> bool:
        """檢查用戶權限"""
        user_permissions = cls.ROLE_PERMISSIONS.get(user_role, [])
        
        if "*" in user_permissions:
            return True
            
        permission = f"{action}:{resource}"
        if permission in user_permissions:
            return True
            
        action_wildcard = f"{action}:*"
        return action_wildcard in user_permissions
```

#### 5.2.3 權限裝飾器
```python
# app/core/dependencies.py

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """需要管理員權限"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_manager(current_user: User = Depends(get_current_user)) -> User:
    """需要主管以上權限"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return current_user

def require_operator(current_user: User = Depends(get_current_user)) -> User:
    """需要操作員以上權限"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator access required"
        )
    return current_user
```

## 6. AI 服務整合

### 6.1 AI 處理流程
```mermaid
sequenceDiagram
    participant U as Upload API
    participant F as File Service
    participant A as AI Service
    participant W as Whisper ASR
    participant L as LLM (Ollama/Qwen)
    participant D as Database

    U->>F: 檔案上傳
    F->>D: 儲存檔案記錄
    F->>A: 觸發 Background Task
    
    alt 音訊檔案
        A->>W: ASR 轉錄
        W-->>A: 文字結果
    else 文字檔案
        A->>A: 直接讀取內容
    end
    
    A->>L: LLM 分析
    L-->>A: 分析結果
    A->>D: 儲存分析結果
    A->>D: 更新檔案狀態
```

### 6.2 AI 服務實現

#### 6.2.1 AI 服務類
```python
# app/services/ai_service.py

class AIService:
    def __init__(self, db: Session):
        self.db = db
        self.whisper_api_url = settings.WHISPER_API_URL
        self.llm_api_url = settings.LLM_API_URL
    
    async def process_file(self, file_id: int):
        """處理檔案：ASR + LLM 分析"""
        try:
            file_obj = self.db.query(VoiceFile).filter(VoiceFile.id == file_id).first()
            if not file_obj:
                return
            
            # 更新狀態為處理中
            file_obj.status = "processing"
            self.db.commit()
            
            # Step 1: 語音轉文字（如果是音訊檔案）
            if file_obj.file_type == "audio":
                transcribed_text = await self._transcribe_audio(file_obj.file_path)
                file_obj.transcribed_text = transcribed_text
            else:
                # 文字檔案直接讀取
                with open(file_obj.file_path, 'r', encoding='utf-8') as f:
                    transcribed_text = f.read()
                file_obj.transcribed_text = transcribed_text
            
            # Step 2: LLM 分析
            analysis_result = await self._analyze_text(transcribed_text)
            
            # Step 3: 儲存分析結果
            voice_analysis = VoiceAnalysis(
                file_id=file_id,
                sentiment=analysis_result.get("sentiment"),
                summary=analysis_result.get("summary"),
                keywords=analysis_result.get("keywords"),
                analysis_result=analysis_result
            )
            self.db.add(voice_analysis)
            
            # 更新檔案狀態
            file_obj.status = "completed"
            self.db.commit()
            
        except Exception as e:
            # 處理失敗
            file_obj.status = "failed"
            self.db.commit()
            logger.error(f"AI processing failed for file {file_id}: {str(e)}")
    
    async def _transcribe_audio(self, file_path: str) -> str:
        """使用 Whisper 進行語音轉文字"""
        # 實現 Whisper API 呼叫
        pass
    
    async def _analyze_text(self, text: str) -> dict:
        """使用 LLM 分析文字內容"""
        # 獲取標籤配置
        product_labels = self.db.query(ProductLabel).filter(ProductLabel.is_active == True).all()
        feedback_categories = self.db.query(FeedbackCategory).filter(FeedbackCategory.is_active == True).all()
        
        # 構建提示詞
        prompt = self._build_analysis_prompt(text, product_labels, feedback_categories)
        
        # 調用 Ollama/Qwen API
        # 實現 LLM API 呼叫
        pass
    
    def _build_analysis_prompt(self, text: str, product_labels: List, feedback_categories: List) -> str:
        """構建 LLM 分析提示詞"""
        products = [label.name for label in product_labels]
        feedback_types = [category.name for category in feedback_categories]
        
        prompt = f"""
        請分析以下客服對話內容，提取關鍵資訊：

        對話內容：
        {text}

        請提供以下分析結果（以 JSON 格式回答）：
        1. 提及的產品（從以下列表選擇）：{products}
        2. 情感傾向（positive/negative/neutral）
        3. 反饋類型（從以下列表選擇）：{feedback_types}
        4. 關鍵詞（最多5個）
        5. 內容摘要（50字以內）

        JSON 格式：
        {{
            "products": ["產品名稱"],
            "sentiment": "positive/negative/neutral",
            "feedback_types": ["反饋類型"],
            "keywords": ["關鍵詞1", "關鍵詞2"],
            "summary": "摘要內容"
        }}
        """
        return prompt
```

#### 6.2.2 背景任務處理
```python
# app/api/v1/files.py

from fastapi import BackgroundTasks

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db)
):
    """上傳檔案並觸發 AI 處理"""
    file_service = FileService(db)
    uploaded_files = []
    
    for file in files:
        # 儲存檔案
        file_obj = await file_service.save_file(file, current_user.id)
        uploaded_files.append(file_obj)
        
        # 添加背景任務進行 AI 處理
        ai_service = AIService(db)
        background_tasks.add_task(ai_service.process_file, file_obj.id)
    
    return SuccessResponse(data=uploaded_files)
```

## 7. 檔案處理系統

### 7.1 檔案上傳處理

#### 7.1.1 檔案服務
```python
# app/services/file_service.py

class FileService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def save_file(self, file: UploadFile, user_id: int) -> VoiceFile:
        """儲存上傳的檔案"""
        # 驗證檔案類型
        if not self._is_valid_file_type(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"不支援的檔案格式。支援格式：{', '.join(settings.ALLOWED_FILE_TYPES)}"
            )
        
        # 驗證檔案大小
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"檔案大小超過限制 ({settings.MAX_FILE_SIZE // 1024 // 1024}MB)"
            )
        
        # 生成唯一檔名
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.upload_dir / unique_filename
        
        # 儲存檔案到磁碟
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 建立資料庫記錄
        file_type = "audio" if file_extension.lower() in ['.wav', '.mp3'] else "text"
        voice_file = VoiceFile(
            filename=file.filename,
            file_path=str(file_path),
            file_type=file_type,
            file_size=file.size,
            upload_user_id=user_id,
            status="pending"
        )
        
        self.db.add(voice_file)
        self.db.commit()
        self.db.refresh(voice_file)
        
        return voice_file
    
    def _is_valid_file_type(self, filename: str) -> bool:
        """檢查檔案類型是否有效"""
        if not filename:
            return False
        file_extension = Path(filename).suffix.lower()
        return file_extension in settings.ALLOWED_FILE_TYPES
    
    def delete_file(self, file_id: int, user: User) -> bool:
        """刪除檔案"""
        file_obj = self.db.query(VoiceFile).filter(VoiceFile.id == file_id).first()
        if not file_obj:
            raise HTTPException(status_code=404, detail="檔案不存在")
        
        # 權限檢查
        if not self._can_delete_file(file_obj, user):
            raise HTTPException(status_code=403, detail="沒有權限刪除此檔案")
        
        # 刪除磁碟檔案
        try:
            if os.path.exists(file_obj.file_path):
                os.remove(file_obj.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file from disk: {e}")
        
        # 刪除資料庫記錄（級聯刪除分析結果）
        self.db.delete(file_obj)
        self.db.commit()
        
        return True
    
    def _can_delete_file(self, file_obj: VoiceFile, user: User) -> bool:
        """檢查是否有權限刪除檔案"""
        # Admin 和 Manager 可以刪除任何檔案
        if user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            return True
        # 其他用戶只能刪除自己上傳的檔案
        return file_obj.upload_user_id == user.id
```

### 7.2 檔案狀態管理

#### 7.2.1 狀態定義
```python
# app/models/voice_file.py

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"       # 待處理
    PROCESSING = "processing" # 處理中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 處理失敗
```

#### 7.2.2 狀態更新機制
檔案狀態在 AI 處理過程中會自動更新：
- 上傳後：`pending`
- 開始處理：`processing`
- 處理成功：`completed`
- 處理失敗：`failed`

## 8. 儀表板數據服務

### 8.1 統計數據服務

#### 8.1.1 儀表板服務
```python
# app/services/dashboard_service.py

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_stats(self) -> dict:
        """獲取儀表板統計數據"""
        # 總檔案數
        total_files = self.db.query(VoiceFile).count()
        
        # 今日新增檔案數
        today = datetime.now().date()
        today_files = self.db.query(VoiceFile).filter(
            func.date(VoiceFile.created_at) == today
        ).count()
        
        # 處理中檔案數
        processing_files = self.db.query(VoiceFile).filter(
            VoiceFile.status == "processing"
        ).count()
        
        # 處理失敗檔案數
        failed_files = self.db.query(VoiceFile).filter(
            VoiceFile.status == "failed"
        ).count()
        
        return {
            "total_files": total_files,
            "today_files": today_files,
            "processing_files": processing_files,
            "failed_files": failed_files
        }
    
    def get_product_mentions_chart(self, days: int = 7) -> dict:
        """獲取產品提及次數圖表數據"""
        start_date = datetime.now() - timedelta(days=days)
        
        # 查詢分析結果中的產品提及統計
        query = self.db.query(
            VoiceAnalysis.analysis_result
        ).join(VoiceFile).filter(
            VoiceFile.created_at >= start_date,
            VoiceFile.status == "completed"
        ).all()
        
        # 統計產品提及次數
        product_counts = {}
        for result in query:
            if result.analysis_result and "products" in result.analysis_result:
                for product in result.analysis_result["products"]:
                    product_counts[product] = product_counts.get(product, 0) + 1
        
        # 排序並取前10名
        top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "labels": [item[0] for item in top_products],
            "data": [item[1] for item in top_products]
        }
    
    def get_sentiment_distribution_chart(self, days: int = 7) -> dict:
        """獲取情感分析分布圖表數據"""
        start_date = datetime.now() - timedelta(days=days)
        
        sentiment_counts = self.db.query(
            VoiceAnalysis.sentiment,
            func.count(VoiceAnalysis.id).label('count')
        ).join(VoiceFile).filter(
            VoiceFile.created_at >= start_date,
            VoiceFile.status == "completed",
            VoiceAnalysis.sentiment.isnot(None)
        ).group_by(VoiceAnalysis.sentiment).all()
        
        sentiment_map = {
            "positive": "正面",
            "negative": "負面", 
            "neutral": "中性"
        }
        
        labels = []
        data = []
        for sentiment, count in sentiment_counts:
            labels.append(sentiment_map.get(sentiment, sentiment))
            data.append(count)
        
        return {
            "labels": labels,
            "data": data
        }
    
    def get_daily_trend_chart(self, days: int = 7) -> dict:
        """獲取每日趨勢圖表數據"""
        start_date = datetime.now() - timedelta(days=days)
        
        daily_counts = self.db.query(
            func.date(VoiceFile.created_at).label('date'),
            func.count(VoiceFile.id).label('count')
        ).filter(
            VoiceFile.created_at >= start_date
        ).group_by(
            func.date(VoiceFile.created_at)
        ).order_by('date').all()
        
        # 填補缺失的日期
        date_range = []
        for i in range(days):
            date_range.append(start_date.date() + timedelta(days=i))
        
        daily_data = {str(date): 0 for date in date_range}
        for date, count in daily_counts:
            daily_data[str(date)] = count
        
        return {
            "labels": [str(date) for date in date_range],
            "data": [daily_data[str(date)] for date in date_range]
        }
```

## 9. 錯誤處理與日誌

### 9.1 全域異常處理器

#### 9.1.1 異常處理器註冊
```python
# app/main.py

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code * 100 + 1,  # 轉換為自定義錯誤碼
            "message": exc.detail,
            "detail": str(exc.detail)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用異常處理器"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 50001,
            "message": "內部伺服器錯誤",
            "detail": "請聯繫系統管理員"
        }
    )
```

### 9.2 日誌配置

#### 9.2.1 日誌設定
```python
# app/config.py

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "default",
            "class": "logging.FileHandler",
            "filename": "app.log",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["default", "file"],
    },
}
```

## 10. 配置管理

### 10.1 環境配置

#### 10.1.1 配置類
```python
# app/config.py

from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 應用配置
    APP_NAME: str = "奇美食品客服語音分析系統"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # 資料庫配置
    DATABASE_URL: str = "mysql://root:123456@localhost:3306/chime_dashboard"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 檔案上傳配置
    UPLOAD_DIR: str = "storage/uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: List[str] = [".wav", ".mp3", ".txt"]
    
    # AI 服務配置
    WHISPER_API_URL: str = "http://localhost:9000"
    LLM_API_URL: str = "http://localhost:11434"
    
    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 10.2 環境變數配置
```bash
# .env 檔案示例
APP_NAME="奇美食品客服語音分析系統"
DEBUG=false
DATABASE_URL="mysql://root:password@db:3306/chime_dashboard"
SECRET_KEY="your-very-secure-secret-key"
UPLOAD_DIR="/app/storage/uploads"
MAX_FILE_SIZE=104857600
LLM_API_URL="http://ollama:11434"
CORS_ORIGINS=["http://localhost:3000","http://frontend:80"]
```

## 11. 部署與運維

### 11.1 Docker 配置

#### 11.1.1 Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 建立儲存目錄
RUN mkdir -p storage/uploads

# 暴露埠
EXPOSE 8100

# 啟動命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
```

#### 11.1.2 Docker Compose 配置
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8100:8100"
    environment:
      DATABASE_URL: mysql://root:123456@db:3306/chime_dashboard
      LLM_API_URL: http://ollama:11434
    depends_on:
      - db
      - ollama
    volumes:
      - ./storage:/app/storage

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: 123456
      MYSQL_DATABASE: chime_dashboard
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  mysql_data:
  ollama_data:
```

### 11.2 啟動腳本

#### 11.2.1 開發環境啟動
```python
# run_server.py

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8100,
        reload=True,  # 開發模式熱重載
        log_level="info"
    )
```

#### 11.2.2 生產環境啟動
```bash
#!/bin/bash
# 生產環境啟動腳本

# 資料庫初始化
python scripts/init_db.py

# 啟動應用
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8100 \
    --workers 4 \
    --access-log \
    --log-level info
```

## 12. 測試

### 12.1 測試框架配置

#### 12.1.1 測試配置
```python
# app/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

# 測試資料庫
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        yield client
    Base.metadata.drop_all(bind=engine)
```

#### 12.1.2 API 測試範例
```python
# app/tests/test_auth.py

def test_login_success(client):
    """測試登入成功"""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@chimei.com",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "token" in data["data"]
    assert "refreshToken" in data["data"]

def test_login_invalid_credentials(client):
    """測試登入失敗"""
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@chimei.com", 
        "password": "wrongpassword"
    })
    assert response.status_code == 401
```

### 12.2 執行測試

#### 12.2.1 pytest 執行
```bash
# 執行所有測試
pytest app/tests/ -v

# 執行特定測試檔案
pytest app/tests/test_auth.py -v

# 執行特定測試方法
pytest app/tests/test_auth.py::test_login_success -v

# 生成覆蓋率報告
pytest app/tests/ --cov=app --cov-report=html
```

## 13. 性能優化

### 13.1 資料庫優化

#### 13.1.1 索引優化
```sql
-- 用戶表索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- 檔案表索引
CREATE INDEX idx_voice_files_status ON voice_files(status);
CREATE INDEX idx_voice_files_upload_user ON voice_files(upload_user_id);
CREATE INDEX idx_voice_files_created_at ON voice_files(created_at);

-- 分析結果表索引
CREATE INDEX idx_voice_analysis_file_id ON voice_analysis(file_id);
CREATE INDEX idx_voice_analysis_sentiment ON voice_analysis(sentiment);
CREATE INDEX idx_voice_analysis_created_at ON voice_analysis(created_at);
```

#### 13.1.2 查詢優化
```python
# 使用 eager loading 避免 N+1 查詢
def get_files_with_analysis(db: Session, limit: int = 20):
    return db.query(VoiceFile).options(
        joinedload(VoiceFile.analysis),
        joinedload(VoiceFile.uploader)
    ).limit(limit).all()

# 使用原始 SQL 進行複雜統計查詢
def get_dashboard_stats_optimized(db: Session):
    sql = """
    SELECT 
        COUNT(*) as total_files,
        SUM(CASE WHEN DATE(created_at) = CURDATE() THEN 1 ELSE 0 END) as today_files,
        SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing_files,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_files
    FROM voice_files
    """
    result = db.execute(text(sql)).fetchone()
    return {
        "total_files": result.total_files,
        "today_files": result.today_files,
        "processing_files": result.processing_files,
        "failed_files": result.failed_files
    }
```

### 13.2 API 性能優化

#### 13.2.1 快取機制
```python
from functools import lru_cache
from typing import List

# 標籤數據快取（30分鐘）
@lru_cache(maxsize=1)
def get_cached_labels():
    # 實現標籤快取邏輯
    pass

# API 回應快取
from fastapi_cache import cache
from fastapi_cache.decorator import cache

@router.get("/dashboard/stats")
@cache(expire=60)  # 快取1分鐘
async def get_dashboard_stats_cached(db: Session = Depends(get_db)):
    return dashboard_service.get_dashboard_stats()
```

#### 13.2.2 分頁優化
```python
class PaginationParams:
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(1, page)
        self.page_size = min(100, max(1, page_size))  # 限制最大頁面大小
        self.offset = (self.page - 1) * self.page_size

def paginate_query(query, pagination: PaginationParams):
    total = query.count()
    items = query.offset(pagination.offset).limit(pagination.page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": (total + pagination.page_size - 1) // pagination.page_size
    }
```

## 14. 安全性考慮

### 14.1 輸入驗證
```python
# 使用 Pydantic 進行嚴格的輸入驗證
from pydantic import BaseModel, EmailStr, constr, validator

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6, max_length=50)
    name: constr(min_length=1, max_length=100)
    role: UserRole = UserRole.VIEWER
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError('密碼必須包含至少一個數字')
        if not any(c.isalpha() for c in v):
            raise ValueError('密碼必須包含至少一個字母')
        return v
```

### 14.2 SQL 注入防護
```python
# 使用 SQLAlchemy ORM 自動防護 SQL 注入
def get_user_by_email(db: Session, email: str):
    # 安全：使用參數化查詢
    return db.query(User).filter(User.email == email).first()

# 如需使用原始 SQL，使用參數綁定
def get_user_stats(db: Session, user_id: int):
    sql = "SELECT COUNT(*) FROM voice_files WHERE upload_user_id = :user_id"
    result = db.execute(text(sql), {"user_id": user_id})
    return result.scalar()
```

### 14.3 敏感資料保護
```python
# 密碼哈希
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# API 回應中移除敏感欄位
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        # 密碼欄位永不出現在 API 回應中
```

## 15. 監控與維護

### 15.1 健康檢查
```python
# app/api/health.py

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """系統健康檢查"""
    try:
        # 檢查資料庫連線
        db.execute(text("SELECT 1"))
        
        # 檢查檔案儲存目錄
        upload_dir = Path(settings.UPLOAD_DIR)
        if not upload_dir.exists():
            raise Exception("Upload directory not accessible")
        
        # 檢查 AI 服務連線
        # 實現 AI 服務連線檢查
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": settings.VERSION
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )
```

### 15.2 效能監控
```python
# 中間件記錄 API 回應時間
from time import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time()
    response = await call_next(request)
    process_time = time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # 記錄慢查詢
    if process_time > 1.0:  # 超過1秒的請求
        logger.warning(f"Slow request: {request.url} took {process_time:.2f}s")
    
    return response
```

此後端架構文檔詳細描述了奇美食品客服語音分析系統的完整後端實現，包括技術架構、API 設計、資料庫結構、安全機制等各個方面，為系統開發、部署和維護提供全面的技術指導。