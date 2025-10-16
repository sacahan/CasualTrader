# CasualTrader Backend Tests

## 📁 測試文件組織

本目錄包含 CasualTrader 後端的所有測試文件。

### 測試文件說明

#### 基礎導入測試

- **`test_import.py`** - 基礎 TradingAgent 導入測試
- **`test_imports.py`** - 全面的模組導入測試
- **`test_core_imports.py`** - 核心模組導入測試

#### 功能測試

- **`test_complete_verification.py`** - 完整功能驗證測試
  - 測試所有模組導入
  - 驗證 TradingAgent 結構
  - 驗證 AgentsService 結構
  - 確認所有已實作功能

- **`test_full_import.py`** - 完整導入和方法檢查測試

#### 交易工具測試

- **`test_trading_tools.py`** - 交易工具基礎測試
- **`test_trading_tools_standalone.py`** - 獨立交易工具測試
- **`test_trading_integration.py`** - 交易整合功能測試
  - 交易記錄功能
  - 持股更新功能
  - 績效計算功能
  - 資金更新功能

## 🚀 運行測試

### 運行所有測試

```bash
# 從 backend 目錄運行
cd /path/to/CasualTrader/backend
python -m pytest tests/
```

### 運行特定測試

```bash
# 基礎導入測試
python tests/test_import.py

# 完整驗證測試
python tests/test_complete_verification.py

# 交易整合測試
python tests/test_trading_integration.py
```

### 使用 pytest

```bash
# 運行所有測試
pytest tests/

# 運行特定測試文件
pytest tests/test_complete_verification.py

# 運行並顯示詳細輸出
pytest tests/ -v

# 運行並顯示打印輸出
pytest tests/ -s
```

## ✅ 測試覆蓋範圍

### 模組導入

- ✅ TradingAgent
- ✅ AgentsService
- ✅ TradingService
- ✅ Database Models
- ✅ Common Enums

### TradingAgent 功能

- ✅ 初始化 (initialize)
- ✅ 執行 (run)
- ✅ 停止 (stop)
- ✅ 清理 (cleanup)
- ✅ 狀態查詢 (get_status)

### AgentsService 方法

- ✅ create_transaction
- ✅ get_agent_holdings
- ✅ update_agent_holdings
- ✅ calculate_and_update_performance
- ✅ update_agent_funds

### 交易流程

- ✅ 交易記錄到資料庫
- ✅ 自動持股更新（成本平均法）
- ✅ 自動績效計算
- ✅ 自動資金餘額更新

### Sub-agents

- ✅ Technical Analysis Agent
- ✅ Sentiment Analysis Agent
- ✅ Fundamental Analysis Agent
- ✅ Risk Assessment Agent

## 📊 測試結果示例

```
🚀 開始 CasualTrader TradingAgent 完整測試

============================================================
📦 測試模組導入
============================================================
✅ TradingAgent 導入成功
✅ AgentsService 導入成功
✅ TradingService 導入成功
✅ Enums 導入成功
✅ Database Models 導入成功

============================================================
🔍 測試 TradingAgent 結構
============================================================
✅ 方法 initialize 存在
✅ 方法 run 存在
✅ 方法 stop 存在
✅ 方法 cleanup 存在
✅ 方法 get_status 存在

🎉 所有測試通過！TradingAgent 已準備就緒！
```

## 🔧 測試環境設置

### 先決條件

```bash
# 安裝依賴
pip install -e .
pip install pytest pytest-asyncio pytest-cov

# 確保 .env 文件配置正確
cp .env.example .env
# 編輯 .env 文件設置必要的環境變量
```

### 環境變量

測試需要以下環境變量：

- `DEFAULT_AI_MODEL` - AI 模型名稱
- `DEFAULT_MAX_TURNS` - 最大執行輪數
- `DEFAULT_AGENT_TIMEOUT` - Agent 超時時間
- `DEFAULT_MODEL_TEMPERATURE` - 模型溫度參數

## 📝 添加新測試

### 測試文件命名規則

- 所有測試文件以 `test_` 開頭
- 使用描述性名稱，例如 `test_trading_integration.py`

### 測試函數命名規則

- 測試函數以 `test_` 開頭
- 使用描述性名稱，例如 `test_create_transaction()`

### 示例測試結構

```python
#!/usr/bin/env python3
"""
測試描述
"""
import sys
import os

# 添加 backend 目錄到 sys.path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(backend_path))

def test_feature():
    """測試特定功能"""
    # 測試邏輯
    pass

if __name__ == "__main__":
    test_feature()
```

## 🐛 故障排除

### 導入錯誤

如果遇到導入錯誤，確保：

1. 從 backend 目錄運行測試
2. 已安裝所有依賴項
3. Python 路徑配置正確

### 數據庫錯誤

某些測試可能需要數據庫連接。確保：

1. 數據庫服務正在運行
2. 數據庫連接配置正確
3. 測試數據庫已創建

## 📚 相關文檔

- [TradingAgent 實作總結](../TRADING_AGENT_IMPLEMENTATION_SUMMARY.md)
- [Trading Tools 實作文檔](../TRADING_TOOLS_IMPLEMENTATION.md)
- [API 文檔](../docs/api.md)

---

**最後更新**: 2025年10月16日
