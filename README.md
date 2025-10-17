# CasualTrader AI 股票交易模擬器

**版本**: 1.0.0
**日期**: 2025-10-10
**專案類型**: AI Trading Simulator
**架構**: Monorepo (Backend + Frontend)

---

## 📋 專案概述

CasualTrader 是一個即時、可視化的 AI 股票交易模擬器，使用 OpenAI Agent SDK 構建智能交易代理人，支援多種 AI 模型同時進行股票交易，提供觀戰、分析和學習的平台。

### 核心特色

- 🤖 **多 AI 模型競技**: 支援 GPT-4o, Claude Sonnet 4.5, Gemini 2.5 Pro 等主流 AI 模型
- 📊 **即時市場數據**: 透過 MCP 協議獲取台灣股市即時資訊（21 個專業工具）
- 🎯 **智能決策系統**: AI 代理人基於市場數據和研究分析進行自主交易
- 📈 **策略追蹤**: 完整記錄投資策略和決策過程
- 🔄 **即時觀戰**: WebSocket 實時推送 AI 決策和執行過程
- 📚 **教育價值**: 通過觀察 AI 行為學習投資策略

### 技術架構優勢

- ✅ **關注點分離**: 數據獲取 (MCP) vs AI 決策 (Agent)
- ✅ **標準化協議**: MCP 協議確保擴展性和維護性
- ✅ **成本最優化**: 無需維護複雜的爬蟲和數據處理邏輯
- ✅ **即時性保證**: 所有數據來自 MCP 即時查詢
- ✅ **易於測試**: Mock MCP 回應進行單元測試

---

## 🏗️ 技術堆疊

### 前端技術

- **核心框架**: Vite + Svelte 5.0
- **構建工具**: Vite 5.4 (快速熱重載)
- **圖表視覺化**: Chart.js 4.4
- **即時通信**: WebSocket Client
- **樣式設計**: Tailwind CSS 3.3 + PostCSS

### 後端技術

- **Web 框架**: FastAPI 0.115+ (異步 API)
- **AI SDK**: OpenAI Agent SDK 0.3.3+ (支援 LiteLLM)
- **資料庫**: SQLite + SQLAlchemy 2.0 (異步支援)
- **即時通信**: WebSocket (狀態推送)
- **日誌系統**: Loguru

### AI 與工具層

- **支援的 AI 模型**:
  - OpenAI: GPT-4o, GPT-4o-mini, GPT-4-turbo
  - Anthropic: Claude Sonnet 4.5, Claude Opus 4
  - Google: Gemini 2.5 Pro, Gemini 2.0 Flash
  - 其他: DeepSeek, Grok
- **資料來源**: casual-market-mcp (21 個台灣股市專業工具)
- **協議標準**: Model Context Protocol (MCP)

---

## 📂 專案結構

```text
CasualTrader/
├── backend/                    # 後端服務 (Python)
│   ├── src/
│   │   ├── agents/            # AI 代理人系統
│   │   │   ├── core/          # Agent 核心邏輯
│   │   │   ├── functions/     # 專業分析 Agent
│   │   │   ├── integrations/  # MCP 整合
│   │   │   ├── tools/         # Agent 工具
│   │   │   ├── trading/       # 交易邏輯
│   │   │   └── utils/         # 工具函數
│   │   ├── api/               # FastAPI Web 服務
│   │   │   ├── routers/       # API 路由
│   │   │   ├── app.py         # 應用程式主檔
│   │   │   ├── server.py      # 服務啟動
│   │   │   ├── models.py      # API 模型
│   │   │   └── websocket.py   # WebSocket 處理
│   │   └── database/          # 資料庫層
│   │       ├── models.py      # ORM 模型
│   │       ├── migrations.py  # 資料庫遷移
│   │       └── schema.sql     # 資料庫結構
│   ├── tests/                 # 測試套件
│   │   ├── agents/           # Agent 測試
│   │   ├── api/              # API 測試
│   │   └── database/         # 資料庫測試
│   └── pyproject.toml        # Python 專案設定
│
├── frontend/                  # 前端應用 (Svelte)
│   ├── src/
│   │   ├── components/       # UI 元件
│   │   │   ├── Agent/       # Agent 相關元件
│   │   │   ├── Chart/       # 圖表元件
│   │   │   ├── Layout/      # 版面元件
│   │   │   ├── Market/      # 市場資訊元件
│   │   │   └── UI/          # 通用 UI 元件
│   │   ├── lib/             # 工具函數庫
│   │   │   ├── api/         # API 客戶端
│   │   │   ├── api.js       # API 通用函數
│   │   │   ├── constants.js # 常數定義
│   │   │   └── utils.js     # 工具函數
│   │   ├── stores/          # Svelte Store 狀態管理
│   │   ├── types/           # TypeScript 型別定義
│   │   ├── App.svelte       # 應用程式主元件
│   │   ├── main.js          # 應用程式進入點
│   │   └── app.css          # 全域樣式
│   ├── public/              # 靜態資源
│   ├── package.json         # Node.js 專案設定
│   └── vite.config.js       # Vite 構建設定
│
├── docs/                     # 技術文檔
│   ├── SYSTEM_DESIGN.md     # 系統設計規範
│   ├── AGENT_IMPLEMENTATION.md      # Agent 實作規格
│   ├── API_IMPLEMENTATION.md        # API 實作規格
│   ├── FRONTEND_IMPLEMENTATION.md   # 前端實作規格
│   ├── DEPLOYMENT_GUIDE.md          # 部署指南
│   ├── AGENTS_ARCHITECTURE.md       # Agent 架構說明
│   ├── API_ARCHITECTURE.md          # API 架構說明
│   ├── FRONTEND_ARCHITECTURE.md     # 前端架構說明
│   └── PROJECT_STRUCTURE.md         # 專案結構規範
│
├── scripts/                  # 工具腳本
│   ├── db_migrate.sh        # 資料庫遷移
│   ├── run_tests.sh         # 測試執行
│   └── start.sh             # 啟動腳本
│
├── examples/                 # 範例程式碼
├── logs/                     # 日誌目錄
└── README.md                 # 本文件
```

