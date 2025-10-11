# CasualTrader 瀏覽器 End-to-End 測試計劃

**版本**: 1.0
**日期**: 2025-10-11
**測試工具**: Chrome DevTools MCP

---

## 📋 測試概述

### 測試目標

使用 Chrome DevTools MCP 進行真實瀏覽器環境的完整流程測試，確保：

1. 前端 UI 與後端 API 完整整合
2. 資料庫與 API 驗證規則同步
3. WebSocket 即時通信正常
4. 錯誤處理與使用者提示正確
5. 所有使用者操作流程順暢

### 測試優勢

相比傳統 API 測試，瀏覽器 E2E 測試可以發現：

- ✅ 前端表單欄位名稱與後端 API 不匹配
- ✅ 前端驗證規則與後端不一致
- ✅ 資料庫模型選項與 API enum 不同步
- ✅ 實際的網路請求格式問題
- ✅ WebSocket 連線與推送問題
- ✅ UI 渲染錯誤與控制台錯誤
- ✅ 使用者體驗流程問題

---

## 🧪 測試案例清單

### 📦 測試案例分類

- **TC-001 ~ TC-005**: Agent 生命週期管理
- **TC-006 ~ TC-010**: Agent 操作與控制
- **TC-011 ~ TC-015**: 資料查詢與展示
- **TC-016 ~ TC-020**: WebSocket 即時通信
- **TC-021 ~ TC-025**: 錯誤處理與恢復

---

## 🎯 Agent 生命週期管理測試

### TC-001: 創建 Agent 完整流程

**目標**: 驗證從開啟對話框到成功創建 Agent 的完整流程

**前置條件**:

- 後端服務運行於 `http://localhost:8000`
- 前端服務運行於 `http://localhost:3000`
- 資料庫已初始化

**測試步驟**:

1. **開啟應用**

   ```
   - 開啟瀏覽器頁面: http://localhost:3000
   - 等待頁面載入完成
   - 驗證: 顯示 "CasualTrader - 股票代理人交易模擬" 標題
   ```

2. **開啟創建 Agent 對話框**

   ```
   - 點擊 "創建新 Agent" 按鈕
   - 等待對話框出現
   - 驗證: 顯示 "創建新 Agent" 標題
   - 驗證: 顯示所有必填欄位
   ```

3. **填寫表單 - Agent 名稱**

   ```
   - 找到 "Agent 名稱" 輸入框
   - 輸入: "巴菲特"
   - 驗證: 輸入值正確顯示
   ```

4. **填寫表單 - 投資偏好描述**

   ```
   - 找到 "投資偏好描述" 多行輸入框
   - 輸入: "你是 Warren，你的名字致敬你的偶像巴菲特。
           你是一位重視價值的長期投資者，優先考慮長期財富累積。
           你會尋找高品質但股價低於內在價值的公司。"
   - 驗證: 輸入值正確顯示
   ```

5. **設定初始資金**

   ```
   - 找到 "初始資金 (TWD)" 數字輸入框
   - 驗證預設值: 1000000
   - 保持預設值或修改
   - 驗證: 值符合驗證規則 (最小值 1000, 步進 1000)
   ```

6. **設定單一持股比例上限**

   ```
   - 找到 "單一持股比例上限 (%)" 數字輸入框
   - 驗證預設值: 5
   - 輸入: 50
   - 驗證: 值在 1-100 範圍內
   ```

7. **選擇 AI 模型**

   ```
   - 找到 "AI 模型" 下拉選單
   - 驗證預設選項: "GPT-5 Mini"
   - 驗證選項列表:
     * GPT-5 Mini
     * GPT-4o Mini
     * GPT-4.1 Mini
     * Gemini 2.5 Pro
     * Gemini 2.0 Flash
   - 保持預設選擇
   ```

8. **提交表單**

   ```
   - 點擊 "創建 Agent" 按鈕
   - 監控網路請求:
     * 方法: POST
     * URL: http://localhost:8000/api/agents
     * 驗證請求 Body 格式正確
   - 等待回應
   ```

9. **驗證 API 回應**

   ```
   - 驗證: HTTP 狀態碼 201
   - 驗證: 回應包含 agent_id
   - 驗證: 對話框關閉
   - 驗證: 顯示成功通知訊息
   ```

10. **驗證 UI 更新**

    ```
    - 驗證: Agent 卡片出現在列表中
    - 驗證: Agent 資訊正確顯示：
      * 名稱: "巴菲特"
      * AI 模型: "GPT-5 Mini"
      * 初始資金: "1,000,000"
      * 單一持股上限: "50%"
      * 狀態: "idle" 或 "inactive"
      * 創建時間: 當前時間
    ```

11. **驗證資料庫持久化（關鍵步驟）** 🔥

    ```sql
    -- 方法 1: 使用 test_database_verification.py 工具
    cd backend
    uv run python test_database_verification.py

    -- 預期輸出:
    ✅ 資料庫中有 1 個 Agent

    📋 最近創建的 Agent:
    ---
    ID: agent-xxxxx
    Name: 巴菲特
    Model: gpt-5-mini
    Status: inactive
    Initial Funds: 1,000,000.00
    Created At: 2025-10-11 xx:xx:xx

    -- 方法 2: 直接查詢資料庫
    SELECT id, name, model, initial_funds, max_position_size, status,
           instructions, config, created_at, updated_at
    FROM agents
    WHERE name = '巴菲特'
    ORDER BY created_at DESC
    LIMIT 1;

    驗證結果（必須全部通過）:
    - ✅ 存在一筆記錄
    - ✅ name = '巴菲特'
    - ✅ model = 'gpt-5-mini' (對應 GPT-5 Mini)
    - ✅ initial_funds = 1000000.00
    - ✅ max_position_size = 50.00
    - ✅ status = 'inactive' 或 'active'
    - ✅ instructions 包含投資偏好描述
    - ✅ created_at 與當前時間相近（< 1分鐘）
    - ✅ updated_at = created_at（首次創建）
    ```

12. **驗證後端日誌（確認資料庫寫入）** 🔥

    ```bash
    # 檢查後端日誌，應該看到以下訊息：
    INFO - Saving agent state to database for agent-xxxxx
    INFO - Agent state saved to database: agent-xxxxx

    驗證結果:
    - ✅ 日誌顯示資料庫保存成功
    - ✅ 無資料庫錯誤訊息
    ```

13. **驗證相關表資料（選做）**

    ```sql
    -- 驗證 agent_config_cache 是否有對應記錄（如有使用）
    SELECT agent_id, config_data, cached_at
    FROM agent_config_cache
    WHERE agent_id = [從步驟11取得的id];

    -- 驗證 agent_sessions 是否正確初始化（如需要）
    SELECT agent_id, session_count
    FROM agent_sessions
    WHERE agent_id = [agent_id];

    驗證結果:
    - ✅ 相關表的外鍵正確關聯
    - ✅ 初始資料正確設定
    ```

**預期結果**:

