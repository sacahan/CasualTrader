# AI 模型選擇功能 - 文檔更新總結

**日期**: 2025-10-06
**更新類型**: 新功能需求 - AI 模型選擇與追蹤

---

## 📋 更新概述

本次更新為 CasualTrader 系統添加了 **AI 模型選擇與追蹤** 功能，允許用戶在創建 Trade Agent 時選擇不同的 AI 模型（如 GPT-4o, Claude Sonnet 4.5, Gemini 2.5 Pro 等），並在後續的交易執行和策略變更中完整記錄使用的模型資訊。

---

## 🎯 功能需求

1. **前端創建/修改 Trade Agent** - 提供選單設定使用的 AI 模型
2. **模型預設值** - 系統提供合理的預設模型（gpt-4o）
3. **後端 Agent 創建** - 支援模型參數並在創建時保存
4. **執行時追蹤** - 在交易與策略變更時記錄當下的模型種類
5. **前端顯示** - Agent 卡片顯示模型資訊

---

## 📚 已更新的文檔

### 1. SYSTEM_DESIGN.md

**更新內容**:

- ✅ 核心價值新增「多模型支援」描述
- ✅ 技術堆疊中列出支援的 AI 模型清單
- ✅ Agent 生命週期管理加入模型選擇與追蹤說明

**關鍵更新**:

```markdown
### 技術堆疊

**AI 與工具層**:
- **AI 模型**: 支援多種主流模型，包括：
  - OpenAI: GPT-4o, GPT-4o-mini, GPT-4-turbo
  - Anthropic: Claude Sonnet 4.5, Claude Opus 4
  - Google: Gemini 2.5 Pro, Gemini 2.0 Flash
  - 其他: DeepSeek, Grok 等
- **模型選擇**: Agent 創建時可選擇模型，執行期間記錄當前使用模型
```

### 2. API_IMPLEMENTATION.md

**更新內容**:

- ✅ Agent 創建 Request 增加 `ai_model` 欄位
- ✅ 列出支援的 AI 模型清單與說明
- ✅ Response 格式包含模型資訊
- ✅ 新增「資料庫 Schema 更新」章節，說明模型追蹤的目的與實作

**關鍵更新**:

```json
// Request
{
  "name": "Prudent Investor",
  "description": "穩健投資策略代理人",
  "ai_model": "gpt-4o",  // 新增模型選擇
  // ... 其他欄位
}
```

**支援的模型**:

- OpenAI: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
- Anthropic: `claude-sonnet-4.5`, `claude-opus-4`
- Google: `gemini-2.5-pro`, `gemini-2.0-flash`
- 其他: `deepseek-v3`, `grok-2`

### 3. AGENT_IMPLEMENTATION.md

**更新內容**:

- ✅ AgentCreationForm 介面新增 `ai_model` 欄位
- ✅ 前端表單添加 AI 模型選擇下拉選單
- ✅ 詳細的模型選項分組（OpenAI / Anthropic / Google / 其他）
- ✅ 表單提示文字說明模型選擇的影響

**關鍵更新**:

```typescript
interface AgentCreationForm {
  name: string;
  description: string;
  ai_model: string;  // 新增：AI 模型選擇（下拉選單）
  initial_funds: number;
  // ... 其他欄位
}
```

```svelte
<select className="form-select" defaultValue="gpt-4o">
  <optgroup label="OpenAI">
    <option value="gpt-4o">GPT-4o (推薦)</option>
    <option value="gpt-4o-mini">GPT-4o Mini (成本優化)</option>
    <option value="gpt-4-turbo">GPT-4 Turbo</option>
  </optgroup>
  <!-- ... 其他選項 -->
</select>
```

### 4. FRONTEND_IMPLEMENTATION.md

**更新內容**:

- ✅ AgentCard 組件顯示模型標籤
- ✅ AgentCreationForm 組件添加模型選擇控制項
- ✅ 模型資訊在 Agent 標題區域顯示
- ✅ 表單資料結構包含 `ai_model` 欄位

**關鍵更新**:

