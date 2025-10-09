# CasualTrader API 模組架構說明

## 目錄

1. [總覽](#總覽)
2. [模組結構](#模組結構)
3. [應用層 (app.py, server.py)](#應用層-apppy-serverpy)
4. [路由層 (routers/)](#路由層-routers)
5. [模型層 (models.py)](#模型層-modelspy)
6. [WebSocket 層 (websocket.py)](#websocket-層-websocketpy)
7. [配置層 (config.py, docs.py)](#配置層-configpy-docspy)
8. [模組依賴關係](#模組依賴關係)
9. [互動流程](#互動流程)
10. [資料流向](#資料流向)

---

## 總覽

`src/api/` 目錄是 CasualTrader 的 Web 服務層，採用 FastAPI 框架構建 RESTful API 和 WebSocket 即時通訊服務。

### 設計理念

- **RESTful 設計**: 遵循 REST API 最佳實踐
- **異步優先**: 全面使用 async/await 提升並發性能
- **模塊化路由**: 清晰的路由分離和職責劃分
- **即時通訊**: WebSocket 支援即時數據推送
- **自動文檔**: OpenAPI/Swagger 自動生成 API 文檔
- **CORS 支援**: 完整的跨域資源共享配置

### 技術棧

- **FastAPI 0.115+**: 現代高性能 Web 框架
- **Pydantic V2**: 資料驗證和序列化
- **uvicorn**: ASGI 伺服器
- **WebSocket**: 雙向即時通訊
- **loguru**: 結構化日誌記錄

---

## 模組結構

```
src/api/
├── __init__.py
├── app.py                   # FastAPI 應用工廠
├── server.py                # 服務器啟動入口
├── config.py                # 配置管理
├── docs.py                  # API 文檔配置
├── models.py                # Pydantic 資料模型
├── websocket.py             # WebSocket 管理器
└── routers/                 # API 路由模組
    ├── __init__.py
    ├── agents.py            # Agent 管理路由
    ├── trading.py           # 交易數據路由
    └── websocket_router.py  # WebSocket 路由
```

---

## 應用層 (app.py, server.py)

### 職責

- **應用工廠模式**: 創建和配置 FastAPI 應用實例
- **生命週期管理**: 啟動和關閉時的資源管理
- **中間件配置**: CORS、日誌、錯誤處理等
- **路由註冊**: 組織和掛載 API 路由
- **服務器啟動**: 開發和生產環境的服務器配置

### app.py - FastAPI 應用工廠

**功能**:

- 創建 FastAPI 應用實例
- 配置 CORS 中間件
- 註冊 API 路由
- 管理應用生命週期（lifespan）
- 配置靜態文件服務

**核心函數**:

```python
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    應用生命週期管理器

    Startup:
    - 初始化 Agent Manager
    - 啟動 WebSocket Manager
    - 設置日誌系統

    Shutdown:
    - 關閉 WebSocket 連接
    - 停止所有運行中的 Agents
    - 清理資源
    """

def create_app() -> FastAPI:
    """
    創建和配置 FastAPI 應用

    配置項:
    - CORS 中間件（跨域支援）
    - 路由註冊（agents, trading, websocket）
    - API 文檔（Swagger UI, ReDoc）
    - 靜態文件服務
    - 全局異常處理
    """
```

**依賴**:

- `config.py`: 應用配置
- `docs.py`: API 文檔配置
- `routers.*`: API 路由模組
- `websocket.py`: WebSocket 管理器
- `agents.core.agent_manager`: Agent 管理器

**CORS 配置**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 允許的來源
    allow_credentials=True,
    allow_methods=["*"],                  # 允許所有 HTTP 方法
    allow_headers=["*"],                  # 允許所有 Headers
)
```

### server.py - 服務器啟動入口

**功能**:

- 提供命令行啟動接口
- 配置 uvicorn 服務器參數
- 支援開發和生產環境配置

**核心函數**:

```python
def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
) -> None:
    """
    啟動 API 服務器

    開發模式:
    - reload=True (自動重載)
    - workers=1 (單進程)

    生產模式:
    - reload=False
    - workers=4 (多進程)
    """
```

---

## 路由層 (routers/)

### 職責

實現具體的 API 端點邏輯，處理 HTTP 請求並返回響應。

### routers/agents.py - Agent 管理路由

**功能**:

- Agent CRUD 操作（創建、讀取、更新、刪除）
- Agent 執行控制（啟動、停止、暫停）
- Agent 模式切換（Trading, Rebalancing, Observation, Strategy Review）
- Agent 狀態查詢
- Agent 配置管理

**核心端點**:

```python
# Agent CRUD
GET    /api/agents                    # 列出所有代理
POST   /api/agents                    # 創建新代理
GET    /api/agents/{agent_id}         # 取得指定代理詳情
PUT    /api/agents/{agent_id}         # 更新代理配置
DELETE /api/agents/{agent_id}         # 刪除代理

# Agent 執行控制
POST   /api/agents/{agent_id}/start   # 啟動代理
POST   /api/agents/{agent_id}/stop    # 停止代理
POST   /api/agents/{agent_id}/pause   # 暫停代理
POST   /api/agents/{agent_id}/resume  # 恢復代理

# Agent 模式管理
GET    /api/agents/{agent_id}/mode    # 取得當前執行模式
PUT    /api/agents/{agent_id}/mode    # 切換執行模式
GET    /api/agents/{agent_id}/mode-history  # 取得模式切換歷史
```

**關鍵實作**:

```python
@router.post("", response_model=AgentResponse)
async def create_agent(request: CreateAgentRequest) -> AgentResponse:
    """
    創建新的交易代理

    請求體:
    - name: Agent 名稱
    - ai_model: AI 模型選擇（gpt-4o, claude-sonnet-4.5 等）
    - strategy_type: 策略類型（conservative, balanced, aggressive）
    - investment_preferences: 投資偏好描述
    - initial_funds: 初始資金
    - max_turns: 最大執行回合數
    - enabled_tools: 啟用的工具（fundamental, technical 等）

    流程:
    1. 驗證請求參數
    2. 創建 AgentConfig
    3. 註冊到 AgentManager
    4. 初始化資料庫記錄
    5. 返回 Agent 詳情
    """

@router.post("/{agent_id}/start")
async def start_agent(agent_id: str, request: StartAgentRequest):
    """
    啟動交易代理

    流程:
    1. 檢查 Agent 存在性
    2. 驗證 Agent 狀態（必須為 idle 或 stopped）
    3. 啟動 Agent 執行循環
    4. 推送狀態更新到 WebSocket
    5. 返回啟動結果
    """

@router.put("/{agent_id}/mode")
async def update_agent_mode(agent_id: str, request: UpdateModeRequest):
    """
    切換 Agent 執行模式

    模式說明:
    - TRADING: 執行買賣決策
    - REBALANCING: 優化投資組合配置
    - OBSERVATION: 監控市場尋找機會
    - STRATEGY_REVIEW: 分析績效並調整策略

    流程:
    1. 驗證模式轉換合法性
    2. 記錄模式切換歷史
    3. 更新 Agent 狀態
    4. 推送模式變更事件到 WebSocket
    """
```

**依賴**:

- `agents.core.agent_manager`: Agent 生命週期管理
- `agents.core.models`: Agent 資料模型
- `api.models`: API 請求/響應模型
- `api.websocket`: WebSocket 事件推送

---

### routers/trading.py - 交易數據路由

**功能**:

- 投資組合查詢
- 交易歷史記錄
- 持倉明細
- 績效分析
- 市場數據代理

**核心端點**:

```python
# 投資組合管理
GET    /api/trading/agents/{agent_id}/portfolio     # 取得投資組合
GET    /api/trading/agents/{agent_id}/holdings      # 取得持股明細
GET    /api/trading/agents/{agent_id}/performance   # 取得績效數據

# 交易歷史
GET    /api/trading/agents/{agent_id}/transactions  # 取得交易歷史
GET    /api/trading/agents/{agent_id}/decisions     # 取得決策歷史

# 市場數據
GET    /api/trading/market/stock/{symbol}           # 取得股票價格
POST   /api/trading/market/trade/simulate           # 模擬交易
```

**關鍵實作**:

```python
@router.get("/agents/{agent_id}/portfolio")
async def get_agent_portfolio(agent_id: str):
    """
    取得 Agent 投資組合

    返回內容:
    - 現金餘額
    - 持股明細（股票代碼、數量、成本、市值）
    - 總資產價值
    - 未實現損益
    - 已實現損益
    - 投資組合配置比例

    資料來源:
    - 資料庫: Holdings, Trades, AgentState
    - MCP Client: 即時股價
    """

@router.get("/agents/{agent_id}/performance")
async def get_agent_performance(agent_id: str):
    """
    取得 Agent 績效指標

    計算指標:
    - 總報酬率（%）
    - 年化報酬率
    - 最大回撤（%）
    - 夏普比率
    - 勝率
    - 平均單筆獲利
    - 交易次數

    時間範圍:
    - 今日
    - 本週
    - 本月
    - 自創建以來
    """
```

**依賴**:

- `agents.functions.portfolio_queries`: 投資組合查詢邏輯
- `agents.integrations.mcp_client`: 市場數據獲取
- `database.models`: 資料庫模型

---

### routers/websocket_router.py - WebSocket 路由

**功能**:

- WebSocket 連接管理
- 客戶端訂閱管理
- 即時事件推送

**核心端點**:

```python
WS     /ws                                  # WebSocket 連接端點
```

**關鍵實作**:

```python
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = "default"
):
    """
    WebSocket 連接處理

    連接流程:
    1. 接受 WebSocket 連接
    2. 註冊客戶端到 WebSocketManager
    3. 發送歡迎消息
    4. 持續監聽客戶端消息
    5. 推送服務器事件
    6. 處理斷線重連

    支援的消息類型:
    - subscribe: 訂閱 Agent 事件
    - unsubscribe: 取消訂閱
    - ping: 心跳檢測
    - get_status: 查詢 Agent 狀態
    """
```

**依賴**:

- `api.websocket.WebSocketManager`: WebSocket 管理器

---

## 模型層 (models.py)

### 職責

定義所有 API 請求和響應的數據結構，提供類型安全和數據驗證。

### 核心模型

#### 請求模型

```python
class CreateAgentRequest(BaseModel):
    """創建 Agent 請求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    ai_model: str = Field(default="gpt-4o")
    strategy_type: str = Field(default="balanced")
    strategy_prompt: str = Field(default="")
    initial_funds: float = Field(default=1000000.0, ge=100000.0)
    max_turns: int = Field(default=50, ge=1, le=1000)
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    enabled_tools: dict[str, bool] = Field(default_factory=dict)
    investment_preferences: dict[str, Any] = Field(default_factory=dict)
    custom_instructions: str = Field(default="")

class StartAgentRequest(BaseModel):
    """啟動 Agent 請求"""
    execution_mode: str = Field(default="continuous")
    max_iterations: int | None = Field(default=None)
    stop_on_loss_threshold: float | None = Field(default=None)

class UpdateModeRequest(BaseModel):
    """切換模式請求"""
    mode: AgentMode
    reason: str = Field(default="")
    trigger: str = Field(default="manual")
```

#### 響應模型

```python
class AgentResponse(BaseModel):
    """Agent 響應"""
    id: str
    name: str
    description: str
    ai_model: str
    strategy_type: str
    strategy_prompt: str
    color_theme: str
    current_mode: str
    status: str
    initial_funds: float
    current_funds: float | None
    max_turns: int
    risk_tolerance: float
    enabled_tools: dict[str, bool]
    investment_preferences: dict[str, Any]
    custom_instructions: str
    created_at: datetime
    updated_at: datetime
    portfolio: dict[str, Any] | None
    performance: dict[str, Any] | None

class AgentListResponse(BaseModel):
    """Agent 列表響應"""
    agents: list[AgentResponse]
    total: int

class PortfolioResponse(BaseModel):
    """投資組合響應"""
    agent_id: str
    cash: float
    holdings: list[HoldingData]
    total_value: float
    unrealized_pnl: float
    realized_pnl: float
    allocation: dict[str, float]
    updated_at: datetime
```

**依賴**:

- `pydantic`: 數據驗證和序列化
- `agents.core.models`: Agent 核心模型

---

## WebSocket 層 (websocket.py)

### 職責

管理 WebSocket 連接，實現即時雙向通訊。

### 核心類別

```python
class WebSocketManager:
    """WebSocket 連接管理器"""

    async def startup(self) -> None:
        """啟動 WebSocket 管理器"""

    async def shutdown(self) -> None:
        """關閉所有 WebSocket 連接"""

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """接受新的 WebSocket 連接"""

    async def disconnect(self, client_id: str) -> None:
        """斷開指定客戶端連接"""

    async def broadcast(self, message: dict[str, Any]) -> None:
        """廣播消息給所有連接的客戶端"""

    async def send_to_client(self, client_id: str, message: dict[str, Any]) -> None:
        """發送消息給指定客戶端"""

    async def subscribe_agent(self, client_id: str, agent_id: str) -> None:
        """訂閱 Agent 事件"""

    async def unsubscribe_agent(self, client_id: str, agent_id: str) -> None:
        """取消訂閱 Agent 事件"""

    async def push_agent_event(self, agent_id: str, event: dict[str, Any]) -> None:
        """推送 Agent 事件給訂閱者"""
```

### 事件類型

```python
# Agent 狀態更新
{
    "type": "agent_status",
    "data": {
        "agent_id": "agent_001",
        "status": "running",
        "timestamp": "2025-10-09T10:00:00Z"
    }
}

# Agent 模式切換
{
    "type": "agent_mode_change",
    "data": {
        "agent_id": "agent_001",
        "from_mode": "TRADING",
        "to_mode": "STRATEGY_REVIEW",
        "reason": "績效檢討",
        "timestamp": "2025-10-09T10:05:00Z"
    }
}

# 交易執行
{
    "type": "trade_executed",
    "data": {
        "agent_id": "agent_001",
        "action": "buy",
        "symbol": "2330",
        "quantity": 1000,
        "price": 500.0,
        "timestamp": "2025-10-09T10:10:00Z"
    }
}

# 投資組合更新
{
    "type": "portfolio_update",
    "data": {
        "agent_id": "agent_001",
        "total_value": 1050000.0,
        "unrealized_pnl": 50000.0,
        "timestamp": "2025-10-09T10:15:00Z"
    }
}
```

**依賴**:

- `fastapi.WebSocket`: WebSocket 連接對象
- `loguru`: 日誌記錄

---

## 配置層 (config.py, docs.py)

### config.py - 配置管理

**功能**:

- 環境變量管理
- 應用配置參數
- 日誌配置
- 數據庫連接配置

**核心類別**:

```python
class Settings(BaseSettings):
    """應用配置"""

    # 基本配置
    environment: str = "development"
    debug: bool = True

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS 配置
    cors_origins: list[str] = ["http://localhost:5173"]

    # Agent 配置
    max_agents: int = 10

    # 資料庫配置
    database_url: str = "sqlite+aiosqlite:///./casualtrader.db"

    # OpenAI 配置
    openai_api_key: str = ""

    def setup_logging(self) -> None:
        """設置日誌系統"""
        logger.add(
            "logs/api_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="7 days",
            level="INFO",
        )
```

### docs.py - API 文檔配置

**功能**:

- OpenAPI 標籤定義
- API 分組和描述
- 文檔自定義

**核心函數**:

```python
def get_openapi_tags() -> list[dict[str, str]]:
    """
    定義 API 標籤

    標籤分組:
    - agents: Agent 管理
    - trading: 交易數據
    - websocket: 即時通訊
    - system: 系統管理
    """
```

---

## 模組依賴關係

```
app.py (FastAPI 應用)
├── config.py (配置)
├── docs.py (文檔配置)
├── websocket.py (WebSocket 管理器)
├── routers/
│   ├── agents.py
│   │   ├── models.py (API 模型)
│   │   ├── websocket.py (事件推送)
│   │   └── agents.core.agent_manager (Agent 管理)
│   ├── trading.py
│   │   ├── models.py
│   │   ├── agents.functions.portfolio_queries (查詢邏輯)
│   │   └── agents.integrations.mcp_client (市場數據)
│   └── websocket_router.py
│       └── websocket.py (WebSocket 管理器)
└── server.py (服務器啟動)
```

### 依賴層次

1. **配置層** (config.py, docs.py) - 最底層，無外部依賴
2. **模型層** (models.py) - 依賴 Pydantic 和 Agent 核心模型
3. **WebSocket 層** (websocket.py) - 依賴 FastAPI WebSocket
4. **路由層** (routers/) - 依賴模型層、WebSocket 層、Agent 系統
5. **應用層** (app.py, server.py) - 最頂層，整合所有模組

---

## 互動流程

### 1. Agent 創建流程

```
1. 客戶端發送 POST /api/agents
2. agents.py 接收請求
3. 驗證 CreateAgentRequest
4. 創建 AgentConfig
5. 註冊到 AgentManager
6. 初始化資料庫記錄
7. 返回 AgentResponse
8. 推送 agent_created 事件到 WebSocket
```

### 2. Agent 啟動流程

```
1. 客戶端發送 POST /api/agents/{agent_id}/start
2. agents.py 接收請求
3. 驗證 Agent 狀態
4. 調用 AgentManager.start_agent()
5. 啟動 Agent 執行循環
6. 更新資料庫狀態
7. 推送 agent_status 事件到 WebSocket
8. 返回啟動結果
```

### 3. 投資組合查詢流程

```
1. 客戶端發送 GET /api/trading/agents/{agent_id}/portfolio
2. trading.py 接收請求
3. 調用 PortfolioQueries.get_portfolio_summary()
4. 查詢資料庫（Holdings, Trades）
5. 調用 MCP Client 獲取即時股價
6. 計算未實現損益
7. 組裝 PortfolioResponse
8. 返回結果
```

### 4. WebSocket 即時推送流程

```
1. Agent 執行交易決策
2. 記錄交易到資料庫
3. 調用 websocket_manager.push_agent_event()
4. 查找訂閱該 Agent 的客戶端
5. 組裝 trade_executed 事件
6. 推送到所有訂閱客戶端
7. 客戶端接收並更新 UI
```

---

## 資料流向

### 請求處理流程

```
HTTP Request
    ↓
FastAPI Router (agents.py, trading.py)
    ↓
Request Model Validation (models.py)
    ↓
Business Logic (Agent Manager, Portfolio Queries)
    ↓
Database / MCP Client (資料獲取)
    ↓
Response Model Construction (models.py)
    ↓
HTTP Response
```

### WebSocket 推送流程

```
Agent Event (交易、狀態變更)
    ↓
WebSocketManager.push_agent_event()
    ↓
查找訂閱客戶端
    ↓
組裝事件消息
    ↓
WebSocket.send_json()
    ↓
客戶端接收事件
```

### 應用生命週期

```
啟動階段:
1. 載入配置 (config.py)
2. 設置日誌系統
3. 創建 FastAPI 應用
4. 註冊中間件 (CORS)
5. 註冊路由
6. 啟動 AgentManager
7. 啟動 WebSocketManager
8. 開始監聽請求

關閉階段:
1. 停止接受新請求
2. 關閉所有 WebSocket 連接
3. 停止所有運行中的 Agents
4. 清理資源
5. 關閉資料庫連接
6. 完成關閉
```

---

## 性能優化

### 異步優化

- **全面異步**: 所有 I/O 操作使用 async/await
- **並發請求**: 支援高並發 HTTP 請求
- **WebSocket 異步**: 非阻塞的即時通訊

### 資料庫優化

- **連接池**: SQLAlchemy AsyncEngine 連接池管理
- **查詢優化**: 使用 JOIN 減少查詢次數
- **索引優化**: 關鍵欄位添加索引

### WebSocket 優化

- **心跳機制**: 檢測斷線並自動重連
- **訂閱過濾**: 只推送訂閱的 Agent 事件
- **消息壓縮**: 大型消息啟用壓縮

---

## 錯誤處理

### 統一異常處理

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 異常處理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用異常處理"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat(),
        },
    )
```

### 常見錯誤碼

- **400 Bad Request**: 請求參數錯誤
- **404 Not Found**: Agent 不存在
- **409 Conflict**: Agent 狀態衝突（如重複啟動）
- **500 Internal Server Error**: 服務器內部錯誤

---

## 安全性

### CORS 配置

- 開發環境: 允許 localhost:5173
- 生產環境: 配置具體的前端域名

### 輸入驗證

- Pydantic 模型自動驗證
- 自定義驗證器處理複雜邏輯

### 速率限制

- 建議添加 slowapi 實現 API 速率限制
- 防止 DDoS 攻擊

---

## 監控和日誌

### 結構化日誌

```python
# 請求日誌
logger.info(f"Received {request.method} {request.url}")

# Agent 事件
logger.info(f"Agent {agent_id} started", agent_id=agent_id)

# 錯誤日誌
logger.error(f"Failed to create agent: {e}", exc_info=True)
```

### 日誌輪轉

- 每日輪轉
- 保留 7 天
- 自動壓縮舊日誌

---

## 測試策略

### 單元測試

- 測試路由處理函數
- 測試資料模型驗證
- 測試 WebSocket 管理器

### 整合測試

- 測試完整的 API 流程
- 測試 Agent 創建和啟動
- 測試 WebSocket 即時推送

### 端到端測試

- 模擬真實用戶場景
- 測試前後端整合
- 測試 WebSocket 連接穩定性

---

## 部署建議

### 開發環境

```bash
# 使用 uvicorn 直接啟動
uv run uvicorn src.api.app:create_app --factory --reload
```

### 生產環境

```bash
# 使用 gunicorn + uvicorn workers
gunicorn src.api.app:create_app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker 部署

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "src.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 總結

CasualTrader API 層採用現代化的 FastAPI 架構，提供：

- ✅ **RESTful API**: 完整的 Agent 管理和交易數據接口
- ✅ **WebSocket**: 即時雙向通訊
- ✅ **異步優化**: 高並發性能
- ✅ **自動文檔**: OpenAPI/Swagger 文檔
- ✅ **類型安全**: Pydantic 模型驗證
- ✅ **模塊化設計**: 清晰的職責分離
- ✅ **可擴展性**: 易於添加新路由和功能

這個架構為前端提供了穩定可靠的後端服務，支撐整個 CasualTrader 交易模擬器系統。
