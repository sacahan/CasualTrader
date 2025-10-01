# Market MCP Server

台灣股價即時查詢 MCP Server，提供透過 Model Context Protocol 存取台灣證券交易所即時股價資訊的功能。

## 功能特色

- 🚀 **即時股價查詢** - 整合台灣證交所 API 提供即時股票資訊
- 🛡️ **API 頻率限制** - 多層次頻率控制，保護 API 避免過度呼叫
- 💾 **智能快取** - 本地記憶體快取，提升查詢速度
- 🔧 **uvx 執行** - 支援 uvx 本地執行，無需複雜部署
- 📊 **MCP 協議** - 完全遵循 Model Context Protocol 標準

## 快速開始

### 前置需求

確保已安裝 uv 套件管理器：

```bash
# 安裝 uv (包含 uvx)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 驗證安裝
uvx --version
```

### 使用 uvx 執行 (推薦)

```bash
# 直接執行 MCP 伺服器
uvx --from /path/to/CasualTrader market-mcp-server

# 或在專案目錄內執行
cd /path/to/CasualTrader
uvx --from . market-mcp-server
```

**uvx 優勢：**

- 🚀 簡化的命令語法
- ⚡ 自動依賴管理
- 🔒 環境隔離，避免依賴衝突

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

### 測試驗證

```bash
# 執行基本測試
uv run python tests/debug_api.py

# 驗證 MCP 伺服器
./tests/verify-mcp-server.sh

# uvx 完整測試套件
./tests/test_uvx_execution.sh
```

## MCP 客戶端整合

### Claude Desktop 整合

#### 設定檔案位置

**macOS:**

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**

```
%APPDATA%\Claude\claude_desktop_config.json
```

#### 推薦設定 (uvx)

```json
{
  "mcpServers": {
    "casualtrader": {
      "command": "uvx",
      "args": [
        "--from",
        "/Users/sacahan/Documents/workspace/CasualTrader",
        "market-mcp-server"
      ],
      "env": {
        "MARKET_MCP_SERVER_VERSION": "1.0.0"
      }
    }
  }
}
```

#### 替代設定 (uv run)

```json
{
  "mcpServers": {
    "casualtrader": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/sacahan/Documents/workspace/CasualTrader",
        "run",
        "python",
        "-m",
        "market_mcp.server"
      ],
      "env": {
        "MARKET_MCP_SERVER_VERSION": "1.0.0"
      }
    }
  }
}
```

#### 重啟 Claude Desktop

設定完成後，重啟 Claude Desktop 應用程式以載入新的 MCP 伺服器。

### VS Code MCP 擴充功能整合

#### 安裝 MCP 擴充功能

在 VS Code 中搜尋並安裝 "Model Context Protocol" 擴充功能。

#### 工作區設定

在 `.vscode/settings.json` 中添加：

**推薦使用 uvx:**

```json
{
  "mcp.servers": [
    {
      "name": "casualtrader",
      "command": "uvx",
      "args": ["--from", "/path/to/CasualTrader", "market-mcp-server"],
      "env": {
        "MARKET_MCP_SERVER_VERSION": "1.0.0"
      }
    }
  ]
}
```

### 通用 MCP 客戶端整合

任何支援 MCP 協議的客戶端都可以使用以下方式啟動伺服器：

**使用 uvx (推薦):**

```bash
# 直接使用 uvx 執行
uvx --from /path/to/CasualTrader market-mcp-server

# 或設定為 JSON-RPC 進程
uvx --from /path/to/CasualTrader market-mcp-server --stdio
```

**使用 uv run (替代方案):**

```bash
# 使用 uv run
uv --directory /path/to/CasualTrader run python -m market_mcp.server

# 或使用 Python 直接執行
cd /path/to/CasualTrader
python -m market_mcp.server
```

## 支援的工具

### `get_taiwan_stock_price`

取得台灣股票即時價格資訊。

**參數：**

- `symbol` (string): 台灣股票代號 (4位數字，例如: 2330)

**使用範例：**

```json
{
  "tool": "get_taiwan_stock_price",
  "arguments": {
    "symbol": "2330"
  }
}
```

**回應格式：**

成功回應包含完整的股票資訊：

