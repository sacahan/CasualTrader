# 開發者指南

**版本**: 1.0
**最後更新**: 2025-10-21
**目標受眾**: 後端開發者、前端開發者、測試工程師

## 目錄

1. [快速開始](#快速開始)
2. [架構概述](#架構概述)
3. [後端開發](#後端開發)
4. [前端開發](#前端開發)
5. [測試指南](#測試指南)
6. [故障排查](#故障排查)

---

## 快速開始

### 環境要求

**後端**:
- Python 3.12+
- pip 或 uv
- SQLite3
- 4GB RAM

**前端**:
- Node.js 18+
- npm 或 yarn
- 2GB RAM

### 安裝和運行

#### 方式 1: 使用啟動腳本（推薦）

```bash
cd /path/to/CasualTrader
./scripts/start.sh
```

#### 方式 2: 手動啟動

**後端**:
```bash
cd backend
uv sync
uv run python run_server.py
# 訪問: http://localhost:8000
# API 文檔: http://localhost:8000/api/docs
```

**前端**:
```bash
cd frontend
npm install
npm run dev
# 訪問: http://localhost:5173
```

### 驗證安裝

```bash
# 健康檢查
curl http://localhost:8000/api/health

# 列出 agents
curl http://localhost:8000/api/agents

# 前端測試
open http://localhost:5173
```

---

## 架構概述

### 系統架構

```
┌─────────────────────────────────────────────────────┐
│                    前端 (Svelte)                    │
│  - AgentCard 組件                                   │
│  - 4 個執行按鈕 (觀察/交易/再平衡/停止)             │
│  - 實時狀態更新                                     │
└────────────────┬────────────────────────────────────┘
                 │ HTTP/REST
                 ▼
┌─────────────────────────────────────────────────────┐
│              後端 API (FastAPI)                      │
│  - /agents/{id}/start - 啟動執行                    │
│  - /agents/{id}/stop - 停止執行                     │
│  - /agents - 獲取列表                              │
│  - /health - 健康檢查                               │
└────────────┬──────────────────────────────┬─────────┘
             ▼                              ▼
        ┌────────────┐            ┌─────────────────┐
        │ TradingService         │ AgentExecutor   │
        │ - 執行核心邏輯         │ - 狀態管理     │
        │ - 資源管理             │                 │
        └────────────┘            └─────────────────┘
             │
             ▼
        ┌────────────────────────┐
        │    SQLite Database     │
        │ - Agents               │
        │ - Sessions             │
        │ - Transactions         │
        └────────────────────────┘
```

### 數據流

```
用戶點擊 [觀察]
    ↓
前端發送 POST /agents/{id}/start {mode: "OBSERVATION"}
    ↓
後端驗證 Agent 狀態
    ↓
TradingService.execute_single_mode()
    ↓
執行觀察邏輯
    ↓
返回結果
    ↓
前端更新 UI
    ↓
會話記錄存儲到數據庫
```

---

## 後端開發

### 項目結構

```
backend/
├── src/
│   ├── api/
│   │   ├── app.py              # FastAPI 應用工廠
│   │   ├── routers/
│   │   │   └── agent_execution.py # API 路由
│   │   ├── models.py           # Pydantic 模型
│   │   └── config.py           # 配置管理
│   ├── service/
│   │   ├── trading_service.py  # 核心業務邏輯
│   │   ├── agent_executor.py   # 代理執行器
│   │   └── agents_service.py   # Agent 管理
│   ├── database/
│   │   ├── models.py           # SQLAlchemy 模型
│   │   └── config.py           # 數據庫配置
│   ├── common/
│   │   ├── enums.py            # 枚舉定義
│   │   └── logger.py           # 日誌系統
│   └── trading/
│       └── ...                 # 交易邏輯
├── tests/
│   ├── test_e2e_scenarios.py   # E2E 測試
│   ├── test_api_integration.py # API 測試
│   ├── test_single_mode_execution.py # 單元測試
│   └── ...                     # 其他測試
├── pyproject.toml              # 項目配置
├── run_server.py               # 啟動腳本
└── ...
```

### 核心 API

#### TradingService.execute_single_mode()

```python
async def execute_single_mode(
    self,
    agent_id: str,
    mode: AgentMode,
    max_turns: int | None = None,
) -> dict[str, Any]:
    """
    執行單一模式的核心方法

    Args:
        agent_id: Agent 的唯一識別符
        mode: 執行模式 (OBSERVATION/TRADING/REBALANCING)
        max_turns: 最大執行輪數

    Returns:
        包含執行結果的字典

    Raises:
        AgentBusyError: 如果 Agent 已在執行中
        AgentNotFoundError: 如果 Agent 不存在
    """
    agent = None
    try:
        # 檢查並發
        if agent_id in self.active_agents:
            raise AgentBusyError(...)

        # 創建 Agent
        agent = await self._get_or_create_agent(agent_id)
        self.active_agents[agent_id] = agent

        # 執行模式
        result = await agent.run_mode(mode, max_turns)

        # 記錄會話
        await self._record_session(agent_id, mode, result)

        return result

    finally:
        # 資源清理
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
```

#### API 路由

```python
@router.post("/{agent_id}/start")
async def start_agent(
    agent_id: str,
    request: StartModeRequest,
    trading_service: TradingService = Depends(get_trading_service)
) -> dict:
    """啟動 Agent 執行指定模式"""
    try:
        mode = AgentMode(request.mode)
        result = await trading_service.execute_single_mode(
            agent_id=agent_id,
            mode=mode,
            max_turns=request.max_turns,
        )
        return result
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AgentBusyError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 添加新功能

#### 步驟 1: 定義 API 端點

編輯 `backend/src/api/routers/agent_execution.py`:

```python
@router.post("/{agent_id}/new-endpoint")
async def new_endpoint(
    agent_id: str,
    request: NewRequest,
    trading_service: TradingService = Depends(get_trading_service)
) -> dict:
    """新端點的說明"""
    # 實現邏輯
    pass
```

#### 步驟 2: 在 TradingService 中實現業務邏輯

編輯 `backend/src/service/trading_service.py`:

```python
async def new_business_logic(
    self,
    agent_id: str,
    param: str
) -> dict[str, Any]:
    """業務邏輯實現"""
    try:
        # 實現邏輯
        pass
    finally:
        # 清理資源
        pass
```

#### 步驟 3: 添加單元測試

創建 `backend/tests/test_new_feature.py`:

```python
import pytest

class TestNewFeature:
    @pytest.mark.asyncio
    async def test_new_feature(self):
        """新功能測試"""
        # 測試代碼
        pass
```

#### 步驟 4: 測試

```bash
cd backend
python -m pytest tests/test_new_feature.py -v
```

### 日誌系統

#### 記錄日誌

```python
from common.logger import logger

logger.info("Information message")
logger.debug("Debug message")
logger.warning("Warning message")
logger.error("Error message")
logger.success("Success message")
```

#### 查看日誌

```bash
# 實時日誌（開發模式）
tail -f logs/casualtrader.log

# 查看錯誤
grep "ERROR" logs/casualtrader.log
```

---

## 前端開發

### 項目結構

```
frontend/
├── src/
│   ├── App.svelte              # 主應用組件
│   ├── components/
│   │   ├── Agent/
│   │   │   ├── AgentCard.svelte # Agent 卡片組件
│   │   │   └── AgentGrid.svelte # Agent 網格
│   │   └── ...
│   ├── stores/
│   │   └── agents.js           # 狀態管理
│   ├── api/
│   │   └── client.js           # API 客戶端
│   └── main.js                 # 入口
├── package.json                # 依賴配置
├── vite.config.js              # Vite 配置
└── ...
```

### 核心組件

#### AgentCard.svelte

```svelte
<script>
  import { onMount } from 'svelte';

  export let agent;
  export let onObserve;
  export let onTrade;
  export let onRebalance;
  export let onStop;

  let isLoading = false;
  let error = null;

  async function handleObserve() {
    isLoading = true;
    try {
      await onObserve(agent.id);
    } catch (e) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  }

  // ... 其他方法
</script>

<div class="agent-card">
  <h3>{agent.name}</h3>
  <p>狀態: {agent.status}</p>

  <div class="buttons">
    <button on:click={handleObserve} disabled={isLoading}>
      觀察
    </button>
    <button on:click={handleTrade} disabled={isLoading}>
      交易
    </button>
    <button on:click={handleRebalance} disabled={isLoading}>
      再平衡
    </button>
    <button on:click={handleStop} disabled={!isLoading}>
      停止
    </button>
  </div>

  {#if error}
    <div class="error">{error}</div>
  {/if}
</div>
```

### API 客戶端

```javascript
// src/api/client.js
const API_BASE = 'http://localhost:8000/api';

export async function startAgent(agentId, mode) {
  const response = await fetch(
    `${API_BASE}/agents/${agentId}/start`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode })
    }
  );

  if (!response.ok) {
    throw new Error(`Failed: ${response.status}`);
  }

  return response.json();
}

export async function stopAgent(agentId) {
  const response = await fetch(
    `${API_BASE}/agents/${agentId}/stop`,
    { method: 'POST' }
  );

  if (!response.ok) {
    throw new Error(`Failed: ${response.status}`);
  }

  return response.json();
}
```

### 添加新 UI 組件

#### 步驟 1: 創建組件

創建 `frontend/src/components/NewComponent.svelte`:

```svelte
<script>
  export let prop = 'default';
</script>

<div>
  {prop}
</div>

<style>
  div {
    /* 樣式 */
  }
</style>
```

#### 步驟 2: 導入和使用

在 `App.svelte` 中:

```svelte
<script>
  import NewComponent from './components/NewComponent.svelte';
</script>

<NewComponent prop="value" />
```

#### 步驟 3: 測試

```bash
cd frontend
npm run dev
```

---

## 測試指南

### 運行測試

#### 後端測試

```bash
cd backend

# 運行所有測試
python -m pytest tests/ -v

# 運行特定文件
python -m pytest tests/test_e2e_scenarios.py -v

# 運行特定測試
python -m pytest tests/test_e2e_scenarios.py::TestE2EScenario1 -v

# 顯示打印輸出
python -m pytest tests/ -v -s
```

#### 前端測試

```bash
cd frontend

# 構建
npm run build

# 檢查 lint
npm run lint
```

### 編寫測試

#### 後端單元測試

```python
import pytest
from unittest.mock import AsyncMock

class TestFeature:
    @pytest.mark.asyncio
    async def test_basic_functionality(self):
        """測試基本功能"""
        # 準備
        mock_service = AsyncMock()
        mock_service.method.return_value = {'result': 'success'}

        # 執行
        result = await mock_service.method()

        # 驗證
        assert result['result'] == 'success'
        mock_service.method.assert_called_once()
```

#### 前端測試

```javascript
// 使用 Vitest 進行測試
import { describe, it, expect } from 'vitest';

describe('AgentCard', () => {
  it('should display agent name', () => {
    const agent = { id: '1', name: 'Test Agent' };
    // 測試邏輯
  });
});
```

### 測試覆蓋

檢查測試覆蓋:

```bash
# 後端
cd backend
python -m pytest tests/ --cov=src --cov-report=html

# 查看報告
open htmlcov/index.html
```

---

## 故障排查

### 常見後端問題

#### 1. 導入錯誤

**症狀**: `ModuleNotFoundError`

**解決方案**:
```bash
# 確保 PYTHONPATH 設置正確
export PYTHONPATH=/path/to/backend/src
python run_server.py
```

#### 2. 數據庫連接失敗

**症狀**: `sqlite3.OperationalError`

**解決方案**:
```bash
# 檢查數據庫文件
ls -la casualtrader.db

# 重置數據庫
rm casualtrader.db
# 重新啟動應用
```

#### 3. 端口已被佔用

**症狀**: `Address already in use`

**解決方案**:
```bash
# 查找佔用端口的進程
lsof -i :8000

# 殺死進程
kill -9 <PID>
```

### 常見前端問題

#### 1. 模塊解析失敗

**症狀**: 構建時出現 `Cannot find module`

**解決方案**:
```bash
# 清除 node_modules
rm -rf node_modules
npm install
npm run dev
```

#### 2. CORS 錯誤

**症狀**: 瀏覽器控制台顯示 CORS 錯誤

**解決方案**:
- 確保後端 CORS 配置正確
- 確保前端使用正確的 API URL
- 檢查 `vite.config.js` 的 proxy 配置

#### 3. 樣式加載失敗

**症狀**: 頁面沒有樣式

**解決方案**:
```bash
# 清除緩存
npm cache clean --force
npm install
npm run dev
```

---

## 最佳實踐

### ✅ 後端最佳實踐

1. **使用類型提示**
   ```python
   async def execute(
       self,
       agent_id: str,
       mode: AgentMode,
   ) -> dict[str, Any]:
   ```

2. **實現適當的錯誤處理**
   ```python
   try:
       # 業務邏輯
   except SpecificError as e:
       logger.error(...)
       raise
   finally:
       # 清理資源
   ```

3. **添加詳細的日誌**
   ```python
   logger.info(f"Starting {mode.value} for agent {agent_id}")
   ```

4. **編寫測試**
   ```python
   @pytest.mark.asyncio
   async def test_feature():
       # 測試代碼
   ```

### ✅ 前端最佳實踐

1. **使用組件化設計**
   ```svelte
   <AgentCard {agent} on:observe on:trade />
   ```

2. **管理狀態**
   ```javascript
   const agents = writable([]);
   ```

3. **處理加載狀態**
   ```svelte
   {#if loading}
     <p>加載中...</p>
   {/if}
   ```

4. **顯示錯誤信息**
   ```svelte
   {#if error}
     <div class="error">{error}</div>
   {/if}
   ```

---

## 相關文檔

- [API 參考](./API_REFERENCE.md)
- [用戶指南](./USER_GUIDE.md)
- [設計概述](./DESIGN_OVERVIEW.md)
- [整合測試報告](./INTEGRATION_TEST_REPORT.md)

---

**最後更新**: 2025-10-21
**維護者**: CasualTrader Team
