# Agent 重構 - Milestone & Checklist 追蹤表

**項目開始日期：** 2025-10-30
**預計完成日期：** 2025-11-13（13-18 小時，預計 2-3 天）
**狀態：** 🔵 未開始

---

## 📊 項目概覽

| 項目 | 詳情 |
|------|------|
| **目標** | 將系統從 3 模式簡化為 2 模式，實現動態工具配置和記憶體深度整合 |
| **範圍** | 後端架構重構、數據遷移、前端調整 |
| **風險等級** | 🔴 高（破壞性更新） |
| **評估工時** | 13-18 小時 |
| **團隊** | - |

---

## 🎯 Milestone 總覽

```
Phase 1 (移除 OBSERVATION)
  ├─ 2-3 小時
  ├─ 依賴：無
  └─ 產出：枚舉修改、數據遷移

Phase 2 (動態工具配置)
  ├─ 4-6 小時
  ├─ 依賴：Phase 1 ✓
  └─ 產出：ToolConfig 類、初始化邏輯

Phase 3 (記憶體整合)
  ├─ 3-4 小時
  ├─ 依賴：Phase 2 ✓
  └─ 產出：記憶體工作流程

Phase 4 (測試和文檔)
  ├─ 4-5 小時
  ├─ 依賴：Phase 1-3 ✓
  └─ 產出：測試用例、更新文檔
```

---

## 📌 Phase 1：移除 OBSERVATION 並重構枚舉

**時間：** 2-3 小時 | **狀態：** ⬜ 未開始

### 1.1 修改 `common/enums.py`

- [ ] **準備階段**
  - [ ] 備份現有文件
  - [ ] 建立特性分支 `feature/refactor-agent-modes`
  - [ ] 同步團隊

- [ ] **代碼修改**
  - [ ] 移除 `OBSERVATION` 枚舉值
  - [ ] 保留 `TRADING` 和 `REBALANCING`
  - [ ] 更新 docstring，移除 OBSERVATION 說明
  - [ ] 無需修改其他枚舉

- [ ] **驗證**
  - [ ] 語法檢查無誤
  - [ ] 導入路徑仍有效
  - [ ] 無廢棄的常量引用

**完成標準：**
- ✅ 只有 2 個模式
- ✅ Docstring 清晰
- ✅ 代碼審查通過

---

### 1.2 更新 `database/models.py`

- [ ] **準備階段**
  - [ ] 檢查 Agent model 的 current_mode 字段
  - [ ] 確認是否有 OBSERVATION 的默認值

- [ ] **代碼修改**
  - [ ] 修改 `current_mode` 默認值為 `TRADING`（如有）
  - [ ] 移除任何涉及 OBSERVATION 的驗證邏輯
  - [ ] 更新字段 docstring

- [ ] **驗證**
  - [ ] ORM 層仍能正常工作
  - [ ] 數據庫約束檢查
  - [ ] 沒有遺漏的 OBSERVATION 引用

**完成標準：**
- ✅ 模型定義清晰
- ✅ 無 OBSERVATION 相關邏輯
- ✅ 與枚舉保持一致

---

### 1.3 數據庫遷移

- [ ] **準備階段**
  - [ ] 全量備份生產數據庫
  - [ ] 驗證備份可恢復
  - [ ] 在測試環境測試遷移腳本

- [ ] **數據遷移**
  - [ ] 運行遷移 SQL：`UPDATE agent_sessions SET mode = 'TRADING' WHERE mode = 'OBSERVATION'`
  - [ ] 驗證遷移結果：`SELECT COUNT(*) FROM agent_sessions WHERE mode = 'OBSERVATION'` (應為 0)
  - [ ] 驗證 TRADING 模式的 session 數量
  - [ ] 驗證數據完整性（checksum）

- [ ] **回滾準備**
  - [ ] 記錄遷移前的數據快照
  - [ ] 準備回滾腳本（如需要）
  - [ ] 文檔化遷移步驟

**完成標準：**
- ✅ 所有 OBSERVATION session 已遷移
- ✅ 無數據丟失
- ✅ 數據檢查通過

