# Agent 重構實作指南

## 核心架構變更

### 當前架構（V1）
```
┌─────────────────────────────────────────────────────┐
│                    TradingAgent                      │
├─────────────────────────────────────────────────────┤
│ 固定初始化（所有工具全量加載）                          │
│ ├─ 3 個 MCP Servers (memory + market + tavily)      │
│ ├─ OpenAI Tools (web_search + code_interpreter)    │
│ ├─ Trading Tools (buy + sell + portfolio)          │
│ └─ 4 個 Sub-agents (tech + fund + sentiment + risk) │
│                                                      │
│ 3 種執行模式（高重複）                               │
│ ├─ TRADING (完整分析 + 交易)                        │
│ ├─ REBALANCING (投資組合分析 + 調整)                │
│ └─ OBSERVATION (分析 + 無交易)                      │
│                                                      │
│ 記憶體使用（基礎）                                   │
│ └─ 提示語中提及 memory_mcp                          │
└─────────────────────────────────────────────────────┘
```

### 重構後架構（V2）
```
┌─────────────────────────────────────────────────────────────────┐
│                   TradingAgent (模式感知)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 構造函數                                                         │
│   ↓                                                             │
│ initialize(mode: AgentMode)  ← 動態初始化（按需加載）           │
│   ├─ _setup_mcp_servers(mode)       ← 根據模式選擇 MCP        │
│   ├─ _setup_openai_tools()          ← 根據模式選擇工具         │
│   ├─ _setup_trading_tools(mode)     ← 根據模式配置交易工具      │
│   ├─ _load_subagents_as_tools()     ← 根據模式載入 Sub-agents  │
│   └─ build_instructions(mode)       ← 根據模式構建指令         │
│                                                                  │
│ 執行流程                                                         │
│   ↓                                                             │
│ run(mode: AgentMode)                                            │
│   ├─ _build_memory_context(mode)    ← 查詢上一輪記憶          │
│   ├─ _build_task_prompt(mode)       ← 構建模式特定提示        │
│   └─ Runner.run(agent, task_prompt) ← 執行 Agent              │
│                                                                  │
│ 記憶體集成（深度）                                              │
│ ├─ 上一輪執行記憶融入指令                                      │
│ ├─ 決策過程詳細記錄到知識庫                                    │
│ └─ 下一步行動規劃存入知識庫（閉環）                           │
│                                                                  │
│ 2 種執行模式（明確分工）                                        │
│ ├─ TRADING:      完整分析 + 新標的搜尋 + 交易執行 + 記憶       │
│ └─ REBALANCING:  現有持股分析 + 被動調整 + 記憶               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 工具配置對比

### TRADING 模式（完整）
```
┌─ MCP Servers ─────────────────────┐
│ ✅ memory_mcp      - 知識庫        │
│ ✅ casual_market_mcp - 市場數據    │
│ ✅ tavily_mcp      - 網路搜尋      │
└────────────────────────────────────┘
        ↓
┌─ OpenAI Tools ────────────────────┐
│ ✅ web_search        - 搜尋最新信息 │
│ ✅ code_interpreter  - 數據分析    │
└────────────────────────────────────┘
        ↓
┌─ Trading Tools ───────────────────┐
│ ✅ buy_tool              - 買進    │
│ ✅ sell_tool             - 賣出    │
│ ✅ portfolio_tool        - 管理    │
│ ✅ record_trade_tool     - 記錄    │
└────────────────────────────────────┘
        ↓
┌─ Sub-agents (4/4) ────────────────┐
│ ✅ technical_analyst   - 技術分析  │
│ ✅ fundamental_analyst - 基本面    │
│ ✅ sentiment_analyst   - 情緒分析  │
│ ✅ risk_analyst        - 風險評估  │
└────────────────────────────────────┘

