# AI 模型選擇功能規格

**版本**: 1.0
**日期**: 2025-10-06
**功能類型**: 新增功能

---

## 📋 功能概述

### 需求背景

為了提供更靈活的 AI 交易策略測試環境，系統需要支援多種主流 AI 模型的選擇與比較。用戶可以在創建 Trade Agent 時選擇不同的 AI 模型，系統會追蹤並記錄每個交易決策和策略變更時使用的模型資訊。

### 核心功能

1. **Agent 創建時選擇 AI 模型** - 提供下拉選單選擇所需的 AI 模型
2. **模型資訊持久化** - Agent 配置中保存所選模型
3. **執行時模型追蹤** - 交易和策略變更記錄中包含當前使用的模型
4. **前端模型顯示** - Agent 卡片顯示當前使用的 AI 模型

---

## 🤖 支援的 AI 模型

### OpenAI 系列

- **gpt-4o** (推薦，預設值)
  - 平衡性能與成本
  - 適合大多數交易場景
  
- **gpt-4o-mini** (成本優化)
  - 較低的 API 成本
  - 適合頻繁交易的場景
  
- **gpt-4-turbo**
  - 快速響應
  - 適合需要即時決策的場景

### Anthropic Claude 系列

- **claude-sonnet-4.5**
  - 高性能推理能力
  - 適合複雜的投資分析
  
- **claude-opus-4**
  - 最強推理能力
  - 適合需要深度分析的場景

### Google Gemini 系列

- **gemini-2.5-pro**
  - 多模態分析能力
  - 適合結合圖表分析的場景
  
- **gemini-2.0-flash**
  - 快速響應
  - 適合高頻交易場景

### 其他模型

- **deepseek-v3**
  - 開源替代方案
  
- **grok-2**
  - X (Twitter) 開發的模型

---

## 🎨 前端實作

### 1. Agent 創建表單 (AgentCreationForm.svelte)

#### 模型選擇下拉選單

```svelte
<div class="input-group">
  <label class="block text-sm font-medium text-gray-700 mb-2">AI 模型 *</label>
  <select
    bind:value={formData.ai_model}
    class="form-select w-full px-4 py-2 border border-gray-300 rounded-lg"
    required
  >
    <optgroup label="OpenAI">
      <option value="gpt-4o" selected>GPT-4o (推薦)</option>
      <option value="gpt-4o-mini">GPT-4o Mini (成本優化)</option>
      <option value="gpt-4-turbo">GPT-4 Turbo</option>
    </optgroup>
    <optgroup label="Anthropic Claude">
      <option value="claude-sonnet-4.5">Claude Sonnet 4.5</option>
      <option value="claude-opus-4">Claude Opus 4</option>
    </optgroup>
    <optgroup label="Google Gemini">
      <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
      <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
    </optgroup>
    <optgroup label="其他">
      <option value="deepseek-v3">DeepSeek V3</option>
      <option value="grok-2">Grok 2</option>
    </optgroup>
  </select>
  <p class="text-xs text-gray-500 mt-1">
    選擇用於投資決策的 AI 模型，不同模型具有不同的推理風格與成本
  </p>
</div>
```

#### 表單資料結構

```typescript
interface AgentCreationFormData {
  name: string;
  description: string;
  ai_model: string;                      // 新增：AI 模型選擇
  initial_funds: number;
  investment_preferences: string;
  strategy_adjustment_criteria: string;
  // ... 其他欄位
}

// 預設值
const defaultFormData: AgentCreationFormData = {
  name: '',
  description: '',
  ai_model: 'gpt-4o',                    // 預設為 GPT-4o
  initial_funds: 1000000,
  investment_preferences: '',
  strategy_adjustment_criteria: '',
};
```

### 2. Agent 卡片顯示 (AgentCard.svelte)

#### 顯示模型資訊

```svelte
<div class="agent-header flex justify-between items-start mb-4">
  <div class="agent-info">
    <h3 class="text-lg font-semibold text-gray-900">{agent.name}</h3>
    <div class="flex items-center gap-2">
      <p class="text-sm text-gray-600">{agent.description}</p>
      <!-- 模型標籤 -->
      <span class="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
        {agent.ai_model}
      </span>
    </div>
  </div>
  <!-- ... 其他內容 -->
</div>
```

### 3. Agent 詳情頁面

在 Agent 詳情頁面中顯示完整的模型資訊：