- ✅ API 回應正確（status 201, agent_id 存在）
- ✅ UI 狀態正確更新（卡片顯示、資訊正確）
- ✅ **資料庫記錄已創建且資料完整正確** 🔥
- ✅ **後端日誌顯示資料庫保存成功** 🔥
- ✅ 相關表外鍵正確關聯
- ✅ 無控制台錯誤
- ✅ 無網路請求失敗

**失敗情況處理**:

- ❌ **如果 API 回應 201 但資料庫無記錄** (TC-001 曾發現的問題):
  - 問題: `AgentManager.create_agent()` 沒有呼叫資料庫服務
  - 修復: 確保 `AgentManager` 已注入 `AgentDatabaseService`
  - 修復: 確保 `create_agent()` 呼叫 `save_agent_state()`
  - 參考: 詳見 `docs/TC-001_FIX_SUMMARY.md`
  - **這是嚴重的資料不一致問題！**

- ❌ **如果資料庫保存失敗但 API 回應成功**:
  - 問題: 錯誤處理不完整
  - 修復: 確保資料庫錯誤時清理內存狀態並回傳錯誤
  - 檢查: 後端日誌是否有 "Failed to save agent to database"

- ❌ **如果出現 422 驗證錯誤**:
  - 檢查請求 Body 格式
  - 檢查前後端驗證規則一致性

- ❌ **如果模型選項無法創建**:
  - 檢查資料庫 `ai_model_configs` 表
  - 檢查 API `AIModel` enum 定義
  - 確保兩者同步

- ❌ **如果資料庫記錄存在但資料不正確**:
  - 檢查欄位映射是否正確
  - 檢查資料轉換邏輯
  - 檢查預設值設定

---

### TC-002: Agent 模型選項與驗證一致性

**目標**: 確認前端顯示的 AI 模型選項與後端驗證規則一致

**測試步驟**:

1. **取得前端模型選項**

   ```
   - 開啟創建 Agent 對話框
   - 點擊 AI 模型下拉選單
   - 記錄所有可選模型的 value 值
   ```

2. **測試每個模型**

   ```
   For each model in dropdown:
     - 選擇該模型
     - 填寫其他必填欄位
     - 提交表單
     - 驗證: 創建成功（status 201）
     - 清除並重新測試下一個
   ```

3. **驗證每個模型的資料庫持久化** 🔥

   ```bash
   # 方法 1: 使用 test_database_verification.py 工具
   cd backend
   uv run python test_database_verification.py
   # 檢查每個測試 Agent 是否正確寫入

   # 方法 2: 直接查詢每個模型的 Agent
   ```

   ```sql
   For each model created:
     -- 查詢資料庫:
     SELECT id, name, model FROM agents WHERE name = [測試名稱];

     驗證:
     - ✅ 記錄存在
     - ✅ model 欄位值正確對應選擇的模型
     - ✅ 清除測試資料
   ```

4. **驗證資料庫同步**

   ```sql
   -- 查詢啟用的模型
   SELECT model_key, display_name, is_enabled
   FROM ai_model_configs
   WHERE is_enabled = 1
   ORDER BY display_order;

   驗證:
   - ✅ 結果集與前端下拉選單選項一致
   - ✅ 每個模型都有對應的 display_name
   ```

5. **驗證後端 enum**

   ```python
   # 檢查: backend/src/api/models.py 的 AIModel enum
   # 比對資料庫查詢結果

   驗證:
   - ✅ enum 值 = 資料庫 model_key
   - ✅ 完全一致，無遺漏或多餘
   ```

**預期結果**:

- ✅ 前端選項 = 資料庫啟用模型 = 後端 enum（三者同步）
- ✅ 所有模型都可以成功創建 Agent
- ✅ **每個模型創建的 Agent 都正確寫入資料庫** 🔥
- ✅ **model 欄位值正確對應選擇的模型** 🔥
- ✅ 無孤立資料或不一致

**失敗情況處理**:

- ❌ **如果某個模型創建成功但資料庫無記錄**:
  - 問題: 與 TC-001 相同的根本原因
  - 參考: `docs/TC-001_FIX_SUMMARY.md`

---

### TC-003: 表單驗證測試

**目標**: 驗證前端表單驗證與後端 API 驗證一致

**測試案例**:

#### 3.1 必填欄位驗證

```
測試項目:
- Agent 名稱為空 → 應該顯示錯誤
- 投資偏好描述為空 → 應該顯示錯誤
- 初始資金為 0 → 應該顯示錯誤
```

#### 3.2 數值範圍驗證

```
測試項目:
- 初始資金 < 1000 → 應該顯示錯誤
- 初始資金不是 1000 的倍數 → 應該顯示錯誤
- 單一持股比例 < 1% → 應該顯示錯誤
- 單一持股比例 > 100% → 應該顯示錯誤
```

#### 3.3 字串長度驗證

```
測試項目:
- Agent 名稱 > 100 字元 → 應該顯示錯誤
- 投資偏好描述 < 10 字元 → 應該顯示錯誤（後端要求）
```

---

### TC-004: WebSocket 即時推送測試

**目標**: 驗證 WebSocket 連線與即時推送功能

**測試步驟**:

1. **驗證初始連線**

   ```
   - 開啟頁面
   - 檢查控制台訊息
   - 驗證: "WebSocket connected" 訊息出現
   - 驗證: 頁面顯示 "即時連線" 狀態
   ```

2. **測試 Agent 狀態推送**

   ```
   - 創建 Agent
   - 啟動 Agent
   - 驗證: 收到 agent_status WebSocket 訊息
   - 驗證: UI 狀態即時更新（無需重新整理）
   ```

3. **測試交易執行推送**

   ```
   - Agent 執行交易時
   - 驗證: 收到 trade_execution WebSocket 訊息
   - 驗證: 交易記錄即時出現在列表中
   ```

4. **測試斷線重連**

   ```
   - 模擬網路斷線
   - 等待重連
   - 驗證: 自動重新連線成功
   - 驗證: 繼續接收推送訊息
   ```

---

### TC-005: 錯誤處理與使用者提示

**目標**: 驗證錯誤情況下的使用者體驗

**測試案例**:

#### 5.1 後端服務未啟動

```
- 停止後端服務
- 嘗試創建 Agent
- 驗證: 顯示友善的錯誤訊息
- 驗證: 不會白屏或崩潰
```

#### 5.2 API 返回 422 驗證錯誤

```
- 發送不符合規則的請求
- 驗證: 顯示具體的驗證錯誤訊息
- 驗證: 標示出錯誤的欄位
```

#### 5.3 網路逾時

```
- 模擬慢速網路
- 提交表單
- 驗證: 顯示載入狀態
- 驗證: 逾時後顯示錯誤訊息
```

---

## 🔧 測試工具使用指南

### Chrome DevTools MCP 基本操作

#### 1. 開啟頁面

```javascript
mcp_chrome-devtoo_new_page({url: "http://localhost:3000"})
```

#### 2. 取得頁面快照

```javascript
mcp_chrome-devtoo_take_snapshot()
// 返回頁面元素樹，包含每個元素的 uid
```

#### 3. 點擊元素

```javascript
mcp_chrome-devtoo_click({uid: "element_uid"})
```

#### 4. 填寫表單