---

### 1.4 相關代碼掃描

- [ ] **後端代碼掃描**
  - [ ] 檢查 `src/trading/` 中的 OBSERVATION 引用
  - [ ] 檢查 `src/service/` 中的 OBSERVATION 引用
  - [ ] 檢查 `src/api/` 中的 OBSERVATION 引用
  - [ ] 檢查所有 test 文件中的 OBSERVATION 引用
  - [ ] 檢查配置文件和常數定義

- [ ] **前端代碼掃描**
  - [ ] 檢查 UI 中的 OBSERVATION 按鈕/選項
  - [ ] 檢查 API 調用中的 OBSERVATION 模式
  - [ ] 檢查文檔和幫助文本

- [ ] **修復發現的引用**
  - [ ] 移除相關的條件判斷
  - [ ] 移除相關的 UI 元素
  - [ ] 更新文檔

**完成標準：**
- ✅ `grep -r "OBSERVATION" src/` 無結果
- ✅ `grep -r "observation" src/` 除註釋外無結果
- ✅ 前端無 OBSERVATION 相關代碼

---

### Phase 1 驗收標準

- ✅ `common/enums.py` 只包含 TRADING 和 REBALANCING
- ✅ 數據庫中無 OBSERVATION mode 的 session
- ✅ 所有代碼引用已清理
- ✅ 測試套件運行通過（無破壞）
- ✅ 文檔更新完成

---

## 📌 Phase 2：動態工具配置架構

**時間：** 4-6 小時 | **狀態：** ⬜ 未開始 | **依賴：** Phase 1 ✓

### 2.1 新建 `src/trading/tool_config.py`

- [ ] **設計階段**
  - [ ] 確認 ToolRequirements dataclass 的所有字段
  - [ ] 確認 ToolConfig 類的邏輯
  - [ ] 確認工具映射關係

- [ ] **代碼實現**
  - [ ] 創建 `ToolRequirements` dataclass
    - [ ] 包含 OpenAI 工具配置
    - [ ] 包含交易工具配置
    - [ ] 包含 Sub-agents 配置
    - [ ] 包含 MCP 配置
  - [ ] 創建 `ToolConfig` 類
    - [ ] 實現 `get_requirements(mode: AgentMode)` 方法
    - [ ] TRADING 模式：完整工具集
    - [ ] REBALANCING 模式：簡化工具集
  - [ ] 添加類型提示和 docstring

- [ ] **驗證**
  - [ ] 單元測試：TRADING 配置
  - [ ] 單元測試：REBALANCING 配置
  - [ ] 配置值無誤
  - [ ] 無遺漏的字段

**完成標準：**
- ✅ 文件存在且語法正確
- ✅ 兩種模式配置清晰
- ✅ 單元測試通過率 100%

---

### 2.2 修改 `src/trading/trading_agent.py`

- [ ] **準備階段**
  - [ ] 備份原始文件
  - [ ] 分析現有初始化邏輯
  - [ ] 標識所有工具初始化點

- [ ] **修改 `initialize()` 方法**
  - [ ] 添加 `mode: AgentMode | None` 參數
  - [ ] 添加模式確定邏輯
  - [ ] 獲取 ToolConfig 配置
  - [ ] 修改 MCP 初始化邏輯
    - [ ] 根據 `include_memory_mcp` 條件加載
    - [ ] 根據 `include_casual_market_mcp` 條件加載
    - [ ] 根據 `include_tavily_mcp` 條件加載
  - [ ] 修改 OpenAI 工具初始化邏輯
    - [ ] 根據 `include_web_search` 條件加載
    - [ ] 根據 `include_code_interpreter` 條件加載
  - [ ] 修改交易工具初始化邏輯
    - [ ] 根據 `include_buy_sell_tools` 條件加載
    - [ ] 根據 `include_portfolio_tools` 條件加載
  - [ ] 修改 Sub-agents 加載邏輯
    - [ ] 根據各 agent 的 flag 條件加載

- [ ] **添加日誌記錄**
  - [ ] 記錄初始化開始
  - [ ] 記錄選中的模式
  - [ ] 記錄加載的工具數量
  - [ ] 記錄初始化完成