```svelte
<!-- Agent 卡片顯示模型 -->
<div class="agent-info">
  <h3>{agent.name}</h3>
  <div class="flex items-center gap-2">
    <p>{agent.description}</p>
    <span class="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
      {agent.ai_model}
    </span>
  </div>
</div>
```

### 5. 新增文檔: AI_MODEL_SELECTION_FEATURE.md

**完整的功能規格文檔**，包含：

- ✅ 功能概述與需求背景
- ✅ 支援的 AI 模型完整清單
- ✅ 前端實作規格（表單、卡片、詳情頁）
- ✅ 後端實作規格（API、Agent 配置、追蹤機制）
- ✅ 資料庫 Schema 更新
- ✅ 模型追蹤與分析功能
- ✅ 測試計劃
- ✅ 未來擴展建議（動態模型切換、自動模型推薦）

---

## 💾 資料庫 Schema 更新

### src/database/schema.sql

**已更新的表**:

1. **agents 表**

   ```sql
   model TEXT NOT NULL DEFAULT 'gpt-4o'  -- AI 模型選擇
   ```

2. **transactions 表**

   ```sql
   ai_model TEXT  -- 執行交易時使用的 AI 模型
   ```

3. **strategy_changes 表**

   ```sql
   ai_model TEXT  -- 進行策略變更時使用的 AI 模型
   ```

**Schema 更新目的**:

- 📊 模型比較 - 比較不同 AI 模型的投資績效
- 💰 成本分析 - 追蹤不同模型的 API 使用成本
- 🔍 決策追溯 - 了解特定交易背後使用的模型
- 📈 效能評估 - 評估不同模型在不同市場條件下的表現

---

## 🎨 前端實作要點

### 1. Agent 創建表單

**位置**: `frontend/src/components/Agent/AgentCreationForm.svelte`

**實作內容**:

```svelte
<!-- AI 模型選擇 -->
<div class="input-group">
  <label>AI 模型 *</label>
  <select bind:value={formData.ai_model} required>
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
  <small>選擇用於投資決策的 AI 模型</small>
</div>
```

### 2. Agent 卡片顯示

**位置**: `frontend/src/components/Agent/AgentCard.svelte`

**實作內容**:

```svelte
<div class="agent-info">
  <h3>{agent.name}</h3>
  <div class="flex items-center gap-2">
    <p class="text-sm text-gray-600">{agent.description}</p>
    <!-- 模型標籤 -->
    <span class="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
      {agent.ai_model}
    </span>
  </div>
</div>
```

---

## 🔧 後端實作要點

### 1. API Request Model

**位置**: `src/agents/core/models.py`

```python
class AgentCreationRequest(BaseModel):
    name: str
    description: str
    ai_model: str = Field(default="gpt-4o")  # 新增
    initial_funds: float
    investment_preferences: str
    strategy_adjustment_criteria: str
    
    @validator('ai_model')
    def validate_ai_model(cls, v):
        supported = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo',
                     'claude-sonnet-4.5', 'claude-opus-4',
                     'gemini-2.5-pro', 'gemini-2.0-flash',
                     'deepseek-v3', 'grok-2']
        if v not in supported:
            raise ValueError(f'不支援的模型: {v}')
        return v
```

### 2. Agent Config

**位置**: `src/agents/core/models.py`

```python
@dataclass
class AgentConfig:
    name: str
    description: str
    model: str = "gpt-4o"  # AI 模型選擇
    initial_funds: float = 1000000.0
    # ... 其他配置
```

### 3. Trading Agent 創建

**位置**: `src/agents/trading/trading_agent.py`

```python
def create_trading_agent(agent_config: AgentConfig) -> Agent:
    trading_agent = Agent(
        name=agent_config.name,
        instructions=generate_trading_instructions(agent_config),
        tools=[...],
        model=agent_config.model,  # 使用用戶選擇的模型
        max_turns=agent_config.max_turns
    )
    return trading_agent
```

### 4. 交易執行追蹤

