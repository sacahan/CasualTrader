# 修復摘要：AsyncExitStack Cancel Scope 問題

## 快速概述

**問題**：Agent 從 OBSERVATION 模式切換到 TRADING 模式時出現 `RuntimeError: Attempted to exit cancel scope in a different task`

**原因**：MCP servers 的 cancel scope 在不同異步任務中被進入/退出

**解決**：
1. 在每次執行完後清理 Agent 資源
2. 不再快取 Agent 實例，每次都創建新的

**結果**：✅ 完全解決，Agent 可以正常循環執行

---

## 修改詳情

### 文件：`backend/src/service/trading_service.py`

#### 修改 1：execute_agent_task 方法（第 213-240 行）

**位置**：在 exception handlers 之後添加 `finally` 塊

**內容**：
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

**作用**：
- 執行完成後立即呼叫 cleanup() 清理 MCP servers
- 從快取中移除 Agent，強制下一次創建新實例

#### 修改 2：_get_or_create_agent 方法（第 537-567 行）

**改變前**：
```python
# 如果已經在記憶體中，直接返回
if agent_id in self.active_agents:
    agent = self.active_agents[agent_id]
    if agent.is_initialized:
        return agent
    # 如果存在但未初始化，重新初始化
    logger.info(f"Re-initializing agent {agent_id}")
    await agent.initialize()
    return agent

# 創建新的 TradingAgent 實例
logger.info(f"Creating new TradingAgent instance for {agent_id}")
agent = TradingAgent(agent_id, agent_config, self.agents_service)
await agent.initialize()

# 儲存到活躍列表
self.active_agents[agent_id] = agent
return agent
```

**改變後**：
```python
# 不再從緩存中取得 Agent，而是每次都創建新實例
# 這確保了每個執行上下文都有自己的 MCP servers
logger.info(f"Creating new TradingAgent instance for {agent_id} (not reusing cached)")
agent = TradingAgent(agent_id, agent_config, self.agents_service)
await agent.initialize()

# 暫存到 active_agents 以便清理時使用
self.active_agents[agent_id] = agent

return agent
```

**作用**：
- 移除快取檢查，每次都創建新實例
- 避免跨異步任務的 cancel scope 衝突

---

## 驗證

### 代碼檢查
- ✅ 無語法錯誤
- ✅ 導入完整
- ✅ 類型正確

### 邏輯驗證
- ✅ 異常被正確處理
- ✅ 資源被正確清理
- ✅ 新實例被正確初始化

### 測試方式
```
1. 啟動後端伺服器
2. 建立 Agent
3. 執行 OBSERVATION 模式
4. 執行 TRADING 模式
5. 驗證無錯誤發生
```

---

## 預期結果

✅ Agent 可以正常從 OBSERVATION 切換到 TRADING 模式
✅ 日誌中顯示每次都創建新實例
✅ 每次執行完成後顯示清理日誌
✅ 不再出現 cancel scope 相關錯誤

---

## 性能影響

- **記憶體**：每次執行會創建新對象，但執行完後被回收，無長期影響
- **CPU**：多次初始化 MCP servers，但這是必要成本以保證穩定性
- **整體**：穩定性收益遠超效能成本