```javascript
mcp_chrome-devtoo_fill_form({
  elements: [
    {uid: "name_input_uid", value: "巴菲特"},
    {uid: "description_input_uid", value: "投資策略描述"}
  ]
})
```

#### 5. 監控網路請求

```javascript
mcp_chrome-devtoo_list_network_requests({
  resourceTypes: ["fetch", "xhr"]
})
```

#### 6. 檢查控制台錯誤

```javascript
mcp_chrome-devtoo_list_console_messages()
```

#### 7. 截圖驗證

```javascript
mcp_chrome-devtoo_take_screenshot({
  fullPage: true,
  format: "png"
})
```

---

## 📊 測試報告格式

### 測試結果記錄

```markdown
## 測試執行報告

**執行日期**: 2025-10-11
**執行人**: [測試人員]
**測試環境**:
- 後端: http://localhost:8000
- 前端: http://localhost:3000
- 資料庫: SQLite (backend/casualtrader.db)
- 瀏覽器: Chrome 141.0.0.0

### 測試案例執行結果

| 案例 ID | 案例名稱 | UI 測試 | API 測試 | DB 驗證 | 執行時間 | 備註 |
|---------|---------|---------|---------|---------|----------|------|
| TC-001 | 創建 Agent 完整流程 | ✅ PASS | ✅ PASS | ❌ FAIL | 15s | DB 無記錄！ |
| TC-002 | 模型選項一致性 | ✅ PASS | ❌ FAIL | N/A | 8s | enum 不同步 |
| TC-003 | 表單驗證測試 | ✅ PASS | ✅ PASS | ✅ PASS | 12s | - |
| TC-004 | WebSocket 推送 | ✅ PASS | ✅ PASS | ⚠️ PARTIAL | 10s | 狀態推送正常但 DB 未更新 |
| TC-005 | 錯誤處理 | ⚠️ PARTIAL | ✅ PASS | N/A | 20s | 錯誤訊息待改善 |

### 發現的問題

1. **[CRITICAL] Agent 創建成功但資料庫無記錄**
   - 描述: API 返回 201，UI 顯示正常，但 `SELECT * FROM agents` 為空
   - 影響: 資料未持久化，重啟後 Agent 消失，系統不可用
   - 根因: `AgentManager.create_agent()` 未呼叫 `AgentDatabaseService.create_agent()`
   - 修復: 在 `AgentManager` 中注入資料庫服務並呼叫寫入方法
   - 優先級: **P0 - 必須立即修復**

2. **[CRITICAL] 後端 AIModel enum 與資料庫不同步**
   - 描述: `ai_model_configs` 表中有 `gpt-5-mini`，但 `AIModel` enum 中沒有
   - 影響: 使用者選擇 gpt-5-mini 會創建失敗（422 驗證錯誤）
   - 修復: 將 gpt-5-mini 加入 AIModel enum，或從資料庫移除
   - 優先級: **P0 - 必須立即修復**

3. **[HIGH] 前端發送欄位與後端不一致**
   - 描述: 前端發送 `description`，後端期望 `strategy_prompt`
   - 影響: 創建 Agent 時 422 錯誤
   - 修復: 前端改為發送 `strategy_prompt`
   - 優先級: **P1 - 高優先級**

4. **[HIGH] Agent 狀態變更未更新資料庫**
   - 描述: 啟動/停止 Agent 時 WebSocket 推送正常，但 `agents.status` 未更新
   - 影響: 重啟服務後狀態不一致
   - 修復: 在狀態變更時呼叫資料庫更新方法
   - 優先級: **P1 - 高優先級**

### 修復驗證

- [x] 問題 1 已修復並驗證
- [x] 問題 2 已修復並驗證
- [ ] 重新執行完整測試套件

### 結論

初次測試發現多個前後端不一致問題，證明瀏覽器 E2E 測試的必要性。
傳統 API 測試無法發現這些問題。建議所有主要功能都加入瀏覽器 E2E 測試。
```

---

## 🎯 測試檢查清單

### 每次發布前必測項目

- [ ] TC-001: 創建 Agent 完整流程
- [ ] TC-002: Agent 模型選項與驗證一致性
- [ ] TC-003: 表單驗證測試
- [ ] TC-004: WebSocket 即時推送測試
- [ ] TC-005: 錯誤處理與使用者提示
- [ ] Agent 啟動/停止功能
- [ ] Agent 刪除功能
- [ ] Agent 配置更新功能
- [ ] 交易記錄查看
- [ ] 策略變更記錄查看
- [ ] 績效圖表顯示
- [ ] 多 Agent 同時運行

### 前後端一致性檢查清單

#### 資料模型同步

- [ ] 資料庫 `ai_model_configs.model_key` ↔ 後端 `AIModel` enum
- [ ] 前端表單欄位名稱 ↔ 後端 Pydantic 模型欄位
- [ ] 前端驗證規則 ↔ 後端 `Field` 驗證
- [ ] 前端預設值 ↔ 後端 `Field` 預設值
- [ ] WebSocket 事件類型 ↔ 前後端約定

#### 資料持久化檢查

- [ ] Agent 創建 → `agents` 表有記錄
- [ ] Agent 啟動 → `agents.status` 更新為 'active'
- [ ] Agent 啟動 → `agent_sessions` 創建新記錄
- [ ] Agent 停止 → `agents.status` 更新為 'inactive'
- [ ] Agent 停止 → `agent_sessions.ended_at` 已設定
- [ ] Agent 刪除 → 所有相關表記錄級聯刪除
- [ ] 交易執行 → `transactions` 表有記錄
- [ ] 交易執行 → `agent_holdings` 正確更新
- [ ] 交易執行 → `agent_performance` 創建快照
- [ ] 策略變更 → `strategy_changes` 表有記錄

#### 資料一致性檢查

- [ ] API 回應的 `agent_id` 在資料庫中存在
- [ ] UI 顯示的資料與資料庫查詢結果一致
- [ ] WebSocket 推送的資料與資料庫狀態一致
- [ ] 外鍵約束正確設定且無孤立記錄
- [ ] 時間戳記正確更新（created_at, updated_at, last_active_at）

---

## 📝 維護建議

1. **自動化測試腳本**: 將測試步驟寫成可重複執行的腳本
2. **持續整合**: 將瀏覽器測試加入 CI/CD 流程
3. **定期同步檢查**: 每次修改資料模型或驗證規則時，執行一致性檢查
4. **測試資料管理**: 建立測試用的 Agent 配置和市場資料
5. **截圖對比**: 保存正確的 UI 截圖，用於回歸測試對比

## 🗄️ 資料庫驗證最佳實踐

### 為什麼需要資料庫驗證？

傳統的 E2E 測試只驗證：

- ✅ API 是否返回 200/201
- ✅ UI 是否正確顯示

但**無法發現**：

- ❌ API 返回成功但資料未寫入資料庫
- ❌ 資料寫入但欄位值不正確
- ❌ 相關表的外鍵關聯遺漏
- ❌ 級聯刪除未正確執行
- ❌ 時間戳記未更新

### 資料庫驗證的重要性