- [ ] **驗證**
  - [ ] 代碼語法無誤
  - [ ] 邏輯流程清晰
  - [ ] 無遺漏的參數傳遞

**完成標準：**
- ✅ `initialize()` 方法支持模式參數
- ✅ 工具根據模式動態加載
- ✅ 日誌清晰可追蹤

---

### 2.3 修改相關初始化方法

- [ ] **修改 `_setup_mcp_servers(tool_requirements)`**
  - [ ] 接收 ToolRequirements 參數
  - [ ] 根據 flags 條件初始化
  - [ ] 記錄加載的 MCP 伺服器

- [ ] **修改 `_setup_openai_tools(tool_requirements)`**
  - [ ] 接收 ToolRequirements 參數
  - [ ] 根據 flags 條件構建工具列表
  - [ ] 記錄加載的 OpenAI 工具

- [ ] **修改 `_setup_trading_tools(tool_requirements)`**
  - [ ] 接收 ToolRequirements 參數
  - [ ] 根據 flags 條件構建工具列表
  - [ ] 買/賣工具只在 TRADING 模式加載
  - [ ] 投資組合工具在兩種模式都加載

- [ ] **修改 `_load_subagents_as_tools(tool_requirements)`**
  - [ ] 接收 ToolRequirements 參數
  - [ ] 根據 flags 條件加載 Sub-agents
  - [ ] REBALANCING 只加載 Technical + Risk agents

**完成標準：**
- ✅ 所有初始化方法支持工具配置
- ✅ 工具按需動態加載
- ✅ 無工具重複加載

---

### 2.4 集成測試

- [ ] **TRADING 模式測試**
  - [ ] 驗證 WebSearch 加載
  - [ ] 驗證 CodeInterpreter 加載
  - [ ] 驗證買賣工具加載
  - [ ] 驗證 4 個 Sub-agents 加載
  - [ ] 驗證 3 個 MCP 伺服器加載

- [ ] **REBALANCING 模式測試**
  - [ ] 驗證 WebSearch 未加載
  - [ ] 驗證 CodeInterpreter 加載
  - [ ] 驗證買賣工具未加載
  - [ ] 驗證 2 個 Sub-agents 加載（Tech + Risk）
  - [ ] 驗證 2 個 MCP 伺服器加載（無 Tavily）

- [ ] **性能測試**
  - [ ] 測量 TRADING 初始化時間
  - [ ] 測量 REBALANCING 初始化時間
  - [ ] 確認 REBALANCING 初始化時間 < TRADING

**完成標準：**
- ✅ TRADING 模式初始化成功
- ✅ REBALANCING 模式初始化成功
- ✅ 工具加載符合預期配置

---

### Phase 2 驗收標準

- ✅ `tool_config.py` 存在且配置清晰
- ✅ `trading_agent.py` 支持動態工具加載
- ✅ 兩種模式的初始化都能成功
- ✅ 工具加載符合預期
- ✅ 集成測試通過率 100%
- ✅ 性能符合預期

---

## 📌 Phase 3：記憶體工作流程深度整合

**時間：** 3-4 小時 | **狀態：** ⬜ 未開始 | **依賴：** Phase 2 ✓

### 3.1 分析當前記憶體系統

- [ ] **代碼審查**
  - [ ] 識別現有的 `_load_execution_memory()` 實現
  - [ ] 識別現有的 `_save_execution_memory()` 實現
  - [ ] 檢查 memory_mcp 的使用方式
  - [ ] 檢查 system prompt 生成邏輯

- [ ] **設計工作流程**
  - [ ] 確認執行前階段邏輯
  - [ ] 確認執行中階段邏輯
  - [ ] 確認執行後階段邏輯

**完成標準：**
- ✅ 現有記憶體系統已理解
- ✅ 集成點已識別

---

### 3.2 修改 `run()` 方法

- [ ] **添加執行前階段**
  - [ ] 調用 `_load_execution_memory()`
  - [ ] 融入到 system prompt（調用 `_build_instructions()` 時傳遞）
  - [ ] 記錄加載的記憶數量

