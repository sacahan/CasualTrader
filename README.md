# Market MCP Server

台灣股價即時查詢 MCP Server，提供透過 Model Context Protocol 存取台灣證券交易所即時股價資訊的功能。

## 功能特色

- 🚀 **即時股價查詢** - 整合台灣證交所 API 提供即時股票資訊
- 🛡️ **API 頻率限制** - 多層次頻率控制，保護 API 避免過度呼叫
- 💾 **智能快取** - 本地記憶體快取，提升查詢速度
- 🔧 **uvx 執行** - 支援 uvx 本地執行，無需複雜部署
- 📊 **MCP 協議** - 完全遵循 Model Context Protocol 標準

## 快速開始

### 使用 uvx 執行 (推薦)

```bash
# 直接執行 (首次會自動安裝相依性)
uvx --from . market-mcp-server
```

### 開發環境安裝

```bash
# 使用 uv 管理環境
uv sync --dev

# 執行測試
uv run pytest

# 程式碼檢查
uv run ruff check
uv run mypy market_mcp
```

## MCP 客戶端整合

### Claude Desktop

在 Claude Desktop 的設定檔案中新增：

```json
{
  "mcpServers": {
    "market": {
      "command": "uvx",
      "args": ["--from", ".", "market-mcp-server"]
    }
  }
}
```

## 支援的工具

### `get_taiwan_stock_price`

取得台灣股票即時價格資訊。

**參數：**

- `symbol` (string): 台灣股票代號 (4位數字，例如: 2330)

**回應範例：**

```json
{
  "symbol": "2330",
  "company_name": "台積電",
  "current_price": 1305.0,
  "change": 5.0,
  "change_percent": 0.38,
  "volume": 36584,
  "update_time": "2025-09-30T14:30:00Z"
}
```

## 專案結構

```
market_mcp/
├── __init__.py          # 套件初始化
├── main.py              # uvx 執行入口點
├── server.py            # MCP Server 核心實作
├── config.py            # 設定管理
└── utils/
    ├── __init__.py
    └── logging.py       # 日誌工具

tests/                   # 測試檔案
├── __init__.py
└── test_server.py       # 基礎架構測試

specs/                   # 專案規劃文件
├── prd/                 # 產品需求文件
├── tsd/                 # 技術規格文件
├── epics/               # Epic 規劃
└── tasks/               # 開發任務
```

## 開發狀態

- [x] **Task-001**: MCP Server 基礎架構建立
- [ ] **Task-002**: 台灣證交所 API 整合
- [ ] **Task-003**: API 頻率限制和快取系統  
- [ ] **Task-004**: MCP 工具介面和資料格式標準化

## 設定選項

透過環境變數自訂伺服器設定：

```bash
# API 設定
export MARKET_MCP_API_TIMEOUT=5
export MARKET_MCP_API_RETRIES=3

# 頻率限制
export MARKET_MCP_RATE_LIMIT_PER_SYMBOL=30
export MARKET_MCP_RATE_LIMIT_GLOBAL_PER_MINUTE=20

# 快取設定
export MARKET_MCP_CACHE_TTL=30
export MARKET_MCP_CACHE_MAXSIZE=1000

# 日誌設定
export MARKET_MCP_LOG_LEVEL=INFO
```

## SpecPilot 開發工作流

此專案使用 SpecPilot 進行 AI 驅動的規格管理和任務執行：

### 工作流程指令

```bash
# 檢視專案狀態
./scripts/specpilot-workflow.sh status

# 開始執行任務
./scripts/specpilot-workflow.sh start-task <task-id>

# 完成任務
./scripts/specpilot-workflow.sh complete-task

# 檢視下一個建議動作
./scripts/specpilot-workflow.sh next-action
```

### 規劃文件

- **PRD**: 產品需求文件 (`specs/prd/`)
- **TSD**: 技術規格文件 (`specs/tsd/`)
- **Epic**: 功能模組分解 (`specs/epics/`)
- **Task**: 具體開發任務 (`specs/tasks/`)

## 授權

MIT License