**案例: TC-001 Agent 創建**

```
❌ 只測試 API + UI:
   API 返回 201 ✅
   UI 顯示 Agent 卡片 ✅
   → 測試通過 ✅
   → 但資料庫無記錄！❌

✅ 加入資料庫驗證:
   API 返回 201 ✅
   UI 顯示 Agent 卡片 ✅
   查詢 agents 表 ❌ (無記錄)
   → 測試失敗 ❌
   → 發現 AgentManager 未呼叫資料庫服務 ✅
```

### 每個測試案例都應包含的驗證層級

```
1. API 層驗證
   - HTTP 狀態碼
   - 回應 Body 格式
   - 回應資料正確性

2. UI 層驗證
   - 元素顯示/隱藏
   - 資料展示正確
   - 互動反饋正常

3. 資料庫層驗證 ⭐
   - 主表記錄存在
   - 欄位值正確
   - 相關表記錄正確
   - 外鍵關聯完整
   - 時間戳記正確
```

### SQL 查詢範例

```sql
-- 基本存在性驗證
SELECT COUNT(*) FROM agents WHERE id = ?;
-- 預期: 1

-- 完整資料驗證
SELECT * FROM agents WHERE id = ?;
-- 驗證每個欄位值

-- 關聯資料驗證
SELECT a.id, a.name,
       COUNT(DISTINCT h.ticker) as holdings_count,
       COUNT(DISTINCT t.id) as transactions_count,
       COUNT(DISTINCT p.id) as performance_snapshots
FROM agents a
LEFT JOIN agent_holdings h ON a.id = h.agent_id
LEFT JOIN transactions t ON a.id = t.agent_id
LEFT JOIN agent_performance p ON a.id = p.agent_id
WHERE a.id = ?
GROUP BY a.id;
```

### 實施建議

1. **測試前準備**

   ```sql
   -- 記錄測試前的資料基線
   SELECT COUNT(*) FROM agents;
   ```

2. **執行操作**
   - 透過瀏覽器執行測試操作

3. **多層驗證**

   ```
   ✅ API 回應驗證
   ✅ UI 狀態驗證
   ✅ 資料庫記錄驗證 ⭐
   ✅ 資料一致性驗證 ⭐
   ```

4. **測試後清理**

   ```sql
   -- 清理測試資料
   DELETE FROM agents WHERE name LIKE 'Test%';
   ```

---

## 🎯 Agent 操作與控制測試

### TC-006: 啟動 Agent

**目標**: 驗證 Agent 啟動功能

**前置條件**:

- 已創建至少一個 Agent
- Agent 狀態為 "idle" 或 "stopped"

**測試步驟**:

1. **找到 Agent 卡片**
   - 在 Agent 列表中找到目標 Agent
   - 驗證顯示 "啟動" 按鈕

2. **點擊啟動按鈕**
   - 點擊 "啟動" 按鈕
   - 驗證按鈕變為載入狀態

3. **驗證狀態變更**
   - 驗證 Agent 狀態變為 "running"
   - 驗證狀態指示器更新
   - 驗證 "啟動" 按鈕變為 "停止" 按鈕

4. **驗證配置鎖定**
   - 驗證出現 "執行中無法編輯配置" 提示
   - 驗證無法編輯 Agent 設定

5. **驗證成功通知**
   - 驗證顯示 "Agent [名稱] 已啟動" 通知

6. **驗證後端日誌** 🔥

   ```bash
   # 檢查後端日誌，應該看到狀態更新訊息：
   INFO - Agent [agent_id] status updated in database: ACTIVE
   INFO - Starting agent [agent_id]

   驗證結果:
   - ✅ 日誌顯示狀態已同步到資料庫
   - ✅ 無資料庫錯誤訊息
   ```

7. **驗證資料庫狀態更新（關鍵步驟）** 🔥

   ```sql
   -- 方法 1: 使用 test_database_verification.py 工具查看狀態
   cd backend
   uv run python test_database_verification.py

   -- 方法 2: 直接查詢 Agent 當前狀態
   SELECT id, name, status, current_mode, last_active_at, updated_at
   FROM agents
   WHERE id = [agent_id];

   驗證（必須全部通過）:
   - ✅ status = 'active'
   - ✅ current_mode 已設定（如 'TRADING' 或 'OBSERVATION'）
   - ✅ last_active_at 已更新為當前時間（< 1分鐘）
   - ✅ updated_at > created_at（時間戳已更新）
   - ✅ updated_at 與當前時間相近（< 1分鐘）
   ```

8. **驗證 Session 記錄（選做）**

   ```sql
   -- 查詢是否創建了執行 session
   SELECT agent_id, session_id, started_at, status
   FROM agent_sessions
   WHERE agent_id = [agent_id]
   ORDER BY started_at DESC
   LIMIT 1;

   驗證:
   - ✅ 存在新的 session 記錄
   - ✅ status = 'running' 或 'active'
   - ✅ started_at 為當前時間
   ```

**預期結果**:

- ✅ Agent 成功啟動
- ✅ UI 狀態正確更新
- ✅ UI 配置正確鎖定
- ✅ **後端日誌顯示資料庫狀態更新成功** 🔥
- ✅ **資料庫 status 正確更新為 'active'** 🔥
- ✅ **last_active_at 時間正確更新** 🔥
- ✅ **Session 記錄已創建**
- ✅ WebSocket 推送狀態變更

**失敗情況處理**:

- ❌ **如果 Agent 啟動但資料庫 status 未更新**:
  - 問題: `AgentManager.start_agent()` 沒有同步資料庫狀態
  - 修復: 確保 `start_agent()` 呼叫 `save_agent_state()`
  - 參考: `docs/TC-001_FIX_SUMMARY.md`

- ❌ **如果 last_active_at 未更新**:
  - 問題: 狀態更新邏輯不完整
  - 檢查: AgentState 是否正確設定 last_active_at 欄位

---

### TC-007: 停止 Agent

**目標**: 驗證 Agent 停止功能

**前置條件**:

- Agent 狀態為 "running"

**測試步驟**:

1. **找到運行中的 Agent**
   - 找到狀態為 "running" 的 Agent
   - 驗證顯示 "停止" 按鈕

2. **點擊停止按鈕**
   - 點擊 "停止" 按鈕
   - 驗證按鈕變為載入狀態

3. **驗證狀態變更**
   - 驗證 Agent 狀態變為 "stopped"
   - 驗證狀態指示器更新
   - 驗證 "停止" 按鈕變為 "啟動" 按鈕

4. **驗證配置解鎖**
   - 驗證 "執行中無法編輯配置" 提示消失
   - 驗證可以編輯 Agent 設定

5. **驗證成功通知**
   - 驗證顯示 "Agent [名稱] 已停止" 通知

6. **驗證後端日誌** 🔥

   ```bash
   # 檢查後端日誌，應該看到停止訊息：
   INFO - Agent [agent_id] status updated in database: INACTIVE
   INFO - Agent [agent_id] stopped successfully

   驗證結果:
   - ✅ 日誌顯示狀態已同步到資料庫
   - ✅ Agent 正確停止
   - ✅ 無資料庫錯誤訊息
   ```