- [ ] **確保執行階段邏輯**
  - [ ] 執行分析階段
  - [ ] 執行決策階段
  - [ ] 執行交易/調整階段
  - [ ] 收集執行結果

- [ ] **添加執行後階段**
  - [ ] 調用 `_plan_next_steps(result)`
  - [ ] 調用 `_save_execution_memory()`，傳遞：
    - [ ] analysis 結果
    - [ ] decision 結果
    - [ ] execution 結果
    - [ ] 計劃的下一步

**完成標準：**
- ✅ `run()` 方法支持記憶體工作流程
- ✅ 記憶體循環完整

---

### 3.3 實現輔助方法

- [ ] **實現 `_load_execution_memory()`**
  - [ ] 從 memory_mcp 查詢最近的執行記錄
  - [ ] 構建記憶體上下文
  - [ ] 返回結構化的記憶體對象

- [ ] **實現 `_save_execution_memory()`**
  - [ ] 記錄分析結果
  - [ ] 記錄決策理由
  - [ ] 記錄交易/調整結果
  - [ ] 存入 memory_mcp

- [ ] **實現 `_plan_next_steps()`**
  - [ ] 分析當前執行結果
  - [ ] 識別下一步行動
  - [ ] 返回計劃列表

- [ ] **修改 `_build_instructions()`**
  - [ ] 支持 memory 參數
  - [ ] 將記憶融入 system prompt
  - [ ] 融入格式：過往決策、進場條件、失敗原因

**完成標準：**
- ✅ 記憶體加載和保存邏輯完整
- ✅ 記憶體融入 system prompt
- ✅ 下一步規劃邏輯清晰

---

### 3.4 集成測試

- [ ] **記憶體工作流程測試**
  - [ ] 測試執行前記憶體加載
  - [ ] 測試執行中記憶體記錄
  - [ ] 測試執行後記憶體保存
  - [ ] 測試下一步規劃

- [ ] **記憶體一致性測試**
  - [ ] 驗證記憶體完整性
  - [ ] 驗證記憶體無丟失
  - [ ] 驗證記憶體按時間順序存儲

- [ ] **記憶體融入測試**
  - [ ] 驗證記憶體融入 system prompt
  - [ ] 驗證 Agent 能基於記憶體做決策
  - [ ] 驗證記憶體對執行的影響

**完成標準：**
- ✅ 記憶體工作流程完整
- ✅ 記憶體融入成功
- ✅ 集成測試通過率 100%

---

### Phase 3 驗收標準

- ✅ `_load_execution_memory()` 實現完整
- ✅ `_save_execution_memory()` 實現完整
- ✅ 記憶體融入 system prompt
- ✅ 記憶體工作流程測試通過
- ✅ Agent 能基於記憶體做決策

---

## 📌 Phase 4：測試和文檔

**時間：** 4-5 小時 | **狀態：** ⬜ 未開始 | **依賴：** Phase 1-3 ✓

### 4.1 單元測試

- [ ] **工具配置測試**
  - [ ] `test_tool_config_trading_mode()` - 驗證 TRADING 配置
  - [ ] `test_tool_config_rebalancing_mode()` - 驗證 REBALANCING 配置
  - [ ] `test_tool_requirements_dataclass()` - 驗證數據類完整性

- [ ] **初始化邏輯測試**
  - [ ] `test_agent_initialize_trading_mode()` - 驗證 TRADING 初始化
  - [ ] `test_agent_initialize_rebalancing_mode()` - 驗證 REBALANCING 初始化
  - [ ] `test_agent_initialize_default_mode()` - 驗證默認模式
  - [ ] `test_agent_initialize_idempotent()` - 驗證冪等性

- [ ] **記憶體方法測試**
  - [ ] `test_load_execution_memory()` - 驗證記憶體加載
  - [ ] `test_save_execution_memory()` - 驗證記憶體保存
  - [ ] `test_plan_next_steps()` - 驗證下一步規劃

**完成標準：**
- ✅ 所有單元測試通過
- ✅ 代碼覆蓋率 > 85%