```svelte
<div class="model-info-section mb-6">
  <h4 class="text-sm font-medium text-gray-700 mb-2">AI 模型資訊</h4>
  <div class="bg-gray-50 p-4 rounded-lg">
    <div class="grid grid-cols-2 gap-4">
      <div>
        <span class="text-xs text-gray-500">當前模型</span>
        <div class="text-sm font-medium">{agent.ai_model}</div>
      </div>
      <div>
        <span class="text-xs text-gray-500">創建時間</span>
        <div class="text-sm">{formatDate(agent.created_at)}</div>
      </div>
    </div>
  </div>
</div>
```

---

## 🔧 後端實作

### 1. API Request Model

```python
class AgentCreationRequest(BaseModel):
    """Agent 創建請求"""
    
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    ai_model: str = Field(default="gpt-4o")  # 新增：AI 模型選擇
    initial_funds: float = Field(gt=0, le=100000000)
    investment_preferences: str
    strategy_adjustment_criteria: str
    # ... 其他欄位
    
    @validator('ai_model')
    def validate_ai_model(cls, v):
        """驗證 AI 模型是否支援"""
        supported_models = [
            'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo',
            'claude-sonnet-4.5', 'claude-opus-4',
            'gemini-2.5-pro', 'gemini-2.0-flash',
            'deepseek-v3', 'grok-2'
        ]
        if v not in supported_models:
            raise ValueError(f'不支援的 AI 模型: {v}')
        return v
```

### 2. Agent 配置資料結構

```python
@dataclass
class AgentConfig:
    """Agent 完整配置資料結構"""
    
    # 基本資訊
    name: str
    description: str
    agent_type: str = "trading"
    model: str = "gpt-4o"                  # AI 模型選擇
    
    # 資金配置
    initial_funds: float = 1000000.0
    current_funds: float | None = None
    
    # ... 其他配置欄位
```

### 3. Trading Agent 創建

```python
def create_trading_agent(agent_config: AgentConfig) -> Agent:
    """創建基於用戶配置的交易Agent"""
    
    # 根據用戶選擇的模型創建 Agent
    trading_agent = Agent(
        name=agent_config.name,
        instructions=generate_trading_instructions(agent_config),
        tools=[...],  # 工具列表
        model=agent_config.model,          # 使用用戶選擇的模型
        max_turns=agent_config.max_turns
    )
    
    return trading_agent
```

### 4. 交易執行時記錄模型

```python
async def execute_trade(
    agent_id: str,
    symbol: str,
    action: str,
    quantity: int,
    price: float
) -> Transaction:
    """執行交易並記錄使用的 AI 模型"""
    
    # 獲取 Agent 配置
    agent = await get_agent(agent_id)
    
    # 創建交易記錄
    transaction = Transaction(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        symbol=symbol,
        action=action,
        quantity=quantity,
        price=price,
        ai_model=agent.model,              # 記錄當前使用的模型
        status="executed",
        execution_time=datetime.now()
    )
    
    await save_transaction(transaction)
    return transaction
```

### 5. 策略變更時記錄模型

```python
async def record_strategy_change(
    agent_id: str,
    trigger_reason: str,
    new_strategy_addition: str,
    change_summary: str,
    agent_explanation: str
) -> StrategyChange:
    """記錄策略變更並追蹤使用的 AI 模型"""
    
    # 獲取當前 Agent
    agent = await get_agent(agent_id)
    
    # 創建策略變更記錄
    change = StrategyChange(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        trigger_reason=trigger_reason,
        change_type="auto",
        old_strategy=agent.instructions,
        new_strategy=agent.instructions + "\n\n" + new_strategy_addition,
        change_summary=change_summary,
        agent_explanation=agent_explanation,
        ai_model=agent.model,              # 記錄當前使用的模型
        timestamp=datetime.now()
    )
    
    await save_strategy_change(change)
    return change
```

---

## 💾 資料庫 Schema

### agents 表更新

```sql
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    instructions TEXT NOT NULL,
    model TEXT NOT NULL DEFAULT 'gpt-4o',  -- AI 模型選擇
    -- ... 其他欄位
);
```

### transactions 表更新

```sql
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    -- ... 交易資訊
    ai_model TEXT,                          -- 執行交易時使用的 AI 模型
    decision_reason TEXT,
    market_data JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- ... 其他欄位
);
```

### strategy_changes 表更新