7. **驗證資料庫狀態更新（關鍵步驟）** 🔥

   ```sql
   -- 方法 1: 使用 test_database_verification.py 工具查看狀態
   cd backend
   uv run python test_database_verification.py

   -- 方法 2: 直接查詢 Agent 停止後的狀態
   SELECT id, name, status, current_mode, last_active_at, updated_at
   FROM agents
   WHERE id = [agent_id];

   驗證（必須全部通過）:
   - ✅ status = 'inactive' 或 'stopped'
   - ✅ current_mode 保持或重設
   - ✅ last_active_at 為停止時間（< 1分鐘）
   - ✅ updated_at > 啟動時的 updated_at（已更新）
   - ✅ updated_at 與當前時間相近（< 1分鐘）
   ```

8. **驗證 Session 結束（選做）**

   ```sql
   -- 查詢 session 是否正確結束
   SELECT agent_id, session_id, started_at, ended_at, status
   FROM agent_sessions
   WHERE agent_id = [agent_id]
   ORDER BY started_at DESC
   LIMIT 1;

   驗證:
   - ✅ ended_at 已設定為當前時間
   - ✅ status = 'stopped' 或 'completed'
   - ✅ session 持續時間合理 (ended_at - started_at)
   ```

**預期結果**:

- ✅ Agent 成功停止
- ✅ UI 狀態正確更新
- ✅ UI 配置正確解鎖
- ✅ **後端日誌顯示資料庫狀態更新成功** 🔥
- ✅ **資料庫 status 正確更新為 'inactive'** 🔥
- ✅ **last_active_at 時間正確更新** 🔥
- ✅ **Session 記錄已正確結束**
- ✅ WebSocket 推送狀態變更

**失敗情況處理**:

- ❌ **如果 Agent 停止但資料庫 status 未更新**:
  - 問題: `AgentManager.stop_agent()` 沒有同步資料庫狀態
  - 修復: 確保 `stop_agent()` 呼叫 `save_agent_state()`
  - 參考: `docs/TC-001_FIX_SUMMARY.md`

- ❌ **如果 last_active_at 未更新**:
  - 問題: 狀態更新邏輯不完整
  - 檢查: AgentState 是否正確設定 last_active_at 欄位

---

### TC-008: 刪除 Agent

**目標**: 驗證 Agent 刪除功能與確認機制

**前置條件**:

- 已創建至少一個 Agent
- Agent 狀態為非 "running"（如果運行中需先停止）

**測試步驟**:

1. **點擊刪除按鈕**
   - 找到 Agent 卡片上的 "刪除" 按鈕
   - 點擊 "刪除" 按鈕

2. **驗證確認對話框**
   - 驗證出現確認對話框
   - 驗證顯示警告訊息：

     ```
     確定要刪除 Agent "[名稱]"?

     此操作無法復原,所有相關資料(持倉、交易記錄、策略變更)將被永久刪除。
     ```

3. **取消刪除**
   - 點擊 "取消" 按鈕
   - 驗證 Agent 仍然存在
   - 驗證沒有任何變更

4. **確認刪除**
   - 再次點擊 "刪除" 按鈕
   - 點擊 "確定" 按鈕

5. **驗證刪除成功**
   - 驗證 Agent 卡片從列表中消失
   - 驗證顯示 "Agent [名稱] 已刪除" 通知

6. **驗證後端日誌** 🔥

   ```bash
   # 檢查後端日誌，應該看到刪除訊息：
   INFO - Deleting agent from database: [agent_id]
   INFO - Agent deleted from database: [agent_id]
   INFO - Agent [agent_id] removed successfully

   驗證結果:
   - ✅ 日誌顯示資料庫刪除成功
   - ✅ 無資料庫錯誤訊息
   ```

7. **驗證資料庫完全清除（關鍵步驟）** 🔥

   ```bash
   # 方法 1: 使用 test_database_verification.py 工具快速驗證
   cd backend
   uv run python test_database_verification.py
   # 預期: 不應該列出已刪除的 Agent

   # 方法 2: 直接查詢各表驗證級聯刪除
   ```

   ```sql
   -- 1. 驗證主表記錄已刪除
   SELECT COUNT(*) FROM agents WHERE id = '[agent_id]';
   驗證: 結果 = 0 ✅

   -- 2. 驗證相關持倉記錄已刪除
   SELECT COUNT(*) FROM agent_holdings WHERE agent_id = '[agent_id]';
   驗證: 結果 = 0 ✅

   -- 3. 驗證交易記錄已刪除（或標記為已刪除）
   SELECT COUNT(*) FROM transactions WHERE agent_id = '[agent_id]';
   驗證: 結果 = 0 或所有記錄 is_deleted = true ✅

   -- 4. 驗證績效記錄已刪除
   SELECT COUNT(*) FROM agent_performance WHERE agent_id = '[agent_id]';
   驗證: 結果 = 0 ✅

   -- 5. 驗證策略變更記錄已刪除
   SELECT COUNT(*) FROM strategy_changes WHERE agent_id = '[agent_id]';
   驗證: 結果 = 0 ✅

   -- 6. 驗證 Session 記錄已刪除
   SELECT COUNT(*) FROM agent_sessions WHERE agent_id = '[agent_id]';
   驗證: 結果 = 0 ✅

   -- 7. 驗證配置快取已清除
   SELECT COUNT(*) FROM agent_config_cache WHERE agent_id = '[agent_id]';
   驗證: 結果 = 0 ✅
   ```

8. **驗證級聯刪除完整性**

   ```text
   檢查清單:
   - ✅ 主表 agents 記錄已刪除
   - ✅ 所有外鍵關聯的子表記錄已清除
   - ✅ 無孤立資料殘留
   - ✅ 資料庫完整性約束正常
   - ✅ 後端日誌無錯誤
   ```

**預期結果**:

- ✅ 確認對話框正確顯示且文字清楚警告
- ✅ 取消功能正常（不刪除任何資料）
- ✅ 刪除功能正常（UI 即時更新）
- ✅ **後端日誌顯示資料庫刪除成功** 🔥
- ✅ **資料庫中 Agent 及所有相關記錄完全清除** 🔥
- ✅ **級聯刪除正確執行** 🔥
- ✅ **無資料殘留或孤立記錄** 🔥

**失敗情況處理**:

- ❌ **如果 Agent 從 UI 消失但資料庫記錄仍存在**:
  - 問題: `AgentManager.remove_agent()` 沒有呼叫資料庫刪除
  - 修復: 確保 `remove_agent()` 呼叫 `database_service.delete_agent()`
  - 參考: `docs/TC-001_FIX_SUMMARY.md`

- ❌ **如果主表已刪除但子表有孤立記錄**:
  - 問題: 資料庫外鍵約束未設定 CASCADE DELETE
  - 修復: 檢查資料庫 schema，確保所有外鍵設定 `ON DELETE CASCADE`

- ❌ **如果刪除失敗但沒有錯誤訊息**:
  - 問題: 錯誤處理不完整
  - 檢查: 後端日誌是否有 "Failed to delete agent from database"

