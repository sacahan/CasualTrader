# CasualTrader 重構行動計劃

**建立日期**: 2025-11-09
**最後更新**: 2025-11-09
**執行狀態**: 🟡 進行中 (3/8 階段完成)
**基準**: backend/casualtrader.db (實際資料庫 schema)
**方針**: **不考慮向後相容**，直接移除所有不使用的程式碼

---

## 📊 進度追蹤

### 整體進度
```
████████████░░░░░░░░░░░░░░░░ 50% (3/6 主要階段完成)
```

### Milestone 達成狀況

| Milestone | 狀態 | 完成日期 | 備註 |
|-----------|------|---------|------|
| M0: 資料庫 Migration | ✅ 完成 | 2025-11-09 | 由使用者手動執行 |
| M1: ORM 模型層修正 | ✅ 完成 | 2025-11-09 | 通過所有契約測試 |
| M2: Service 層修正 | ✅ 完成 | 2025-11-09 | 測試通過率 91% |
| M3: API Schema 層修正 | ✅ 完成 | 2025-11-09 | 測試通過率 90.6% |
| M4: API Router 修正 | ⏳ 待執行 | - | 預計 1-2 小時 |
| M5: Frontend 修正 | ⏳ 待執行 | - | 預計 2-3 小時 |
| M6: 文件同步更新 | ⏳ 待執行 | - | 預計 1-2 小時 |
| M7: 完整測試驗證 | ⏳ 待執行 | - | 預計 1 小時 |

### 階段檢查清單

#### ✅ 階段 0: 資料庫 Migration
- [x] 備份資料庫
- [x] 執行 Migration 腳本
- [x] 驗證欄位變更
- [x] 驗證索引完整性

#### ✅ 階段 1: ORM 模型修正
- [x] AgentPerformance.winning_trades → sell_trades_count
- [x] AgentPerformance.winning_trades_correct 新增
- [x] AgentSession.tools_called 型別修正
- [x] 契約測試通過 (11/11)

#### ✅ 階段 2: Service 層修正
- [x] agents_service.py 績效計算邏輯更新
- [x] trading_service.py 績效計算邏輯更新
- [x] 新增 TODO 註解
- [x] 績效歷史回傳欄位更新
- [x] 測試修正 (test_delete_agent_integration.py)
- [x] 新增測試 (test_performance_calculation.py, 6/6 通過)

#### ✅ 階段 3: API Schema 層修正
- [x] 移除 EnabledTools 類別定義
- [x] CreateAgentRequest: 移除 4 個欄位 (strategy_prompt, max_turns, enabled_tools, custom_instructions)
- [x] UpdateAgentRequest: 移除 2 個欄位 (enabled_tools, custom_instructions)
- [x] AgentResponse: 移除 5 個欄位，新增 1 個欄位 (last_active_at)
- [x] StartAgentRequest: 移除 max_turns 參數 (agent_execution.py)
- [x] 測試驗證 (571/630 通過，90.6%)

#### ⏳ 階段 4: API Router 修正
- [ ] agents.py: 移除不存在欄位處理
- [ ] agent_execution.py: 移除 max_turns 參數
- [ ] 確認 JSON 序列化正確
- [ ] API 測試通過

#### ⏳ 階段 5: Frontend 修正
- [ ] api.js: 移除 startAgent 的 maxTurns
- [ ] 檢查 UI 元件是否使用移除的欄位
- [ ] 清理不使用的欄位顯示
- [ ] Frontend 測試通過

#### ⏳ 階段 6: 文件同步更新
- [ ] API_CONTRACT_SPECIFICATION.md
- [ ] ORM_CONTRACT_SPECIFICATION.md
- [ ] SERVICE_CONTRACT_SPECIFICATION.md

#### ⏳ 階段 7: 最終驗證
- [ ] Backend 所有測試通過
- [ ] Frontend 測試通過
- [ ] 手動測試完整流程
- [ ] 更新 CHANGELOG

### 時間追蹤

| 階段 | 預計時間 | 實際時間 | 狀態 |
|------|---------|---------|------|
| 階段 0 | 30 分鐘 | - | ✅ 完成 (使用者執行) |
| 階段 1 | 30 分鐘 | 15 分鐘 | ✅ 完成 |
| 階段 2 | 2 小時 | 1 小時 | ✅ 完成 |
| 測試修正/新增 | 2 小時 | 1.25 小時 | ✅ 完成 |
| 階段 3 | 1-2 小時 | 1 小時 | ✅ 完成 |
| 階段 4 | 1-2 小時 | - | ⏳ 待執行 |
| 階段 5 | 2-3 小時 | - | ⏳ 待執行 |
| 階段 6 | 1-2 小時 | - | ⏳ 待執行 |
| 階段 7 | 1 小時 | - | ⏳ 待執行 |
| **總計** | **10-16 小時** | **3.5 小時** | **50% 完成** |

---

## 執行摘要

基於以下文件進行全面重構：

- **DATABASE_SCHEMA_SPECIFICATION.md** - 實際資料庫 schema (標準)
- **PERFORMANCE_CALCULATION_ANALYSIS.md** - 績效計算邏輯分析
- **REFACTORING_COMPLETION_REPORT.md** - 階段 1-2 完成報告

**核心原則**:

1. 以 `backend/casualtrader.db` 的 schema 為準
2. **直接移除**所有不存在的欄位和功能，不考慮向後相容
3. 同步修改前端和後端
4. 修正績效計算邏輯錯誤

