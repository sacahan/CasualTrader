# MCP 整合指南

CasualTrader MCP 伺服器提供標準化的股票價格查詢工具，本指南說明如何與各種 MCP 客戶端整合。

## 🚀 快速開始

### 1. 安裝和設定

```bash
# 克隆專案
git clone <repository-url>
cd CasualTrader

# 安裝依賴
uv install

# 驗證安裝
uv run python -m market_mcp.server --help
```

### 2. 測試伺服器

```bash
# 執行基本測試
uv run python debug_api.py

# 驗證 MCP 伺服器
./verify-mcp-server.sh
```

## 🔧 客戶端整合

### Claude Desktop 整合

#### 1. 設定檔案位置

**macOS:**

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**

```
%APPDATA%\Claude\claude_desktop_config.json
```

#### 2. 設定內容

**推薦使用 uvx (簡化版本):**

```json
{
  "mcpServers": {
    "casualtrader": {
      "command": "uvx",
      "args": [
        "--from",
        "/path/to/CasualTrader",
        "market-mcp-server"
      ],
      "env": {
        "MARKET_MCP_SERVER_VERSION": "1.0.0"
      }
    }
  }
}
```

**替代方案使用 uv run:**

```json
{
  "mcpServers": {
    "casualtrader": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/CasualTrader",
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

#### 3. 重啟 Claude Desktop

設定完成後，重啟 Claude Desktop 應用程式以載入新的 MCP 伺服器。

### VS Code MCP 擴充功能整合

#### 1. 安裝 MCP 擴充功能

在 VS Code 中搜尋並安裝 "Model Context Protocol" 擴充功能。

#### 2. 工作區設定

**推薦使用 uvx:**

在 `.vscode/settings.json` 中添加：

```json
{
  "mcp.servers": [
    {
      "name": "casualtrader",
      "command": "uvx",
      "args": [
        "--from",
        "/path/to/CasualTrader",
        "market-mcp-server"
      ],
      "env": {
        "MARKET_MCP_SERVER_VERSION": "1.0.0"
      }
    }
  ]
}
```

**替代方案使用 uv run:**

```json
{
  "mcp.servers": [
    {
      "name": "casualtrader",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/CasualTrader", 
        "run",
        "python",
        "-m",
        "market_mcp.server"
      ],
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

## 🛠️ 工具使用說明

### get_taiwan_stock_price

查詢台灣股票即時價格資訊。

#### 參數

- `symbol` (string, 必要): 4位數字的台灣股票代號

#### 範例

```json
{
  "tool": "get_taiwan_stock_price",
  "arguments": {
    "symbol": "2330"
  }
}
```

#### 回應格式

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

## 🚨 錯誤處理

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

## 🔧 進階配置

### 環境變數

```bash
# 伺服器版本
export MARKET_MCP_SERVER_VERSION=1.0.0

# 日誌等級
export LOG_LEVEL=INFO

# API 客戶端配置
export TWSE_API_TIMEOUT=30
export TWSE_API_RETRY_COUNT=3
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

#### 1. 快取設定

MCP 伺服器支援內建快取機制，減少重複 API 呼叫：

```python
# 快取設定 (預設值)
CACHE_TTL = 10  # 快取存活時間 (秒)
MAX_CACHE_SIZE = 100  # 最大快取項目數
```

#### 2. 併發處理

伺服器支援併發請求處理，但會自動限制 API 呼叫頻率以避免觸及限制。

## 📝 最佳實務

### 1. 錯誤處理

總是檢查工具回應的狀態，適當處理錯誤情況：

```javascript
// 客戶端處理範例
try {
  const result = await mcpClient.callTool('get_taiwan_stock_price', {
    symbol: '2330'
  });
  
  if (result.isError) {
    console.error('查詢失敗:', result.error);
    // 根據錯誤類型提供適當的使用者回饋
  } else {
    console.log('股價資訊:', result.content);
  }
} catch (error) {
  console.error('MCP 連線錯誤:', error);
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
      await new Promise(resolve => 
        setTimeout(resolve, this.minInterval - timeSinceLastCall)
      );
    }
    
    this.lastCall = Date.now();
    return await mcpClient.callTool('get_taiwan_stock_price', { symbol });
  }
};
```

### 3. 使用者體驗

提供清晰的載入狀態和錯誤訊息：

```javascript
// 使用者介面處理範例
async function queryStock(symbol) {
  showLoading('查詢股價中...');
  
  try {
    const result = await mcpClient.callTool('get_taiwan_stock_price', {
      symbol: symbol.trim()
    });
    
    hideLoading();
    displayStockInfo(result);
    
  } catch (error) {
    hideLoading();
    showError(`查詢失敗: ${error.message}`);
  }
}
```

## 🆘 故障排除

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

### 2. 客戶端無法連接

檢查項目：

- MCP 設定檔案格式是否正確
- 檔案路徑是否存在
- 權限設定是否正確

```bash
# 測試伺服器是否正常運作
echo '{"method":"initialize","params":{}}' | uv run python -m market_mcp.server
```

### 3. API 查詢失敗

檢查項目：

- 網路連線狀態
- 防火牆設定
- DNS 解析

```bash
# 測試網路連線
curl -I https://www.twse.com.tw/
ping www.twse.com.tw
```

## 📞 技術支援

如需技術支援，請提供以下資訊：

1. **系統資訊:**
   - 作業系統版本
   - Python 版本
   - uv 版本

2. **錯誤資訊:**
   - 完整錯誤訊息
   - 操作步驟
   - 預期結果vs實際結果

3. **設定資訊:**
   - MCP 設定檔內容
   - 環境變數設定
   - 日誌輸出

## 🔄 更新說明

### 版本 1.0.0

- 初始 MCP 工具介面實作
- 支援台灣股票價格查詢
- 完整的錯誤處理和驗證
- Claude Desktop 和 VS Code 整合支援

---

更多詳細資訊請參考：

- [API 文件](./api_documentation.md)
- [開發者指南](../README.md)
- [範例程式碼](../examples/)