---

### TC-009: 選擇 Agent

**目標**: 驗證 Agent 選擇與詳細資訊展示

**前置條件**:

- 已創建至少兩個 Agent

**測試步驟**:

1. **點擊第一個 Agent 卡片**
   - 點擊任一 Agent 卡片
   - 驗證卡片出現藍色邊框和選中標記

2. **驗證詳細資訊載入**
   - 驗證右側展示詳細資訊
   - 驗證顯示績效圖表
   - 驗證顯示策略歷史

3. **切換選擇不同 Agent**
   - 點擊另一個 Agent 卡片
   - 驗證前一個 Agent 卡片選中狀態取消
   - 驗證新 Agent 卡片顯示選中狀態
   - 驗證詳細資訊更新為新 Agent

4. **驗證資料載入**
   - 驗證 API 請求正確發送
   - 驗證效能資料正確展示
   - 驗證策略變更記錄正確展示

**預期結果**:

- ✅ 選擇狀態正確切換
- ✅ 詳細資訊正確載入
- ✅ 視覺反饋清晰

---

### TC-010: 查看 Agent 策略歷史

**目標**: 驗證策略變更記錄展示功能

**前置條件**:

- 已創建至少一個 Agent
- Agent 已執行並有策略變更記錄

**測試步驟**:

1. **選擇有策略記錄的 Agent**
   - 選擇一個有策略變更的 Agent
   - 找到 "查看策略歷史" 按鈕或連結

2. **開啟策略歷史視窗**
   - 點擊 "查看策略歷史" 按鈕
   - 驗證模態視窗開啟

3. **驗證策略記錄展示**
   - 驗證顯示所有策略變更記錄
   - 驗證每筆記錄包含：
     - 變更時間
     - 觸發原因
     - 變更內容
     - Agent 說明
     - 當時績效資料

4. **驗證記錄排序**
   - 驗證記錄按時間倒序排列（最新在上）

5. **關閉視窗**
   - 點擊關閉按鈕或背景遮罩
   - 驗證模態視窗關閉

**預期結果**:

- ✅ 策略記錄正確展示
- ✅ 資訊完整清晰
- ✅ 互動流暢

---

## 📊 資料查詢與展示測試

### TC-011: 績效圖表展示

**目標**: 驗證 Agent 績效圖表正確渲染與互動

**前置條件**:

- 已創建至少一個 Agent
- Agent 已執行一段時間並有績效資料

**測試步驟**:

1. **選擇 Agent**
   - 選擇一個有績效資料的 Agent
   - 等待績效圖表載入

2. **驗證圖表渲染**
   - 驗證使用 Chart.js 渲染圖表
   - 驗證圖表類型為折線圖
   - 驗證 X 軸為時間軸
   - 驗證 Y 軸為資產價值

3. **驗證資料點**
   - 驗證圖表顯示所有績效資料點
   - 驗證資料點連線流暢
   - 驗證顏色符合 Agent 主題色

4. **測試圖表互動**
   - 滑鼠懸停在資料點上
   - 驗證顯示詳細資訊提示框（tooltip）
   - 驗證提示框顯示：
     - 時間
     - 資產價值
     - 收益率

5. **測試響應式設計**
   - 調整瀏覽器視窗大小
   - 驗證圖表自動調整大小
   - 驗證在小螢幕上仍可閱讀

**預期結果**:

- ✅ 圖表正確渲染
- ✅ 資料正確展示
- ✅ 互動功能正常
- ✅ 響應式設計良好

---

### TC-012: 市場狀態指示器

**目標**: 驗證市場開盤/收盤狀態正確顯示

**測試步驟**:

1. **驗證初始狀態載入**
   - 頁面載入時檢查導航欄
   - 驗證顯示市場狀態指示器

2. **市場開盤狀態**
   - 如果在交易時間（週一至週五 09:00-13:30）
   - 驗證顯示 "市場開盤" 或類似文字
   - 驗證狀態指示器為綠色

3. **市場收盤狀態**
   - 如果在非交易時間
   - 驗證顯示 "市場已收盤" 或類似文字
   - 驗證狀態指示器為灰色或紅色

4. **測試狀態刷新**
   - 等待 30 秒（市場資料刷新間隔）
   - 驗證狀態自動更新（如果跨越開盤/收盤時間）

**預期結果**:

- ✅ 市場狀態正確顯示
- ✅ 狀態指示器顏色正確
- ✅ 自動刷新功能正常

---

### TC-013: WebSocket 連線狀態指示

**目標**: 驗證 WebSocket 連線狀態正確顯示

**測試步驟**:

1. **驗證初始連線**
   - 頁面載入後檢查導航欄
   - 驗證顯示 "即時連線" 或類似文字
   - 驗證連線狀態指示器為綠色

2. **檢查控制台訊息**
   - 開啟瀏覽器開發者工具
   - 檢查控制台
   - 驗證顯示 "WebSocket connected" 訊息

3. **模擬斷線**
   - 開啟 Chrome DevTools Network 標籤
   - 切換到 Offline 模式
   - 等待幾秒

4. **驗證斷線狀態**
   - 驗證連線狀態指示器變為紅色或灰色
   - 驗證顯示 "連線中斷" 或類似文字

5. **測試重連**
   - 切回 Online 模式
   - 驗證自動重新連線
   - 驗證狀態指示器恢復綠色
   - 驗證顯示 "即時連線"

**預期結果**:

- ✅ 連線狀態正確顯示
- ✅ 斷線偵測正常
- ✅ 自動重連功能正常

---

### TC-014: Agent 資訊卡片完整性

**目標**: 驗證 Agent 卡片顯示所有必要資訊

**前置條件**:

- 已創建至少一個 Agent

**測試步驟**:

1. **驗證基本資訊**
   - 驗證顯示 Agent 名稱
   - 驗證顯示 AI 模型標籤
   - 驗證模型標籤格式化正確（如 "GPT-5 Mini"）

2. **驗證狀態指示器**
   - 驗證顯示 Agent 狀態（idle/running/stopped/error）
   - 驗證顯示當前交易模式（如果有）
   - 驗證狀態顏色正確

3. **驗證投資偏好描述**
   - 驗證顯示投資偏好描述
   - 驗證長文字正確截斷（line-clamp-3）
   - 驗證懸停時可看到完整文字（如有實作）

4. **驗證財務資訊**
   - 驗證顯示 "初始資金"
   - 驗證金額格式化正確（千分位逗號）
   - 驗證顯示 "單一持股上限"
   - 驗證百分比正確

5. **驗證時間資訊**
   - 驗證顯示 "創建時間"
   - 驗證時間格式化正確
   - 驗證時區正確

6. **驗證操作按鈕**
   - 根據 Agent 狀態驗證顯示正確按鈕：
     - idle/stopped: 顯示 "啟動"、"刪除"
     - running: 顯示 "停止"、"刪除"（可能禁用）

**預期結果**:

- ✅ 所有資訊正確顯示
- ✅ 格式化正確
- ✅ 按鈕狀態正確

---

### TC-015: 空狀態展示