**當前狀態**:
- ✅ 資料庫層: Migration 完成
- ✅ ORM 層: 模型修正完成，契約測試通過
- ✅ Service 層: 邏輯更新完成，集成測試通過 91%
- ⏳ API 層: 待修正
- ⏳ Frontend: 待修正

---

## 重構範圍總覽

### 🔴 Backend 修改

1. 移除不存在欄位的 Schema 定義
2. 修正 ORM 模型型別不一致
3. 修正績效計算邏輯錯誤
4. 清理 Service 層不使用的邏輯
5. 更新 API 回應格式

### 🔵 Frontend 修改

1. 移除 `max_turns` 參數 (API 呼叫)
2. 更新 Agent 型別定義
3. 清理不使用的欄位顯示

### 📄 文件修改

1. 更新所有 SPECIFICATION 文件
2. 同步 API 契約文件

---

## 修改清單

### 🔴 優先級 0: 績效計算邏輯修正 (最高優先級)

基於 `PERFORMANCE_CALCULATION_ANALYSIS.md` 分析結果，以下欄位需要立即修正：

#### 0.1 修正 winning_trades 語義錯誤

**問題**: 欄位命名為 `winning_trades`，但實際儲存的是 `sell_trades_count`

**檔案**:

- `backend/src/service/agents_service.py`
- `backend/src/service/trading_service.py`

**修正方案**: 重新命名資料庫欄位

```sql
-- Migration script
ALTER TABLE agent_performance
RENAME COLUMN winning_trades TO sell_trades_count;

-- 新增真正的 winning_trades 欄位 (初期設為 0，待實現計算邏輯)
ALTER TABLE agent_performance
ADD COLUMN winning_trades_correct INTEGER DEFAULT 0;
```

**程式碼修正**:

```python
# ❌ Before (agents_service.py:783, 797)
performance.winning_trades = completed_trades  # completed_trades 是賣出交易數

# ✅ After
performance.sell_trades_count = completed_trades  # 明確語義
performance.winning_trades_correct = 0  # TODO: 實現真實獲利交易數計算
```

#### 0.2 修正 win_rate 計算邏輯

**問題**: 當前計算的是「交易完成率」(賣出/總交易)，非「勝率」(獲利交易/總交易)

**檔案**: `backend/src/service/agents_service.py:762-766`

```python
# ❌ Before (錯誤定義)
win_rate = (completed_trades / total_trades * 100)  # completed_trades 是賣出交易數

# ✅ After (暫時方案 - 標註錯誤)
# TODO: win_rate 當前為「交易完成率」非真實勝率，待實現買賣配對邏輯後修正
win_rate = (completed_trades / total_trades * 100) if total_trades > 0 else Decimal("0")
```

**長期方案**: 實現買賣配對邏輯 (FIFO)，計算真實獲利交易數

#### 0.3 標註未實現的績效欄位

**檔案**: `backend/src/service/agents_service.py:792-793`

```python
# ✅ 明確標註為未實現，不誤導使用者
performance = AgentPerformance(
    agent_id=agent_id,
    date=today,
    total_value=total_value,
    cash_balance=Decimal(str(cash_balance)),

    # 未實現欄位 - 需要額外實現
    unrealized_pnl=Decimal("0"),  # TODO: 需要實時股價 API
    realized_pnl=Decimal("0"),    # TODO: 需要買賣配對邏輯 (FIFO)
    daily_return=None,             # TODO: 需要歷史績效資料
    max_drawdown=None,             # TODO: 需要歷史淨值曲線

    # 已實現欄位
    total_return=total_return,
    win_rate=win_rate,  # 注意: 當前為交易完成率，非真實勝率
    total_trades=total_trades,
    sell_trades_count=completed_trades,  # 重新命名
    winning_trades_correct=0,            # 新增欄位，待實現
)
```

---

### 🔴 優先級 1: 資料庫模型 (ORM)

#### 1.1 models.py - Agent 模型需要移除的欄位

**檔案**: `backend/src/database/models.py`

**實際資料庫沒有的欄位** (需從 ORM 模型移除):

```python
# ❌ 需要移除 - 資料庫中不存在
class Agent(Base):
    # 這些欄位在實際資料庫中不存在
    # 需要從 ORM 模型中移除
    pass  # 目前模型正確，無需移除欄位
```

**檢查結果**: ✅ Agent 模型與資料庫 schema 一致，無需修改

#### 1.2 models.py - AgentSession 模型欄位型別修正

**檔案**: `backend/src/database/models.py`

**問題**: `tools_called` 欄位型別不一致

```python
# ❌ 當前定義 (models.py)
tools_called: Mapped[list[str] | None] = mapped_column(
    JSON,
    doc="呼叫的工具列表"
)

# ✅ 應改為 (根據資料庫 schema)
tools_called: Mapped[str | None] = mapped_column(
    Text,  # 資料庫使用 TEXT，非 JSON
    doc="呼叫的工具列表 (JSON 字串格式)"
)
```

**位置**: `backend/src/database/models.py` 第 139 行附近

---

### 🟡 優先級 2: API Schema 定義

#### 2.1 schemas/agent.py - 需要移除不存在的欄位

**檔案**: `backend/src/schemas/agent.py`

**問題**: Schema 定義了資料庫中不存在的欄位

