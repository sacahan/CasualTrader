# 測試執行指南

## 問題總結

之前的測試未能發現API與Agent之間的參數不匹配問題，主要原因：

1. **Mock過度**: 測試大量使用mock，沒有真實驗證數據轉換
2. **缺少端到端測試**: 沒有測試完整的API → Agent Manager → Trading Agent流程
3. **參數轉換錯誤**:
   - `ai_model` vs `model`
   - `strategy_prompt` vs `instructions`
   - `risk_tolerance` float vs str
   - `strategy_type` 沒有傳遞到Agent

## 已修復的問題

### 1. Agent模型擴展 (`src/agents/core/models.py`)

- ✅ `InvestmentPreferences` 添加 `strategy_type` 字段
- ✅ 添加 `risk_tolerance_from_float()` 轉換方法
- ✅ 添加 `risk_tolerance_to_float()` 反向轉換方法

### 2. API Router修復 (`src/api/routers/agents.py`)

- ✅ 正確轉換 `risk_tolerance` (float → str)
- ✅ 正確傳遞 `strategy_type`
- ✅ 正確創建 `InvestmentPreferences` dataclass
- ✅ 簡化創建流程，移除重複代碼

### 3. Agent Manager修復 (`src/agents/core/agent_manager.py`)

- ✅ `list_agents()` 改為返回 `list[dict]` 而非 `list[str]`
- ✅ `get_agent()` 改為返回 `dict` 而非 `CasualTradingAgent`
- ✅ 添加 `get_agent_instance()` 用於內部獲取實例
- ✅ 添加 `_agent_to_dict()` 統一轉換邏輯

## 測試執行方式

### 選項 1: 執行端到端測試

```bash
# 運行新建的端到端測試
python -m pytest tests/test_e2e_api_integration.py -v -s

# 或使用測試腳本
python scripts/run_e2e_tests.py
```

### 選項 2: 啟動API服務器進行手動測試

```bash
# 啟動API服務器
uvicorn src.api.server:app --reload --port 8000

# 在另一個終端執行測試請求
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試代理",
    "ai_model": "gpt-4o",
    "strategy_type": "balanced",
    "strategy_prompt": "測試策略",
    "risk_tolerance": 0.5
  }'
```

### 選項 3: 使用Python直接測試

```python
from fastapi.testclient import TestClient
from src.api.app import create_app

client = TestClient(create_app())

response = client.post("/api/agents", json={
    "name": "測試代理",
    "ai_model": "gpt-4o",
    "strategy_type": "balanced",
    "strategy_prompt": "測試策略",
    "risk_tolerance": 0.5
})

print(response.json())
```

## 測試覆蓋範圍

### ✅ 已測試

1. API參數到Agent參數的轉換
2. Risk tolerance的float ↔ str轉換
3. Strategy type的正確傳遞
4. InvestmentPreferences的正確構建
5. 參數驗證（無效值的拒絕）
6. Agent列表和檢索的正確格式

### ⚠️ 待測試

1. Agent實際執行功能
2. 交易工具的正確調用
3. WebSocket事件廣播
4. 數據庫持久化
5. 併發Agent執行
6. 錯誤恢復機制

## 預期結果

### 成功標準

- ✅ 所有端到端測試通過
- ✅ API輸入參數正確轉換為Agent配置
- ✅ Agent創建成功且狀態正確
- ✅ 可以檢索到創建的Agent且數據一致
- ✅ 參數驗證正確拒絕無效輸入

### 失敗處理

如果測試失敗：

1. 檢查錯誤日誌中的參數不匹配
2. 驗證數據轉換邏輯
3. 確認模型定義的一致性
4. 查看完整的stack trace

## 下一步

1. **運行端到端測試** - 驗證所有修復
2. **啟動API服務器** - 進行手動驗證
3. **檢查日誌** - 確認沒有警告或錯誤
4. **更新其他測試** - 修復使用舊API的測試
5. **文檔更新** - 記錄API與Agent的參數映射

## 參數映射表

| API字段 | API類型 | Agent字段 | Agent類型 | 轉換邏輯 |
|---------|---------|-----------|-----------|----------|
| ai_model | AIModel enum | model | str | .value |
| strategy_prompt | str | instructions | str | 直接 |
| strategy_type | StrategyType enum | investment_preferences.strategy_type | str | .value |
| risk_tolerance | float (0.0-1.0) | investment_preferences.risk_tolerance | str | from_float() |
| enabled_tools | EnabledTools | enabled_tools | dict | .model_dump() |
| investment_preferences | InvestmentPreferences | investment_preferences | dataclass | 重新構建 |

## 常見問題

### Q: 為什麼之前的測試沒發現這些問題？

A: 因為使用了過多的mock，沒有真實執行數據轉換流程。

### Q: 如何確保未來不再出現類似問題？

A: 維護端到端測試，減少mock使用，定期運行完整測試套件。

### Q: 參數轉換的性能影響？

A: 轉換開銷極小，主要是字符串操作和對象構建。
