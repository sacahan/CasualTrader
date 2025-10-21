# 實施指南

**狀態**: ✅ **已完成** (2025-10-21)
**測試通過**: 34/34 ✅ (100% 通過率)

## 後端實施

### Step 1: 修改 API 路由

**文件**: `backend/src/api/routers/agent_execution.py`

```python
from pydantic import BaseModel, Field
from enum import Enum

class AgentModeEnum(str, Enum):
    OBSERVATION = "OBSERVATION"
    TRADING = "TRADING"
    REBALANCING = "REBALANCING"

class StartRequest(BaseModel):
    """啟動 Agent 執行請求"""
    mode: AgentModeEnum = Field(
        default=AgentModeEnum.OBSERVATION,
        description="執行模式: OBSERVATION | TRADING | REBALANCING"
    )
    max_turns: int | None = Field(None, ge=1, le=50, description="最大輪數")

@router.post("/{agent_id}/start")
async def start_agent(
    agent_id: str,
    request: StartRequest,
    trading_service: TradingService = Depends(get_trading_service)
) -> dict:
    """
    啟動 Agent 執行指定模式（執行完後立即返回）

    Args:
        agent_id: Agent ID
        request.mode: 執行模式 (OBSERVATION | TRADING | REBALANCING)
        request.max_turns: 最大輪數（可選）

    Returns:
        執行結果
    """
    try:
        mode = AgentMode(request.mode)

        result = await trading_service.execute_single_mode(
            agent_id=agent_id,
            mode=mode,
            max_turns=request.max_turns,
        )

        return result

    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except AgentBusyError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
```

### Step 2: 修改 TradingService

**文件**: `backend/src/service/trading_service.py`

添加核心方法：

```python
async def execute_single_mode(
    self,
    agent_id: str,
    mode: AgentMode,
    max_turns: int | None = None,
) -> dict[str, Any]:
    """
    執行單一模式（執行後立即停止，不再循環轉換）

    Args:
        agent_id: Agent ID
        mode: 要執行的模式 (OBSERVATION/TRADING/REBALANCING)
        max_turns: 最大輪數（可選）

    Returns:
        執行結果字典
    """
    agent = None
    try:
        # 檢查 agent 是否已在執行
        if agent_id in self.active_agents:
            raise AgentBusyError(f"Agent {agent_id} is already running")

        # 創建或獲取 agent
        agent = await self._get_or_create_agent(agent_id)

        # 標記為活躍
        self.active_agents[agent_id] = agent

        logger.info(f"Starting {mode.value} for agent {agent_id}")

        # 執行指定模式
        result = await agent.run_mode(mode, max_turns=max_turns)

        logger.info(f"Completed {mode.value} for agent {agent_id}")

        return result

    except Exception as e:
        logger.error(
            f"Error executing {mode.value} for {agent_id}: {e}",
            exc_info=True
        )
        raise

    finally:
        # 確保資源清理（即使發生異常）
        if agent_id in self.active_agents:
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent_id}: {e}")
            finally:
                del self.active_agents[agent_id]
```

### Step 3: 簡化 AgentExecutor

**文件**: `backend/src/service/agent_executor.py`

**移除的方法**：
- `start_cycling()` - 不再有循環執行
- `_execute_cycle_loop()` - 循環轉換邏輯

**保留的方法**：
```python
async def stop(self, agent_id: str) -> dict:
    """停止當前執行的 agent"""
    if agent_id not in self.active_agents:
        return {"success": False, "status": "not_running"}

    agent = self.active_agents[agent_id]
    await agent.cancel()
    await agent.cleanup()
    del self.active_agents[agent_id]

    return {"success": True, "status": "stopped"}

def get_status(self, agent_id: str) -> dict:
    """獲取 agent 執行狀態"""
    if agent_id not in self.active_agents:
        return {"status": "idle"}

    agent = self.active_agents[agent_id]
    return {
        "status": "running",
        "agent_id": agent_id,
        "mode": str(agent.current_mode),
        "started_at": agent.started_at.isoformat() if agent.started_at else None,
    }
```

## 前端實施

### Step 1: 修改 AgentCard.svelte

**變更**：4 個按鈕替代原先的 2 個