結果：完整市場分析 + 新機會搜尋 + 主動交易決策
```

### REBALANCING 模式（優化）
```
┌─ MCP Servers ──────────────────────┐
│ ✅ memory_mcp           - 知識庫    │
│ ✅ casual_market_mcp    - 市場數據  │
│ ❌ tavily_mcp           - 不需要    │
└─────────────────────────────────────┘
        ↓
┌─ OpenAI Tools ───────────────────────┐
│ ❌ web_search          - 不需要      │
│ ✅ code_interpreter    - 數據分析   │
└─────────────────────────────────────────┘
        ↓
┌─ Trading Tools ───────────────────────┐
│ ❌ buy_tool              - 不需要    │
│ ❌ sell_tool             - 不需要    │
│ ✅ portfolio_tool        - 管理      │
│ ✅ record_trade_tool     - 記錄      │
└─────────────────────────────────────────┘
        ↓
┌─ Sub-agents (2/4) ────────────────────┐
│ ✅ technical_analyst    - 技術分析    │
│ ❌ fundamental_analyst  - 不需要      │
│ ❌ sentiment_analyst    - 不需要      │
│ ✅ risk_analyst         - 風險評估    │
└─────────────────────────────────────────┘

結果：現有持股分析 + 被動調整 + 風險管理
```

---

## 記憶體工作流程（有機循環）

### TRADING 模式的記憶循環
```
┌───────────────────────────────────────────────────────────┐
│ 上一輪 TRADING 執行完成                                   │
│ (存在記憶庫中的知識)                                      │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ 🔄 本輪 TRADING 開始                                     │
│                                                           │
│ Step 1: 查詢記憶庫                                       │
│ ├─ 上一次的分析結果                                      │
│ ├─ 識別的新標的和進場條件                                │
│ ├─ 失敗經驗和教訓                                        │
│ └─ 監控條件是否觸發                                      │
│    ↓                                                     │
│ Step 2: 市場分析                                        │
│ ├─ 調用 web_search 查詢最新新聞                         │
│ ├─ 調用 technical_analyst 進行技術分析                  │
│ ├─ 調用 fundamental_analyst 進行基本面分析              │
│ ├─ 調用 sentiment_analyst 評估市場情緒                  │
│ └─ 調用 risk_analyst 進行風險評估                       │
│    ↓                                                     │
│ Step 3: 新機會識別                                      │
│ ├─ 對比記憶庫中的過往分析                                │
│ ├─ 識別符合策略的新標的                                  │
│ └─ 評估進場時機                                          │
│    ↓                                                     │
│ Step 4: 交易決策和執行                                  │
│ ├─ 決策是否交易                                          │
│ ├─ 確定買入/賣出數量                                     │
│ └─ 執行交易                                              │
│    ↓                                                     │
│ Step 5: 記錄到記憶庫（關鍵！）                          │
│ ├─ 本次分析的完整過程                                    │
│ ├─ 所有交易決策的理由                                    │
│ ├─ 新標的的進場條件和監控指標                            │
│ ├─ 失敗原因（如有）                                     │
│ └─ 下一輪應執行的動作和觸發條件                          │
│                                                           │
│ ⏭️  下一輪執行時回到 Step 1                             │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### REBALANCING 模式的記憶循環
```
┌──────────────────────────────────────────────────────┐
│ 上一輪 REBALANCING 執行完成                          │
│ (存在記憶庫中的持股分析)                             │
├──────────────────────────────────────────────────────┤
│                                                      │
│ 🔄 本輪 REBALANCING 開始                            │
│                                                      │
│ Step 1: 查詢記憶庫                                  │
│ ├─ 上一次的投資組合配置                             │
│ ├─ 每只持股的風險評級                               │
│ ├─ 上次調整的理由                                   │
│ └─ 設定的調整條件                                   │
│    ↓                                                │
│ Step 2: 現有持股分析                               │
│ ├─ 調用 technical_analyst 分析技術面                │
│ ├─ 調用 risk_analyst 評估風險                       │
│ └─ 對比記憶庫中的過往分析                           │
│    ↓                                                │
│ Step 3: 調整決策                                   │
│ ├─ 識別需要調整的持股                               │
│ ├─ 評估調整是否符合策略                             │
│ └─ 決策具體調整方案                                 │
│    ↓                                                │
│ Step 4: 執行調整                                   │
│ └─ 執行投資組合調整                                 │
│    ↓                                                │
│ Step 5: 記錄到記憶庫（關鍵！）                      │
│ ├─ 調整前後的配置對比                               │
│ ├─ 調整的完整理由                                   │
│ ├─ 每只持股的當前風險評級                           │
│ ├─ 下次調整的觸發條件                               │
│ └─ 需要 TRADING 補充的標的類別                      │
│                                                      │
│ ⏭️  下一輪執行時回到 Step 1                        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 模式特定指令（簡化對比）

### TRADING 模式指令要點
```
🎯 目標：主動發掘機會並執行交易

