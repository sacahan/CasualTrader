# API 實作規格

**版本**: 1.1
**日期**: 2025-10-08
**相關設計**: SYSTEM_DESIGN.md

---

## 📋 概述

本文檔詳述 CasualTrader AI 股票交易模擬器的後端 API 實作規格，包含：

1. **REST API 端點** - 完整的 HTTP API 介面定義
2. **WebSocket 事件** - 即時通信事件規格
3. **資料模型** - API 請求/回應格式
4. **錯誤處理** - 統一的錯誤處理機制
5. **認證授權** - API 安全性實作
6. **套件依賴清單** - 完整的依賴套件管理
7. **使用文檔** - API 使用指南和測試工具

---

## 🌐 REST API 端點

### 1. Agent 管理 API

#### 1.1 基礎 CRUD 操作

```http
GET    /api/agents                    # 取得所有代理人列表
POST   /api/agents                    # 創建新代理人
GET    /api/agents/{id}               # 取得指定代理人詳情
PUT    /api/agents/{id}               # 更新代理人設定
DELETE /api/agents/{id}               # 刪除代理人
```

**創建代理人 Request** (基於 OpenAI Agents SDK):

```json
{
  "name": "Prudent Investor",
  "description": "穩健投資策略代理人",
  "ai_model": "gpt-4o",
  "strategy_type": "conservative",
  "strategy_prompt": "保守投資策略，專注於穩定成長...",
  "color_theme": "#007bff",
  "initial_funds": 1000000.0,
  "max_turns": 50,
  "risk_tolerance": 0.3,

  "enabled_tools": {
    "fundamental_analysis": true,
    "technical_analysis": true,
    "risk_assessment": true,
    "sentiment_analysis": false,
    "web_search": true,
    "code_interpreter": false
  },

  "investment_preferences": {
    "preferred_sectors": ["技術業", "金融業"],
    "excluded_stocks": ["2498", "2609"],
    "max_position_size": 0.15,
    "rebalance_frequency": "weekly"
  },

  "custom_instructions": "重點關注ESG評級較高的公司"
}
```

**支援的 AI 模型列表** (`ai_model` 欄位):

- **OpenAI 系列**:
  - `gpt-4o` (推薦，預設值)
  - `gpt-4o-mini` (成本優化)
  - `gpt-4-turbo`

- **Anthropic Claude 系列**:
  - `claude-sonnet-4.5` (高性能推理)
  - `claude-opus-4`

- **Google Gemini 系列**:
  - `gemini-2.5-pro` (多模態能力)
  - `gemini-2.0-flash` (快速響應)

- **其他模型**:
  - `deepseek-v3`
  - `grok-2`

**模型選擇說明**:

- 前端下拉選單提供模型選擇
- 預設值為 `gpt-4o`（平衡性能與成本）
- 模型資訊在 Agent 創建時保存，執行期間記錄在交易與策略變更記錄中

**Response**:

```json
{
  "id": "agent_001",
  "name": "Prudent Investor",
  "description": "穩健投資策略代理人",
  "ai_model": "gpt-4o",
  "strategy_type": "conservative",
  "strategy_prompt": "保守投資策略...",
  "color_theme": "#007bff",
  "current_mode": "TRADING",
  "status": "stopped",
  "initial_funds": 1000000.0,
  "max_turns": 50,
  "risk_tolerance": 0.3,

  "enabled_tools": {
    "fundamental_analysis": true,
    "technical_analysis": true,
    "risk_assessment": true,
    "sentiment_analysis": false,
    "web_search": true,
    "code_interpreter": false
  },

  "investment_preferences": {
    "preferred_sectors": ["技術業", "金融業"],
    "excluded_stocks": ["2498", "2609"],
    "max_position_size": 0.15,
    "rebalance_frequency": "weekly"
  },

  "custom_instructions": "重點關注ESG評級較高的公司",
  "created_at": "2025-10-06T10:00:00Z",
  "updated_at": "2025-10-06T10:00:00Z"
}
```

#### 1.2 Agent 執行控制

```http
POST   /api/agents/{id}/start         # 啟動代理人
POST   /api/agents/{id}/stop          # 停止代理人
POST   /api/agents/{id}/pause         # 暫停代理人
POST   /api/agents/{id}/resume        # 恢復代理人
PUT    /api/agents/{id}/strategy      # 更新策略
POST   /api/agents/{id}/reset         # 重置帳戶
```

**啟動代理人 Request**:

```json
{
  "execution_mode": "continuous", // continuous | single_cycle
  "max_cycles": 100, // 最大執行週期數
  "stop_on_loss_threshold": 0.15 // 虧損停止閾值
}
```

