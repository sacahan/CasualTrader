# 手動模式觸發 - 完整設計

**狀態**: ✅ **已完成實施和整合測試** (2025-10-21)

## 核心問題

當前 Agent 自動循環轉換導致：
- ❌ `RuntimeError: cancel scope in a different task` 錯誤
- ❌ 用戶無法控制執行流程
- ❌ 架構過度複雜

## 解決方案

**改為手動觸發**：用戶主動選擇執行哪個模式

### API 端點設計

**維持原有 `/start` 端點，只修改簽名**：

```bash
# 舊
POST /agents/{agentId}/start
Body: {}

# 新 - 直接修改簽名（無需向後兼容）
POST /agents/{agentId}/start
Body: {
  "mode": "OBSERVATION" | "TRADING" | "REBALANCING"
  // mode 默認為 "OBSERVATION"
}

POST /agents/{agentId}/stop  # 實現改變，路由不變
```

**設計原則**：
- ✅ 復用現有 `/start` 端點
- ✅ 添加 `mode` 參數
- ✅ 無需新建 `/execute` 端點
- ✅ 無需向後兼容性（直接修改）

## 前端變更

**UI 按鈕：2 個 → 4 個**

```
舊：[開始] [停止]
新：[觀察] [交易] [再平衡] [停止]
```

## 後端核心邏輯

### TradingService

添加核心方法 `execute_single_mode()`：

```python
async def execute_single_mode(
    self,
    agent_id: str,
    mode: AgentMode,
    max_turns: int | None = None,
) -> dict[str, Any]:
    """
    執行單一模式（執行後立即返回，不自動轉換）

    關鍵特性：
    - 執行完指定 mode 立即返回
    - finally 塊確保資源清理
    - 無自動轉換到下一個模式
    """
    try:
        agent = await self._get_or_create_agent(agent_id)
        result = await agent.run_mode(mode)
        return result
    finally:
        # 確保資源清理，解決 cancel scope 衝突
        if agent_id in self.active_agents:
            await self.active_agents[agent_id].cleanup()
            del self.active_agents[agent_id]
```

### AgentExecutor

**簡化職責**：
- ❌ 移除循環邏輯（`start_cycling()`, `_execute_cycle_loop()`）
- ✅ 保留 `stop()` 方法（中斷當前執行）
- ✅ 保留 `get_status()` 方法（返回狀態）

## 核心特性

✅ **執行完後立即停止** - 不自動轉換模式
✅ **完整的資源清理** - 避免 cancel scope 衝突
✅ **用戶完全控制** - 決定執行順序和時機
✅ **支持連續執行** - 可依次點擊多個按鈕

## 代碼改動規模

| 文件 | 改動 | 難度 |
|------|------|------|
| `agent_execution.py` | 修改 `/start` 簽名 | ⭐ |
| `trading_service.py` | 添加 `execute_single_mode()` | ⭐⭐ |
| `agent_executor.py` | 移除循環邏輯 | ⭐⭐ |
| `AgentCard.svelte` | 添加 3 個按鈕 | ⭐ |
| 父組件 | 修改 API 調用 | ⭐ |

**總難度**：⭐ ~ ⭐⭐（相對簡單）
**預計時間**：5-8 小時開發 + 1-2 小時測試

## 成功指標

- ✅ API 端點 `/start` 支持 `mode` 參數
- ✅ 前端 4 按鈕正確顯示和工作
- ✅ 無 cancel scope 相關錯誤
- ✅ 連續執行多個模式無問題
- ✅ 資源正確清理（無內存洩漏）
- ✅ 所有測試通過