```python
# ❌ 這些欄位在資料庫中不存在
class CreateAgentRequest(BaseModel):
    strategy_prompt: str = Field(..., min_length=10)  # ❌ 不存在
    max_turns: int = Field(default=10, ge=1, le=30)  # ❌ 不存在
    enabled_tools: EnabledTools = Field(default_factory=EnabledTools)  # ❌ 不存在
    custom_instructions: str = Field(default="")  # ❌ 不存在
```

```python
# ❌ 這些欄位在資料庫中不存在
class UpdateAgentRequest(BaseModel):
    strategy_prompt: str | None = Field(None, min_length=10)  # ❌ 不存在
    enabled_tools: EnabledTools | None = None  # ❌ 不存在
    custom_instructions: str | None = None  # ❌ 不存在
```

```python
# ❌ 這些欄位在資料庫中不存在
class AgentResponse(BaseModel):
    strategy_prompt: str  # ❌ 不存在
    max_turns: int  # ❌ 不存在
    enabled_tools: EnabledTools  # ❌ 不存在
    custom_instructions: str  # ❌ 不存在
    runtime_status: str | None = None  # ❌ 不存在 (這是執行時狀態，非持久化)
```

**修正方案: 完全移除不存在的欄位** (不考慮向後相容)

**刪除 EnabledTools 定義**:

```python
# ❌ 完全移除 (不再使用)
class EnabledTools(BaseModel):
    fundamental_analysis: bool = True
    technical_analysis: bool = True
    # ...
```

**修正後的 Schema**:

```python
class CreateAgentRequest(BaseModel):
    """建立新交易代理人請求模型 (僅包含持久化欄位)"""
    name: str = Field(..., min_length=1, max_length=200)  # ✅ 改為 200
    description: str = Field(default="")  # ✅ 移除長度限制
    ai_model: str = Field(default="gpt-4o-mini", min_length=1, max_length=50)
    color_theme: str = Field(
        default="34, 197, 94",
        pattern=r"^\d{1,3},\s*\d{1,3},\s*\d{1,3}$"
    )
    initial_funds: float = Field(default=1000000.0, gt=0)
    max_position_size: float = Field(default=50.0, ge=1, le=100)  # ✅ 改為 float
    investment_preferences: list[str] = Field(default_factory=list)


class UpdateAgentRequest(BaseModel):
    """更新代理人請求模型"""
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    color_theme: str | None = Field(None, pattern=r"^\d{1,3},\s*\d{1,3},\s*\d{1,3}$")
    investment_preferences: list[str] | None = None
    ai_model: str | None = Field(None, max_length=50)
    max_position_size: float | None = Field(None, ge=1, le=100)


class AgentResponse(BaseModel):
    """代理人資訊回應模型 (僅包含實際存在的欄位)"""
    id: str
    name: str
    description: str
    ai_model: str
    color_theme: str
    current_mode: str
    max_position_size: float  # ✅ 改為 float
    status: str
    initial_funds: float
    current_funds: float | None = None
    investment_preferences: list[str]
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime | None = None  # ✅ 新增
```

**影響範圍**: 前端需要移除相關欄位的使用

#### 2.2 schemas/agent.py - investment_preferences 型別修正

**問題**: 資料庫使用 TEXT 儲存，非 JSON

```python
# ✅ 當前 Schema 定義正確
investment_preferences: list[str]

# 但需要在 service 層處理 JSON 序列化/反序列化
# 資料庫: TEXT 欄位，儲存 '["2330", "2454"]'
# API: list[str]，回傳 ["2330", "2454"]
```

**處理邏輯** (在 service 層):

```python
# 寫入資料庫時
agent.investment_preferences = json.dumps(preferences_list)

# 從資料庫讀取時
preferences_list = json.loads(agent.investment_preferences) if agent.investment_preferences else []
```

---

### 🟡 優先級 3: Service 層

#### 3.1 agents_service.py - 欄位處理修正

**檔案**: `backend/src/service/agents_service.py`

**需要修正的地方**:

1. **移除不存在欄位的處理**:
   - 移除 `strategy_prompt`, `max_turns`, `enabled_tools`, `custom_instructions` 的處理邏輯

2. **investment_preferences JSON 處理**:

   ```python
   # 建立 agent 時
   agent = Agent(
       # ... 其他欄位 ...
       investment_preferences=json.dumps(request.investment_preferences)
   )

   # 讀取 agent 時
   investment_prefs = (
       json.loads(agent.investment_preferences)
       if agent.investment_preferences
       else []
   )
   ```

#### 3.2 session_service.py - tools_called 欄位處理

**檔案**: `backend/src/service/session_service.py`

**修正**: `tools_called` 應儲存為 JSON 字串，非 list

```python
# ❌ 錯誤 (假設當前是這樣)
session.tools_called = ["tool1", "tool2"]

# ✅ 正確
import json
session.tools_called = json.dumps(["tool1", "tool2"])

# 讀取時
tools = json.loads(session.tools_called) if session.tools_called else []
```

---

### 🟢 優先級 4: API Router

#### 4.1 routers/agents.py - 回應格式修正

**檔案**: `backend/src/api/routers/agents.py`

**檢查點**:

1. ✅ `list_agents` 端點已正確處理 `investment_preferences` JSON 解析
2. ✅ `get_agent` 端點已正確處理 `investment_preferences` JSON 解析
3. ❌ 需移除不存在欄位的回應 (如果有):
   - `strategy_prompt`
   - `max_turns`
   - `enabled_tools`
   - `custom_instructions`
   - `runtime_status`

**範例修正** (list_agents):