---

### 4.2 集成測試

- [ ] **TRADING 模式完整流程測試**
  - [ ] `test_e2e_trading_complete_flow()` - 從初始化到執行
  - [ ] `test_trading_mode_uses_correct_tools()`
  - [ ] `test_trading_mode_with_memory_integration()`

- [ ] **REBALANCING 模式完整流程測試**
  - [ ] `test_e2e_rebalancing_complete_flow()` - 從初始化到執行
  - [ ] `test_rebalancing_mode_uses_correct_tools()`
  - [ ] `test_rebalancing_mode_with_memory_integration()`

- [ ] **模式切換測試**
  - [ ] `test_switch_trading_to_rebalancing()`
  - [ ] `test_switch_rebalancing_to_trading()`

- [ ] **記憶體集成測試**
  - [ ] `test_memory_persists_across_runs()`
  - [ ] `test_memory_influences_decision()`
  - [ ] `test_next_steps_planning()`

**完成標準：**
- ✅ 所有集成測試通過
- ✅ 代碼覆蓋率 > 80%

---

### 4.3 迴歸測試

- [ ] **現有功能測試**
  - [ ] 運行整個測試套件
  - [ ] 確認無新的失敗
  - [ ] 確認性能無退步

- [ ] **邊界情況測試**
  - [ ] `test_agent_with_no_memory()` - 首次執行
  - [ ] `test_agent_with_corrupted_memory()` - 記憶體損壞
  - [ ] `test_agent_with_empty_portfolio()` - 空投資組合
  - [ ] `test_agent_with_network_failure()` - 網絡失敗

**完成標準：**
- ✅ 迴歸測試通過率 100%
- ✅ 邊界情況處理正確

---

### 4.4 文檔更新

- [ ] **API 文檔**
  - [ ] 更新 AgentMode 的文檔
  - [ ] 文檔化 ToolConfig 類
  - [ ] 文檔化新增的 initialize 參數
  - [ ] 文檔化記憶體工作流程

- [ ] **實施指南**
  - [ ] 更新遷移步驟
  - [ ] 添加故障排除指南
  - [ ] 添加性能優化建議

- [ ] **用戶文檔**
  - [ ] 說明 2 種模式的區別
  - [ ] 說明何時使用哪種模式
  - [ ] 更新前端用戶指南

- [ ] **開發文檔**
  - [ ] 記錄架構變更
  - [ ] 記錄破壞性變更
  - [ ] 記錄遷移路徑

**完成標準：**
- ✅ 所有文檔更新完成
- ✅ 文檔準確且清晰

---

### 4.5 前端更新

- [ ] **移除 OBSERVATION**
  - [ ] 移除 OBSERVATION 按鈕
  - [ ] 移除 OBSERVATION 選項
  - [ ] 移除相關的 UI 條件判斷

- [ ] **更新模式選擇**
  - [ ] 更新下拉菜單為 TRADING 和 REBALANCING
  - [ ] 更新模式說明和幫助文本
  - [ ] 驗證 UI 響應式設計

- [ ] **更新 API 調用**
  - [ ] 更新 API 端點調用
  - [ ] 移除 OBSERVATION 相關的邏輯
  - [ ] 驗證 API 響應處理

**完成標準：**
- ✅ 前端無 OBSERVATION 相關代碼
- ✅ 前端完整性測試通過

---

### Phase 4 驗收標準

- ✅ 單元測試覆蓋率 > 85%
- ✅ 集成測試全部通過
- ✅ 迴歸測試全部通過
- ✅ 所有文檔更新完成
- ✅ 前端調整完成

---

## 🎬 收尾和部署

### 部署前檢查

- [ ] **代碼審查**
  - [ ] 至少 2 人審查
  - [ ] 架構審查通過
  - [ ] 代碼質量檢查通過

- [ ] **性能驗證**
  - [ ] 性能基準測試
  - [ ] 內存使用率檢查
  - [ ] 初始化時間檢查

- [ ] **安全檢查**
  - [ ] 安全掃描
  - [ ] 依賴項檢查
  - [ ] 權限驗證

