# 關鍵問題修復計劃

## 問題診斷

### 1. API與Agent參數不匹配

#### API模型 (src/api/models.py - CreateAgentRequest)

- `ai_model`: AIModel enum
- `strategy_type`: StrategyType enum
- `strategy_prompt`: str
- `risk_tolerance`: float (0.0-1.0)
- `enabled_tools`: EnabledTools (Pydantic模型)
- `investment_preferences`: InvestmentPreferences (Pydantic模型)

#### Agent模型 (src/agents/core/models.py - AgentConfig)

- `model`: str (不是ai_model!)
- `instructions`: str (不是strategy_prompt!)
- `investment_preferences.risk_tolerance`: str ("low"/"medium"/"high", 不是float!)
- `investment_preferences`: InvestmentPreferences (dataclass, 不是Pydantic!)
- `enabled_tools`: dict[str, bool]

### 2. 數據轉換問題

在 `src/api/routers/agents.py` 第103-115行的轉換邏輯有誤：

```python
config = AgentConfig(
    name=request.name,
    description=request.description,
    model=request.ai_model.value,  # ✅ 正確
    initial_funds=request.initial_funds,  # ✅ 正確
    max_turns=request.max_turns,  # ✅ 正確
    instructions=request.strategy_prompt,  # ✅ 正確
    additional_instructions=request.custom_instructions,  # ✅ 正確
    enabled_tools=request.enabled_tools.model_dump(),  # ✅ 正確
)
```

**缺少的轉換**:

- ❌ strategy_type 沒有傳遞
- ❌ risk_tolerance 沒有轉換 (float -> str)
- ❌ investment_preferences 沒有正確轉換

## 修復計劃

### Step 1: 統一數據模型

- 修改 `src/agents/core/models.py` 使 InvestmentPreferences 支援 strategy_type
- 添加 risk_tolerance 轉換函數

### Step 2: 修復API Router

- 正確轉換所有參數
- 添加驗證和錯誤處理

### Step 3: 建立端到端測試

- 測試 API -> Agent Manager -> Trading Agent 完整流程
- 驗證數據在每一層都正確轉換
- 測試實際執行功能

### Step 4: 修復現有測試

- 更新所有 mock 數據以匹配實際結構
- 添加參數驗證測試