```python
# ✅ 當前已正確處理 investment_preferences
investment_prefs = []
if agent.investment_preferences:
    try:
        investment_prefs = json.loads(agent.investment_preferences)
    except (json.JSONDecodeError, TypeError):
        investment_prefs = []

agent_dict = {
    "id": agent.id,
    "name": agent.name,
    # ... 其他實際存在的欄位 ...
    "investment_preferences": investment_prefs,
    # ❌ 不要包含: strategy_prompt, max_turns, enabled_tools, custom_instructions
}
```

---

### 🟢 優先級 5: 規範文件更新

#### 5.1 API_CONTRACT_SPECIFICATION.md

**檔案**: `docs/API_CONTRACT_SPECIFICATION.md`

**需要修正**:

1. **Agent 模型定義** (第 94-123 行):
   - ❌ 移除: `enabled_tools`, `max_turns`, `strategy_prompt`, `custom_instructions`, `runtime_status`
   - ✅ 保留所有資料庫實際存在的欄位

2. **EnabledTools 定義** (第 78-89 行):
   - 如果採用方案 A (完全移除)，則刪除此定義
   - 如果需要保留 (執行時配置)，則標註為"非持久化"

3. **API 端點規範**:
   - 更新所有 Request/Response 範例，移除不存在的欄位

#### 5.2 ORM_CONTRACT_SPECIFICATION.md

**檔案**: `docs/ORM_CONTRACT_SPECIFICATION.md`

**需要修正**:

1. **表名**:
   - ❌ `agent` → ✅ `agents`
   - ❌ `transaction` → ✅ `transactions`
   - ❌ `session` → ✅ `agent_sessions`
   - ✅ `agent_performance` (正確)

2. **Agent 模型** (第 25-68 行):
   - 移除不存在的欄位定義
   - 更新欄位型別和長度以符合實際 schema

3. **Session 模型** (第 145-184 行):
   - 表名改為 `agent_sessions`
   - 欄位名改為 `start_time`, `end_time` (非 `started_at`, `ended_at`)
   - 移除 `initial_cash`, `final_value`, `pnl`
   - 新增 `initial_input`, `final_output`, `tools_called`, `error_message`, `execution_time_ms`

4. **Transaction 模型** (第 186-235 行):
   - 表名改為 `transactions`
   - 欄位名 `symbol` → `ticker`
   - 欄位名 `executed_at` → `execution_time`
   - 移除 `tax` (已合併到 `commission`)
   - 新增 `company_name`, `decision_reason`, `market_data`

#### 5.3 SERVICE_CONTRACT_SPECIFICATION.md

**檔案**: `docs/SERVICE_CONTRACT_SPECIFICATION.md`

**需要修正**:

1. **AgentResponse 型別定義**:
   - 移除不存在的欄位

2. **方法簽名**:
   - 確認所有 service 方法的參數和回傳型別符合實際 schema

---

---

### 🔵 優先級 6: Frontend 修改

#### 6.1 移除 max_turns 參數

**檔案**: `frontend/src/shared/api.js`

**位置**: 第 95-107 行

```javascript
// ❌ Before
startAgent(agentId, mode = 'TRADING', maxTurns = null) {
  const body = {
    mode,
    ...(maxTurns && { max_turns: maxTurns }),  // ← 移除此參數
  };
  return this.request(`/api/agent-execution/${agentId}/start`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// ✅ After
startAgent(agentId, mode = 'TRADING') {
  const body = { mode };
  return this.request(`/api/agent-execution/${agentId}/start`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}
```

#### 6.2 更新前端 Agent 型別定義 (如果有)

**檢查檔案**: `frontend/src/types/*.ts` 或 JSDoc 註解

**移除欄位**:

- `enabled_tools`
- `max_turns`
- `strategy_prompt`
- `custom_instructions`
- `runtime_status`

#### 6.3 清理前端 UI 相關程式碼

**檢查檔案**:

- `frontend/src/components/AgentCard.jsx` (或 .tsx)
- `frontend/src/pages/AgentDetail.jsx` (或 .tsx)
- `frontend/src/forms/AgentForm.jsx` (或 .tsx)

**移除**:

- 這些欄位的顯示
- 這些欄位的輸入控制元件
- 這些欄位的驗證邏輯

#### 6.4 更新前端測試

**檔案**: `frontend/tests/integration/agent-card-execution.test.js`

**移除**: 包含這些欄位的測試案例

---

## 執行順序

### 階段 0: 資料庫 Schema 修正 (最優先)

0. ❌ 執行 Migration 腳本

   ```sql
   -- 修正 agent_performance 表
   ALTER TABLE agent_performance
   RENAME COLUMN winning_trades TO sell_trades_count;

   ALTER TABLE agent_performance
   ADD COLUMN winning_trades_correct INTEGER DEFAULT 0;
   ```

### 階段 1: 模型層修正 (必須先完成)

1. ✅ 檢查 `backend/src/database/models.py`
   - Agent 模型: 已正確 ✅
   - AgentSession 模型: 修正 `tools_called` 型別 (JSON → Text)
   - 其他模型: 需檢查

### 階段 2: 績效計算邏輯修正

2. ❌ 修正 `backend/src/service/agents_service.py` 績效計算
   - 修正 `winning_trades` → `sell_trades_count`
   - 新增 `winning_trades_correct` (初期為 0)
   - 標註 `win_rate` 為交易完成率