📋 主要步驟：
1. 📚 查詢記憶庫中的過往分析和失敗經驗
2. 🔍 使用 web_search 搜尋最新市場信息
3. 📊 調用所有 sub-agents 進行全面分析
4. 💡 識別符合策略的新投資機會
5. 📈 決策並執行買賣交易
6. 📝 詳細記錄決策理由到記憶庫
7. 🎯 規劃下一輪應執行的動作

🔧 可用工具：所有工具（完整集合）

⚠️  限制：遵守持股比例、資金限制
```

### REBALANCING 模式指令要點
```
⚖️  目標：優化投資組合和風險管理

📋 主要步驟：
1. 📚 查詢記憶庫中的持股分析記錄
2. 📊 分析現有持股的技術面和風險
3. 🎯 評估是否需要調整
4. 📈 執行必要的投資組合調整
5. 📝 記錄調整理由到記憶庫
6. 🔔 設定下次調整的觸發條件

🔧 可用工具：portfolio、technical、risk（精選工具）

⚠️  限制：不搜尋新標的、聚焦現有持股
```

---

## 實作優先級和步驟

### Week 1: 基礎架構（高優先級）

#### Day 1-2: 準備和遷移（2 天）
```
□ 備份數據庫
  └─ mysqldump casualtrader > backup_$(date +%Y%m%d).sql

□ 創建 tool_config.py
  └─ 定義 ToolRequirements 和 ToolConfig

□ 修改 enums.py
  └─ 移除 OBSERVATION，保留 TRADING + REBALANCING

□ 數據遷移
  ├─ 遷移 session 記錄
  ├─ 更新 agent 默認模式
  └─ 驗證數據完整性

□ 更新所有導入和引用
  └─ 搜尋所有 OBSERVATION 引用並替換
```

#### Day 3-4: 動態初始化（2 天）
```
□ 重構 _setup_mcp_servers()
  ├─ 添加 mode 參數
  ├─ 根據模式選擇 MCP
  └─ 添加日誌記錄

□ 重構 _setup_openai_tools()
  ├─ 根據 tool_requirements 選擇工具
  └─ 添加日誌記錄

□ 重構 _setup_trading_tools()
  ├─ 根據模式選擇交易工具
  └─ 移除 buy/sell 工具選項

□ 修改 _load_subagents_as_tools()
  ├─ 根據 tool_requirements 載入 sub-agents
  └─ 動態構建 mcp_servers 列表

□ 修改 initialize() 方法
  └─ 接受 mode 參數並傳遞
```

#### Day 5: 單元測試（1 天）
```
□ 測試 ToolConfig.get_requirements()
  ├─ TRADING 模式配置
  └─ REBALANCING 模式配置

□ 測試工具初始化
  ├─ MCP servers 正確加載
  ├─ Sub-agents 根據模式加載
  └─ 工具列表正確生成
```

### Week 2: 記憶體整合（高優先級）

#### Day 1-2: 指令構建（2 天）
```
□ 重構 _build_instructions()
  ├─ 添加 mode 參數
  ├─ 添加 memory_context 參數
  ├─ TRADING 特定指令
  └─ REBALANCING 特定指令

