# CasualTrader 專案結構規範

**版本**: 2.0
**日期**: 2025-10-09
**適用於**: Monorepo 架構 - Backend + Frontend

---

## 📋 概述

本文檔定義 CasualTrader 專案的統一檔案結構，採用 **Monorepo** 架構，清楚分離前後端關注點，便於開發、測試和部署。

**重構狀態**:

- ✅ 文檔已更新為 Monorepo 結構
- ⏳ 代碼重構進行中 (參見 `RESTRUCTURE_GUIDE.md`)

---

## 🏗️ 整體架構

```
CasualTrader/                  # 專案根目錄 (Monorepo)
├── backend/                   # 🐍 Python 後端應用
├── frontend/                  # 🎨 前端應用 (Vite + Svelte)
├── tests/                     # 🧪 跨模塊整合測試
├── docs/                      # 📚 專案文檔
├── scripts/                   # 🔧 開發與部署腳本
├── .github/                   # ⚙️ GitHub Actions & Copilot
├── docker-compose.yml         # 🐳 Docker 編排配置
└── README.md                  # 📖 專案主文檔
```

---

## 🐍 Backend 結構 (Python/FastAPI)

```
backend/
├── src/                       # Python 源代碼根目錄
│   ├── agents/                # ✅ Agent 系統模塊 (Phase 1-2)
│   │   ├── core/              # 核心 Agent 架構
│   │   │   ├── base_agent.py              # Agent 抽象基類
│   │   │   ├── agent_manager.py           # Agent 生命週期管理
│   │   │   ├── agent_session.py           # Agent 會話管理
│   │   │   ├── models.py                  # 核心數據模型
│   │   │   ├── instruction_generator.py   # 動態指令生成
│   │   │   ├── strategy_tracker.py        # 策略追蹤
│   │   │   └── strategy_auto_adjuster.py  # 策略自動調整
│   │   │
│   │   ├── tools/             # 專業分析工具（自主型 Agent）
│   │   │   ├── fundamental_agent.py       # 基本面分析 Agent
│   │   │   ├── technical_agent.py         # 技術分析 Agent
│   │   │   ├── risk_agent.py              # 風險評估 Agent
│   │   │   └── sentiment_agent.py         # 市場情緒分析 Agent
│   │   │   # 每個 Agent 內建：
│   │   │   # - WebSearchTool (搜尋最新資訊)
│   │   │   # - CodeInterpreterTool (執行進階計算)
│   │   │   # - 成本控制準則
│   │   │
│   │   ├── functions/         # 業務邏輯函數
│   │   │   ├── portfolio_queries.py       # 投資組合查詢
│   │   │   ├── market_status.py           # 市場狀態檢查
│   │   │   ├── trading_validation.py      # 交易驗證
│   │   │   └── strategy_change_recorder.py # 策略變更記錄
│   │   │
│   │   ├── integrations/      # 外部服務整合
│   │   │   ├── mcp_client.py              # MCP 工具客戶端
│   │   │   ├── database_service.py        # 資料庫服務
│   │   │   ├── persistent_agent.py        # 持久化 Agent
│   │   │   └── openai_tools.py            # OpenAI 工具定義
│   │   │
│   │   ├── trading/           # 交易執行層
│   │   │   └── trading_agent.py           # 主要交易 Agent
│   │   │
│   │   └── utils/             # Agent 工具函數
│   │       ├── logger.py                  # 日誌工具
│   │       ├── risk_analytics.py          # 風險計算
│   │       └── technical_indicators.py    # 技術指標
│   │
│   ├── api/                   # ✅ FastAPI 應用 (Phase 3)
│   │   ├── app.py             # FastAPI 應用工廠
│   │   ├── server.py          # 服務器啟動入口
│   │   ├── config.py          # 配置管理
│   │   ├── docs.py            # API 文檔配置
│   │   ├── models.py          # Pydantic 資料模型
│   │   ├── websocket.py       # WebSocket 管理器
│   │   │
│   │   └── routers/           # API 路由模組
│   │       ├── __init__.py
│   │       ├── agents.py              # Agent 管理路由
│   │       ├── trading.py             # 交易數據路由
│   │       └── websocket_router.py    # WebSocket 路由
│   │
│   └── database/              # ✅ 資料庫層 (Phase 1)
│       ├── models.py          # SQLAlchemy 資料模型
│       ├── migrations.py      # 資料庫遷移
│       └── schema.sql         # 資料庫結構定義
│
├── tests/                     # 後端單元與整合測試
│   ├── agents/                # Agent 系統測試
│   │   ├── core/
│   │   │   ├── test_base_agent.py
│   │   │   ├── test_agent_manager.py
│   │   │   ├── test_agent_session.py
│   │   │   └── test_models.py
│   │   ├── tools/
│   │   │   ├── test_fundamental_agent.py
│   │   │   ├── test_technical_agent.py
│   │   │   ├── test_risk_agent.py
│   │   │   └── test_sentiment_agent.py
│   │   ├── functions/
│   │   │   ├── test_portfolio_queries.py
│   │   │   ├── test_market_status.py
│   │   │   └── test_trading_validation.py
│   │   └── integrations/
│   │       ├── test_mcp_client.py
│   │       ├── test_database_service.py
│   │       └── test_persistent_agent.py
│   │
│   ├── api/                   # API 測試
│   │   ├── test_app.py
│   │   ├── routers/
│   │   │   ├── test_agents.py
│   │   │   ├── test_trading.py
│   │   │   └── test_websocket.py
│   │   └── test_websocket_manager.py
│   │
│   └── database/              # 資料庫測試
│       ├── test_models.py
│       └── test_migrations.py
│
├── pyproject.toml             # Python 專案配置 (uv)
├── uv.lock                    # UV 依賴鎖定檔
├── casualtrader.db            # SQLite 資料庫檔案
├── .env.example               # 環境變數範例
└── README.md                  # 後端說明文檔
```