#### 1.3 Agent 模式控制

```http
GET    /api/agents/{id}/mode          # 取得當前執行模式
PUT    /api/agents/{id}/mode          # 切換執行模式
GET    /api/agents/{id}/mode-history  # 取得模式切換歷史
```

**切換模式 Request**:

```json
{
  "mode": "strategy_review",
  "reason": "手動切換到策略檢討模式",
  "trigger": "manual"
}
```

**模式歷史 Response**:

```json
{
  "transitions": [
    {
      "id": "transition_001",
      "from_mode": "trading",
      "to_mode": "strategy_review",
      "timestamp": "2025-10-06T14:30:00Z",
      "reason": "虧損超過 10%",
      "trigger": "system",
      "portfolio_snapshot": {...}
    }
  ]
}
```

#### 1.4 Agent 配置管理

```http
GET    /api/agents/{id}/config        # 取得執行配置
PUT    /api/agents/{id}/config        # 更新執行配置
```

**配置更新 Request**:

```json
{
  "max_turns": 50,
  "execution_timeout": 600,
  "risk_tolerance": "moderate"
}
```

**註**: OpenAI Agents SDK trace 預設自動啟用,無需額外配置。詳見 `AGENT_IMPLEMENTATION.md` 的「執行追蹤」章節。

### 2. 投資組合與交易 API

#### 2.1 投資組合管理

```http
GET    /api/agents/{id}/portfolio     # 取得投資組合
GET    /api/agents/{id}/holdings      # 取得持股明細
GET    /api/agents/{id}/performance   # 取得績效數據
```

**投資組合 Response**:

```json
{
  "agent_id": "agent_001",
  "total_value": 1150000.0,
  "cash_balance": 200000.0,
  "invested_value": 950000.0,
  "total_return": 0.15,
  "daily_return": 0.02,
  "holdings": [
    {
      "ticker": "2330",
      "quantity": 1000,
      "average_cost": 580.0,
      "current_price": 595.0,
      "market_value": 595000.0,
      "unrealized_pnl": 15000.0
    }
  ],
  "updated_at": "2025-10-06T15:00:00Z"
}
```

#### 2.2 交易歷史

```http
GET    /api/agents/{id}/transactions  # 取得交易歷史
GET    /api/agents/{id}/decisions     # 取得決策歷史
```

**交易歷史 Response**:

```json
{
  "transactions": [
    {
      "id": "tx_001",
      "agent_id": "agent_001",
      "ticker": "2330",
      "action": "buy",
      "quantity": 1000,
      "price": 580.0,
      "total_amount": 580000.0,
      "fees": 1160.0,
      "timestamp": "2025-10-06T09:30:00Z",
      "reason": "技術分析顯示突破阻力位"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45
  }
}
```

### 3. 追蹤系統 API

#### 3.1 追蹤記錄查詢

```http
GET    /api/traces/{agent_id}                 # 取得追蹤歷史
GET    /api/traces/{agent_id}/{trace_id}      # 取得特定追蹤詳情
DELETE /api/traces/{agent_id}/{trace_id}      # 刪除追蹤記錄
GET    /api/traces/stats/{agent_id}           # 取得追蹤統計
```

**追蹤歷史 Query Parameters**:

```
?limit=10&mode=trading&from=2025-10-01&to=2025-10-06
```

**追蹤詳情 Response**:

```json
{
  "trace_id": "agent_001_trading_20251006_143025",
  "trace_name": "agent_001-trading",
  "agent_id": "agent_001",
  "mode": "trading",
  "timestamp": "2025-10-06T14:30:25Z",
  "execution_time_seconds": 45.2,
  "turns_used": 12,
  "final_output": "完成交易決策，買入台積電 1000 股...",
  "tools_called": ["get_taiwan_stock_price", "buy_taiwan_stock"],
  "error_occurred": false,
  "detailed_log": {...}
}
```

### 4. 市場數據 API

#### 4.1 市場數據代理

```http
GET    /api/market/stock/{ticker}            # 取得股票價格
GET    /api/market/portfolio/value           # 計算投資組合價值
POST   /api/market/trade/simulate            # 模擬交易
```

**模擬交易 Request**:

```json
{
  "agent_id": "agent_001",
  "action": "buy",
  "ticker": "2330",
  "quantity": 1000,
  "price_type": "market" // market | limit
}
```

### 5. 系統管理 API

#### 5.1 系統狀態

```http
GET    /api/system/health                    # 系統健康檢查
GET    /api/system/stats                     # 系統統計
POST   /api/system/maintenance               # 進入維護模式
```

---

## 📡 WebSocket 事件規格

### 1. 連線管理

