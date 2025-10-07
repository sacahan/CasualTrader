# CasualTrader 專案結構規範

**版本**: 1.0
**日期**: 2025-10-06
**適用於**: API、Agent、Frontend 三大模塊

---

## 📋 概述

本文檔定義 CasualTrader 專案的統一檔案結構，採用 **Monorepo** 架構，清楚分離前後端關注點，便於開發、測試和部署。

---

## 🏗️ 整體架構

```
CasualTrader/                  # 專案根目錄
├── backend/                   # 後端應用 (Python/FastAPI)
├── frontend/                  # 前端應用 (Vite + Svelte)
├── tests/                     # 整合測試目錄
├── docs/                      # 專案文檔
├── scripts/                   # 開發腳本
├── docker-compose.yml         # Docker 編排配置
└── README.md                  # 專案主文檔
```

---

## 🐍 Backend 結構 (Python/FastAPI)

```
backend/
├── src/
│   ├── agents/                # Agent 系統模塊
│   │   ├── core/              # 核心 Agent 實作
│   │   │   ├── trading_agent.py         # TradingAgent 實作
│   │   │   ├── instruction_generator.py # Agent指令生成器
│   │   │   ├── strategy_tracker.py      # 策略變更追蹤
│   │   │   └── models.py                # Agent 資料模型
│   │   ├── tools/             # 專門化分析工具
│   │   │   ├── fundamental_agent.py     # 基本面分析工具
│   │   │   ├── technical_agent.py       # 技術分析工具
│   │   │   ├── risk_agent.py           # 風險評估工具
│   │   │   └── sentiment_agent.py       # 市場情緒分析工具
│   │   ├── functions/         # 交易驗證功能
│   │   │   ├── trading_validation.py    # 交易參數驗證
│   │   │   ├── market_status.py         # 市場狀態檢查
│   │   │   └── portfolio_queries.py     # 投資組合查詢
│   │   └── integrations/      # 外部服務整合
│   │       ├── mcp_client.py            # CasualMarket MCP客戶端
│   │       └── mcp_function_wrappers.py # MCP工具包裝
│   │
│   ├── api/                   # FastAPI 應用
│   │   ├── main.py            # FastAPI 應用主檔案
│   │   ├── routers/           # API 路由定義
│   │   │   ├── agents.py              # Agent 管理路由
│   │   │   ├── portfolio.py           # 投資組合路由
│   │   │   ├── strategy_changes.py    # 策略變更路由
│   │   │   ├── traces.py              # 追蹤系統路由
│   │   │   ├── market.py              # 市場數據路由
│   │   │   └── system.py              # 系統管理路由
│   │   ├── services/          # 業務邏輯服務層
│   │   │   ├── agent_service.py       # Agent 業務邏輯
│   │   │   ├── portfolio_service.py   # 投資組合服務
│   │   │   ├── strategy_service.py    # 策略變更服務
│   │   │   ├── trace_service.py       # 追蹤服務
│   │   │   ├── websocket_service.py   # 即時通知服務
│   │   │   └── mcp_client_wrapper.py  # MCP 客戶端包裝
│   │   ├── models/            # API 資料模型
│   │   │   ├── requests.py            # API 請求模型
│   │   │   ├── responses.py           # API 回應模型
│   │   │   └── websocket_events.py    # WebSocket 事件模型
│   │   ├── middleware/        # FastAPI 中間件
│   │   │   ├── auth.py                # 認證中間件
│   │   │   ├── rate_limit.py          # 頻率限制
│   │   │   └── logging.py             # 請求日誌
│   │   └── utils/             # API 工具函數
│   │       ├── exceptions.py          # 自定義異常
│   │       ├── validators.py          # 資料驗證
│   │       └── websocket_manager.py   # WebSocket 管理
│   │
│   └── shared/                # 共享組件
│       ├── database/          # 資料庫相關
│       │   ├── models.py              # 資料模型
│       │   ├── connection.py          # 資料庫連接
│       │   └── migrations/            # 資料庫遷移
│       ├── utils/             # 共享工具
│       │   ├── logging.py             # 統一日誌
│       │   ├── config.py              # 配置管理
│       │   └── constants.py           # 常數定義
│       └── types/             # 共享類型定義
│           ├── api_types.py           # API 類型
│           ├── agent_types.py         # Agent 類型
│           └── market_types.py        # 市場資料類型
│
├── pyproject.toml             # Python 專案配置
├── requirements.txt           # Python 依賴
├── .env.example               # 環境變數範例
└── README.md                  # 後端說明文檔
```

### Backend 模塊職責

- **agents/**: Agent 系統核心邏輯、工具和外部整合
- **api/**: REST API 端點、WebSocket、業務邏輯服務
- **shared/**: 跨模塊共享的資料庫、工具和類型定義

---

## 🎨 Frontend 結構 (Vite + Svelte)

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
tests/
├── backend/                   # 後端測試
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

- **tests/backend/**: 後端單元測試和整合測試
- **tests/frontend/**: 前端單元、整合和 E2E 測試
- **tests/integration/**: 跨前後端的完整流程測試

---

## 📚 Docs 結構

```
docs/
├── SYSTEM_DESIGN.md           # 系統設計總覽
├── PROJECT_STRUCTURE.md       # 專案結構規範 (本文檔)
├── API_IMPLEMENTATION.md      # API 實作規格
├── AGENT_IMPLEMENTATION.md    # Agent 系統實作規格
├── FRONTEND_IMPLEMENTATION.md # 前端實作規格
└── DEPLOYMENT_GUIDE.md        # 部署指南
```

---

## 🛠️ Scripts 結構

```
scripts/
├── start-dev.sh               # 啟動開發環境 (前後端)
├── run-tests.sh               # 執行所有測試
├── deploy.sh                  # 部署腳本
├── setup-backend.sh           # 後端環境設置
└── setup-frontend.sh          # 前端環境設置
```

---

## 🐳 Docker 結構

```
CasualTrader/
├── docker-compose.yml         # Docker 編排配置
├── backend/
│   └── Dockerfile             # 後端 Docker 配置
└── frontend/
    └── Dockerfile             # 前端 Docker 配置
```

---

## 🔄 模塊間依賴關係

```
Frontend (Svelte)
    ↓ HTTP/WebSocket
Backend API (FastAPI)
    ↓ Function Calls
Agent System (OpenAI Agents)
    ↓ MCP Protocol
CasualMarket (External MCP Server)
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

## ✅ 專案結構檢查清單

### Backend 結構驗證

- [ ] `backend/src/agents/` 目錄存在且包含核心、工具、函數子目錄
- [ ] `backend/src/api/` 目錄包含 main.py 和完整的路由結構
- [ ] `backend/src/shared/` 目錄包含資料庫、工具和類型子目錄
- [ ] `backend/pyproject.toml` 配置正確的依賴

### Frontend 結構驗證

- [ ] `frontend/src/components/` 按功能分類組織
- [ ] `frontend/src/routes/` 包含 SvelteKit 路由結構
- [ ] `frontend/src/stores/` 包含狀態管理檔案
- [ ] `frontend/package.json` 配置正確的依賴

### Tests 結構驗證

- [ ] `tests/backend/` 鏡像後端源碼結構
- [ ] `tests/frontend/` 包含單元、整合和 E2E 測試
- [ ] `tests/integration/` 包含跨模塊整合測試

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