```python
async def execute_trade(...) -> Transaction:
    agent = await get_agent(agent_id)
    
    transaction = Transaction(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        symbol=symbol,
        action=action,
        quantity=quantity,
        price=price,
        ai_model=agent.model,  # 記錄當前模型
        status="executed",
        execution_time=datetime.now()
    )
    
    await save_transaction(transaction)
    return transaction
```

### 5. 策略變更追蹤

```python
async def record_strategy_change(...) -> StrategyChange:
    agent = await get_agent(agent_id)
    
    change = StrategyChange(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        trigger_reason=trigger_reason,
        change_summary=change_summary,
        agent_explanation=agent_explanation,
        ai_model=agent.model,  # 記錄當前模型
        timestamp=datetime.now()
    )
    
    await save_strategy_change(change)
    return change
```

---

## ✅ 實作檢查清單

### 文檔更新

- ✅ SYSTEM_DESIGN.md - 系統設計更新
- ✅ API_IMPLEMENTATION.md - API 規格更新
- ✅ AGENT_IMPLEMENTATION.md - Agent 配置介面更新
- ✅ FRONTEND_IMPLEMENTATION.md - 前端組件更新
- ✅ AI_MODEL_SELECTION_FEATURE.md - 完整功能規格文檔
- ✅ schema.sql - 資料庫 Schema 更新

### 資料庫

- ✅ agents.model 欄位 - 記錄 Agent 使用的模型
- ✅ transactions.ai_model 欄位 - 記錄交易時的模型
- ✅ strategy_changes.ai_model 欄位 - 記錄策略變更時的模型

### 後端實作 (待實作)

- [ ] AgentCreationRequest 添加 ai_model 欄位與驗證
- [ ] AgentConfig 添加 model 欄位
- [ ] create_trading_agent 使用配置中的模型
- [ ] execute_trade 記錄當前模型
- [ ] record_strategy_change 記錄當前模型
- [ ] Agent CRUD API 處理模型欄位

### 前端實作 (待實作)

- [ ] AgentCreationForm 添加模型選擇下拉選單
- [ ] AgentCard 顯示模型標籤
- [ ] Agent 詳情頁面顯示模型資訊
- [ ] 表單驗證與提交包含模型資訊

### 測試 (待實作)

- [ ] 前端表單測試
- [ ] 後端 API 測試
- [ ] 資料庫追蹤測試
- [ ] 端到端整合測試

---

## 🚀 下一步行動

### 立即實作

1. **後端實作** - 更新 Agent 相關的 Python 模組
   - `src/agents/core/models.py` - 更新資料模型
   - `src/agents/trading/trading_agent.py` - Agent 創建邏輯
   - `src/database/models.py` - SQLAlchemy 模型更新

2. **前端實作** - 更新 Svelte 組件
   - `frontend/src/components/Agent/AgentCreationForm.svelte`
   - `frontend/src/components/Agent/AgentCard.svelte`
   - `frontend/src/lib/api.js` - API 客戶端更新

3. **資料庫遷移** - 如果需要更新現有資料庫
   - 創建遷移腳本
   - 為現有 Agent 設定預設模型

### 測試驗證

1. **單元測試** - 驗證模型驗證器、API 處理
2. **整合測試** - 驗證端到端流程
3. **UI 測試** - 驗證前端顯示與互動

### 未來擴展

1. **動態模型切換** - 允許 Agent 執行期間切換模型
2. **模型績效分析** - 提供模型比較儀表板
3. **自動模型推薦** - 基於績效自動推薦最佳模型
4. **成本追蹤** - 追蹤不同模型的 API 使用成本

---

## 📞 相關聯繫

如需進一步討論實作細節或有任何問題，請參考：

- **功能規格**: `docs/AI_MODEL_SELECTION_FEATURE.md`
- **系統設計**: `docs/SYSTEM_DESIGN.md`
- **API 規格**: `docs/API_IMPLEMENTATION.md`
- **Agent 實作**: `docs/AGENT_IMPLEMENTATION.md`
- **前端實作**: `docs/FRONTEND_IMPLEMENTATION.md`

---

**文檔更新完成日期**: 2025-10-06
**狀態**: ✅ 文檔更新完成，待程式碼實作
