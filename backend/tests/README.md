# CasualTrader Backend Tests

## 📁 測試架構

測試已按照分層架構組織，遵循 Unit / Integration / E2E 最佳實踐。

### 測試結構

```text
tests/
├── unit/                    # 單元測試 (20-30%)
│   ├── conftest.py         # 單元級 fixtures (Mock 一切)
│   └── test_*.py
│
├── integration/            # 整合測試 (30-40%)
│   ├── conftest.py         # 整合級 fixtures (Mock 外部 API)
│   └── test_*.py
│
└── e2e/                    # E2E 測試 (30-50%)
    ├── conftest.py         # E2E 級 fixtures
    └── test_*.py
```

### 各層級特點

| 層級 | 目的 | Mock 策略 | 執行時間 | 測試數量 |
|------|------|----------|---------|---------|
| **Unit** | 測試個別方法 | Mock 一切 | < 100ms | 20-30% |
| **Integration** | 測試多個組件交互 | Mock 外部依賴 | 0.5-2s | 30-40% |
| **E2E** | 測試完整工作流 | Mock 外部服務 | 2-5s | 30-50% |

---

## 🚀 快速開始

### 常見命令速查表

```bash
# 快速開發 - 只測試單元 (~1秒)
pytest tests/unit/ -v

# 驗證功能 - 單元 + 整合 (~3秒)
pytest tests/unit/ tests/integration/ -v

# 完整驗證 - 所有層級 (~8秒)
pytest tests/ -v

# 顯示打印輸出
pytest tests/ -v -s

# 只執行某個測試文件
pytest tests/unit/test_core_imports.py -v

# 只執行某個測試函數
pytest tests/unit/test_core_imports.py::test_import_core_modules -v

# 執行失敗的測試
pytest tests/ --lf

# 執行新的測試
pytest tests/ --ff

# 生成覆蓋率報告
pytest tests/ --cov=src --cov-report=html
```

### 決策樹：選擇測試層級

根據你修改的內容選擇執行的測試層級：

```text
你修改了什麼？

├─ 單個函數或類的邏輯 ✓ 不涉及其他模組
│  └─> 執行 Unit 層
│      pytest tests/unit/ -v
│      ⏱️ ~1秒 ⚡
│
├─ 多個模組間的交互
│  └─> 執行 Unit + Integration 層
│      pytest tests/unit/ tests/integration/ -v
│      ⏱️ ~3秒 ⚡
│
└─ API 端點、工作流、系統層面
   └─> 執行全部層
       pytest tests/ -v
       ⏱️ ~8秒
```

---

## 👨‍💻 開發工作流程

### 第一步：啟動開發

```bash
# 進入項目目錄
cd backend/

# 確保依賴已安裝
uv sync

# 啟動快速開發模式（只執行單元測試）
pytest tests/unit/ -v
```

**預期結果**: ✅ ~1秒內看到所有單元測試通過

### 第二步：修改代碼

修改你的代碼，然後立即運行測試。

### 第三步：快速驗證

```bash
# 只執行相關的單元測試
pytest tests/unit/ -v -s

# 看到紅色 ❌ 表示測試失敗
# 修改代碼使其通過
```

**時間成本**: ~1秒 × N 次迭代 = 迅速反饋迴圈

### 第四步：完整功能驗證

當準備提交時，運行完整測試套件：

```bash
# 完整驗證
pytest tests/ -v

# 確保所有層級都通過
```

---

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

- `DEFAULT_AI_MODEL` - AI 模型名稱（預設: gpt-4）
- `DEFAULT_MAX_TURNS` - 最大執行輪數（預設: 5）
- `DEFAULT_AGENT_TIMEOUT` - Agent 超時時間（預設: 30）
- `DEFAULT_MODEL_TEMPERATURE` - 模型溫度參數（預設: 0.7）

### 各層級 Fixtures

**Unit 層** (tests/unit/conftest.py - Mock 一切):

```python
- mock_db_session          # AsyncMock 數據庫
- mock_agent_config        # Mock Agent 配置
- mock_trading_agent       # Mock 交易代理
```

**Integration 層** (tests/integration/conftest.py - Mock 外部 API):

```python
- test_db_session          # 實際 SQLite 數據庫
- mock_mcp_client          # Mock MCP API
- mock_trading_service     # Mock 交易服務
```

**E2E 層** (tests/e2e/conftest.py):

```python
- mocked_services          # 模擬的外部服務
- real_database            # 實際數據庫連接
```

---

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

---

## � 添加新測試

### 測試文件命名規則

- 所有測試文件以 `test_` 開頭
- 使用描述性名稱，例如 `test_trading_integration.py`
- 放在相應的層級目錄中（unit / integration / e2e）

### 測試函數命名規則

- 測試函數以 `test_` 開頭
- 使用描述性名稱，例如 `test_create_transaction()`
- 使用格式：`test_<component>_<scenario>_<expected_result>`

### 示例測試結構

```python
#!/usr/bin/env python3
"""
測試描述

Scenario: 驗證某個功能
Given: 初始條件
When: 執行某個操作
Then: 預期結果
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_feature_behavior():
    """測試特定功能的行為"""
    # Arrange: 設置測試數據
    mock_db = AsyncMock()
    mock_db.query.return_value = [{"id": 1}]

    # Act: 執行要測試的功能
    result = await some_function(mock_db)

    # Assert: 驗證結果
    assert result is not None
    assert mock_db.query.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 測試指引

遵循 `.github/instructions/test.instructions.md` 中的測試標準：

- **Mock 只外部依賴** - 數據庫、API、文件系統
- **測試真實業務邏輯** - 不 mock 核心功能
- **驗證完整工作流** - unit + integration + E2E
- **測試生命週期** - 初始化、清理、狀態轉換
- **編寫有意義的測試** - 在生產環境失敗時也會失敗

---

## 🐛 故障排除

### 導入錯誤

如果遇到導入錯誤，確保：

1. 從 backend 目錄運行測試
2. 已安裝所有依賴項 (`uv sync`)
3. Python 路徑配置正確

### 數據庫錯誤

某些測試可能需要數據庫連接。確保：

1. 數據庫服務正在運行
2. 數據庫連接配置正確
3. 測試數據庫已創建

### 超時問題

如果測試超時：

1. 檢查 `DEFAULT_AGENT_TIMEOUT` 環境變量
2. 考慮增加 pytest 超時時間
3. 檢查是否有外部 API 調用速度慢

---

## 📊 測試結果示例

```bash
🚀 開始 CasualTrader 測試套件

============================================================
📦 測試模組導入
============================================================
✅ TradingAgent 導入成功
✅ AgentsService 導入成功
✅ TradingService 導入成功
✅ Enums 導入成功
✅ Database Models 導入成功

============================================================
🔍 Unit 層測試
============================================================
✅ test_agent_initialization_check
✅ test_trading_transaction_creation
✅ test_fund_calculation

============================================================
� Integration 層測試
============================================================
✅ test_service_manages_agent_lifecycle
✅ test_database_session_handling

============================================================
🔍 E2E 層測試
============================================================
✅ test_e2e_initialization_flow
✅ test_e2e_agent_execution_and_cleanup

🎉 所有測試通過！系統已準備就緒！
```

---

## 📚 相關文檔

- [Testing Guidelines](.github/instructions/test.instructions.md) - 詳細測試標準
- [Python Development Standards](.github/instructions/python.instructions.md)
- [Timestamp Management](.github/instructions/timestamp.instructions.md)

---

**最後更新**: 2025年10月22日
