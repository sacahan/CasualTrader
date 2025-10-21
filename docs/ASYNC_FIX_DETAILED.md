# 修復摘要：AsyncExitStack Cancel Scope 問題

## 問題

當 Trading Agent 完成 `OBSERVATION` 模式準備進入 `TRADING` 模式時，出現以下錯誤：

```python
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
```

這個錯誤來自 `anyio` 的 cancel scope 管理，發生在 MCP（Model Context Protocol）servers 的上下文管理器中。

## 根本原因分析

1. **MCP Servers 綁定到異步任務**：
   - MCP servers 通過 `AsyncExitStack` 在特定的異步任務中初始化
   - cancel scope 被綁定到該任務的上下文中

2. **Agent 實例快取導致的跨任務問題**：
   - `TradingService` 在 `self.active_agents` 中緩存 Agent 實例
   - OBSERVATION 模式執行時，MCP servers 在該執行任務中被初始化
   - 執行完成後，Agent 實例仍然被快取，保留著已進入的 cancel scope

3. **TRADING 模式重用同一實例**：
   - TRADING 模式嘗試重用緩存的 Agent 實例
   - 同一個 Agent 實例在不同的異步任務中被執行
   - 新任務中的 cancel scope 退出與舊任務中的進入不匹配

4. **缺少清理邏輯**：
   - `execute_agent_task` 方法沒有在完成後清理 MCP servers
   - `AsyncExitStack` 持續保持對資源的管理狀態

## 實施的修復

### 修復 1：完整的資源清理 (在 `execute_agent_task` 中)

**文件**：`backend/src/service/trading_service.py`

**位置**：第 213-228 行

**內容**：在 `execute_agent_task` 方法末尾添加 `finally` 塊：

```python
finally:
    # 清理 Agent 資源和 MCP servers（無論成功或失敗都要清理）
    if agent_id in self.active_agents:
        trading_agent = self.active_agents.get(agent_id)
        if trading_agent is not None:
            try:
                await trading_agent.cleanup()
                logger.info(f"Cleaned up MCP servers and Agent resources for {agent_id}")
            except Exception as cleanup_error:
                logger.warning(
                    f"Error during agent cleanup for {agent_id}: {cleanup_error}",
                    exc_info=False,
                )
        # 移除活躍 Agent，強制重新初始化下一個模式
        del self.active_agents[agent_id]
        logger.debug(f"Removed {agent_id} from active_agents cache")
```

**效果**：

- ✅ 確保每次執行完後都呼叫 `cleanup()` 清理 MCP servers
- ✅ 及時從 `active_agents` 移除實例，避免跨任務重用

### 修復 2：改進 Agent 實例策略 (在 `_get_or_create_agent` 中)

**文件**：`backend/src/service/trading_service.py`

**位置**：第 537-567 行

**內容**：修改為每次都創建新實例而非重用：

```python
async def _get_or_create_agent(
    self, agent_id: str, agent_config: Agent | None = None
) -> TradingAgent:
    """
    取得或創建 TradingAgent 實例

    NOTE: 為了避免 MCP servers cancel scope 在不同異步任務中被進入/退出的問題，
    我們不再緩存 Agent 實例。每次執行都創建新的 Agent 實例，
    並在執行完後立即清理。

    Args:
        agent_id: Agent ID
        agent_config: Agent 配置

    Returns:
        TradingAgent 實例

    Raises:
        AgentInitializationError: 初始化失敗
    """
    # 不再從緩存中取得 Agent，而是每次都創建新實例
    # 這確保了每個執行上下文都有自己的 MCP servers
    logger.info(f"Creating new TradingAgent instance for {agent_id} (not reusing cached)")
    agent = TradingAgent(agent_id, agent_config, self.agents_service)
    await agent.initialize()

    # 暫存到 active_agents 以便清理時使用
    self.active_agents[agent_id] = agent

    return agent
```

**效果**：

- ✅ 每個執行都有獨立的 MCP servers 和 cancel scope
- ✅ 避免跨異步任務的 cancel scope 衝突
- ✅ 簡化生命週期管理

## 修復前後的執行流程對比

### 修復前（問題流程）

```text
OBSERVATION 模式執行：
1. 建立 Agent 實例 (task-1)
2. 初始化 MCP servers (在 task-1 中)
3. 執行 OBSERVATION 邏輯
4. 執行完成，但 Agent 實例仍在 active_agents 中快取
❌ MCP servers 沒有清理，cancel scope 仍在 task-1

TRADING 模式執行：
1. 試圖重用 active_agents 中的 Agent 實例 (task-2)
2. 執行 TRADING 邏輯
❌ 同一 cancel scope 被不同的 task 進入/退出 → 錯誤！
```

### 修復後（正確流程）

```text
OBSERVATION 模式執行：
1. 建立新的 Agent 實例 (task-1)
2. 初始化 MCP servers (在 task-1 中)
3. 執行 OBSERVATION 邏輯
4. 執行完成後：
   - 呼叫 await trading_agent.cleanup()
   - 清理 MCP servers 和 cancel scope
   - 從 active_agents 移除實例
✅ 資源已完全釋放

TRADING 模式執行：
1. 建立新的 Agent 實例 (task-2)
2. 初始化新的 MCP servers (在 task-2 中)
3. 執行 TRADING 邏輯
4. 執行完成後再次清理
✅ 每個模式有獨立的資源上下文
```

## 驗證修復

修復後應能觀察到的日誌：

```text
2025-10-21 00:04:25 | INFO     | service.trading_service:_get_or_create_agent:550 | Creating new TradingAgent instance for agent-5e101682 (not reusing cached)
2025-10-21 00:04:25 | INFO     | trading.trading_agent:__init__:145 | TradingAgent created: agent-5e101682
2025-10-21 00:04:25 | INFO     | service.trading_service:execute_agent_task:161 | Task completed for agent agent-5e101682, session xxx (2500ms)
2025-10-21 00:04:25 | INFO     | service.trading_service:execute_agent_task:214 | Cleaned up MCP servers and Agent resources for agent-5e101682
2025-10-21 00:04:25 | DEBUG    | service.trading_service:execute_agent_task:220 | Removed agent-5e101682 from active_agents cache

[轉換到 TRADING 模式]

2025-10-21 00:04:30 | INFO     | service.trading_service:_get_or_create_agent:550 | Creating new TradingAgent instance for agent-5e101682 (not reusing cached)
2025-10-21 00:04:30 | INFO     | trading.trading_agent:__init__:145 | TradingAgent created: agent-5e101682
2025-10-21 00:04:30 | INFO     | service.trading_service:execute_agent_task:161 | Task completed for agent agent-5e101682, session yyy (1800ms)
2025-10-21 00:04:30 | INFO     | service.trading_service:execute_agent_task:214 | Cleaned up MCP servers and Agent resources for agent-5e101682
```

**注意**：不應該再看到 `RuntimeError: Attempted to exit cancel scope in a different task` 的錯誤。

## 性能影響

- **正面影響**：避免了複雜的跨異步任務狀態管理
- **微小負面影響**：每次執行都創建新的 Agent 和 MCP servers 連接，但這是合理的代價以換取穩定性
- **整體**：穩定性收益遠超過微小的性能成本

## 涉及文件

- `backend/src/service/trading_service.py`

## 相關參考

- Python 文檔：[contextlib.AsyncExitStack](https://docs.python.org/3/library/contextlib.html#contextlib.AsyncExitStack)
- anyio 文檔：[CancelScope](https://anyio.readthedocs.io/en/stable/basics.html#cancellation)
- MCP 文檔：[Model Context Protocol](https://modelcontextprotocol.io)