**連線端點**: `ws://localhost:8000/ws`

**認證**: 透過 query parameter 或 header 傳遞 token

### 2. 事件類型定義

```typescript
interface WebSocketEvent {
  type:
    | "agent_status" // Agent 狀態變更
    | "agent_mode_change" // Agent 模式切換
    | "trade_executed" // 交易執行
    | "portfolio_update" // 投資組合更新
    | "trace_completed" // 追蹤完成
    | "market_update" // 市場數據更新
    | "strategy_adjustment" // 策略調整
    | "system_notification"; // 系統通知
  timestamp: string;
  data: any;
}
```

### 3. 具體事件規格

#### 3.1 Agent 狀態事件

```typescript
interface AgentStatusEvent {
  type: "agent_status";
  agent_id: string;
  status: "running" | "stopped" | "paused" | "error";
  current_mode: "trading" | "rebalancing" | "strategy_review" | "observation";
  message?: string;
  execution_info?: {
    cycle_count: number;
    last_action: string;
    next_execution_at: string;
  };
}
```

#### 3.2 模式切換事件

```typescript
interface AgentModeChangeEvent {
  type: "agent_mode_change";
  agent_id: string;
  from_mode: string;
  to_mode: string;
  reason: string;
  trigger: "system" | "agent" | "manual";
  timestamp: string;
  portfolio_impact?: {
    before_value: number;
    after_value: number;
  };
}
```

#### 3.3 交易執行事件

```typescript
interface TradeExecutedEvent {
  type: "trade_executed";
  agent_id: string;
  transaction: {
    id: string;
    ticker: string;
    action: "buy" | "sell";
    quantity: number;
    price: number;
    total_amount: number;
    fees: number;
  };
  decision_context: {
    reasoning: string;
    confidence_score: number;
    risk_assessment: string;
  };
  portfolio_update: {
    new_total_value: number;
    new_cash_balance: number;
    return_rate: number;
  };
}
```

#### 3.4 追蹤完成事件

```typescript
interface TraceCompletedEvent {
  type: "trace_completed";
  agent_id: string;
  trace_id: string;
  trace_name: string;
  mode: string;
  turns_used: number;
  execution_time_seconds: number;
  summary: string;
  outcome: "success" | "error" | "timeout";
  timestamp: string;
}
```

#### 3.5 投資組合更新事件

```typescript
interface PortfolioUpdateEvent {
  type: "portfolio_update";
  agent_id: string;
  portfolio: {
    total_value: number;
    cash_balance: number;
    invested_value: number;
    total_return: number;
    daily_change: number;
    holdings: Array<{
      ticker: string;
      quantity: number;
      market_value: number;
      unrealized_pnl: number;
    }>;
  };
  trigger: "trade" | "market_close" | "manual_refresh";
}
```

---

## 🔧 實作詳細規格

### 1. FastAPI 應用架構

```python
from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="CasualTrader API",
    description="AI 股票交易模擬器 API",
    version="1.0.0"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由組織
from .routers import agents, portfolio, traces, market, system

app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(traces.router, prefix="/api/traces", tags=["traces"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
```

### 2. 資料模型定義

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AgentStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    ERROR = "error"

class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    ai_model: str = Field(..., regex="^(gpt-4o|gpt-4o-mini|deepseek|grok|gemini)$")
    strategy_prompt: str = Field(..., min_length=10)
    color_theme: str = Field(default="#007bff", regex="^#[0-9A-Fa-f]{6}$")
    initial_funds: float = Field(default=1000000.0, ge=100000.0, le=10000000.0)

class AgentResponse(BaseModel):
    id: str
    name: str
    ai_model: str
    strategy_prompt: str
    color_theme: str
    current_mode: AgentMode
    status: AgentStatus
    initial_funds: float
    created_at: datetime
    updated_at: datetime

class PortfolioResponse(BaseModel):
    agent_id: str
    total_value: float
    cash_balance: float
    invested_value: float
    total_return: float
    daily_return: float
    holdings: List[Dict[str, Any]]
    updated_at: datetime
```

### 3. 錯誤處理機制

```python
from fastapi import HTTPException
from typing import Dict, Any

class APIError(Exception):
    def __init__(self, status_code: int, message: str, details: Dict[str, Any] = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}

class AgentNotFoundError(APIError):
    def __init__(self, agent_id: str):
        super().__init__(404, f"Agent {agent_id} not found")

class InvalidModeTransitionError(APIError):
    def __init__(self, from_mode: str, to_mode: str):
        super().__init__(400, f"Invalid mode transition from {from_mode} to {to_mode}")

@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now().isoformat()
            }
        }
    )
