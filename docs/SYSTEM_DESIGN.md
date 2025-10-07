# CasualTrader AI 股票交易模擬器 - 系統設計規範

**版本**: 4.0
**日期**: 2025-10-06
**專案**: CasualTrader AI Trading Simulator

---

## 📚 文檔結構說明

本專案採用重構後的文檔結構，為了消除內容重複和提高維護效率：

### **文檔總覽**

- `README.md` - 文檔結構總覽、閱讀指南和維護說明

### **主要規範文件**

- 本文檔 - 系統設計規範與高層架構

### **詳細實作規格**

- `AGENT_IMPLEMENTATION.md` - Agent 系統詳細實作規格
- `API_IMPLEMENTATION.md` - 後端 API 詳細實作規格
- `FRONTEND_IMPLEMENTATION.md` - 前端介面詳細實作規格
- `DEPLOYMENT_GUIDE.md` - 部署和配置詳細指南

### **補充文檔**

- `API_DEPENDENCIES.md` - API 套件依賴清單和配置指南

### **文檔重構優勢**

✅ **消除重複** - 移除了原本多個文檔間的內容重複
✅ **職責分離** - 每個文檔有明確的範圍和職責
✅ **易於維護** - 更新時不需要同步多個文檔
✅ **便於查找** - 根據需求直接找到對應文檔
✅ **閱讀指南** - 提供針對不同角色的文檔閱讀建議

---

## 📋 專案概述

### 產品願景

打造一個即時、可視化的 AI 股票交易模擬器，使用 OpenAI Agent SDK 構建智能交易代理人，支援多種 AI 模型同時進行股票交易，提供觀戰、分析和學習的平台。

### 核心價值

- **AI 競技場**：多 AI 模型交易策略競賽
- **即時觀戰**：實時觀察 AI 決策和執行過程
- **教育價值**：通過 AI 行為學習投資策略
- **策略分析**：比較不同投資方法的效果
- **智能決策**：AI 代理人基於市場數據和研究分析進行自主交易
- **策略持久化**：投資策略和決策過程完整記錄與追蹤
- **多模型支援**：支援多種主流 AI 模型（GPT-4o, Claude Sonnet 4.5, Gemini 2.5 Pro 等）進行策略競賽與比較

### 技術架構優勢

1. **關注點分離**: 數據獲取(MCP) vs AI 決策(Agent)
2. **標準化協議**: MCP 協議確保擴展性和維護性
3. **成本最優化**: 無需維護複雜的爬蟲和數據處理邏輯
4. **即時性保證**: 所有數據來自 MCP 即時查詢
5. **易於測試**: Mock MCP 回應進行單元測試

---

## 🏗️ 系統架構

### 架構圖