3. ❌ 修正 `backend/src/service/trading_service.py` 績效計算
   - 同步修正績效欄位名稱

### 階段 3: Schema 層修正

4. ❌ 修正 `backend/src/schemas/agent.py`
   - **刪除** `EnabledTools` 定義
   - **移除** `CreateAgentRequest` 中的不存在欄位
   - **移除** `UpdateAgentRequest` 中的不存在欄位
   - **移除** `AgentResponse` 中的不存在欄位
   - **新增** `last_active_at` 到 `AgentResponse`

5. ❌ 修正 `backend/src/database/models.py`
   - AgentSession.tools_called: JSON → Text
   - AgentPerformance: 新增 `sell_trades_count`, `winning_trades_correct`

### 階段 4: Service 層修正

6. ❌ 修正 `backend/src/service/agents_service.py`
   - **移除** 不存在欄位的處理邏輯
   - 確認 `investment_preferences` JSON 序列化/反序列化處理
   - 更新績效計算邏輯

7. ❌ 修正 `backend/src/service/session_service.py`
   - 確認 `tools_called` 儲存為 JSON 字串 (非 list)

### 階段 5: API 層修正

8. ❌ 修正 `backend/src/api/routers/agents.py`
   - **移除** 不存在欄位的回應
   - 確認 JSON 處理正確
   - 確認回應包含 `last_active_at`

9. ❌ 修正 `backend/src/api/routers/agent_execution.py` (如果存在)
   - **移除** `max_turns` 參數處理

### 階段 6: Frontend 修正

10. ❌ 修正 `frontend/src/shared/api.js`
    - **移除** `startAgent()` 的 `maxTurns` 參數

11. ❌ 清理前端 UI 相關程式碼
    - 移除不存在欄位的顯示和輸入

12. ❌ 更新前端測試
    - 移除相關測試案例

### 階段 7: 文件同步

13. ❌ 更新 `docs/API_CONTRACT_SPECIFICATION.md`
    - 移除不存在欄位的定義
    - 更新 Agent 模型定義
    - 更新績效欄位說明

14. ❌ 更新 `docs/ORM_CONTRACT_SPECIFICATION.md`
    - 更新表名和欄位
    - 更新績效欄位說明

15. ❌ 更新 `docs/SERVICE_CONTRACT_SPECIFICATION.md`
    - 更新方法簽名
    - 移除不存在欄位

16. ✅ `docs/DATABASE_SCHEMA_SPECIFICATION.md` - 已完成 (基準文件)

17. ✅ `docs/PERFORMANCE_CALCULATION_ANALYSIS.md` - 已完成 (分析文件)

### 階段 8: 測試驗證

18. ❌ 執行契約測試

    ```bash
    cd backend && pytest tests/contract/ -v
    ```

19. ❌ 執行集成測試

    ```bash
    cd backend && pytest tests/integration/ -v
    ```

20. ❌ 手動測試 API 端點
    - 測試 Agent CRUD
    - 測試 Agent 執行
    - 測試績效查詢

21. ❌ Frontend 測試

    ```bash
    cd frontend && npm test
    ```

22. ❌ E2E 測試
    - 建立 Agent
    - 執行 Agent (不帶 max_turns)
    - 查看績效資料

---

## 詳細修改指南

### 修改 1: models.py - AgentSession.tools_called

**檔案**: `backend/src/database/models.py`
**行數**: ~139

```python
# ❌ Before
tools_called: Mapped[list[str] | None] = mapped_column(
    JSON,
    doc="呼叫的工具列表，例如: ['get_stock_price', 'analyze_trend']"
)

# ✅ After
tools_called: Mapped[str | None] = mapped_column(
    Text,
    doc="呼叫的工具列表 (JSON 字串格式)，例如: '[\"get_stock_price\", \"analyze_trend\"]'"
)
```

### 修改 2: schemas/agent.py - CreateAgentRequest

**檔案**: `backend/src/schemas/agent.py`
**行數**: 28-58

```python
# ❌ Before
class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    ai_model: str = Field(default="gpt-4o-mini", ...)
    strategy_prompt: str = Field(..., min_length=10)  # ❌ 移除
    color_theme: str = Field(default="34, 197, 94", ...)
    initial_funds: float = Field(default=1000000.0, gt=0)
    max_position_size: int = Field(default=50, ge=1, le=100)
    max_turns: int = Field(default=10, ge=1, le=30)  # ❌ 移除
    enabled_tools: EnabledTools = Field(default_factory=EnabledTools)  # ❌ 移除
    investment_preferences: list[str] = Field(default_factory=list)
    custom_instructions: str = Field(default="")  # ❌ 移除

# ✅ After
class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)  # ✅ 改為 200
    description: str = Field(default="")  # ✅ 移除長度限制 (TEXT)
    ai_model: str = Field(default="gpt-4o-mini", min_length=1, max_length=50)
    color_theme: str = Field(
        default="34, 197, 94",
        pattern=r"^\d{1,3},\s*\d{1,3},\s*\d{1,3}$"
    )
    initial_funds: float = Field(default=1000000.0, gt=0)
    max_position_size: float = Field(default=50.0, ge=1, le=100)  # ✅ 改為 float
    investment_preferences: list[str] = Field(default_factory=list)
```

### 修改 3: schemas/agent.py - UpdateAgentRequest

**檔案**: `backend/src/schemas/agent.py`
**行數**: 60-78