```sql
CREATE TABLE IF NOT EXISTS strategy_changes (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    -- ... 變更資訊
    agent_explanation TEXT,
    ai_model TEXT,                          -- 進行策略變更時使用的 AI 模型
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- ... 其他欄位
);
```

---

## 📊 模型追蹤與分析

### 1. 模型績效比較 API

```http
GET /api/analytics/model-performance
```

**Response**:

```json
{
  "models": [
    {
      "model": "gpt-4o",
      "agents_count": 5,
      "total_trades": 150,
      "avg_return": 8.5,
      "win_rate": 65.3,
      "total_pnl": 425000.0
    },
    {
      "model": "claude-sonnet-4.5",
      "agents_count": 3,
      "total_trades": 120,
      "avg_return": 9.2,
      "win_rate": 68.1,
      "total_pnl": 380000.0
    }
  ]
}
```

### 2. Agent 模型使用歷史

```http
GET /api/agents/{agent_id}/model-usage
```

**Response**:

```json
{
  "agent_id": "agent_001",
  "current_model": "gpt-4o",
  "usage_stats": {
    "total_trades": 50,
    "total_strategy_changes": 5,
    "trades_by_model": {
      "gpt-4o": 50
    },
    "strategy_changes_by_model": {
      "gpt-4o": 5
    }
  }
}
```

---

## ✅ 測試計劃

### 前端測試

- [ ] Agent 創建表單顯示模型選擇下拉選單
- [ ] 預設值為 gpt-4o
- [ ] 選擇不同模型後可以成功提交
- [ ] Agent 卡片正確顯示模型標籤
- [ ] Agent 詳情頁面顯示模型資訊

### 後端測試

- [ ] API 接收並驗證 ai_model 參數
- [ ] Agent 創建時正確保存模型資訊
- [ ] 交易執行時正確記錄使用的模型
- [ ] 策略變更時正確記錄使用的模型
- [ ] 模型驗證器拒絕不支援的模型

### 資料庫測試

- [ ] agents 表正確保存 model 欄位
- [ ] transactions 表正確保存 ai_model 欄位
- [ ] strategy_changes 表正確保存 ai_model 欄位
- [ ] 查詢能正確檢索模型相關資訊

### 整合測試

- [ ] 完整流程：創建 Agent → 執行交易 → 策略變更，所有步驟都正確記錄模型
- [ ] 多個不同模型的 Agent 同時運行
- [ ] 模型績效比較 API 返回正確統計資料

---

## 📝 未來擴展

### 動態模型切換

未來可以考慮支援 Agent 執行期間動態切換模型：

```python
async def switch_agent_model(
    agent_id: str,
    new_model: str,
    reason: str
) -> dict:
    """動態切換 Agent 使用的 AI 模型"""
    
    agent = await get_agent(agent_id)
    old_model = agent.model
    
    # 更新模型
    agent.model = new_model
    await update_agent(agent)
    
    # 記錄模型切換
    await record_model_switch(
        agent_id=agent_id,
        old_model=old_model,
        new_model=new_model,
        reason=reason
    )
    
    return {
        "success": True,
        "message": f"模型已從 {old_model} 切換為 {new_model}"
    }
```

### 自動模型選擇

基於績效表現自動推薦或切換最適合的模型：

```python
async def recommend_best_model(
    agent_id: str,
    performance_threshold: float = 0.05
) -> str:
    """基於歷史績效推薦最佳模型"""
    
    # 獲取各模型的績效統計
    model_performance = await get_model_performance_stats()
    
    # 找出表現最佳的模型
    best_model = max(
        model_performance,
        key=lambda x: x['avg_return']
    )
    
    return best_model['model']
```

---

## 🎯 完成標準

- ✅ 前端提供完整的 AI 模型選擇介面
- ✅ 後端正確處理和驗證模型參數
- ✅ 資料庫正確保存和追蹤模型資訊
- ✅ Agent 卡片顯示當前使用的模型
- ✅ 交易和策略變更記錄包含模型資訊
- ✅ 所有測試通過
- ✅ 文檔更新完成

---

**相關文檔**:

- `SYSTEM_DESIGN.md` - 系統架構與技術堆疊更新
- `API_IMPLEMENTATION.md` - API 規格與資料模型更新
- `AGENT_IMPLEMENTATION.md` - Agent 配置介面更新
- `FRONTEND_IMPLEMENTATION.md` - 前端組件實作規格
- `../src/database/schema.sql` - 資料庫 Schema 定義