---

## 🚀 快速開始

### 🎯 選擇使用方式

**方式 A：使用 MCP Client（推薦，最簡單）** ⭐

直接在 Claude Desktop 或其他 MCP Client 中使用 casual-market 獲取台灣股市數據。

```bash
# 一鍵配置
./scripts/setup_mcp_client.sh
```

詳細指南：[快速開始 MCP Client](./docs/QUICKSTART_MCP.md)

---

**方式 B：運行完整的 CasualTrader 應用**

運行後端和前端，建立完整的 AI 交易模擬器。

繼續以下步驟...

### 系統需求

- **Python**: >= 3.12
- **Node.js**: >= 18.0
- **作業系統**: macOS, Linux, Windows
- **uv**: Python 套件管理器（用於 MCP）

### 環境設定

1. **複製專案**

```zsh
git clone https://github.com/sacahan/CasualTrader.git
cd CasualTrader
```

2. **設定 MCP Client（可選但推薦）**

```zsh
# 自動配置 Claude Desktop
./scripts/setup_mcp_client.sh

# 或手動配置，參考：docs/SETUP_MCP_CLIENT.md
```

3. **設定後端環境**

```zsh
cd backend

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 Windows: venv\Scripts\activate

# 安裝依賴
pip install -e ".[dev]"

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入 API Keys
```

4. **設定前端環境**

```zsh
cd frontend

# 安裝依賴
npm install
```

### 環境變數設定

在 `backend/.env` 中設定以下變數：

```bash
# AI 模型 API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key

# 資料庫設定
DATABASE_URL=sqlite+aiosqlite:///casualtrader.db

# API 設定
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# CORS 設定
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```

### 啟動服務

1. **啟動後端服務**

```zsh
cd backend
python -m src.api.server

# 或使用腳本
./scripts/start.sh
```

服務啟動於: `http://localhost:8000`
API 文件: `http://localhost:8000/docs`

1. **啟動前端開發服務**

```zsh
cd frontend
npm run dev
```

前端啟動於: `http://localhost:5173`

### 執行測試

```zsh
# 後端測試
cd backend
pytest tests/

# 或使用腳本
./scripts/run_tests.sh

# 測試覆蓋率
pytest --cov=src tests/
```

---

## 📖 核心功能

### 1. AI 代理人系統

- **基礎分析 Agent**: 分析公司財報、營收、產業地位
- **技術分析 Agent**: K 線、均線、技術指標分析
- **風險評估 Agent**: 評估交易風險、部位管理
- **情緒分析 Agent**: 分析市場情緒、新聞影響
- **投資組合查詢**: 即時查詢持倉、績效、現金狀況
- **策略追蹤**: 記錄策略變更、決策理由

### 2. 交易功能

- 台灣股票買賣（最小單位 1000 股）
- 即時市場資訊查詢
- 交易驗證與成本計算
- 投資組合管理
- 交易歷史記錄

### 3. 市場資訊

- 即時股價查詢（支援股票代號或公司名稱）
- 公司基本資料、財報資訊
- 月營收、股利分配資訊
- 外資持股、融資融券數據
- 市場指數、產業類股資訊

### 4. 即時通信

- WebSocket 推送交易事件
- Agent 狀態變更通知
- 市場資訊更新
- 錯誤與警告訊息

---

## 📚 文檔導覽

### 依角色閱讀建議

**系統架構師 / 技術主管**:

1. 閱讀本文件了解專案全貌
2. `docs/SYSTEM_DESIGN.md` - 系統設計規範與高層架構
3. `docs/AGENTS_ARCHITECTURE.md` - Agent 模組架構
4. `docs/API_ARCHITECTURE.md` - API 模組架構
5. `docs/FRONTEND_ARCHITECTURE.md` - 前端模組架構

**後端工程師**:

1. `docs/SYSTEM_DESIGN.md` - 系統設計概覽
2. `docs/AGENT_IMPLEMENTATION.md` - Agent 詳細實作規格
3. `docs/API_IMPLEMENTATION.md` - API 詳細實作規格
4. `docs/AGENTS_ARCHITECTURE.md` - Agent 架構深入了解

**前端工程師**:

1. `docs/SYSTEM_DESIGN.md` - 系統設計概覽
2. `docs/FRONTEND_IMPLEMENTATION.md` - 前端詳細實作規格
3. `docs/FRONTEND_ARCHITECTURE.md` - 前端架構深入了解
4. `docs/API_IMPLEMENTATION.md` - API 介面規格

**DevOps 工程師**:

1. `docs/DEPLOYMENT_GUIDE.md` - 部署和配置詳細指南
2. `docs/SYSTEM_DESIGN.md` - 系統架構了解
3. `docs/PROJECT_STRUCTURE.md` - 專案結構規範

### 文檔結構說明

- **README.md** - 專案概覽、快速開始、文檔導覽（本文件）
- **SYSTEM_DESIGN.md** - 系統設計規範與高層架構
- **\*\_IMPLEMENTATION.md** - 各模組詳細實作規格
- **\*\_ARCHITECTURE.md** - 各模組架構深入說明
- **DEPLOYMENT_GUIDE.md** - 部署和配置詳細指南
- **PROJECT_STRUCTURE.md** - 專案結構規範

---

## 🔧 開發指南

### 程式碼風格

本專案遵循以下編碼規範：

- **Python**: PEP 8, Ruff 格式化, Type Hints
- **JavaScript**: ESLint, Prettier, JSDoc 註解
- **Svelte**: Prettier + Svelte Plugin

### 提交規範

使用語義化提交訊息：

```text
feat: 新增功能
fix: 修復錯誤
docs: 文檔更新
style: 程式碼格式調整
refactor: 重構程式碼
test: 測試相關
chore: 建置或輔助工具變更
```

### 分支策略

- `main`: 穩定版本
- `develop`: 開發版本
- `feature/*`: 功能開發
- `bugfix/*`: 錯誤修復
- `hotfix/*`: 緊急修復

### 測試策略

- **單元測試**: 測試個別元件功能
- **整合測試**: 測試元件間互動
- **端對端測試**: 測試完整流程
- **測試覆蓋率目標**: >= 80%

---

## 🚧 開發狀態

### 已完成功能 (✅)

- **Phase 1**: 資料層與基礎設施
  - SQLite 資料庫結構
  - MCP 整合與市場資料工具
  - Agent 基礎架構
- **Phase 2**: AI 代理人系統
  - 專業分析 Agent（基礎、技術、風險、情緒）
  - 投資組合查詢功能
  - 策略追蹤系統
- **Phase 3**: Web API 服務
  - FastAPI REST API
  - WebSocket 即時通信
  - Agent 管理 API
  - 交易 API

### 開發中功能 (⏳)

- **Phase 4**: 前端介面（準備中，預計 2025-10-10 開始）
  - Svelte 元件開發
  - Chart.js 圖表整合
  - WebSocket 客戶端
  - 響應式設計

### 未來規劃 (📋)

- 更多 AI 模型支援
- 進階技術指標分析
- 回測系統
- 績效報表與排行榜
- 多用戶支援

---

## 🤝 貢獻指南

歡迎貢獻！請遵循以下步驟：

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

### 貢獻準則

- 遵循專案編碼規範
- 新增功能需包含測試
- 更新相關文檔
- 提交前執行測試確保通過

---

## 📄 授權

本專案採用 MIT 授權條款。詳見 [LICENSE](LICENSE) 檔案。

---

## 📧 聯絡方式

- **專案維護者**: sacahan
- **專案網址**: [https://github.com/sacahan/CasualTrader](https://github.com/sacahan/CasualTrader)
- **問題回報**: [GitHub Issues](https://github.com/sacahan/CasualTrader/issues)

---

## 🙏 致謝

感謝以下專案和服務：

- [OpenAI Agent SDK](https://github.com/openai/openai-agents) - AI 代理人框架
- [FastAPI](https://fastapi.tiangolo.com/) - 現代化 Web 框架
- [Svelte](https://svelte.dev/) - 創新的前端框架
- [casual-market-mcp](https://github.com/casualtrader/casual-market-mcp) - 台灣股市資料工具

---

**最後更新**: 2025-10-10
**版本**: 1.0.0
**維護者**: sacahan