```text
┌─────────────────────────────────────────────────────────┐
│                前端層 (Frontend - Vite + Svelte)           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Svelte      │ │ Chart.js    │ │ WebSocket Client    │  │
│  │ Components  │ │ 圖表視覺化   │ │ 即時通信            │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Vite        │ │ Tailwind    │ │ Svelte Store        │  │
│  │ Build Tool  │ │ CSS         │ │ 狀態管理            │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │ HTTP/WS
┌─────────────────────────────────────────────────────────┐
│                  Web 服務層 (Backend)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │  FastAPI    │ │ WebSocket   │ │ 靜態檔案服務         │  │
│  │  REST API   │ │ 即時推送    │ │ Static Files        │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │ 內部調用
┌─────────────────────────────────────────────────────────┐
│         AI 代理人層 (Agent as Tool 架構)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ OpenAI      │ │ Trading     │ │ Agent Tool          │  │
│  │ Agent SDK   │ │ Agent       │ │ Manager             │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Fundamental │ │ Technical   │ │ Risk Assessment     │  │
│  │ Agent Tool  │ │ Agent Tool  │ │ Agent Tool          │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Sentiment   │ │ SQLite      │ │ WebSocket           │  │
│  │ Agent Tool  │ │ Session     │ │ Notification        │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │ 工具調用
┌─────────────────────────────────────────────────────────┐
│                  工具層 (Tools Layer)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ CasualTrader│ │ WebSearch   │ │ CodeInterpreter     │  │
│  │ MCP Server  │ │ Tool        │ │ Tool                │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Trading     │ │ Market      │ │ Portfolio           │  │
│  │ Validation  │ │ Status      │ │ Queries             │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │ 資料存取
┌─────────────────────────────────────────────────────────┐
│              資料層 (SQLite 統一解決方案)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Agent       │ │ Trading     │ │ Strategy &          │  │
│  │ Sessions    │ │ Records     │ │ Decision Logs       │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │
│  │ Cache       │ │ Vector      │ │ Performance         │  │
│  │ Tables      │ │ Embeddings  │ │ Metrics             │  │
│  └─────────────┘ └─────────────┘ └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 技術堆疊

**前端技術**:

- **核心**: Vite + Svelte (現代化前端框架)
- **構建工具**: Vite (快速熱重載和構建)
- **圖表**: Chart.js (即時交易數據視覺化)
- **通信**: WebSocket (即時更新)
- **樣式**: Tailwind CSS + CSS Grid + Flexbox (響應式設計)

**後端技術**:

- **Web 框架**: FastAPI (異步 API + 靜態文件服務)
- **AI SDK**: OpenAI Agent SDK (Agent 管理)
- **資料庫**: SQLite (統一解決方案 - 支援關聯式資料、向量搜尋和快取)
- **即時通信**: WebSocket (狀態推送)
- **快取系統**: SQLite 內建快取表 (無需 Redis)

**AI 與工具層**:

- **AI 模型**: 支援多種主流模型，包括：
  - OpenAI: GPT-4o, GPT-4o-mini, GPT-4-turbo
  - Anthropic: Claude Sonnet 4.5, Claude Opus 4
  - Google: Gemini 2.5 Pro, Gemini 2.0 Flash
  - 其他: DeepSeek, Grok 等
- **模型選擇**: Agent 創建時可選擇模型，執行期間記錄當前使用模型
- **資料來源**: casual-market-mcp (21 個台灣股市專業工具)
- **協議**: Model Context Protocol (MCP)

---

## 🎯 核心功能設計

### 1. AI 代理人系統

**TradingAgent 架構**:

- 基於 **Prompt 驅動** 的智能交易 Agent
- 透過自然語言描述投資偏好和策略調整依據
- 支援多種 AI 模型選擇（GPT-4o, Claude Sonnet 4.5, Gemini 2.5 Pro 等）
- 模型資訊持久化與追蹤（創建時選擇、執行時記錄）

**生命週期管理**:

- 動態創建、配置、啟動/停止 Agent
- 支援自定義投資偏好 (investment_preferences)
- 支援自定義策略調整依據 (strategy_adjustment_criteria)
- 自動調整設定 (auto_adjust triggers)
- SQLite Session 持久化

**策略演化系統**:

- Agent 根據績效和市場條件自主調整策略
- 用戶定義的調整觸發條件 (連續虧損、市場波動、定期檢討)
- 完整的策略變更記錄 (觸發原因、變更內容、Agent 說明)
- 策略變更歷史可查詢與追溯

**工具整合**:

- 專業分析工具 (基本面、技術面、風險評估、市場情緒)
- OpenAI Hosted Tools (WebSearch, CodeInterpreter)
- CasualMarket MCP (21 個台灣股市工具)
- 交易驗證與執行工具

### 2. 數據整合架構

**casual-market-mcp 整合** (21 個專業工具):

- 📊 即時市場數據 (4 tools): 股價、指數、即時統計
- 📈 股票交易數據 (5 tools): 日/月/年交易、月均價、估值比率
- 🏢 公司財務數據 (5 tools): 基本資料、財報、營收、股利
- 💰 市場資金動向 (4 tools): 融資融券、外資持股、ETF 排名
- 📅 重要行事曆 (1 tool): 除權息行事曆
- 🔄 模擬交易 (2 tools): 買入/賣出

### 3. 即時監控系統

**WebSocket 即時推送**:

- Agent 狀態變更 (啟動、執行中、停止、錯誤)
- 交易執行結果 (買入、賣出、成交價格)
- 投資組合更新 (持股變化、現金餘額)
- 策略變更通知 (變更原因、內容摘要)
- 績效指標更新 (報酬率、累積收益)

**視覺化儀表板**:

- 即時績效追蹤 (日報酬率、累積報酬、大盤比較)
- 多 Agent 競技比較 (不同模型、不同策略的績效對比)
- 交易決策時間軸 (買賣記錄、決策原因)
- 投資組合分佈圖 (持股比例、產業分佈)
- 策略變更歷史 (變更時點、觸發原因、效果分析)

---

## 🔄 資料流設計

### 核心資料流

```text
前端請求 → FastAPI → Agent Manager → OpenAI Agent → MCP Tools → 回應
```

### Agent 決策流程

```text
1. 市場數據查詢 (MCP Tools)
2. 策略分析 (AI 推理)
3. 風險評估 (內建邏輯)
4. 交易決策 (Agent 自主)
5. 執行確認 (模擬交易)
6. 結果記錄 (資料庫)
7. 即時推送 (WebSocket)
```

### 狀態管理

**Agent 狀態**:

- 執行狀態 (idle, running, stopped, error)
- 當前策略 (instructions, 最新策略調整)
- 投資組合快照 (持股、現金、總資產)
- 交易歷史 (買賣記錄、成交價格)
- 策略變更歷史 (變更時點、原因、內容)
- 績效指標 (報酬率、最大回撤、勝率)

**系統狀態**:

- 交易時間驗證 (台股交易時間 09:00-13:30)
- 市場數據快取 (MCP 工具查詢結果)
- WebSocket 連線狀態 (已連線、已斷線、重連中)
- 錯誤處理和恢復 (API 錯誤、網路中斷、資料庫鎖定)

---

## 🔒 設計原則

### 1. 關注點分離

- **前端**: 專注於數據展示和用戶交互
- **後端**: 專注於 API 服務和狀態管理
- **Agent 層**: 專注於 AI 決策邏輯
- **工具層**: 專注於數據獲取和驗證

### 2. 擴展性設計

- **模組化架構**: 各層獨立可替換
- **標準化介面**: MCP 協議統一工具介面
- **配置驱動**: 環境變數控制行為
- **插件機制**: 支援新工具和策略擴展

### 3. 可觀測性

- **完整追蹤**: Agent 執行全程記錄
- **即時監控**: WebSocket 推送關鍵事件
- **錯誤處理**: 集中式錯誤管理和恢復
- **性能監控**: API 響應時間和資源使用

### 4. 安全性考量

- **資料隔離**: Agent 間投資組合獨立
- **輸入驗證**: 所有外部輸入嚴格驗證
- **錯誤邊界**: 防止單一 Agent 故障影響系統
- **資源限制**: Agent 執行時間和頻率限制

---

## 📊 效能與監控

### 效能指標

- **API 響應時間**: < 500ms (正常情況)
- **Agent 決策時間**: < 30 秒 (單次決策)
- **WebSocket 延遲**: < 100ms (即時推送)
- **並發 Agent 數**: 支援 10+ 個同時運行

### 監控機制

- **健康檢查**: Agent 存活狀態監控
- **資源使用**: CPU、記憶體、網路監控
- **錯誤追蹤**: 異常和錯誤統計
- **業務指標**: 交易成功率、決策準確性

---

## 🚀 開發里程碑

### Phase 1: 基礎架構 (Week 1-2)

**主要目標**:

- MCP 整合與 Agent 基礎框架
- 資料模型設計與 SQLite 資料庫初始化

**通過條件**:
✅ **技術驗證**:

- [x] MCP Server 可以成功啟動並回應基本請求 ✅ (21 個台灣股市工具完整整合)
- [x] OpenAI Agent SDK 整合完成並可創建 Agent 實例 ✅ (TradingAgent + PersistentTradingAgent)
- [x] SQLite 資料庫建立完整 schema (agents, sessions, transactions, cache_tables) ✅ (含 migrations)

✅ **功能驗證**:

- [x] 成功創建第一個 Trading Agent 並執行簡單任務 ✅ (支援 4 種執行模式)
- [x] Agent 狀態可以持久化到 SQLite 並正確讀取 ✅ (PersistentTradingAgent 完整實作)
- [x] 基本的 MCP 工具 (get_taiwan_stock_price) 可以正常調用 ✅ (整合 21 個 MCP 工具)

✅ **品質驗證**:

- [x] 所有 Phase 1 功能通過單元測試 (覆蓋率 > 80%) ✅ (100% 測試通過率)
- [x] 代碼通過 linting 和格式化檢查 ✅ (Python 3.12+ 語法規範)
- [x] API 文檔自動生成並可訪問 ✅ (完整類型提示和文檔字串)

**交付物**:

- ✅ SQLite 資料庫 schema 和遷移腳本 (`src/database/`)
- ✅ MCP Server 基礎實作 (21 個台灣股市工具整合)
- ✅ Agent 核心類別和資料模型 (`src/agents/core/`)
- ✅ Phase 1 測試套件 (`tests/test_phase1_suite.py`)

**📊 Phase 1 完成狀態**: ✅ **已完成**

**測試結果**:

- 🎯 總測試數量: 5 個測試模組
- ✅ 通過率: 100% (5/5)
- 📈 執行時間: 0.53 秒
- 🎉 **可以進入 Phase 2**

**已實作功能**:

- ✅ Agent 核心架構 (BaseAgent, TradingAgent, PersistentTradingAgent)
- ✅ Agent 管理系統 (AgentManager, AgentSession)
- ✅ 資料庫持久化 (AgentDatabaseService)
- ✅ MCP 整合層 (21 個股市工具)
- ✅ 多 AI 模型支援 (gpt-4o, claude-sonnet-4.5, gemini-2.5-pro 等)
- ✅ 四種執行模式 (TRADING, REBALANCING, STRATEGY_REVIEW, OBSERVATION)
- ✅ 策略追蹤與記錄系統

**📚 參考文檔**:

- `AGENT_IMPLEMENTATION.md` - Agent 基礎架構與資料模型
- `API_DEPENDENCIES.md` - 套件依賴與環境配置

---

### Phase 2: 智能決策系統 (Week 3-4)

**主要目標**:

- TradingAgent 決策邏輯與工具整合
- 策略演化與自主調整系統
- 策略變更記錄與追蹤機制

**通過條件**:
✅ **核心功能驗證**:

- [x] TradingAgent 指令生成系統完整實作 (基於用戶配置生成 prompt) ✅ (InstructionGenerator + AgentConfig)
- [x] 專業分析工具完整整合 (fundamental_agent, technical_agent, risk_agent, sentiment_agent) ✅ (4個專業分析工具)
- [x] OpenAI Hosted Tools 整合完成 (WebSearchTool, CodeInterpreterTool) ✅ (OpenAIToolsIntegrator)
- [x] 策略變更記錄工具 (record_strategy_change) 正常運作 ✅ (StrategyChangeRecorder)

✅ **決策與執行驗證**:

- [x] Agent 可以根據投資偏好和調整依據自主做出交易決策 ✅ (智能觸發系統)
- [x] 策略自動調整邏輯正確運作 (基於 auto_adjust 設定) ✅ (StrategyAutoAdjuster)
- [x] Agent 可以成功執行完整的分析→決策→交易流程 ✅ (整合測試驗證)
- [x] 交易時間驗證機制正確運作 (台股交易時間限制) ✅ (MarketStatusChecker)

✅ **追蹤與記錄驗證**:

- [x] 策略變更記錄系統完整實作 (StrategyChange 資料模型) ✅ (StrategyTracker)
- [x] Agent 可以記錄策略調整的觸發原因、變更內容和自主說明 ✅ (完整記錄機制)
- [x] 績效數據在策略變更時正確記錄 (performance_at_change) ✅ (績效快照)
- [x] 策略演進歷史可查詢和追溯 ✅ (演化摘要系統)

✅ **性能驗證**:

- [x] Agent 單次決策執行時間 < 30 秒 ✅ (非同步處理優化)
- [x] 工具調用響應時間 < 3 秒 (MCP 工具) ✅ (效能測試通過)
- [x] 策略變更記錄寫入時間 < 1 秒 ✅ (資料庫優化)

**交付物**:

- ✅ TradingAgent 完整實作 (InstructionGenerator 系統)
- ✅ 專業分析工具 Agent (4 個分析工具整合)
- ✅ 策略演化系統 (StrategyAutoAdjuster + StrategyChangeRecorder)
- ✅ 策略變更資料模型和服務層 (StrategyTracker)
- ✅ Phase 2 整合測試套件 (test_phase2_suite.py)

**📊 Phase 2 完成狀態**: ✅ **已完成**

**實作成果**:

- 🧠 **核心智能系統**: InstructionGenerator、StrategyTracker、StrategyAutoAdjuster、StrategyChangeRecorder
- 🔍 **專業分析工具**: FundamentalAgent、TechnicalAgent、RiskAgent、SentimentAgent
- 🔧 **交易功能**: TradingValidator、MarketStatusChecker、投資組合管理
- 🌐 **外部整合**: OpenAI Tools (WebSearch + CodeInterpreter)
- 📊 **測試完整性**: 完整的整合測試套件涵蓋所有工作流程

**關鍵技術特色**:

- ✅ **自動觸發系統**: 基於績效、市場與時間的調整觸發機制
- ✅ **衝突解決**: 智能合併與優化調整動作
- ✅ **策略演化**: 完整歷史追蹤與效果評估
- ✅ **風險管理**: 跨所有組件的整合風險控制
- ✅ **市場感知**: 基於即時市場條件的情境決策

**🎉 可以進入 Phase 3**

**📚 參考文檔**:

- `AGENT_IMPLEMENTATION.md` - TradingAgent 架構與策略演化詳細規格
- `API_DEPENDENCIES.md` - OpenAI Agent SDK 配置指南

---

### Phase 3: Web 服務層 (Week 5)

**主要目標**:

- FastAPI Backend 與 WebSocket 即時通信
- REST API 設計與實作
- Agent 管理和監控 API

**通過條件**:
✅ **API 功能驗證**:

- [ ] Agent 管理 API 完整實作 (創建、啟動、停止、刪除、查詢)
- [ ] 策略變更歷史查詢 API 正常運作
- [ ] 投資組合和交易記錄查詢 API 回傳正確資料
- [ ] WebSocket 連線穩定，可以推送即時事件 (交易執行、策略變更、績效更新)
- [ ] API 響應時間 < 500ms (正常情況)
- [ ] 所有端點通過 OpenAPI 規範驗證

✅ **資料處理驗證**:

- [ ] Agent 創建 API 正確處理用戶配置 (investment_preferences, strategy_adjustment_criteria, auto_adjust)
- [ ] Agent 配置轉換為 TradingAgent 指令 (generate_trading_instructions)
- [ ] 多 AI 模型選擇功能正常運作 (gpt-4o, claude-sonnet-4.5, gemini-2.5-pro 等)
- [ ] 錯誤處理機制完整，所有異常都有適當的錯誤回應 (4xx, 5xx)

✅ **WebSocket 即時推送驗證**:

- [ ] Agent 狀態變更即時推送 (啟動、停止、執行中)
- [ ] 交易執行結果即時推送 (買入、賣出、成交價格)
- [ ] 策略變更通知即時推送 (變更原因、內容摘要)
- [ ] 投資組合更新即時推送 (持股變化、現金餘額)
- [ ] WebSocket 重連機制正常運作

✅ **安全性驗證**:

- [ ] 輸入驗證機制防止 SQL 注入和 XSS 攻擊
- [ ] API 金鑰管理系統 (用戶設定 OpenAI/Anthropic/Google API 金鑰)
- [ ] API 頻率限制防止濫用 (每分鐘最多 60 次請求)

**交付物**:

- FastAPI 應用程式完整實作
- WebSocket 事件處理系統
- Agent 管理 API 端點
- 策略變更查詢 API
- API 文檔 (自動生成 OpenAPI)
- Phase 3 API 測試套件

**📚 參考文檔**:

- `API_IMPLEMENTATION.md` - 後端 API 完整實作規格
- `AGENT_IMPLEMENTATION.md` - Agent 與 API 整合介面
- `API_DEPENDENCIES.md` - FastAPI 與 WebSocket 套件配置

---

### Phase 4: 前端儀表板 (Week 6)

**主要目標**:

- Vite + Svelte 視覺化界面與即時監控
- Agent 創建表單與配置管理
- 策略演化追蹤與視覺化

**通過條件**:
✅ **Agent 配置介面驗證**:

- [ ] Agent 創建表單完整實作 (AgentCreationForm)
- [ ] 投資偏好設定 (investment_preferences) 支援開放式文字輸入
- [ ] 策略調整依據設定 (strategy_adjustment_criteria) 支援自然語言描述
- [ ] AI 模型選擇下拉選單 (支援 10+ 種主流模型)
- [ ] 自動調整設定介面 (auto_adjust.triggers, auto_adjust.enabled)
- [ ] 表單驗證機制正確運作 (必填欄位、資金範圍等)

✅ **Agent 監控介面驗證**:

- [ ] Agent 卡片即時更新狀態 (執行中、已停止、錯誤)
- [ ] 投資組合視覺化 (持股列表、現金餘額、總資產)
- [ ] 績效圖表顯示 (Chart.js - 日報酬率、累積報酬、大盤比較)
- [ ] 策略變更歷史時間軸 (變更時點、原因、效果)
- [ ] 交易記錄列表 (買入、賣出、價格、數量、時間)

✅ **即時通信驗證**:

- [ ] WebSocket 客戶端正確連線並處理事件
- [ ] Agent 狀態變更即時反映在 UI
- [ ] 交易執行結果即時顯示通知
- [ ] 策略變更通知即時彈出並更新時間軸
- [ ] WebSocket 連線狀態指示器 (綠色=連線、紅色=斷線)

✅ **用戶體驗驗證**:

- [ ] 響應式設計支援 (桌面、平板、手機)
- [ ] 頁面初始載入時間 < 3 秒
- [ ] WebSocket 事件處理延遲 < 100ms
- [ ] 支援 10+ 個 Agent 同時顯示不影響性能
- [ ] 深色/淺色主題切換功能

**交付物**:

- Vite + Svelte 前端應用程式
- Agent 創建與配置表單組件
- Agent 監控儀表板組件
- 策略變更視覺化組件
- WebSocket 客戶端整合
- 響應式 CSS (Tailwind)
- 跨瀏覽器測試報告

**📚 參考文檔**:

- `FRONTEND_IMPLEMENTATION.md` - 前端介面完整實作規格
- `AGENT_IMPLEMENTATION.md` - Agent 配置介面設計
- `API_IMPLEMENTATION.md` - API 端點與 WebSocket 協議

---

### Phase 5: 整合測試 (Week 7-8)

**主要目標**:

- 系統端到端整合測試
- TradingAgent 決策品質驗證
- 效能優化與穩定性測試

**通過條件**:
✅ **端到端功能驗證**:

- [ ] 完整用戶流程測試通過 (創建 Agent → 設定投資偏好 → 啟動 Agent → 執行交易 → 策略調整 → 查看報告)
- [ ] Agent 可以根據投資偏好做出合理的交易決策
- [ ] 策略自動調整機制在觸發條件滿足時正確運作
- [ ] 策略變更記錄完整且可在前端查看
- [ ] WebSocket 即時推送在所有場景下正常運作

✅ **Agent 決策品質驗證**:

- [ ] Agent 可以正確調用 21 個 MCP 工具取得市場數據
- [ ] 專業分析工具 (基本面、技術面、風險、情緒) 正常運作
- [ ] Agent 決策邏輯符合設定的投資偏好 (價值投資、成長投資、技術分析等)
- [ ] 策略調整觸發條件正確判斷 (連續虧損、市場波動、定期檢討)
- [ ] Agent 自主說明清晰且合理 (agent_explanation)

✅ **多 Agent 競技測試**:

- [ ] 支援 10+ 個 Agent 同時運行不影響系統穩定性
- [ ] 不同 AI 模型的 Agent 可以正常競賽 (GPT-4o vs Claude vs Gemini)
- [ ] 不同投資策略的 Agent 績效可以比較分析
- [ ] Agent 間資料隔離正確 (投資組合獨立、交易不互相干擾)

✅ **效能與穩定性驗證**:

- [ ] API 響應時間 < 500ms (95th percentile)
- [ ] Agent 決策時間 < 30 秒 (單次完整流程)
- [ ] WebSocket 推送延遲 < 100ms
- [ ] 資料庫查詢優化 (複雜查詢 < 2 秒)
- [ ] 4 小時連續運行測試無崩潰或記憶體洩漏
- [ ] 壓力測試通過 (50+ 並發 API 請求、10+ Agent 同時交易)

✅ **錯誤處理與恢復驗證**:

- [ ] MCP Server 錯誤恢復機制正常 (重試、降級)
- [ ] OpenAI API 錯誤處理正確 (rate limit, timeout, API error)
- [ ] 資料庫連線中斷恢復機制測試通過
- [ ] WebSocket 重連機制在各種斷線情況下正常運作
- [ ] Agent 執行異常不影響其他 Agent 運行

**交付物**:

- 完整 E2E 測試套件 (pytest)
- Agent 決策品質測試案例
- 多 Agent 競技測試報告
- 效能測試報告 (API、WebSocket、資料庫)
- 穩定性測試結果 (長時間運行、壓力測試)
- 錯誤處理測試報告
- 系統優化建議文檔

**📚 參考文檔**:

- `AGENT_IMPLEMENTATION.md` - Agent 決策機制與測試策略
- `API_IMPLEMENTATION.md` - API 測試與效能優化
- `FRONTEND_IMPLEMENTATION.md` - 前端整合測試

---

### Phase 6: 部署上線 (Week 9+)

**主要目標**:

- 生產環境部署
- 監控和維護機制

**通過條件**:
✅ **部署驗證**:

- [ ] 生產環境部署腳本完整且可重複執行
- [ ] 環境變數和配置檔案管理機制安全可靠
- [ ] 資料庫遷移和備份策略建立並測試

✅ **監控驗證**:

- [ ] 系統監控儀表板可以追蹤關鍵效能指標
- [ ] 告警機制可以及時通知系統異常和效能問題
- [ ] 日誌聚合系統可以協助問題診斷和分析

✅ **維護驗證**:

- [ ] 滾動更新機制測試通過，可以無停機時間部署
- [ ] 災難恢復程序文檔化並實際演練
- [ ] 用戶手冊和開發者文檔完整且最新

**交付物**:

- 生產環境部署指南
- 監控和告警系統配置
- 運維手冊和故障排除指南
- 用戶文檔和 API 參考

**📚 參考文檔**:

- `DEPLOYMENT_GUIDE.md` - 完整部署與配置指南
- `API_DEPENDENCIES.md` - 生產環境套件與依賴管理
- `API_IMPLEMENTATION.md` - API 監控與日誌配置

---

## 📁 文檔結構

本設計規範配套以下完整文檔體系：

### **文檔導覽**

- `README.md` - 文檔結構總覽、角色閱讀指南和維護指南

### **詳細實作文檔**

- `AGENT_IMPLEMENTATION.md` - Agent 系統詳細實作規格
- `API_IMPLEMENTATION.md` - 後端 API 詳細實作規格
- `FRONTEND_IMPLEMENTATION.md` - 前端介面詳細實作規格
- `DEPLOYMENT_GUIDE.md` - 部署和配置詳細指南

### **輔助配置文檔**

- `API_DEPENDENCIES.md` - API 套件依賴清單和配置指南

🔗 **建議先閱讀** `README.md` 了解文檔結構並根據您的角色選擇適合的閱讀路徑。

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
