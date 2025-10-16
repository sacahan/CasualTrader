# 缺失的後端 API 路由

## 概述

此文檔列出了前端 `api.js` 中調用但後端尚未實現的 API 端點。

## 📋 需要實現的路由

### 1. Agent CRUD 路由 (`/api/agents`)

**建議創建**: `backend/src/api/routers/agents.py`

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("")
async def list_agents():
    """列出所有 agents"""
    pass

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """取得單一 agent 詳情"""
    pass

@router.post("")
async def create_agent(agent_data: dict):
    """創建新 agent"""
    pass

@router.put("/{agent_id}")
async def update_agent(agent_id: str, updates: dict):
    """更新 agent 配置"""
    pass

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """刪除 agent"""
    pass

@router.post("/{agent_id}/mode")
async def switch_agent_mode(agent_id: str, mode: str):
    """切換 agent 模式"""
    pass

@router.post("/{agent_id}/reset")
async def reset_agent(agent_id: str):
    """重置 agent (清除投資組合和歷史)"""
    pass
```

### 2. Trading & Portfolio 路由 (`/api/trading`)

**建議創建**: `backend/src/api/routers/trading.py`

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/trading", tags=["trading"])

@router.get("/agents/{agent_id}/portfolio")
async def get_portfolio(agent_id: str):
    """取得投資組合"""
    pass

@router.get("/agents/{agent_id}/trades")
async def get_trades(agent_id: str, limit: int = 50, offset: int = 0):
    """取得交易記錄"""
    pass

@router.get("/agents/{agent_id}/performance")
async def get_performance(agent_id: str):
    """取得績效指標"""
    pass

@router.get("/agents/{agent_id}/holdings")
async def get_holdings(agent_id: str):
    """取得持股明細"""
    pass

@router.get("/agents/{agent_id}/transactions")
async def get_transactions(agent_id: str, limit: int = 50, offset: int = 0):
    """取得交易歷史"""
    pass

## 🔄 需要註冊到主應用

在 `backend/src/api/app.py` 中註冊新路由：

```python
from .routers import agent_execution, ai_models, websocket_router
from .routers import agents, trading, system  # 新增

def create_app() -> FastAPI:
    # ...

    # Include routers
    app.include_router(agent_execution.router)
    app.include_router(ai_models.router, prefix="/api")
    app.include_router(websocket_router.router)

    # 新增路由
    app.include_router(agents.router)
    app.include_router(trading.router)

    # ...
```

## ✅ 已實現的路由

### Agent Execution (`/api/agent-execution`)

- ✅ `POST /{agent_id}/execute` - 執行 Agent 任務
- ✅ `GET /{agent_id}/status` - 取得 Agent 狀態
- ✅ `GET /{agent_id}/history` - 取得執行歷史
- ✅ `GET /{agent_id}/sessions/{session_id}` - 取得會話詳情
- ✅ `GET /{agent_id}/statistics` - 取得統計資訊

### AI Models (`/api/models`)

- ✅ `GET /available` - 獲取可用 AI 模型列表
- ✅ `GET /available/grouped` - 獲取分組的 AI 模型列表
- ✅ `GET /{model_key}` - 獲取特定模型資訊
- ✅ `GET /` - 獲取所有模型列表

### WebSocket

- ✅ `WS /ws` - WebSocket 連接

### System

- ✅ `GET /api/health` - 健康檢查

## 📝 注意事項

1. **前端 API 路徑已更新**: `executeAgent` 等方法已更新為使用正確的 `/api/agent-execution` 路徑
2. **TODO 標記**: 所有未實現的端點都已標記 `TODO: 後端尚未實現此端點`
3. **優先級建議**:
   - **高**: Agent CRUD (創建、讀取、更新、刪除)
   - **高**: Portfolio & Holdings (投資組合、持股)
   - **中**: Trading History (交易記錄、績效)

## 🔗 相關服務

以下服務已存在，可用於實現路由：

- `AgentsService` (`backend/src/service/agents_service.py`)
  - `get_agent_config()`
  - `list_active_agents()`
  - `update_agent_status()`
  - `create_transaction()`
  - `get_agent_holdings()`
  - `calculate_and_update_performance()`

- `TradingService` (`backend/src/service/trading_service.py`)
  - `execute_agent_task()`
  - `get_agent_status()`
  - `get_execution_history()`
  - `get_session_details()`
  - `get_agent_statistics()`

## 💡 實現建議

1. **使用現有服務**: 優先使用 `AgentsService` 和 `TradingService` 的現有方法
2. **遵循現有模式**: 參考 `agent_execution.py` 的錯誤處理和響應模型
3. **添加文檔**: 使用 OpenAPI 標籤和描述
4. **添加測試**: 為每個端點添加單元測試
5. **漸進式實現**: 先實現核心 CRUD，再添加進階功能
