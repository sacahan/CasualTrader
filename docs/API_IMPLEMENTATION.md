# API 實作規格

**版本**: 1.0
**日期**: 2025-10-06
**相關設計**: SYSTEM_DESIGN.md

---

## 📋 概述

本文檔詳述 CasualTrader AI 股票交易模擬器的後端 API 實作規格，包含：

1. **REST API 端點** - 完整的 HTTP API 介面定義
2. **WebSocket 事件** - 即時通信事件規格
3. **資料模型** - API 請求/回應格式
4. **錯誤處理** - 統一的錯誤處理機制
5. **認證授權** - API 安全性實作

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

```

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
  "enable_tracing": true,
  "execution_timeout": 600,
  "risk_tolerance": "moderate"
}
```

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
      "symbol": "2330",
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
      "symbol": "2330",
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
GET    /api/market/stock/{symbol}            # 取得股票價格
GET    /api/market/portfolio/value           # 計算投資組合價值
POST   /api/market/trade/simulate            # 模擬交易
```

**模擬交易 Request**:

```json
{
  "agent_id": "agent_001",
  "action": "buy",
  "symbol": "2330",
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
    symbol: string;
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
      symbol: string;
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

    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """取得股票價格"""
        try:
            result = await self.client.call_tool("get_taiwan_stock_price", {"symbol": symbol})
            return result
        except Exception as e:
            raise APIError(500, f"Failed to get stock price: {str(e)}")

    async def execute_trade(self, agent_id: str, action: str, symbol: str, quantity: int) -> Dict[str, Any]:
        """執行模擬交易"""
        try:
            tool_name = f"{action}_taiwan_stock"
            result = await self.client.call_tool(tool_name, {
                "symbol": symbol,
                "quantity": quantity
            })

            # 記錄交易到資料庫
            await self.record_transaction(agent_id, action, symbol, quantity, result)

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

## ✅ 實作檢查清單

### 核心 API

- [ ] 實作 Agent 管理 CRUD API（包含 AI 模型選擇）
- [ ] 實作 Agent 控制 API (start/stop/pause)
- [ ] 實作模式切換 API
- [ ] 實作投資組合查詢 API
- [ ] 實作交易歷史 API（包含 AI 模型資訊）

### WebSocket 系統

- [ ] 實作 WebSocket 連線管理
- [ ] 實作即時事件推送
- [ ] 實作事件過濾和路由
- [ ] 實作連線狀態監控

### 整合功能

- [ ] 實作 CasualMarket MCP 整合
- [ ] 實作統一錯誤處理
- [ ] 實作 API 認證授權
- [ ] 實作請求頻率限制
- [ ] 實作 API 文檔生成

### 測試

- [ ] 單元測試：API 端點
- [ ] 整合測試：WebSocket 事件
- [ ] 效能測試：並發請求
- [ ] 端到端測試：完整流程

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