```

### 4. WebSocket 連線管理

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    self.disconnect(connection, client_id)

    async def broadcast(self, message: dict):
        for client_connections in self.active_connections.values():
            for connection in client_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    pass

manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = "default"):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 處理客戶端訊息
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
```

### 5. CasualMarket MCP 整合

**外部依賴專案**:

- **GitHub**: <https://github.com/sacahan/CasualMarket>
- **功能**: 台灣股票市場數據 MCP 服務
- **安裝**: `uvx --from git+https://github.com/sacahan/CasualMarket.git market-mcp-server`

```python
class CasualMarketMCPClient:
    """CasualMarket MCP 客戶端包裝器，整合外部 CasualMarket 專案"""

    def __init__(self):
        self.client = None  # MCP 客戶端實例

    async def get_stock_price(self, ticker: str) -> Dict[str, Any]:
        """取得股票價格"""
        try:
            result = await self.client.call_tool("get_taiwan_stock_price", {"ticker": ticker})
            return result
        except Exception as e:
            raise APIError(500, f"Failed to get stock price: {str(e)}")

    async def execute_trade(self, agent_id: str, action: str, ticker: str, quantity: int) -> Dict[str, Any]:
        """執行模擬交易"""
        try:
            tool_name = f"{action}_taiwan_stock"
            result = await self.client.call_tool(tool_name, {
                "ticker": ticker,
                "quantity": quantity
            })

            # 記錄交易到資料庫
            await self.record_transaction(agent_id, action, ticker, quantity, result)

            return result
        except Exception as e:
            raise APIError(500, f"Failed to execute trade: {str(e)}")
```

---

## 📁 檔案結構

> **注意**: 完整的專案結構定義請參閱 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
> 本節僅列出與 API 系統直接相關的檔案。

### API 系統相關檔案

```
backend/src/api/                   # FastAPI 應用模塊
├── main.py                        # FastAPI 應用主檔案
├── routers/                       # API 路由定義
│   ├── agents.py                  # Agent 管理路由
│   ├── portfolio.py               # 投資組合路由
│   ├── strategy_changes.py        # 策略變更路由
│   ├── traces.py                  # 追蹤系統路由
│   ├── market.py                  # 市場數據路由
│   └── system.py                  # 系統管理路由
├── models/                        # API 資料模型
│   ├── requests.py                # API 請求模型
│   ├── responses.py               # API 回應模型
│   └── websocket_events.py        # WebSocket 事件模型
├── services/                      # 業務邏輯服務層
│   ├── agent_service.py           # Agent 業務邏輯
│   ├── portfolio_service.py       # 投資組合服務
│   ├── strategy_service.py        # 策略變更服務
│   ├── trace_service.py           # 追蹤服務
│   ├── websocket_service.py       # 即時通知服務
│   └── mcp_client_wrapper.py      # MCP 客戶端包裝
├── middleware/                    # FastAPI 中間件
│   ├── auth.py                    # 認證中間件
│   ├── rate_limit.py              # 頻率限制
│   └── logging.py                 # 請求日誌
└── utils/                         # API 工具函數
    ├── exceptions.py              # 自定義異常
    ├── validators.py              # 資料驗證
    └── websocket_manager.py       # WebSocket 管理

backend/src/shared/                # 共享組件
├── database/                      # 資料庫相關
│   ├── models.py                  # 資料模型
│   ├── connection.py              # 資料庫連接
│   └── migrations/                # 資料庫遷移
├── utils/                         # 共享工具
│   ├── logging.py                 # 統一日誌
│   ├── config.py                  # 配置管理
│   └── constants.py               # 常數定義
└── types/                         # 共享類型定義
    ├── api_types.py               # API 類型
    ├── agent_types.py             # Agent 類型
    └── market_types.py            # 市場資料類型

tests/backend/api/                 # API 測試
├── test_main.py                   # FastAPI 主應用測試
├── routers/                       # 路由測試
│   ├── test_agents.py             # Agent 路由測試
│   ├── test_portfolio.py          # 投資組合路由測試
│   ├── test_strategy_changes.py   # 策略變更路由測試
│   ├── test_traces.py             # 追蹤路由測試
│   ├── test_market.py             # 市場數據路由測試
│   └── test_system.py             # 系統路由測試
├── services/                      # 服務層測試
│   ├── test_agent_service.py      # Agent 服務測試
│   ├── test_portfolio_service.py  # 投資組合服務測試
│   ├── test_strategy_service.py   # 策略變更服務測試
│   └── test_trace_service.py      # 追蹤服務測試
├── middleware/                    # 中間件測試
│   ├── test_auth.py               # 認證測試
│   └── test_rate_limit.py         # 頻率限制測試
└── utils/                         # 工具測試
    ├── test_exceptions.py         # 異常處理測試
    ├── test_validators.py         # 驗證器測試
    └── test_websocket_manager.py  # WebSocket 管理測試

tests/backend/shared/              # 共享組件測試
├── database/
│   └── test_models.py
└── utils/
    ├── test_config.py
    └── test_logging.py

tests/integration/                 # 跨模塊整合測試
├── test_api_agent_integration.py  # API-Agent 整合測試
│   ├── test_websocket_flow.py     # WebSocket 流程測試
│   └── test_mcp_integration.py    # MCP 整合測試
└── fixtures/                      # 測試用固定數據
    ├── agent_data.json
    ├── portfolio_data.json
    ├── market_data.json
    └── websocket_events.json
```