```python
# ❌ Before
class UpdateAgentRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    strategy_prompt: str | None = Field(None, min_length=10)  # ❌ 移除
    color_theme: str | None = Field(None, ...)
    enabled_tools: EnabledTools | None = None  # ❌ 移除
    investment_preferences: list[str] | None = None
    custom_instructions: str | None = None  # ❌ 移除
    ai_model: str | None = Field(None, ...)
    max_position_size: int | None = Field(None, ge=1, le=100)

# ✅ After
class UpdateAgentRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    color_theme: str | None = Field(
        None, pattern=r"^\d{1,3},\s*\d{1,3},\s*\d{1,3}$"
    )
    investment_preferences: list[str] | None = None
    ai_model: str | None = Field(None, max_length=50)
    max_position_size: float | None = Field(None, ge=1, le=100)
```

### 修改 4: schemas/agent.py - AgentResponse

**檔案**: `backend/src/schemas/agent.py`
**行數**: 104-128

```python
# ❌ Before
class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    ai_model: str
    strategy_prompt: str  # ❌ 移除
    color_theme: str
    current_mode: str
    max_position_size: int
    status: str
    runtime_status: str | None = None  # ❌ 移除
    initial_funds: float
    current_funds: float | None = None
    max_turns: int  # ❌ 移除
    enabled_tools: EnabledTools  # ❌ 移除
    investment_preferences: list[str]
    custom_instructions: str  # ❌ 移除
    created_at: datetime
    updated_at: datetime

# ✅ After
class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    ai_model: str
    color_theme: str
    current_mode: str
    max_position_size: float  # ✅ 改為 float
    status: str
    initial_funds: float
    current_funds: float | None = None
    investment_preferences: list[str]
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime | None = None  # ✅ 新增
```

### 修改 5: agents_service.py - create_agent

**檔案**: `backend/src/service/agents_service.py`

```python
# ✅ 確認 investment_preferences JSON 序列化
import json

async def create_agent(self, request: CreateAgentRequest) -> Agent:
    agent = Agent(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        ai_model=request.ai_model,
        color_theme=request.color_theme,
        initial_funds=Decimal(str(request.initial_funds)),
        current_funds=Decimal(str(request.initial_funds)),
        max_position_size=Decimal(str(request.max_position_size)),
        # ✅ JSON 序列化
        investment_preferences=json.dumps(request.investment_preferences),
        status=AgentStatus.INACTIVE,
        current_mode=AgentMode.TRADING,
        # ❌ 不要設定: strategy_prompt, enabled_tools, custom_instructions
    )
    self.session.add(agent)
    await self.session.commit()
    await self.session.refresh(agent)
    return agent
```

### 修改 6: agents_service.py - get_agent_config

```python
# ✅ 確認 investment_preferences JSON 反序列化
async def get_agent_config(self, agent_id: str) -> dict:
    agent = await self._get_agent_by_id(agent_id)

    # ✅ JSON 反序列化
    investment_prefs = (
        json.loads(agent.investment_preferences)
        if agent.investment_preferences
        else []
    )

    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "ai_model": agent.ai_model,
        "color_theme": agent.color_theme,
        "status": agent.status.value,
        "current_mode": agent.current_mode.value,
        "initial_funds": float(agent.initial_funds),
        "current_funds": float(agent.current_funds),
        "max_position_size": float(agent.max_position_size),
        "investment_preferences": investment_prefs,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
        "last_active_at": agent.last_active_at,
        # ❌ 不要包含: strategy_prompt, max_turns, enabled_tools, custom_instructions
    }
```

---

## 檢查清單

### 資料庫修改

- [ ] 執行 Migration: 重新命名 `winning_trades` → `sell_trades_count`
- [ ] 執行 Migration: 新增 `winning_trades_correct` 欄位

### Backend 程式碼修改

- [ ] `backend/src/database/models.py` - AgentSession.tools_called 型別 (JSON → Text)
- [ ] `backend/src/database/models.py` - AgentPerformance 欄位重新命名
- [ ] `backend/src/schemas/agent.py` - **刪除** EnabledTools 定義
- [ ] `backend/src/schemas/agent.py` - **移除** 不存在欄位 (5 個)
- [ ] `backend/src/service/agents_service.py` - 績效計算邏輯修正
- [ ] `backend/src/service/agents_service.py` - JSON 處理 + 移除不存在欄位處理
- [ ] `backend/src/service/trading_service.py` - 績效計算邏輯修正
- [ ] `backend/src/service/session_service.py` - tools_called JSON 字串處理
- [ ] `backend/src/api/routers/agents.py` - 回應格式檢查 + 移除不存在欄位
- [ ] `backend/src/api/routers/agent_execution.py` - 移除 max_turns 參數

### Frontend 程式碼修改

- [ ] `frontend/src/shared/api.js` - **移除** startAgent() 的 maxTurns 參數
- [ ] `frontend/src/components/` - 清理不存在欄位的顯示
- [ ] `frontend/src/forms/` - 清理不存在欄位的輸入控制元件
- [ ] `frontend/tests/` - 清理相關測試

### 文件同步

- [ ] `docs/API_CONTRACT_SPECIFICATION.md` - 更新 Agent 模型 + 移除不存在欄位
- [ ] `docs/ORM_CONTRACT_SPECIFICATION.md` - 更新表名、欄位、績效欄位
- [ ] `docs/SERVICE_CONTRACT_SPECIFICATION.md` - 更新方法簽名
- [ ] ✅ `docs/DATABASE_SCHEMA_SPECIFICATION.md` - 已建立 (基準文件)
- [ ] ✅ `docs/PERFORMANCE_CALCULATION_ANALYSIS.md` - 已建立 (分析文件)
- [ ] ✅ `docs/REFACTORING_ACTION_PLAN.md` - 已更新 (本文件)