**目標**: 驗證沒有 Agent 時的空狀態正確顯示

**前置條件**:

- 資料庫中沒有任何 Agent

**測試步驟**:

1. **開啟應用**
   - 清空所有 Agent
   - 重新整理頁面

2. **驗證空狀態顯示**
   - 驗證顯示空狀態提示
   - 驗證顯示標題："尚無 Agent" 或類似文字
   - 驗證顯示提示文字："點擊「創建新 Agent」開始您的 AI 交易之旅"

3. **驗證引導操作**
   - 驗證 "創建新 Agent" 按鈕醒目顯示
   - 驗證沒有錯誤訊息

4. **測試創建流程**
   - 點擊 "創建新 Agent" 按鈕
   - 驗證可以正常創建 Agent
   - 驗證創建後空狀態消失，顯示 Agent 卡片

**預期結果**:

- ✅ 空狀態友善清晰
- ✅ 引導使用者操作
- ✅ 無錯誤訊息

---

## 🔔 WebSocket 即時通信測試

### TC-016: Agent 狀態變更推送

**目標**: 驗證 Agent 狀態變更通過 WebSocket 即時推送

**前置條件**:

- 已創建至少一個 Agent
- WebSocket 已連線

**測試步驟**:

1. **準備監聽**
   - 開啟瀏覽器開發者工具
   - 切換到 Network > WS 標籤
   - 找到 WebSocket 連線

2. **觸發狀態變更**
   - 啟動一個 Agent
   - 觀察 WebSocket 訊息

3. **驗證推送訊息**
   - 驗證收到 WebSocket 訊息
   - 驗證訊息類型為 "agent_status"
   - 驗證訊息包含：
     - agent_id
     - status: "running"
     - timestamp

4. **驗證 UI 即時更新**
   - 驗證 Agent 卡片狀態即時更新
   - 驗證無需手動刷新頁面
   - 驗證狀態指示器即時變更

5. **測試停止推送**
   - 停止 Agent
   - 驗證收到對應的 WebSocket 訊息
   - 驗證 UI 即時更新

**預期結果**:

- ✅ WebSocket 推送正常
- ✅ UI 即時更新
- ✅ 無延遲或遺漏

---

### TC-017: 交易執行推送

**目標**: 驗證交易執行通過 WebSocket 即時推送

**前置條件**:

- Agent 正在運行
- Agent 執行交易操作

**測試步驟**:

1. **監聽 WebSocket**
   - 開啟 WS 監聽
   - 等待 Agent 執行交易

2. **驗證交易推送**
   - 驗證收到 "trade_execution" 訊息
   - 驗證訊息包含：
     - agent_id
     - trade_id
     - ticker（股票代號）
     - action（buy/sell）
     - quantity（數量）
     - price（價格）
     - timestamp

3. **驗證 UI 更新**
   - 驗證交易記錄即時出現
   - 驗證投資組合即時更新
   - 驗證績效圖表即時更新

**預期結果**:

- ✅ 交易推送正常
- ✅ 資料完整
- ✅ UI 即時更新

---

### TC-018: 策略變更推送

**目標**: 驗證策略變更通過 WebSocket 即時推送

**前置條件**:

- Agent 正在運行
- Agent 觸發策略調整

**測試步驟**:

1. **監聽 WebSocket**
   - 開啟 WS 監聽
   - 等待策略變更事件

2. **驗證策略變更推送**
   - 驗證收到 "strategy_change" 訊息
   - 驗證訊息包含：
     - agent_id
     - trigger_reason
     - change_content
     - agent_explanation
     - timestamp

3. **驗證 UI 更新**
   - 驗證策略歷史即時更新
   - 驗證通知提示顯示

**預期結果**:

- ✅ 策略變更推送正常
- ✅ UI 即時更新

---

### TC-019: 多 Agent 並發推送

**目標**: 驗證多個 Agent 同時運行時推送不混亂

**前置條件**:

- 已創建至少 3 個 Agent
- 所有 Agent 都在運行

**測試步驟**:

1. **啟動多個 Agent**
   - 依序啟動 3 個 Agent
   - 驗證都成功啟動

2. **監聽 WebSocket**
   - 觀察 WebSocket 訊息流

3. **驗證訊息隔離**
   - 驗證每個訊息正確標記 agent_id
   - 驗證 UI 更新時不影響其他 Agent

4. **測試選擇不同 Agent**
   - 切換選擇不同 Agent
   - 驗證只顯示選中 Agent 的資訊
   - 驗證 WebSocket 訊息仍然接收所有 Agent

**預期結果**:

- ✅ 多 Agent 推送正常
- ✅ 資料不混亂
- ✅ UI 隔離正確

---

### TC-020: WebSocket 重連後資料同步

**目標**: 驗證 WebSocket 重連後資料正確同步

**測試步驟**:

1. **建立初始狀態**
   - 創建並啟動一個 Agent
   - 等待一些資料產生

2. **模擬斷線**
   - 使用 Chrome DevTools 模擬斷線
   - 等待 5 秒

3. **恢復連線**
   - 恢復網路連線
   - 驗證 WebSocket 自動重連

4. **驗證資料同步**
   - 驗證 Agent 列表重新載入
   - 驗證所有 Agent 狀態正確
   - 驗證選中的 Agent 資料正確

5. **驗證推送恢復**
   - 驗證開始接收新的 WebSocket 訊息
   - 驗證沒有訊息遺漏（或有重連補償機制）

**預期結果**:

- ✅ 自動重連成功
- ✅ 資料正確同步
- ✅ 推送恢復正常

---

## 🚨 錯誤處理與恢復測試

### TC-021: 後端服務離線處理

**目標**: 驗證後端服務離線時的錯誤處理

**測試步驟**:

1. **停止後端服務**
   - 停止 backend 服務
   - 保持前端運行

2. **嘗試操作**
   - 嘗試創建 Agent
   - 嘗試啟動 Agent
   - 嘗試載入資料

3. **驗證錯誤提示**
   - 驗證顯示友善的錯誤訊息
   - 驗證不會白屏或崩潰
   - 驗證控制台有錯誤日誌但不影響 UI

4. **驗證錯誤通知**
   - 驗證顯示通知：" 無法連線到服務器，請稍後再試"
   - 驗證通知顏色為錯誤色（紅色）

5. **測試恢復**
   - 重啟後端服務
   - 重新嘗試操作
   - 驗證功能恢復正常

**預期結果**:

- ✅ 錯誤處理友善
- ✅ 不影響其他功能
- ✅ 恢復機制正常

---

### TC-022: API 422 驗證錯誤處理

**目標**: 驗證 API 返回驗證錯誤時的處理

**測試步驟**:

1. **觸發驗證錯誤**
   - 開啟創建 Agent 對話框
   - 填寫不符合規則的資料：
     - Agent 名稱留空
     - 投資偏好描述少於 10 字元
     - 初始資金設為 0

2. **提交表單**
   - 點擊 "創建 Agent" 按鈕

3. **驗證前端驗證**
   - 驗證前端先進行驗證
   - 驗證顯示欄位錯誤提示
   - 驗證錯誤欄位標記為紅色