---

## 📊 資料庫 Schema 更新

### AI 模型追蹤

為了支援多 AI 模型功能，資料庫 schema 已更新以追蹤模型使用情況：

**agents 表** - 記錄 Agent 使用的 AI 模型:

```sql
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    model TEXT NOT NULL DEFAULT 'gpt-4o',  -- AI 模型選擇
    -- ... 其他欄位
);
```

**transactions 表** - 記錄交易時使用的 AI 模型:

```sql
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    -- ... 交易資訊
    ai_model TEXT,                          -- 執行交易時使用的 AI 模型
    -- ... 其他欄位
);
```

**strategy_changes 表** - 記錄策略變更時使用的 AI 模型:

```sql
CREATE TABLE IF NOT EXISTS strategy_changes (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    -- ... 變更資訊
    ai_model TEXT,                          -- 進行策略變更時使用的 AI 模型
    -- ... 其他欄位
);
```

### 模型追蹤目的

1. **模型比較**: 比較不同 AI 模型的投資績效與決策品質
2. **成本分析**: 追蹤不同模型的 API 使用成本
3. **決策追溯**: 了解特定交易或策略變更背後使用的模型
4. **效能評估**: 評估不同模型在不同市場條件下的表現

---

## 📦 套件依賴清單

### 核心依賴套件

#### 1. Web 框架和 API

```toml
# 主要 Web 框架
"fastapi>=0.104.0"          # 現代化異步 Web 框架
"uvicorn[standard]>=0.24.0" # ASGI 服務器
"websockets>=12.0"          # WebSocket 支援

# 中間件和擴展
"fastapi-cors>=1.0.0"       # CORS 支援
"fastapi-limiter>=0.1.5"    # API 速率限制
```

#### 2. 數據驗證和模型

```toml
"pydantic>=2.5.0"           # 數據驗證和序列化
"pydantic-settings>=2.1.0"  # 設定管理
"typing-extensions>=4.8.0"  # 類型提示擴展
```

#### 3. 資料庫和 ORM

```toml
"sqlalchemy>=2.0.0"         # ORM 框架
"alembic>=1.13.0"          # 資料庫遷移
"asyncpg>=0.29.0"          # PostgreSQL 異步驅動
"aiosqlite>=0.19.0"        # SQLite 異步驅動（開發用）
```

#### 4. 快取和會話

```toml
"redis>=5.0.0"             # Redis 客戶端
"aioredis>=2.0.0"          # Redis 異步客戶端
"python-memcached>=1.62"   # Memcached 支援（可選）
```

#### 5. AI 和 Agent 整合

```toml
"openai>=1.30.0"           # OpenAI API 客戶端
"openai-agents>=0.1.0"     # OpenAI Agent SDK
"anthropic>=0.25.0"        # Claude API（可選）
```

#### 6. MCP 工具整合

```toml
"casual-market-mcp>=1.0.0" # 台灣股市 MCP 工具
"mcp>=1.0.0"               # Model Context Protocol 核心
"fastmcp>=2.7.0"           # FastMCP 框架
```

#### 7. HTTP 客戶端和網路

```toml
"httpx>=0.25.0"            # 現代化 HTTP 客戶端
"aiohttp>=3.9.0"           # 異步 HTTP 客戶端
"requests>=2.31.0"         # 傳統 HTTP 客戶端（相容性）
```

#### 8. 日誌和監控

```toml
"structlog>=23.2.0"        # 結構化日誌
"loguru>=0.7.0"            # 簡化日誌記錄
"prometheus-client>=0.19.0" # Prometheus 指標
"sentry-sdk[fastapi]>=1.38.0" # 錯誤追蹤（生產環境）
```

#### 9. 安全性

```toml
"passlib[bcrypt]>=1.7.4"   # 密碼雜湊
"python-jose[cryptography]>=3.3.0" # JWT 處理
"python-multipart>=0.0.6"  # 表單數據處理
"cryptography>=41.0.0"     # 加密工具
```