```
✅ 已取得 台灣積體電路製造股份有限公司 (2330) 的股價資訊

📈 **台灣積體電路製造股份有限公司 (2330)**
💰 **目前價格:** NT$ 595.00
📈 **漲跌:** +5.00 (+0.85%)
📊 **開盤:** NT$ 590.00
📊 **最高:** NT$ 598.00
📊 **最低:** NT$ 588.00
📊 **昨收:** NT$ 590.00
📦 **成交量:** 25.6K
🔺 **漲停價:** NT$ 649.00
🔻 **跌停價:** NT$ 531.00

📋 **五檔資訊:**
  買1: 594.00  |  賣1: 595.00
  買2: 593.00  |  賣2: 596.00
  買3: 592.00  |  賣3: 597.00
  買4: 591.00  |  賣4: 598.00
  買5: 590.00  |  賣5: 599.00

⏰ **更新時間:** 2025-09-30T14:30:00
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

## 錯誤處理

### 常見錯誤

#### 1. 股票代號格式錯誤

```
❌ 錯誤: 股票代號格式不正確，請輸入 4 位數字 (例如: 2330)
🔍 錯誤代碼: E001
📋 錯誤類型: VALIDATION_ERROR
```

**解決方案:**

- 確認股票代號是 4 位數字
- 常見範例: 2330 (台積電), 2317 (鴻海)

#### 2. 找不到股票

```
❌ 錯誤: 找不到指定的股票代號
🔍 錯誤代碼: E002
📋 錯誤類型: SYMBOL_NOT_FOUND
```

**解決方案:**

- 檢查股票代號是否正確
- 該股票可能已下市或暫停交易

#### 3. API 頻率限制

```
❌ 錯誤: API 請求頻率過高，請稍後再試
🔍 錯誤代碼: E004
📋 錯誤類型: RATE_LIMIT_ERROR
```

**解決方案:**

- 稍等片刻後再試
- 避免短時間內大量查詢

## 進階配置

### 環境變數設定

透過環境變數自訂伺服器設定：

```bash
# 伺服器版本
export MARKET_MCP_SERVER_VERSION=1.0.0

# 日誌等級
export LOG_LEVEL=INFO

# API 客戶端配置
export TWSE_API_TIMEOUT=30
export TWSE_API_RETRY_COUNT=3

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

### 日誌設定

日誌檔案位置：

- 標準輸出: 一般運作日誌
- 標準錯誤: 錯誤和警告

日誌等級：

- DEBUG: 詳細除錯資訊
- INFO: 一般操作資訊 (預設)
- WARNING: 警告訊息
- ERROR: 錯誤訊息

### 效能調整

#### 快取設定

MCP 伺服器支援內建快取機制，減少重複 API 呼叫：

```python
# 快取設定 (預設值)
CACHE_TTL = 10  # 快取存活時間 (秒)
MAX_CACHE_SIZE = 100  # 最大快取項目數
```

#### 併發處理

伺服器支援併發請求處理，但會自動限制 API 呼叫頻率以避免觸及限制。

## 故障排除

### 1. 伺服器無法啟動

檢查項目：

- Python 和 uv 是否正確安裝
- 專案目錄路徑是否正確
- 依賴是否完整安裝

```bash
# 診斷命令
uv --version
python --version
uv run python -c "import market_mcp; print('OK')"
```

### 2. uvx 未找到命令

```bash
# 重新載入 shell 環境
source ~/.bashrc  # 或 source ~/.zshrc

# 手動添加到 PATH (如果需要)
export PATH="$HOME/.cargo/bin:$PATH"
```

### 3. 專案依賴問題

```bash
# 更新專案依賴
uv sync

# 清除快取並重新安裝
uv cache clean
uv sync
```

### 4. 客戶端無法連接

檢查項目：

- MCP 設定檔案格式是否正確
- 檔案路徑是否存在
- 權限設定是否正確

```bash
# 測試伺服器是否正常運作
echo '{"method":"initialize","params":{}}' | uv run python -m market_mcp.server

# 檢查伺服器是否正常啟動
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | uvx --from . market-mcp-server

# 檢查日誌輸出
uvx --from . market-mcp-server --verbose
```

### 5. API 查詢失敗

檢查項目：

- 網路連線狀態
- 防火牆設定
- DNS 解析

```bash
# 測試網路連線
curl -I https://www.twse.com.tw/
ping www.twse.com.tw
```

## 最佳實務

### 1. 錯誤處理

總是檢查工具回應的狀態，適當處理錯誤情況：

```javascript
// 客戶端處理範例
try {
  const result = await mcpClient.callTool("get_taiwan_stock_price", {
    symbol: "2330",
  });

  if (result.isError) {
    console.error("查詢失敗:", result.error);
    // 根據錯誤類型提供適當的使用者回饋
  } else {
    console.log("股價資訊:", result.content);
  }
} catch (error) {
  console.error("MCP 連線錯誤:", error);
}
```

### 2. 頻率控制

避免過於頻繁的查詢請求：

```javascript
// 實作簡單的頻率控制
const rateLimiter = {
  lastCall: 0,
  minInterval: 1000, // 1秒最小間隔

  async callTool(symbol) {
    const now = Date.now();
    const timeSinceLastCall = now - this.lastCall;

    if (timeSinceLastCall < this.minInterval) {
      await new Promise((resolve) =>
        setTimeout(resolve, this.minInterval - timeSinceLastCall),
      );
    }

    this.lastCall = Date.now();
    return await mcpClient.callTool("get_taiwan_stock_price", { symbol });
  },
};
```

### 3. 使用者體驗

提供清晰的載入狀態和錯誤訊息：

```javascript
// 使用者介面處理範例
async function queryStock(symbol) {
  showLoading("查詢股價中...");

  try {
    const result = await mcpClient.callTool("get_taiwan_stock_price", {
      symbol: symbol.trim(),
    });

    hideLoading();
    displayStockInfo(result);
  } catch (error) {
    hideLoading();
    showError(`查詢失敗: ${error.message}`);
  }
}
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