□ 新增 _build_memory_context()
  ├─ 查詢上一輪執行記錄
  ├─ 提取關鍵決策點
  └─ 格式化成提示內容

□ 修改 _build_task_prompt()
  ├─ TRADING 模式：完整分析步驟 + 記憶查詢
  └─ REBALANCING 模式：聚焦持股分析 + 記憶查詢

□ 添加記憶規劃指引
  ├─ 強制記錄決策過程
  ├─ 規劃下一步動作
  └─ 設定監控條件
```

#### Day 3-4: 執行流程（2 天）
```
□ 修改 run() 方法
  ├─ 驗證模式有效性
  ├─ 調用 initialize(mode)
  ├─ 調用 _build_task_prompt(mode)
  └─ 等待執行完成

□ 添加執行後處理
  ├─ 驗證記憶庫記錄
  ├─ 記錄執行統計
  └─ 驗證下一步規劃

□ 錯誤處理
  ├─ 記憶庫查詢失敗處理
  ├─ 模式不支持處理
  └─ 降級方案
```

#### Day 5: 集成測試（1 天）
```
□ TRADING 模式完整流程
  ├─ 初始化 + 執行 + 記憶記錄
  └─ 驗證記憶庫內容

□ REBALANCING 模式完整流程
  ├─ 初始化 + 執行 + 記憶記錄
  └─ 驗證記憶庫內容

□ 跨模式測試
  └─ 連續執行兩種模式，驗證記憶共享
```

### Week 3: API 和前端（中優先級）

#### Day 1-2: API 層更新（2 天）
```
□ 更新 agent_execution.py
  ├─ 移除 OBSERVATION 端點或遷移到 TRADING
  ├─ 驗證模式參數
  └─ 更新文檔

□ 更新 agents.py router
  ├─ 移除 OBSERVATION 選項
  ├─ 更新驗證邏輯
  └─ 更新 API 文檔

□ 測試所有 API 端點
  ├─ GET /agents
  ├─ POST /agents/{id}/execute
  └─ GET /sessions/{id}
```

#### Day 3-4: 前端調整（2 天）
```
□ 更新執行模式選擇
  ├─ 移除 OBSERVATION 按鈕
  ├─ 只保留 TRADING 和 REBALANCING
  └─ 更新 UI/UX

□ 更新 API 調用
  ├─ 移除 OBSERVATION 相關調用
  ├─ 更新模式驗證
  └─ 測試所有場景

□ 更新幫助文本和文檔
  └─ 說明兩種模式的用途
```

#### Day 5: 端到端測試（1 天）
```
□ 前端 + API + 後端 集成測試
  ├─ TRADING 完整流程
  └─ REBALANCING 完整流程

□ 瀏覽器兼容性測試
```

### Week 4: 優化和文檔（低優先級）

#### Day 1-2: 性能優化（2 天）
```
□ 分析資源占用
  ├─ MCP 伺服器啟動時間
  ├─ Sub-agent 加載時間
  └─ 記憶庫查詢時間

□ 優化初始化
  ├─ 並行加載不相關組件
  ├─ 緩存配置
  └─ 預熱機制

□ 性能測試
  └─ 對比 V1 和 V2 性能指標
```

#### Day 3-4: 完整文檔（2 天）
```
□ 架構文檔
  ├─ 更新系統設計
  ├─ 新增工具配置章節
  └─ 新增記憶體工作流程章節

□ API 文檔
  ├─ 更新 Swagger/OpenAPI 定義
  ├─ 添加模式選擇說明
  └─ 添加示例請求

□ 操作文檔
  ├─ TRADING 模式使用指南
  └─ REBALANCING 模式使用指南
```

#### Day 5: 最終驗收（1 天）
```
□ 回歸測試
  ├─ 所有單元測試通過
  ├─ 所有集成測試通過
  └─ 性能指標達標