#### 10. 環境和配置

```toml
"python-dotenv>=1.0.0"     # 環境變數載入
"pyyaml>=6.0.1"            # YAML 配置支援
"click>=8.1.0"             # CLI 工具
```

### 開發依賴套件

```toml
[project.optional-dependencies]
dev = [
    # 測試框架
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "pytest-xdist>=3.5.0",     # 並行測試

    # 代碼品質
    "ruff>=0.1.0",              # Linting 和格式化
    "mypy>=1.7.0",              # 類型檢查
    "black>=23.11.0",           # 代碼格式化
    "isort>=5.12.0",            # import 排序

    # 開發工具
    "pre-commit>=3.6.0",        # Git hooks
    "ipython>=8.17.0",          # 互動式 Python
    "jupyter>=1.0.0",           # Jupyter Notebook
    "watchdog>=3.0.0",          # 檔案監控

    # 文檔生成
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.4.0",
    "mkdocs-mermaid2-plugin>=1.1.0",

    # 效能分析
    "memory-profiler>=0.61.0",
    "py-spy>=0.3.14",
]
```

---

## 📚 API 使用文檔

### 快速開始

#### 啟動服務

```bash
# 方式 1: 使用統一啟動腳本 (推薦)
./scripts/start.sh -b              # 僅啟動後端 API
./scripts/start.sh                 # 同時啟動前後端

# 方式 2: 直接使用 uvicorn
uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

#### 訪問文檔

- **Swagger UI**: <http://localhost:8000/api/docs>
- **ReDoc**: <http://localhost:8000/api/redoc>
- **OpenAPI JSON**: <http://localhost:8000/api/openapi.json>

### 環境配置

#### .env 文件配置

創建 `.env` 文件並配置以下參數：

```bash
# API Server Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_WORKERS=1

# CORS Settings
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
CORS_ALLOW_CREDENTIALS=true

# Logging Settings
LOG_LEVEL=INFO
LOG_FORMAT=<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>
LOG_FILE=logs/api_{time:YYYY-MM-DD}.log
LOG_ROTATION=500 MB
LOG_RETENTION=30 days
LOG_COMPRESSION=zip

# Database Settings
DATABASE_URL=sqlite+aiosqlite:///./casualtrader.db
DATABASE_ECHO=false

# Agent Settings
MAX_AGENTS=10
DEFAULT_AI_MODEL=gpt-4o-mini
DEFAULT_INITIAL_CAPITAL=1000000

# WebSocket Settings
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100

# Environment
ENVIRONMENT=development
DEBUG=true
```

### 日誌系統

#### 日誌級別

- `DEBUG`: 詳細的除錯資訊
- `INFO`: 一般資訊訊息
- `WARNING`: 警告訊息
- `ERROR`: 錯誤訊息
- `CRITICAL`: 嚴重錯誤

#### 日誌格式

```
2025-10-08 12:15:30.123 | INFO     | src.api.app:create_app:65 - Creating FastAPI application...
2025-10-08 12:15:35.456 | INFO     | src.api.routers.agents:create_agent:80 - Creating new agent: 積極型成長投資者
2025-10-08 12:15:40.789 | SUCCESS  | src.api.routers.agents:create_agent:95 - Agent created successfully: agent_20251008_123456
```

#### 查看日誌

```bash
# 查看最新日誌
tail -f logs/api_$(date +%Y-%m-%d).log

# 查看特定級別日誌
grep "ERROR" logs/api_2025-10-08.log

# 查看特定代理的日誌
grep "agent_20251008_123456" logs/api_2025-10-08.log
```

### 測試工具

#### 使用 curl 測試

```bash
# 健康檢查
curl http://localhost:8000/api/health

# 創建代理
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試代理",
    "ai_model": "gpt-4o-mini",
    "strategy_prompt": "穩健投資",
    "initial_funds": 1000000
  }'

# 列出代理
curl http://localhost:8000/api/agents

# 查詢投資組合
curl http://localhost:8000/api/trading/agents/{agent_id}/portfolio
```

#### 使用 Python 測試

```python
import requests

# API 基礎 URL
BASE_URL = "http://localhost:8000/api"

# 創建代理
response = requests.post(
    f"{BASE_URL}/agents",
    json={
        "name": "測試代理",
        "ai_model": "gpt-4o-mini",
        "strategy_prompt": "穩健投資",
        "initial_funds": 1000000
    }
)
agent = response.json()
print(f"代理已創建: {agent['id']}")

