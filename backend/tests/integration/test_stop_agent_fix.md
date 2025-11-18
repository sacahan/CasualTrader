# 停止 Agent 功能測試指南

## 問題描述

按下 Agent 卡片的「停止」按鈕時：

- 按下後顯示「未知狀態」
- reload 後還是執行中狀態

## 根本原因分析

### 後端問題

1. **缺少 `TradingAgent.cancel()` 方法**
   - `TradingService.stop_agent()` 嘗試呼叫 `await agent.cancel()`
   - 但 `TradingAgent` 類沒有實現此方法，導致 AttributeError

### 前端問題

1. **狀態映射不正確**
   - 前端將所有停止狀態硬編碼為 `'idle'`
   - 但後端返回 `'stopped'` 或 `'not_running'`
   - `statusLabelMap` 缺少 `'stopped'` 的映射

2. **WebSocket 事件不完整**
   - 後端只廣播 `execution_stopped` 事件
   - 沒有廣播 `agent_status` 事件更新 Agent 狀態

## 修復清單

### ✅ 已完成的修復

#### 後端修復

1. **新增 `TradingAgent.cancel()` 方法**
   - 檔案：`backend/src/trading/trading_agent.py`
   - 功能：清理資源並停止 Agent 執行
   - 更新 Agent 狀態為 INACTIVE（遵循 timestamp.instructions.md）

2. **改進 `TradingAgent.cleanup()` 方法**
   - 檔案：`backend/src/trading/trading_agent.py`
   - 功能：明確設置 Agent 狀態為 INACTIVE
   - 正確處理 MCP servers 關閉

3. **改進停止 API 端點**
   - 檔案：`backend/src/api/routers/agent_execution.py`
   - 新增 `agent_status` 事件廣播
   - 確保前端收到狀態更新

#### 前端修復

1. **修復 `stopAgent()` 函數**
   - 檔案：`frontend/src/stores/agents.js`
   - 使用後端返回的實際狀態而不是硬編碼
   - 正規化 `'not_running'` 為 `'idle'`

2. **改進狀態標籤映射**
   - 檔案：`frontend/src/components/Agent/AgentCard.svelte`
   - 新增 `'stopped'` 狀態支持
   - 提供備用標籤以防止「未知狀態」

## 測試步驟

### 準備工作

```bash
cd /Users/sacahan/Documents/workspace/CasualTrader

# 1. 啟動後端（如果未運行）
cd backend && python run_server.py &

# 2. 啟動前端（新終端）
cd frontend && npm run dev
```

### 測試場景 1：正常停止

1. 打開 <http://localhost:3000/>
2. 找到「華倫・巴菲特」Agent 卡片
3. 按下「交易執行」按鈕
   - Agent 應該開始運行，狀態顯示「運行中」
4. 等待 3-5 秒
5. 按下「停止」按鈕
   - 驗證：按鈕應該禁用
   - 驗證：狀態應該改為「已停止」
   - 驗證：WebSocket 通知應該出現

### 測試場景 2：Reload 後狀態一致

1. 完成測試場景 1
2. 按 F5 重新整理頁面
   - 驗證：Agent 狀態應該仍然是「已停止」
   - 驗證：不應該顯示「未知狀態」

### 測試場景 3：啟動 → 停止 → 重新啟動

1. 按下「交易執行」
   - 狀態應變為「運行中」
2. 按下「停止」
   - 狀態應變為「已停止」
3. 按下「交易執行」
   - 狀態應變為「運行中」
   - 應該成功啟動，無錯誤信息

## 檢查清單

### 後端檢查

- [ ] 沒有 AttributeError 關於 `cancel()` 方法
- [ ] 日誌顯示 "Agent execution cancelled"
- [ ] 日誌顯示 "Agent stopped"
- [ ] WebSocket 事件被廣播

### 前端檢查

- [ ] 停止後狀態顯示「已停止」而不是「未知狀態」
- [ ] 停止按鈕正確禁用
- [ ] 刷新後狀態仍然正確
- [ ] 沒有 JavaScript 錯誤

## 如果測試失敗

### 調試步驟

1. 打開瀏覽器開發者工具（F12）
2. 檢查 Network 標籤：
   - POST `/api/agent-execution/{agent_id}/stop` 應該返回 200
   - 響應應該包含 `"status": "stopped"`
3. 檢查 Console 標籤：
   - 查找 JavaScript 錯誤或警告
4. 後端日誌：
   - 查找「Stopping agent」或「cancel」相關的日誌

### 常見問題

**問題：按鈕點擊後沒有反應**

- 解決：檢查 API 請求是否成功（Network 標籤）
- 檢查 WebSocket 連接是否正常

**問題：狀態顯示「未知狀態」**

- 解決：檢查 statusLabelMap 是否包含該狀態
- 檢查後端返回的狀態值

**問題：Reload 後還是運行中**

- 解決：檢查後端是否正確保存了停止狀態
- 驗證數據庫中的 Agent 狀態

## 相關文件

### 修改的文件

- `backend/src/trading/trading_agent.py` - 新增 cancel() 方法
- `backend/src/api/routers/agent_execution.py` - 改進停止端點
- `frontend/src/stores/agents.js` - 修復 stopAgent() 函數
- `frontend/src/components/Agent/AgentCard.svelte` - 改進狀態標籤

### 相關文檔

- `backend/.github/instructions/timestamp.instructions.md` - 時間戳管理指南
- `backend/.github/copilot-instructions.md` - 編碼指南

## 預期結果

停止 Agent 後：

1. ✅ 前端立即顯示「已停止」狀態
2. ✅ 停止按鈕立即禁用
3. ✅ 頁面刷新後狀態仍然為「已停止」
4. ✅ 可以立即重新啟動 Agent
5. ✅ 沒有「未知狀態」提示