### Backend 模塊職責

- **src/agents/**: Agent 系統核心邏輯、專業分析工具、外部整合
- **src/api/**: REST API 端點、WebSocket 即時通信
- **src/database/**: SQLAlchemy 資料模型、遷移腳本
- **tests/**: 完整的單元測試和整合測試覆蓋

---

## 🎨 Frontend 結構 (Vite + Svelte)

**狀態**: ⏳ Phase 4 準備中

```
frontend/
├── public/                    # 靜態資源
│   ├── favicon.ico
│   └── vite.svg
│
├── src/                       # 前端源代碼
│   ├── App.svelte             # 主應用程式組件
│   ├── main.js                # Vite 進入點
│   ├── app.css                # 全域樣式
│   │
│   ├── components/            # 可重用組件
│   │   ├── Layout/            # 佈局組件
│   │   │   ├── Navbar.svelte
│   │   │   └── Sidebar.svelte
│   │   ├── Agent/             # Agent 相關組件
│   │   │   ├── AgentCard.svelte
│   │   │   ├── AgentGrid.svelte
│   │   │   ├── AgentModal.svelte
│   │   │   ├── AgentCreationForm.svelte
│   │   │   ├── AgentDashboard.svelte
│   │   │   ├── AgentConfigEditor.svelte
│   │   │   ├── AgentToolsSelector.svelte
│   │   │   ├── AgentPerformancePanel.svelte
│   │   │   ├── StrategyHistoryView.svelte
│   │   │   └── StrategyChangeModal.svelte
│   │   ├── Chart/             # 圖表組件
│   │   │   ├── PerformanceChart.svelte
│   │   │   └── MarketChart.svelte
│   │   ├── Market/            # 市場相關組件
│   │   │   ├── MarketPanel.svelte
│   │   │   └── StockQuote.svelte
│   │   └── UI/                # 基礎 UI 組件
│   │       ├── Button.svelte
│   │       ├── Modal.svelte
│   │       └── StatusIndicator.svelte
│   │
│   ├── routes/                # SvelteKit 路由頁面
│   │   ├── +layout.svelte
│   │   ├── +page.svelte       # 主儀表板
│   │   ├── agents/            # Agent 管理頁面
│   │   │   ├── +page.svelte
│   │   │   └── [id]/
│   │   │       └── +page.svelte
│   │   └── settings/          # 設定頁面
│   │       └── +page.svelte
│   │
│   ├── stores/                # Svelte stores 狀態管理
│   │   ├── agents.js          # Agent 狀態管理
│   │   ├── websocket.js       # WebSocket 連線狀態
│   │   ├── market.js          # 市場數據狀態
│   │   └── notifications.js   # 通知系統
│   │
│   ├── lib/                   # 前端工具函數
│   │   ├── api.js             # API 客戶端
│   │   ├── websocket.js       # WebSocket 管理
│   │   ├── utils.js           # 共用工具
│   │   └── constants.js       # 前端常數
│   │
│   └── types/                 # TypeScript 類型定義
│       ├── agent.ts           # Agent 類型
│       ├── api.ts             # API 類型
│       └── websocket.ts       # WebSocket 類型
│
├── vite.config.js             # Vite 配置
├── tailwind.config.js         # Tailwind CSS 配置
├── postcss.config.js          # PostCSS 配置
├── package.json               # NPM 配置
├── tsconfig.json              # TypeScript 配置
├── .env.example               # 環境變數範例
└── README.md                  # 前端說明文檔
```

### Frontend 模塊職責

- **components/**: 可重用 UI 組件，按功能分類組織
- **routes/**: SvelteKit 頁面路由和頁面組件
- **stores/**: Svelte 響應式狀態管理
- **lib/**: 前端工具函數和 API 客戶端

---

## 🧪 Tests 結構

```
tests/                         # 跨模塊整合測試（根目錄）
└── integration/               # 前後端整合測試
    ├── test_api_agent_integration.py
    ├── test_websocket_flow.py
    └── test_end_to_end_workflow.py

# 後端單元測試在 backend/tests/
# 前端單元測試在 frontend/tests/
```

### 舊的測試結構 (已重構)

```
tests/                         # ❌ 舊結構 (已移除)
├── backend/                   # → 移至 backend/tests/
│   ├── agents/                # Agent 系統測試
│   │   ├── core/
│   │   │   ├── test_trading_agent.py
│   │   │   ├── test_instruction_generator.py
│   │   │   ├── test_strategy_tracker.py
│   │   │   └── test_models.py
│   │   ├── tools/
│   │   │   ├── test_fundamental_agent.py
│   │   │   ├── test_technical_agent.py
│   │   │   ├── test_risk_agent.py
│   │   │   └── test_sentiment_agent.py
│   │   ├── functions/
│   │   │   ├── test_trading_validation.py
│   │   │   ├── test_market_status.py
│   │   │   └── test_portfolio_queries.py
│   │   └── integrations/
│   │       ├── test_mcp_client.py
│   │       └── test_mcp_integration.py
│   │
│   ├── api/                   # API 測試
│   │   ├── test_main.py
│   │   ├── routers/
│   │   │   ├── test_agents.py
│   │   │   ├── test_portfolio.py
│   │   │   ├── test_strategy_changes.py
│   │   │   ├── test_traces.py
│   │   │   ├── test_market.py
│   │   │   └── test_system.py
│   │   ├── services/
│   │   │   ├── test_agent_service.py
│   │   │   ├── test_portfolio_service.py
│   │   │   ├── test_strategy_service.py
│   │   │   └── test_trace_service.py
│   │   ├── middleware/
│   │   │   ├── test_auth.py
│   │   │   └── test_rate_limit.py
│   │   └── utils/
│   │       ├── test_exceptions.py
│   │       ├── test_validators.py
│   │       └── test_websocket_manager.py
│   │
│   └── shared/                # 共享組件測試
│       ├── database/
│       │   └── test_models.py
│       └── utils/
│           ├── test_config.py
│           └── test_logging.py
│
├── frontend/                  # 前端測試
│   ├── unit/                  # 單元測試
│   │   ├── components/        # 組件測試
│   │   │   ├── Agent/
│   │   │   │   ├── AgentCard.test.js
│   │   │   │   ├── AgentDashboard.test.js
│   │   │   │   ├── AgentCreationForm.test.js
│   │   │   │   ├── StrategyHistoryView.test.js
│   │   │   │   └── AgentConfigEditor.test.js
│   │   │   ├── Chart/
│   │   │   │   └── PerformanceChart.test.js
│   │   │   └── UI/
│   │   │       ├── Button.test.js
│   │   │       └── Modal.test.js
│   │   ├── stores/            # Store 測試
│   │   │   ├── agents.test.js
│   │   │   ├── websocket.test.js
│   │   │   └── market.test.js
│   │   └── lib/               # 工具函數測試
│   │       ├── api.test.js
│   │       ├── websocket.test.js
│   │       └── utils.test.js
│   │
│   ├── integration/           # 整合測試
│   │   ├── api-integration.test.js
│   │   ├── websocket-flow.test.js
│   │   └── agent-workflow.test.js
│   │
│   └── e2e/                   # 端到端測試
│       ├── agent-management.test.js
│       ├── trading-simulation.test.js
│       └── dashboard-functionality.test.js
│
└── integration/               # 跨模塊整合測試
    ├── test_api_agent_integration.py
    ├── test_frontend_backend_flow.py
    └── test_end_to_end_workflow.py
```

### Tests 模塊職責

- **backend/tests/**: 後端單元測試和模組內整合測試
- **frontend/tests/**: 前端單元、整合和 E2E 測試 (Phase 4)
- **tests/integration/**: 跨前後端的完整流程測試（根目錄）

---

## 📚 Docs 結構

```
docs/
├── SYSTEM_DESIGN.md           # 系統設計總覽
├── PROJECT_STRUCTURE.md       # 專案結構規範 (本文檔)
├── RESTRUCTURE_GUIDE.md       # 🆕 Monorepo 重構指南
│
├── AGENTS_ARCHITECTURE.md     # Agent 模組架構說明
├── API_ARCHITECTURE.md        # API 模組架構說明
├── FRONTEND_ARCHITECTURE.md   # Frontend 模組架構說明
│
├── AGENT_IMPLEMENTATION.md    # Agent 系統實作規格
├── API_IMPLEMENTATION.md      # API 實作規格
├── FRONTEND_IMPLEMENTATION.md # 前端實作規格
│
└── DEPLOYMENT_GUIDE.md        # 部署指南
```

---

## 🛠️ Scripts 結構

```
scripts/
├── start_api.sh               # ✅ 啟動後端 API 服務
├── start_frontend.sh          # ⏳ 啟動前端開發服務器 (Phase 4)
├── start_dev.sh               # 🆕 同時啟動前後端 (開發模式)
├── run_tests.sh               # 🆕 執行所有測試 (前後端 + 整合)
├── setup_backend.sh           # 🆕 後端環境設置
├── setup_frontend.sh          # ⏳ 前端環境設置 (Phase 4)
└── deploy.sh                  # 🆕 生產部署腳本
```

---

## 🐳 Docker 結構

```
CasualTrader/
├── docker-compose.yml         # Docker 編排配置（前後端）
│
├── backend/
│   ├── Dockerfile             # 後端 Docker 配置
│   └── .dockerignore          # Docker 忽略規則
│
└── frontend/                  # ⏳ Phase 4
    ├── Dockerfile             # 前端 Docker 配置
    └── .dockerignore          # Docker 忽略規則
```

---

## 🔄 模塊間依賴關係

```
┌─────────────────────────────────────────────┐
│  Frontend (Svelte) - ⏳ Phase 4             │
│  Location: frontend/src/                    │
└──────────────────┬──────────────────────────┘
                   │ HTTP/WebSocket
┌──────────────────▼──────────────────────────┐
│  Backend API (FastAPI) - ✅ Phase 3         │
│  Location: backend/src/api/                 │
└──────────────────┬──────────────────────────┘
                   │ Function Calls
┌──────────────────▼──────────────────────────┐
│  Agent System - ✅ Phase 1-2                │
│  Location: backend/src/agents/              │
└──────────────────┬──────────────────────────┘
                   │ MCP Protocol
┌──────────────────▼──────────────────────────┐
│  CasualMarket MCP Server (External)         │
│  21 個台灣股市專業工具                        │
└─────────────────────────────────────────────┘

資料持久化層:
┌─────────────────────────────────────────────┐
│  SQLite Database - ✅ Phase 1               │
│  Location: backend/casualtrader.db          │
│  Models: backend/src/database/models.py     │
└─────────────────────────────────────────────┘
```

---

## 📝 檔案命名規範

### Python 檔案

- **模組檔案**: `snake_case.py` (例如: `trading_agent.py`)
- **測試檔案**: `test_<module_name>.py` (例如: `test_trading_agent.py`)
- **私有模組**: `_internal.py` (底線開頭)

### JavaScript/Svelte 檔案

- **組件檔案**: `PascalCase.svelte` (例如: `AgentCard.svelte`)
- **工具檔案**: `camelCase.js` (例如: `websocket.js`)
- **測試檔案**: `<file_name>.test.js` (例如: `api.test.js`)
- **類型定義**: `camelCase.ts` (例如: `agent.ts`)

### 配置檔案

- **Python**: `pyproject.toml`, `requirements.txt`
- **JavaScript**: `package.json`, `vite.config.js`
- **Docker**: `Dockerfile`, `docker-compose.yml`

---

## ✅ Monorepo 結構檢查清單

### 根目錄結構 ✅

- [x] `backend/` 目錄存在並包含完整後端代碼
- [x] `docs/` 目錄包含所有技術文檔
- [x] `scripts/` 目錄包含開發與部署腳本
- [x] `.github/` 目錄包含 CI/CD 和 Copilot 配置
- [ ] `frontend/` 目錄已創建 (Phase 4)
- [ ] `tests/integration/` 包含跨模塊測試
- [ ] `docker-compose.yml` 配置前後端服務

### Backend 結構驗證 ✅

- [x] `backend/src/agents/` 包含 core, tools, functions, integrations, trading, utils
- [x] `backend/src/api/` 包含 app.py, server.py, models.py, websocket.py, routers/
- [x] `backend/src/database/` 包含 models.py, migrations.py, schema.sql
- [x] `backend/tests/` 鏡像 src/ 結構並包含完整測試
- [x] `backend/pyproject.toml` 配置正確（uv 管理）
- [x] `backend/casualtrader.db` SQLite 資料庫
- [x] `backend/.env` 或 `backend/.env.example` 環境變數配置

### Frontend 結構驗證 ⏳ (Phase 4)

- [ ] `frontend/src/components/` 按功能分類組織
- [ ] `frontend/src/routes/` 包含 SvelteKit 路由結構
- [ ] `frontend/src/stores/` 包含狀態管理檔案
- [ ] `frontend/src/lib/` 包含 API 客戶端和工具函數
- [ ] `frontend/package.json` 配置正確的依賴
- [ ] `frontend/vite.config.js` Vite 配置
- [ ] `frontend/tailwind.config.js` Tailwind CSS 配置

### 整合測試驗證 ⏳

- [ ] `tests/integration/` 存在並包含跨模塊測試
- [ ] 前後端 API 整合測試
- [ ] WebSocket 通信測試
- [ ] 端到端工作流程測試

### 腳本與工具驗證 🔧

- [x] `scripts/start_api.sh` 可啟動後端服務
- [ ] `scripts/start_frontend.sh` 可啟動前端 (Phase 4)
- [ ] `scripts/start_dev.sh` 可同時啟動前後端
- [ ] `scripts/run_tests.sh` 可執行所有測試
- [ ] `scripts/setup_backend.sh` 可配置後端環境
- [ ] `scripts/setup_frontend.sh` 可配置前端環境 (Phase 4)

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