# 啟動代理
requests.post(
    f"{BASE_URL}/agents/{agent['id']}/start",
    json={"mode": "TRADING"}
)

# 查詢投資組合
portfolio = requests.get(
    f"{BASE_URL}/trading/agents/{agent['id']}/portfolio"
).json()
print(f"投資組合: {portfolio}")
```

### 效能優化建議

1. **連接池**: 使用 HTTP 連接池重用連接
2. **批量操作**: 使用分頁參數避免一次查詢大量數據
3. **WebSocket**: 使用 WebSocket 接收即時更新，減少輪詢
4. **快取**: 適當快取不常變動的數據
5. **壓縮**: 啟用 gzip 壓縮減少傳輸數據量

### 安全建議

1. **生產環境**: 設置 `ENVIRONMENT=production` 和 `DEBUG=false`
2. **CORS**: 限制 `CORS_ORIGINS` 為可信域名
3. **HTTPS**: 生產環境使用 HTTPS
4. **認證**: 添加 API 認證機制
5. **限流**: 啟用 API 請求限流

---

## ✅ 實作檢查清單

### 🔧 環境設定與基礎架構

#### 開發環境準備

- [ ] 設定 `.env` 環境配置文件
- [ ] 配置 Python 虛擬環境 (uv/venv)
- [ ] 設定 Git hooks 和 pre-commit
- [ ] 配置 IDE/編輯器 (VS Code extensions)

#### 日誌與監控系統

- [ ] 配置日誌系統 (Loguru 結構化日誌)
- [ ] 設定日誌輪轉和壓縮
- [ ] 配置錯誤追蹤 (Sentry SDK)
- [ ] 設定 Prometheus 監控指標

#### 資料庫設定

- [ ] 配置 SQLAlchemy 異步連接
- [ ] 設定資料庫遷移 (Alembic)
- [ ] 建立 AI 模型追蹤 Schema
- [ ] 配置連接池與效能調優

#### 快取與會話管理

- [ ] 設定 Redis 異步客戶端
- [ ] 配置會話管理
- [ ] 實作快取策略
- [ ] 設定快取過期策略

### 📦 套件依賴管理

#### 核心框架安裝

- [ ] 安裝 FastAPI + Uvicorn (Web 框架)
- [ ] 安裝 Pydantic v2 (資料驗證)
- [ ] 安裝 SQLAlchemy 2.0+ (ORM)
- [ ] 安裝 WebSocket 支援套件

#### AI 與 Agent 整合

- [ ] 安裝 OpenAI SDK (>= 1.30.0)
- [ ] 安裝 OpenAI Agents SDK
- [ ] 安裝 Anthropic Claude API (可選)
- [ ] 安裝 Google Gemini API (可選)

#### MCP 工具整合

- [ ] 安裝 CasualMarket MCP 客戶端
- [ ] 配置 MCP 連接設定
- [ ] 測試 MCP 工具連接
- [ ] 實作 MCP 錯誤處理

#### 開發工具套件

- [ ] 安裝測試框架 (pytest + asyncio)
- [ ] 安裝代碼品質工具 (ruff, mypy, black)
- [ ] 安裝文檔生成工具 (mkdocs)
- [ ] 安裝效能分析工具 (py-spy, memory-profiler)

### 🌐 REST API 端點實作

#### Agent 管理 API

- [ ] 實作 Agent CRUD 操作
  - [ ] `GET /api/agents` - 列出所有代理
  - [ ] `POST /api/agents` - 創建新代理
  - [ ] `GET /api/agents/{id}` - 取得代理詳情
  - [ ] `PUT /api/agents/{id}` - 更新代理設定
  - [ ] `DELETE /api/agents/{id}` - 刪除代理
- [ ] 實作 AI 模型選擇功能
- [ ] 實作代理配置驗證
- [ ] 實作代理狀態管理

#### Agent 執行控制 API

- [ ] 實作執行控制端點
  - [ ] `POST /api/agents/{id}/start` - 啟動代理
  - [ ] `POST /api/agents/{id}/stop` - 停止代理
  - [ ] `POST /api/agents/{id}/pause` - 暫停代理
  - [ ] `POST /api/agents/{id}/resume` - 恢復代理
- [ ] 實作模式切換功能
- [ ] 實作策略更新機制
- [ ] 實作帳戶重置功能

#### 投資組合與交易 API

- [ ] 實作投資組合查詢
  - [ ] `GET /api/agents/{id}/portfolio` - 投資組合總覽
  - [ ] `GET /api/agents/{id}/holdings` - 持股明細
  - [ ] `GET /api/agents/{id}/performance` - 績效數據
- [ ] 實作交易歷史查詢
  - [ ] `GET /api/agents/{id}/transactions` - 交易記錄
  - [ ] `GET /api/agents/{id}/decisions` - 決策歷史
- [ ] 整合 AI 模型資訊追蹤

#### 追蹤系統 API

- [ ] 實作追蹤記錄查詢
  - [ ] `GET /api/traces/{agent_id}` - 追蹤歷史
  - [ ] `GET /api/traces/{agent_id}/{trace_id}` - 追蹤詳情
  - [ ] `DELETE /api/traces/{agent_id}/{trace_id}` - 刪除記錄
- [ ] 實作追蹤統計分析
- [ ] 實作追蹤數據過濾

#### 市場數據 API

- [ ] 實作市場數據代理
  - [ ] `GET /api/market/stock/{ticker}` - 股票價格
  - [ ] `GET /api/market/portfolio/value` - 組合估值
  - [ ] `POST /api/market/trade/simulate` - 模擬交易
- [ ] 整合 CasualMarket MCP 服務

#### 系統管理 API

- [ ] 實作系統狀態端點
  - [ ] `GET /api/system/health` - 健康檢查
  - [ ] `GET /api/system/stats` - 系統統計
  - [ ] `POST /api/system/maintenance` - 維護模式
- [ ] 實作系統監控功能

### 📡 WebSocket 即時通訊系統

#### 連線管理

- [ ] 實作 WebSocket 連線管理器
- [ ] 實作客戶端認證機制
- [ ] 實作連線心跳檢測
- [ ] 實作自動重連機制

#### 事件系統

- [ ] 實作事件類型定義
- [ ] 實作 Agent 狀態事件
- [ ] 實作交易執行事件
- [ ] 實作投資組合更新事件
- [ ] 實作追蹤完成事件
- [ ] 實作策略調整事件

#### 事件路由與過濾

- [ ] 實作事件廣播機制
- [ ] 實作個人化訊息推送
- [ ] 實作事件過濾規則
- [ ] 實作事件訂閱管理

### 🔐 安全性與中間件

#### 認證授權

- [ ] 實作 API 認證中間件
- [ ] 實作 JWT 令牌處理
- [ ] 實作權限驗證
- [ ] 實作會話管理

#### 安全防護

- [ ] 實作 CORS 中間件設定
- [ ] 實作 API 請求頻率限制
- [ ] 實作輸入驗證與清理
- [ ] 實作 SQL 注入防護

#### 錯誤處理

- [ ] 實作統一異常處理器
- [ ] 實作自定義異常類別
- [ ] 實作錯誤日誌記錄
- [ ] 實作用戶友好錯誤回應

### 🧪 測試與品質保證

#### 單元測試

- [ ] API 端點測試
- [ ] 服務層邏輯測試
- [ ] 資料模型驗證測試
- [ ] 工具函數測試

#### 整合測試

- [ ] API-Agent 整合測試
- [ ] WebSocket 流程測試
- [ ] MCP 工具整合測試
- [ ] 資料庫操作測試

#### 效能測試

- [ ] API 並發請求測試
- [ ] WebSocket 連線壓力測試
- [ ] 資料庫查詢效能測試
- [ ] 記憶體使用分析

#### 端到端測試

- [ ] 完整交易流程測試
- [ ] 多代理並行測試
- [ ] 錯誤恢復測試
- [ ] 系統整體功能測試

### 📊 監控與維運

#### 效能監控

- [ ] 設定 API 回應時間監控
- [ ] 設定資料庫查詢效能監控
- [ ] 設定記憶體與 CPU 使用監控
- [ ] 設定錯誤率監控

#### 日誌分析

- [ ] 設定結構化日誌格式
- [ ] 設定日誌聚合與搜尋
- [ ] 設定關鍵指標儀表板
- [ ] 設定告警規則

#### 部署準備

- [ ] 設定容器化 (Docker)
- [ ] 設定環境變數管理
- [ ] 設定負載均衡配置
- [ ] 設定備份與恢復策略

### 📚 文檔與維護

#### API 文檔

- [ ] 生成 OpenAPI 規格
- [ ] 設定 Swagger UI
- [ ] 設定 ReDoc 文檔
- [ ] 編寫 API 使用範例

#### 開發文檔

- [ ] 更新專案 README
- [ ] 編寫部署指南
- [ ] 編寫故障排除指南
- [ ] 編寫效能調優指南

#### 測試工具

- [ ] 提供 curl 測試腳本
- [ ] 提供 Python 測試客戶端
- [ ] 提供 WebSocket 測試工具
- [ ] 提供負載測試腳本

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-08
**整合來源**: API_DEPENDENCIES.md + API_DOCUMENTATION.md