### 測試驗證

- [ ] Backend 契約測試通過
- [ ] Backend 集成測試通過
- [ ] Backend API 手動測試通過
- [ ] Frontend 單元測試通過
- [ ] Frontend E2E 測試通過
- [ ] 前後端整合測試通過

---

## 重要注意事項

### ⚠️ 破壞性變更 (Breaking Changes)

本次重構**不考慮向後相容性**，包含以下破壞性變更：

1. **API 契約變更**:
   - `POST /api/agents`: 移除 5 個請求欄位
   - `PUT /api/agents/{id}`: 移除 3 個請求欄位
   - `GET /api/agents/{id}`: 移除 5 個回應欄位
   - `POST /api/agent-execution/{id}/start`: 移除 `max_turns` 參數

2. **資料庫 Schema 變更**:
   - `agent_performance.winning_trades` → `agent_performance.sell_trades_count`
   - 新增 `agent_performance.winning_trades_correct`

3. **前端 API 呼叫變更**:
   - 所有呼叫 `startAgent()` 的地方需要移除 `maxTurns` 參數

### 📝 語義澄清

1. **績效欄位語義**:
   - `sell_trades_count`: 賣出交易數 (原 winning_trades)
   - `winning_trades_correct`: 真實獲利交易數 (新增，初期為 0)
   - `win_rate`: **當前為交易完成率**，非真實勝率 (待修正)

2. **未實現欄位**:
   - `unrealized_pnl`: 固定為 0 (需要實時股價 API)
   - `realized_pnl`: 固定為 0 (需要買賣配對邏輯)
   - `daily_return`: NULL (需要歷史資料)
   - `max_drawdown`: NULL (需要淨值曲線)

3. **JSON 欄位處理**:
   - `investment_preferences`: TEXT 儲存，JSON 序列化/反序列化
   - `tools_called`: TEXT 儲存，JSON 字串格式

### 🔄 執行時配置建議

如果未來需要執行時配置 (如 `max_turns`, `enabled_tools`)：

**選項 A**: 在 API 請求中直接傳入，不儲存

```python
# 在 agent_execution API 中接收
POST /api/agent-execution/{id}/start
{
  "mode": "TRADING",
  "max_turns": 10,  # 執行時參數
  "enabled_tools": {...}  # 執行時參數
}

# 儲存到 agent_sessions.initial_input (JSON)
```

**選項 B**: 建立新表 `agent_execution_configs`

```sql
CREATE TABLE agent_execution_configs (
  agent_id VARCHAR(50),
  max_turns INTEGER,
  enabled_tools JSON,
  -- ...
);
```

**建議**: 採用選項 A，避免資料重複

### 🧪 測試策略

1. **單元測試**:
   - 測試 JSON 序列化/反序列化
   - 測試績效計算邏輯
   - 測試欄位移除後的正確性

2. **契約測試**:
   - 驗證 API Schema 與資料庫一致
   - 驗證回應格式正確

3. **集成測試**:
   - 完整 Agent CRUD 流程
   - Agent 執行流程 (不帶 max_turns)
   - 績效資料查詢

4. **回歸測試**:
   - 確認現有功能不受影響
   - 確認前端顯示正常

---

## 預期影響範圍

### 🔴 後端 (High Impact)

- **影響**: 高 (破壞性變更)
- **工作量**: 4-6 小時
- **風險**: 中等
- **變更數量**:
  - 資料庫 Migration: 1 個
  - ORM 模型修改: 2 個模型
  - Schema 修改: 4 個 Schema 類別
  - Service 層: 3 個檔案
  - API Router: 2 個檔案
  - 文件: 3 個規格文件

### 🔵 前端 (Medium Impact)

- **影響**: 中等
- **工作量**: 2-3 小時
- **風險**: 低
- **變更數量**:
  - API 呼叫: 1 個方法
  - UI 元件: 需要檢查並清理
  - 測試: 需要更新

**已確認前端使用情況**:

- ✅ `max_turns`: 在 `api.js` 中使用 (需移除)
- ❌ `enabled_tools`: 未在前端程式碼中找到
- ❌ `strategy_prompt`: 未在前端程式碼中找到
- ❌ `custom_instructions`: 未在前端程式碼中找到
- ❌ `runtime_status`: 未在前端程式碼中找到

### 🗄️ 資料庫 (Medium Impact)

- **影響**: 中等
- **遷移**: **必須執行 Migration**
- **變更**:
  - 重新命名欄位: 1 個
  - 新增欄位: 1 個
- **資料遷移**: 不需要 (只是重新命名)
- **風險**: 低 (可回滾)

---

## 結論

基於以下分析文件：

- ✅ `DATABASE_SCHEMA_SPECIFICATION.md` - 實際資料庫標準
- ✅ `PERFORMANCE_CALCULATION_ANALYSIS.md` - 績效計算問題分析

主要需要執行：

### 🔴 立即執行 (優先級 0)

1. **修正績效計算邏輯錯誤** ⚠️
   - 重新命名 `winning_trades` → `sell_trades_count`
   - 新增 `winning_trades_correct` 欄位
   - 標註 `win_rate` 的語義問題

