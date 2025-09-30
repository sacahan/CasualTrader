# CasualTrader MCP Server - uvx 執行指南

## 📋 概述

此指南說明如何使用 `uvx` 來執行 CasualTrader MCP Server，這是推薦的執行方式，比傳統的 `uv run` 更簡潔和高效。

## 🚀 快速開始

### 前置需求

確保已安裝 uv 套件管理器：

```bash
# 安裝 uv (包含 uvx)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 驗證安裝
uvx --version
```

### 基本執行

```bash
# 直接執行 MCP 伺服器
uvx --from /path/to/CasualTrader market-mcp-server

# 或在專案目錄內執行
cd /path/to/CasualTrader
uvx --from . market-mcp-server
```

## 🔧 Claude Desktop 設定

### 推薦設定 (uvx)

在 Claude Desktop 設定檔中使用以下配置：

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

### 替代設定 (uv run)

如果需要使用傳統方式：

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

## 💡 uvx 優勢

### 1. 簡化的命令語法

```bash
# uvx 方式 - 簡潔
uvx --from . market-mcp-server

# uv run 方式 - 較複雜
uv run python -m market_mcp.server
```

### 2. 自動依賴管理

- uvx 自動處理專案依賴關係
- 無需手動指定 Python 模組路徑
- 使用 `pyproject.toml` 中定義的腳本入口點

### 3. 環境隔離

- 每次執行都使用乾淨的環境
- 避免不同專案間的依賴衝突
- 確保一致的執行環境

## 🧪 測試驗證

執行提供的測試腳本來驗證 uvx 設定：

```bash
# 執行完整測試套件
./test_uvx_execution.sh

# 測試包含：
# ✅ 專案結構驗證
# ✅ uvx 基本執行測試
# ✅ MCP 協議通信測試
# ✅ Claude Desktop 設定格式驗證
```

## 🔍 疑難排解

### uvx 未找到命令

```bash
# 重新載入 shell 環境
source ~/.bashrc  # 或 source ~/.zshrc

# 手動添加到 PATH (如果需要)
export PATH="$HOME/.cargo/bin:$PATH"
```

### 專案依賴問題

```bash
# 更新專案依賴
uv sync

# 清除快取並重新安裝
uv cache clean
uv sync
```

### MCP 連線問題

```bash
# 檢查伺服器是否正常啟動
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | uvx --from . market-mcp-server

# 檢查日誌輸出
uvx --from . market-mcp-server --verbose
```

## 📚 相關文件

- [MCP 整合指南](docs/mcp_integration_guide.md) - 完整的 MCP 客戶端整合說明
- [API 文件](docs/api_documentation.md) - 工具使用說明和範例
- [專案 README](../README.md) - 專案概述和設定說明

## 🎯 下一步

1. **設定 Claude Desktop**: 使用上述設定檔配置 Claude Desktop
2. **測試整合**: 在 Claude Desktop 中測試股票查詢功能
3. **自訂設定**: 根據需求調整環境變數和參數
4. **監控日誌**: 觀察伺服器運行狀態和效能

---

✨ **提示**: uvx 是執行 Python 應用程式的現代化方式，強烈推薦使用此方法來獲得最佳的使用體驗！