4. **繞過前端驗證測試後端**
   - 使用開發者工具修改 HTML 移除驗證
   - 提交不合規的資料

5. **驗證後端錯誤處理**
   - 驗證收到 422 錯誤
   - 驗證顯示具體的驗證錯誤訊息
   - 驗證標示出錯誤的欄位

**預期結果**:

- ✅ 前端驗證優先
- ✅ 後端驗證作為備援
- ✅ 錯誤訊息清晰具體

---

### TC-023: 網路逾時處理

**目標**: 驗證網路請求逾時時的處理

**測試步驟**:

1. **模擬慢速網路**
   - 使用 Chrome DevTools Network 標籤
   - 設定 Slow 3G 或自訂節流

2. **執行長時間操作**
   - 嘗試創建 Agent
   - 嘗試載入大量資料

3. **驗證載入狀態**
   - 驗證顯示載入指示器（spinner）
   - 驗證按鈕顯示載入狀態
   - 驗證不能重複提交

4. **驗證逾時處理**
   - 等待請求逾時
   - 驗證顯示逾時錯誤訊息
   - 驗證提供重試選項

5. **測試重試**
   - 點擊重試按鈕
   - 驗證重新發送請求
   - 驗證成功後正常運作

**預期結果**:

- ✅ 載入狀態清晰
- ✅ 逾時處理友善
- ✅ 重試功能正常

---

### TC-024: 並發操作衝突處理

**目標**: 驗證多個操作並發時的衝突處理

**測試步驟**:

1. **快速連續操作**
   - 快速連續點擊 "啟動" 按鈕多次
   - 或在多個瀏覽器標籤同時操作同一 Agent

2. **驗證防重複提交**
   - 驗證只發送一次請求
   - 驗證按鈕在請求中禁用
   - 驗證不會產生重複操作

3. **測試狀態同步**
   - 在第二個瀏覽器標籤操作 Agent
   - 驗證第一個標籤透過 WebSocket 同步狀態

4. **測試樂觀更新**
   - 驗證 UI 樂觀更新（立即反映操作）
   - 如果請求失敗，驗證回滾到原狀態

**預期結果**:

- ✅ 防重複提交機制正常
- ✅ 多標籤狀態同步
- ✅ 樂觀更新與回滾正常

---

### TC-025: 資料不一致恢復

**目標**: 驗證前後端資料不一致時的恢復機制

**測試步驟**:

1. **製造資料不一致**
   - 直接修改資料庫（手動或 API）
   - 不通過前端 WebSocket 推送

2. **測試定期刷新**
   - 等待市場資料刷新週期（30 秒）
   - 驗證前端重新載入資料

3. **手動刷新**
   - 重新整理頁面
   - 驗證資料正確載入

4. **測試 WebSocket 補償**
   - 重連 WebSocket
   - 驗證資料重新同步

**預期結果**:

- ✅ 定期刷新機制正常
- ✅ 手動刷新正確
- ✅ WebSocket 補償機制正常

---

## 📱 響應式設計測試

### TC-026: 桌面視窗大小調整

**目標**: 驗證桌面環境下視窗調整的響應式表現

**測試步驟**:

1. **全螢幕測試**
   - 設定視窗為 1920x1080
   - 驗證佈局正常
   - 驗證 Agent 卡片排列美觀

2. **縮小視窗測試**
   - 逐漸縮小視窗寬度
   - 驗證 Agent 網格自動調整列數
   - 驗證圖表自動縮放

3. **最小寬度測試**
   - 設定視窗為 1024x768
   - 驗證所有內容仍可閱讀
   - 驗證無水平滾動條（或合理出現）

**預期結果**:

- ✅ 響應式佈局正常
- ✅ 無內容截斷
- ✅ 視覺效果良好

---

### TC-027: 平板裝置測試

**目標**: 驗證平板裝置上的使用體驗

**測試步驟**:

1. **使用 Chrome DevTools 模擬**
   - 開啟裝置工具列
   - 選擇 iPad (768x1024)

2. **測試觸控操作**
   - 測試點擊按鈕
   - 測試滑動操作
   - 測試表單輸入

3. **驗證佈局調整**
   - 驗證導航欄適配
   - 驗證 Agent 卡片網格調整
   - 驗證模態視窗大小適當

**預期結果**:

- ✅ 平板佈局良好
- ✅ 觸控操作順暢
- ✅ 文字大小適中

---

### TC-028: 手機裝置測試

**目標**: 驗證手機裝置上的使用體驗

**測試步驟**:

1. **使用 Chrome DevTools 模擬**
   - 選擇 iPhone 12 Pro (390x844)

2. **測試垂直佈局**
   - 驗證 Agent 卡片單列顯示
   - 驗證圖表正確縮放
   - 驗證按鈕大小適合觸控

3. **測試表單**
   - 測試創建 Agent 表單
   - 驗證輸入框大小適當
   - 驗證鍵盤不遮擋輸入

4. **測試導航**
   - 驗證導航欄摺疊或適配
   - 驗證狀態指示器清晰可見

**預期結果**:

- ✅ 手機佈局良好
- ✅ 觸控操作友善
- ✅ 可用性良好

---

## 🎨 視覺與 UI 測試

### TC-029: 主題與樣式一致性

**目標**: 驗證整體視覺風格一致性

**測試步驟**:

1. **顏色一致性**
   - 驗證主色調使用一致
   - 驗證狀態顏色語義正確：
     - 綠色：成功、運行中、開盤
     - 紅色：錯誤、停止、收盤
     - 黃色：警告、待命
     - 藍色：資訊、選中

2. **字型一致性**
   - 驗證字型大小階層合理
   - 驗證行高適當
   - 驗證字重使用一致

3. **間距一致性**
   - 驗證元素間距統一
   - 驗證卡片內邊距一致
   - 驗證按鈕大小規範

4. **圓角與陰影**
   - 驗證圓角大小一致
   - 驗證陰影效果統一
   - 驗證懸停效果一致

**預期結果**:

- ✅ 視覺風格統一
- ✅ 符合設計規範
- ✅ 美觀專業

---

### TC-030: 無障礙功能測試

**目標**: 驗證基本的無障礙功能支援

**測試步驟**:

1. **鍵盤導航**
   - 使用 Tab 鍵導航
   - 驗證焦點順序合理
   - 驗證焦點可見性清晰

2. **ARIA 屬性**
   - 使用無障礙工具檢查
   - 驗證重要元素有 aria-label
   - 驗證狀態變更有 aria-live

3. **顏色對比**
   - 使用對比度檢查工具
   - 驗證文字與背景對比度 >= 4.5:1
   - 驗證重要資訊對比度良好

4. **語義化 HTML**
   - 驗證使用適當的 HTML 標籤
   - 驗證按鈕使用 `<button>`
   - 驗證表單使用 `<form>`

**預期結果**:

- ✅ 鍵盤可操作
- ✅ ARIA 屬性完整
- ✅ 對比度符合標準

---

**文檔版本**: 2.0
**最後更新**: 2025-10-11
**新增測試案例**: TC-006 ~ TC-030（共 25 個新案例）