### 🟡 短期執行 (優先級 1-5)

2. **移除不存在的欄位** (破壞性變更)
   - Backend: 移除 5 個欄位定義
   - Frontend: 移除 1 個參數使用
   - 文件: 同步更新

3. **修正型別不一致**
   - `AgentSession.tools_called`: JSON → TEXT
   - `Agent.max_position_size`: int → float

### 🟢 中長期執行 (後續 Sprint)

4. **實現缺失的績效計算** (見 PERFORMANCE_CALCULATION_ANALYSIS.md)
   - `realized_pnl`: 需要買賣配對邏輯 (FIFO)
   - `unrealized_pnl`: 需要實時股價 API
   - `daily_return`: 需要歷史資料查詢
   - `max_drawdown`: 需要淨值曲線追蹤
   - `win_rate`: 修正為真實勝率

---

## 下一步行動

### 立即行動

1. ✅ 審查本重構計劃
2. ❌ 決策確認: 是否接受破壞性變更
3. ❌ 建立 Migration 腳本
4. ❌ 依序執行修改 (階段 0 → 階段 8)

### 風險管理

- ✅ 已備份資料庫 schema
- ❌ 建立回滾計劃
- ❌ 通知前端團隊 API 變更
- ❌ 更新 API 文件和 CHANGELOG

---

**維護者**: CasualTrader 開發團隊
**建立日期**: 2025-11-09
**最後更新**: 2025-11-09
**狀態**: ✅ 計劃完成，待執行
**參考文件**:

- `docs/DATABASE_SCHEMA_SPECIFICATION.md`
- `docs/PERFORMANCE_CALCULATION_ANALYSIS.md`
- `docs/SPECIFICATION_REVIEW_REPORT.md`

---

## 📋 快速檢查清單

### 每日開始前
- [ ] 閱讀當前階段的詳細說明
- [ ] 確認開發環境正常
- [ ] Pull 最新程式碼
- [ ] 備份重要檔案

### 每個階段完成後
- [ ] 執行相關測試
- [ ] 更新本文件的檢查清單 (標記 ✅)
- [ ] 更新進度追蹤表 (頂部)
- [ ] Commit 變更 (使用有意義的 commit message)
- [ ] 記錄實際花費時間

### 每日結束前
- [ ] Push 變更到遠端
- [ ] 更新 REFACTORING_COMPLETION_REPORT.md
- [ ] 記錄遇到的問題和解決方案
- [ ] 規劃隔天工作

### 完成所有階段後
- [ ] 執行完整測試套件
- [ ] 手動測試完整流程
- [ ] 更新所有文件
- [ ] 建立 PR 並請求 Code Review
- [ ] 更新 CHANGELOG

---

## 🔗 相關文件連結

### 必讀文件
- [DATABASE_SCHEMA_SPECIFICATION.md](./DATABASE_SCHEMA_SPECIFICATION.md) - 資料庫標準
- [PERFORMANCE_CALCULATION_ANALYSIS.md](./PERFORMANCE_CALCULATION_ANALYSIS.md) - 績效分析
- [REFACTORING_COMPLETION_REPORT.md](./REFACTORING_COMPLETION_REPORT.md) - 完成報告 ⭐

### 參考文件
- [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) - 重構總結
- [REFACTORING_QUICKSTART.md](./REFACTORING_QUICKSTART.md) - 快速啟動
- [SPECIFICATION_REVIEW_REPORT.md](./SPECIFICATION_REVIEW_REPORT.md) - 審查報告

### API 規格 (待更新)
- [API_CONTRACT_SPECIFICATION.md](./API_CONTRACT_SPECIFICATION.md) - API 契約
- [ORM_CONTRACT_SPECIFICATION.md](./ORM_CONTRACT_SPECIFICATION.md) - ORM 契約
- [SERVICE_CONTRACT_SPECIFICATION.md](./SERVICE_CONTRACT_SPECIFICATION.md) - Service 契約

### Migration
- [backend/migrations/20251109_0000_fix_performance_fields.sql](../backend/migrations/20251109_0000_fix_performance_fields.sql)

---

## 📝 變更日誌

### 2025-11-09
- ✅ 13:15 - 完成階段 3: API Schema 層修正 (測試通過率 90.6%)
- ✅ 13:02 - 新增進度追蹤、Milestone、檢查清單
- ✅ 12:45 - 建立 REFACTORING_COMPLETION_REPORT.md
- ✅ 12:30 - 新增測試 (test_performance_calculation.py, 6/6 通過)
- ✅ 12:15 - 修正測試 (test_delete_agent_integration.py)
- ✅ 12:00 - 完成階段 2: Service 層修正
- ✅ 11:45 - 完成階段 1: ORM 模型修正
- ✅ 11:30 - 完成階段 0: 資料庫 Migration
- ✅ 11:00 - 建立重構行動計劃

---

## 🎯 下一步行動

當前階段: **階段 4 - API Router 修正**

1. 閱讀本文件「階段 4」詳細說明
2. 修改 `backend/src/api/routers/agents.py` (部分已完成)
3. 修改 `backend/src/api/routers/agent_execution.py` (已完成)
4. 修正剩餘測試
5. 確認 JSON 序列化正確

**預計時間**: 1-2 小時
**預計完成**: 今日

---

**最後更新**: 2025-11-09 13:15
**狀態**: 🟡 進行中 (3/6 主要階段完成，50%)
**下一個 Milestone**: M4 - API Router 修正