□ 代碼審查
  ├─ 代碼風格一致
  ├─ 文檔完整
  └─ 測試覆蓋率 >80%

□ 發布準備
  ├─ 變更日誌
  ├─ 升級指南
  └─ 已知問題列表
```

---

## 技術要點

### 1. 模式驗證（必須）
```python
# 所有接受 mode 的地方都需要驗證
VALID_MODES = {AgentMode.TRADING, AgentMode.REBALANCING}

if mode not in VALID_MODES:
    raise ValueError(f"Invalid mode: {mode}")
```

### 2. 工具配置的一致性（必須）
```python
# 工具配置和 MCP 配置必須一致
def _validate_tool_mcp_consistency(requirements, mcp_servers):
    if requirements.include_web_search and not tavily_mcp:
        raise ValueError("web_search requires tavily_mcp")
```

### 3. 記憶庫查詢錯誤處理（重要）
```python
# 記憶庫查詢失敗應該降級處理，不中斷執行
try:
    memory_context = await self._build_memory_context(mode)
except Exception as e:
    logger.warning(f"Failed to build memory context: {e}")
    memory_context = ""  # 降級：使用空上下文
```

### 4. 日誌記錄（重要）
```python
# 每個工具加載都要記錄
logger.info(f"✅ {tool_name} loaded for {mode.value} mode")
logger.info(f"❌ {tool_name} skipped for {mode.value} mode")
```

---

## 關鍵决策點

### 決策 1：舊的 OBSERVATION 記錄如何處理？
**選項 A**：遷移到 TRADING（推薦）
```sql
UPDATE agent_sessions SET mode = 'TRADING'
WHERE mode = 'OBSERVATION';
```

**選項 B**：保留歷史記錄（較保守）
```sql
ALTER TABLE agent_sessions ADD mode_v2 VARCHAR(50);
UPDATE agent_sessions SET mode_v2 = 'TRADING'
WHERE mode = 'OBSERVATION';
```

**推薦**：選項 A（更簡潔，清晰遷移路徑）

### 決策 2：記憶庫查詢失敗時如何處理？
**選項 A**：中斷執行（安全）
**選項 B**：降級執行（用戶體驗好）

**推薦**：選項 B（添加詳細日誌供調試）

### 決策 3：Sub-agent 加載失敗時如何處理？
**選項 A**：中斷 Agent 初始化（安全）
**選項 B**：跳過該 agent，繼續執行（容錯）

**推薦**：選項 B（REBALANCING 不需要所有 agent，應該容錯）

---

## 成功標誌

✅ **架構改進**
- 代碼重複率從 40% 降至 <15%
- MCP 伺服器按需加載（REBALANCING 節省 1 個）
- Sub-agent 按需加載（REBALANCING 節省 2 個）

✅ **功能完善**
- 記憶庫查詢融入初始化
- 決策過程完整記錄
- 下一步動作規劃存入記憶庫
- 形成有機循環

✅ **測試覆蓋**
- 單元測試 > 30 個
- 集成測試 > 15 個
- 覆蓋率 > 85%

✅ **文檔完整**
- API 文檔更新
- 架構文檔更新
- 用戶指南完善

---

## 常見問題

**Q: REBALANCING 模式是否還能執行交易？**
A: 是的，portfolio_tool 中包含買/賣功能，但工具配置中不暴露買/賣工具給 Agent，
   Agent 只能通過 portfolio_tool 進行調整。

**Q: 如何從舊版本升級？**
A:
1. 備份數據庫
2. 運行遷移腳本
3. 更新前端代碼
4. 測試所有功能

**Q: TRADING 模式的性能會下降嗎？**
A: 不會，工具配置相同，只是代碼組織更清晰。

**Q: 舊的 OBSERVATION 記錄會丟失嗎？**
A: 不會，所有 session 記錄都遷移到 TRADING 模式。