- [ ] **備份準備**
  - [ ] 數據庫備份確認
  - [ ] 回滾計劃確認
  - [ ] 通知清單準備

**完成標準：**
- ✅ 代碼審查通過
- ✅ 性能驗證通過
- ✅ 安全檢查通過

---

### 部署步驟

- [ ] **前期準備（部署前 1 小時）**
  - [ ] 通知相關團隊
  - [ ] 確認備份完整
  - [ ] 準備回滾方案
  - [ ] 確認部署環境

- [ ] **部署執行**
  - [ ] 部署後端代碼
  - [ ] 運行數據庫遷移
  - [ ] 部署前端代碼
  - [ ] 驗證系統啟動

- [ ] **部署驗證（部署後 30 分鐘）**
  - [ ] 檢查系統日誌
  - [ ] 運行冒煙測試
  - [ ] 驗證兩種模式都能執行
  - [ ] 驗證記憶體工作流程

- [ ] **後期監控（部署後 24 小時）**
  - [ ] 監控系統性能
  - [ ] 監控錯誤率
  - [ ] 收集用戶反饋
  - [ ] 準備應急方案

**完成標準：**
- ✅ 系統部署成功
- ✅ 冒煙測試通過
- ✅ 無重大錯誤

---

## 📊 進度追蹤

### 每日進度記錄

**Day 1: Phase 1**
- [ ] 2025-11-xx：完成 1.1-1.4
- [ ] 驗收標準達成：□ 是 □ 否

**Day 2: Phase 2**
- [ ] 2025-11-xx：完成 2.1-2.4
- [ ] 驗收標準達成：□ 是 □ 否

**Day 2.5: Phase 3**
- [ ] 2025-11-xx：完成 3.1-3.4
- [ ] 驗收標準達成：□ 是 □ 否

**Day 3: Phase 4 + 部署**
- [ ] 2025-11-xx：完成 4.1-4.5
- [ ] 驗收標準達成：□ 是 □ 否
- [ ] 2025-11-xx：部署前檢查完成
- [ ] 2025-11-xx：部署執行完成

---

## 🚨 風險監控

### 高風險項

| 風險 | 影響 | 檢測方式 | 應對措施 |
|------|------|---------|---------|
| 數據遷移失敗 | 🔴 高 | 驗證 SQL 結果 | 恢復備份 |
| 工具加載失敗 | 🔴 高 | 運行初始化測試 | 調試配置 |
| 記憶體集成問題 | 🟡 中 | 功能測試 | 調整邏輯 |
| 前端不兼容 | 🟡 中 | 集成測試 | 調整 API |

### 風險追蹤表

- [ ] **數據遷移**
  - [ ] 狀態：✅ 完成 / ⚠️ 進行中 / ❌ 失敗
  - [ ] 備註：

- [ ] **Phase 1 完成**
  - [ ] 狀態：✅ 完成 / ⚠️ 進行中 / ❌ 失敗
  - [ ] 備註：

- [ ] **Phase 2 完成**
  - [ ] 狀態：✅ 完成 / ⚠️ 進行中 / ❌ 失敗
  - [ ] 備註：

- [ ] **Phase 3 完成**
  - [ ] 狀態：✅ 完成 / ⚠️ 進行中 / ❌ 失敗
  - [ ] 備註：

- [ ] **Phase 4 完成**
  - [ ] 狀態：✅ 完成 / ⚠️ 進行中 / ❌ 失敗
  - [ ] 備註：

---

## 📝 簽核

| 角色 | 姓名 | 簽名 | 日期 |
|------|------|------|------|
| PM | - | - | - |
| Tech Lead | - | - | - |
| QA Lead | - | - | - |
| DevOps | - | - | - |

---

## 📞 聯繫方式

- **項目經理**：[聯繫方式]
- **技術主管**：[聯繫方式]
- **QA 主管**：[聯繫方式]
- **緊急聯繫**：[聯繫方式]

---

**文檔版本：** 1.0
**最後更新：** 2025-10-30
**狀態：** 🔵 未開始