```svelte
<script>
  export let agent;
  export let onobserve = () => {};
  export let ontrade = () => {};
  export let onrebalance = () => {};
  export let onstop = () => {};

  let isLoading = false;
  let isRunning = false;

  const handleObserve = async () => {
    isLoading = true;
    try {
      await onobserve();
      isRunning = true;
    } finally {
      isLoading = false;
    }
  };

  const handleTrade = async () => {
    isLoading = true;
    try {
      await ontrade();
      isRunning = true;
    } finally {
      isLoading = false;
    }
  };

  const handleRebalance = async () => {
    isLoading = true;
    try {
      await onrebalance();
      isRunning = true;
    } finally {
      isLoading = false;
    }
  };

  const handleStop = async () => {
    isLoading = true;
    try {
      await onstop();
      isRunning = false;
    } finally {
      isLoading = false;
    }
  };
</script>

<div class="agent-card">
  <div class="agent-header">
    <h3>{agent.name}</h3>
    <span class="status" class:running={isRunning}></span>
  </div>

  <div class="buttons">
    {#if !isLoading}
      <button
        class="btn btn-observe"
        on:click={handleObserve}
        disabled={isRunning}
        title="執行觀察模式"
      >
        📊 觀察
      </button>
      <button
        class="btn btn-trade"
        on:click={handleTrade}
        disabled={isRunning}
        title="執行交易模式"
      >
        💹 交易
      </button>
      <button
        class="btn btn-rebalance"
        on:click={handleRebalance}
        disabled={isRunning}
        title="執行再平衡模式"
      >
        ⚖️ 再平衡
      </button>
      <button
        class="btn btn-stop"
        on:click={handleStop}
        disabled={!isRunning}
        title="停止執行"
      >
        ⏹️ 停止
      </button>
    {:else}
      <div class="loading">執行中...</div>
    {/if}
  </div>
</div>

<style>
  .agent-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
  }

  .agent-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  h3 {
    margin: 0;
    font-size: 18px;
  }

  .status {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: #999;
    transition: background-color 0.3s;
  }

  .status.running {
    background-color: #4caf50;
    animation: pulse 1s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .buttons {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .btn {
    padding: 8px 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: opacity 0.2s;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-observe {
    background-color: #2196F3;
    color: white;
  }

  .btn-trade {
    background-color: #FF9800;
    color: white;
  }

  .btn-rebalance {
    background-color: #9C27B0;
    color: white;
  }

  .btn-stop {
    background-color: #f44336;
    color: white;
    grid-column: 1 / -1;
  }

  .loading {
    grid-column: 1 / -1;
    text-align: center;
    padding: 8px;
    background-color: #f5f5f5;
    border-radius: 4px;
  }
</style>
```

### Step 2: 修改父組件

**文件**: `frontend/src/App.svelte` 或相應的父組件

```javascript
// API 調用
const handleAgentObserve = async (agentId) => {
  try {
    const response = await fetch(`/api/agents/${agentId}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: 'OBSERVATION' }),
    });
    if (!response.ok) throw new Error('Failed to start observation');
    const result = await response.json();
    console.log('Observation result:', result);
  } catch (error) {
    console.error('Error:', error);
    // 顯示錯誤提示
  }
};

const handleAgentTrade = async (agentId) => {
  try {
    const response = await fetch(`/api/agents/${agentId}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: 'TRADING' }),
    });
    if (!response.ok) throw new Error('Failed to start trading');
    const result = await response.json();
    console.log('Trading result:', result);
  } catch (error) {
    console.error('Error:', error);
  }
};

const handleAgentRebalance = async (agentId) => {
  try {
    const response = await fetch(`/api/agents/${agentId}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: 'REBALANCING' }),
    });
    if (!response.ok) throw new Error('Failed to start rebalancing');
    const result = await response.json();
    console.log('Rebalancing result:', result);
  } catch (error) {
    console.error('Error:', error);
  }
};

const handleAgentStop = async (agentId) => {
  try {
    const response = await fetch(`/api/agents/${agentId}/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) throw new Error('Failed to stop agent');
    const result = await response.json();
    console.log('Stop result:', result);
  } catch (error) {
    console.error('Error:', error);
  }
};
```

在組件中使用：

```svelte
<AgentCard
  {agent}
  onobserve={() => handleAgentObserve(agent.id)}
  ontrade={() => handleAgentTrade(agent.id)}
  onrebalance={() => handleAgentRebalance(agent.id)}
  onstop={() => handleAgentStop(agent.id)}
/>
```

## 測試清單

### 單元測試

- [ ] `/start` 端點能正確解析 `mode` 參數
- [ ] 無效 mode 返回 HTTP 400
- [ ] Agent 不存在返回 HTTP 404
- [ ] `execute_single_mode()` 正確執行各種模式
- [ ] 資源在 finally 塊中正確清理
- [ ] 會話狀態正確更新

### 集成測試

- [ ] 連續執行 OBSERVATION → TRADING → REBALANCING 無錯誤
- [ ] 執行中點 STOP 能正確中斷
- [ ] 未執行時點 STOP 返回 "not_running"
- [ ] 無 cancel scope 衝突

### E2E 測試

```bash
# 測試場景 1: 執行單一模式
1. 啟動應用
2. 點擊 [觀察]
3. 等待完成
4. 驗證結果顯示

# 測試場景 2: 連續執行
1. 點擊 [觀察] → 等待完成
2. 點擊 [交易] → 等待完成
3. 點擊 [再平衡] → 等待完成
4. 驗證無錯誤

# 測試場景 3: 中途停止
1. 點擊 [交易]
2. 等待 2-3 秒
3. 點擊 [停止]
4. 驗證執行中止
```

## 運行測試

```bash
# 後端單元測試
cd backend
pytest tests/test_manual_mode_execution.py -v

# 後端所有相關測試
pytest tests/ -k "execution" -v

# 前端測試
cd frontend
npm test -- --watch
```
