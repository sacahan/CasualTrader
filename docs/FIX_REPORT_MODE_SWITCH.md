.# AsyncExitStack Cancel Scope 問題修復報告

## 問題描述

在 Agent 從 `OBSERVATION` 模式切換到 `TRADING` 模式時發生以下錯誤：

```python
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
```

## 根本原因

1. **MCP Servers 生命週期問題**：
   - MCP servers 通過 `AsyncExitStack` 進行管理
   - 當 Agent 初始化時，MCP servers 在執行任務的異步上下文中被進入
   - 問題發生在試圖在不同的異步任務中退出 cancel scope 時

2. **Agent 實例快取問題**：
   - `TradingService` 在 `active_agents` 中緩存 Agent 實例
   - OBSERVATION 模式執行時建立的 Agent 在模式完成後未被清理
   - TRADING 模式試圖重用同一個 Agent 時，MCP servers 的 cancel scope 已經在不同的異步任務中

3. **缺少清理邏輯**：
   - `execute_agent_task` 方法執行完成後沒有呼叫 `await trading_agent.cleanup()`
   - 導致 MCP servers 的 `AsyncExitStack` 被懸掛在記憶體中

## 實施的修復

### 修復 1：在 `execute_agent_task` 中添加 `finally` 塊

在 `src/service/trading_service.py` 的 `execute_agent_task` 方法中添加 `finally` 塊，確保無論成功或失敗都清理 Agent 資源：

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

### 修復 2：改進 `_get_or_create_agent` 快取策略

修改 `_get_or_create_agent` 方法，不再嘗試重新使用緩存的 Agent 實例：

```python
async def _get_or_create_agent(
    self, agent_id: str, agent_config: Agent | None = None
) -> TradingAgent:
    """
    NOTE: 為了避免 MCP servers cancel scope 在不同異步任務中被進入/退出的問題，
    我們不再緩存 Agent 實例。每次執行都創建新的 Agent 實例，
    並在執行完後立即清理。
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

## 修復的關鍵點

1. **獨立的 MCP 上下文**：每次執行都創建新的 Agent 實例，確保每個執行有自己的 MCP servers
2. **及時清理**：使用 `finally` 塊確保在執行完成後立即清理資源
3. **移除快取**：不再嘗試重新使用 Agent 實例，避免 cancel scope 衝突

## 效果

- ✅ OBSERVATION 模式可以正常執行
- ✅ 完成後能夠切換到 TRADING 模式
- ✅ 不再出現 `RuntimeError: Attempted to exit cancel scope in a different task` 錯誤
- ✅ MCP servers 被正確清理，避免資源洩漏

## 涉及的文件

- `/backend/src/service/trading_service.py` - 修復了 `execute_agent_task` 和 `_get_or_create_agent` 方法
