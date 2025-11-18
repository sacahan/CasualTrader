# CasualTrader 資料庫 Schema 規格文件

**版本**: 2.0
**最後更新**: 2025-11-09
**狀態**: Active (基於實際 casualtrader.db)
**資料庫**: SQLite 3
**位置**: `backend/casualtrader.db`

---

## 概述

本文件定義 CasualTrader 系統的**標準資料庫 schema**，所有程式碼和文件必須以此為準。

**重要原則**:
- 此文件基於 `backend/casualtrader.db` 的實際 schema
- 所有 ORM 模型、API Schema、服務層都必須符合此規格
- 任何 schema 變更必須先更新此文件，再執行 migration

---

## 資料庫統計

| 表名 | 記錄數 | 用途 |
|------|--------|------|
| `agents` | 4 | 交易代理人主表 |
| `ai_model_configs` | 10 | AI 模型配置 |
| `agent_holdings` | 5 | 代理人持倉 |
| `agent_performance` | 5 | 代理人績效記錄 |
| `transactions` | 10 | 交易記錄 |
| `agent_sessions` | 64 | 代理人執行會話 |

---

## 表結構定義

### 1. agents (交易代理人主表)

**用途**: 儲存交易代理人的基本配置和狀態資訊

**表名**: `agents`
**主鍵**: `id` (VARCHAR(50))

#### 欄位定義

| 欄位名 | 型別 | NULL | 預設值 | 說明 |
|--------|------|------|--------|------|
| `id` | VARCHAR(50) | NOT NULL | (UUID) | 代理人唯一識別碼 |
| `name` | VARCHAR(200) | NOT NULL | - | 代理人名稱 |
| `description` | TEXT | NULL | - | 代理人描述 |
| `ai_model` | VARCHAR(50) | NOT NULL | - | 使用的 AI 模型 key (對應 ai_model_configs.model_key) |
| `color_theme` | VARCHAR(20) | NOT NULL | "34, 197, 94" | UI 卡片顏色主題 (RGB 格式: "R, G, B") |
| `initial_funds` | NUMERIC(15, 2) | NOT NULL | 0.00 | 初始資金 (新台幣) |
| `current_funds` | NUMERIC(15, 2) | NOT NULL | 0.00 | 目前可用資金 (新台幣) |
| `max_position_size` | NUMERIC(5, 2) | NOT NULL | 50.00 | 單一持倉最大比例 (%) |
| `status` | VARCHAR(20) | NOT NULL | "inactive" | 代理人持久化狀態 |
| `current_mode` | VARCHAR(30) | NOT NULL | "TRADING" | 當前交易模式 |
| `investment_preferences` | TEXT | NULL | - | 投資偏好 (JSON 字串格式，存股票代碼列表) |
| `created_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 記錄建立時間 (UTC) |
| `updated_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 記錄更新時間 (UTC) |
| `last_active_at` | DATETIME | NULL | - | 最後活動時間 (UTC) |

#### 欄位詳細說明

**status** (代理人持久化狀態):
- `active`: 啟用中，可執行交易
- `inactive`: 停用，不執行交易
- `error`: 錯誤狀態，需要人工介入
- `suspended`: 暫停，可能因風控或其他原因

**current_mode** (交易模式):
- `TRADING`: 完整工具集，執行買賣交易
- `REBALANCING`: 簡化工具集，調整持倉比例

*注意：OBSERVATION 模式已在 Phase 4 移除*

**investment_preferences**:
- 儲存格式: JSON 字串 `'["2330", "2454", "0050"]'`
- 用途: 代理人偏好的股票代碼清單
- 注意: 雖然是 TEXT 型別，應視為 JSON 處理

#### 約束條件

```sql
PRIMARY KEY (id)
CHECK (status IN ('active', 'inactive', 'error', 'suspended'))
CHECK (current_mode IN ('TRADING', 'REBALANCING'))
```

#### API 層狀態映射

**重要**: `/api/agents` 端點會動態轉換 `status` 欄位，將資料庫的持久化狀態映射到前端期望的執行狀態：

| 數據庫狀態 | 執行會話狀態 | API 回應狀態 | 前端顯示 |
|-----------|-----------|-----------|---------|
| `active` | 有 running session | `running` | 運行中 🟢 |
| `active` | 無 running session | `idle` | 待命 ⚪ |
| `inactive` | - | `inactive` | 未啟動 ⚫ |
| `error` | - | `error` | 錯誤 ❌ |
| `suspended` | - | `suspended` | 暫停 ⏸️ |

**代碼實現位置**: `/backend/src/api/routers/agents.py` → `list_agents()` 函數（第 82-114 行）

**查詢邏輯**:
```python
# 1. 查詢所有有 running sessions 的 agent IDs
running_sessions_result = await db_session.execute(
    select(AgentSession.agent_id).where(AgentSession.status == "running")
)
running_agent_ids = set(row[0] for row in running_sessions_result.fetchall())

# 2. 對每個 agent 進行狀態映射
for agent in agents:
    agent_status = agent.status.value  # 從 DB 取得: 'active', 'inactive', etc.
    if agent.id in running_agent_ids:
        agent_status = "running"  # 有執行會話 → "running"
    elif agent_status == "active":
        agent_status = "idle"  # 活躍但無執行 → "idle"
    # 其他狀態保持不變
```

#### 索引

```sql
CREATE INDEX idx_agents_status ON agents (status);
CREATE INDEX idx_agents_created_at ON agents (created_at);
```

#### 關聯關係

- **一對多**: `agents.id` → `agent_holdings.agent_id`
- **一對多**: `agents.id` → `agent_performance.agent_id`
- **一對多**: `agents.id` → `transactions.agent_id`
- **一對多**: `agents.id` → `agent_sessions.agent_id`
- **多對一**: `agents.ai_model` → `ai_model_configs.model_key` (邏輯關聯)

#### 業務邏輯規則

1. **資金管理**:
   - `current_funds` 不可為負數
   - `current_funds` ≤ `initial_funds` + 所有交易損益
   - 購買前需檢查 `current_funds` 是否足夠

2. **狀態轉換**:
   - `inactive` → `active`: 啟動代理人
   - `active` → `inactive`: 停止代理人
   - 任何狀態 → `error`: 發生錯誤
   - `error` → `inactive`: 錯誤修復後需重置

3. **時間戳更新**:
   - 任何欄位更新時必須更新 `updated_at`
   - 代理人執行任何動作時更新 `last_active_at`

---

### 2. ai_model_configs (AI 模型配置)

**用途**: 管理系統可用的 AI 模型清單和配置

**表名**: `ai_model_configs`
**主鍵**: `id` (INTEGER, AUTOINCREMENT)

#### 欄位定義

| 欄位名 | 型別 | NULL | 預設值 | 說明 |
|--------|------|------|--------|------|
| `id` | INTEGER | NOT NULL | AUTO | 自增主鍵 |
| `model_key` | VARCHAR(100) | NOT NULL | - | 模型唯一識別碼 (如 "gpt-4o", "claude-3-opus") |
| `display_name` | VARCHAR(200) | NOT NULL | - | 顯示名稱 (如 "GPT-4 Optimized") |
| `provider` | VARCHAR(50) | NOT NULL | - | 供應商 (如 "openai", "anthropic") |
| `group_name` | VARCHAR(50) | NOT NULL | - | 模型分組名稱 (用於 UI 分類) |
| `model_type` | VARCHAR(20) | NOT NULL | - | 模型類型 |
| `litellm_prefix` | VARCHAR(100) | NULL | - | LiteLLM 路由前綴 (如 "openai/", "anthropic/") |
| `is_enabled` | BOOLEAN | NOT NULL | TRUE | 是否啟用此模型 |
| `requires_api_key` | BOOLEAN | NOT NULL | TRUE | 是否需要 API Key |
| `api_key_env_var` | VARCHAR(100) | NULL | - | API Key 環境變數名稱 (如 "OPENAI_API_KEY") |
| `display_order` | INTEGER | NOT NULL | 999 | 顯示順序 (越小越前) |
| `created_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 記錄建立時間 |
| `updated_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 記錄更新時間 |

#### 欄位詳細說明

**model_type** (模型類型):
- `openai`: 直接使用 OpenAI API
- `litellm`: 透過 LiteLLM 統一介面

**provider** (供應商):
- `openai`: OpenAI (ChatGPT, GPT-4)
- `anthropic`: Anthropic (Claude)
- `google`: Google (Gemini)
- 其他第三方供應商

#### 約束條件

```sql
PRIMARY KEY (id)
UNIQUE (model_key)
CHECK (model_type IN ('openai', 'litellm'))
```

#### 索引

```sql
CREATE INDEX idx_ai_models_model_key ON ai_model_configs (model_key);
CREATE INDEX idx_ai_models_provider ON ai_model_configs (provider);
CREATE INDEX idx_ai_models_is_enabled ON ai_model_configs (is_enabled);
CREATE INDEX idx_ai_models_display_order ON ai_model_configs (display_order);
```

#### 業務邏輯規則

1. **模型選擇**:
   - 前端只顯示 `is_enabled = TRUE` 的模型
   - 依照 `display_order` 排序
   - 按 `group_name` 分組顯示

2. **API Key 驗證**:
   - 若 `requires_api_key = TRUE`，建立 agent 前需檢查環境變數
   - 環境變數名稱由 `api_key_env_var` 指定

---

### 3. agent_holdings (代理人持倉)

**用途**: 記錄代理人目前持有的股票部位

**表名**: `agent_holdings`
**主鍵**: `id` (INTEGER, AUTOINCREMENT)

#### 欄位定義

| 欄位名 | 型別 | NULL | 預設值 | 說明 |
|--------|------|------|--------|------|
| `id` | INTEGER | NOT NULL | AUTO | 自增主鍵 |
| `agent_id` | VARCHAR(50) | NOT NULL | - | 所屬代理人 ID (外鍵 → agents.id) |
| `ticker` | VARCHAR(10) | NOT NULL | - | 股票代號 (如 "2330", "0050") |
| `company_name` | VARCHAR(200) | NULL | - | 公司名稱 (如 "台積電") |
| `quantity` | INTEGER | NOT NULL | - | 持有股數 |
| `average_cost` | NUMERIC(10, 2) | NOT NULL | - | 平均成本 (每股價格) |
| `total_cost` | NUMERIC(15, 2) | NOT NULL | - | 總成本 (= quantity × average_cost) |
| `created_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 首次建倉時間 |
| `updated_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 最後異動時間 |

#### 約束條件

```sql
PRIMARY KEY (id)
UNIQUE (agent_id, ticker)  -- 每個 agent 對單一股票只有一筆持倉記錄
FOREIGN KEY (agent_id) REFERENCES agents(id)
```

#### 索引

```sql
CREATE INDEX idx_holdings_agent_id ON agent_holdings (agent_id);
CREATE INDEX idx_holdings_ticker ON agent_holdings (ticker);
```

#### 業務邏輯規則

1. **建倉規則**:
   - 首次購買時新增記錄
   - `quantity` > 0 才建立記錄

2. **加碼/減碼**:
   - 加碼: 更新 `quantity`, `average_cost`, `total_cost`
   - 減碼: 更新 `quantity`, `total_cost` (成本不變)
   - 全部賣出: 刪除記錄 (quantity = 0)

3. **平均成本計算**:
   ```python
   new_average_cost = (
       (old_quantity * old_average_cost + buy_quantity * buy_price) /
       (old_quantity + buy_quantity)
   )
   ```

4. **總成本計算**:
   ```python
   total_cost = quantity * average_cost
   ```

---

### 4. agent_performance (代理人績效記錄)

**用途**: 記錄代理人每日績效指標

**表名**: `agent_performance`
**主鍵**: `id` (INTEGER, AUTOINCREMENT)

#### 欄位定義

| 欄位名 | 型別 | NULL | 預設值 | 說明 |
|--------|------|------|--------|------|
| `id` | INTEGER | NOT NULL | AUTO | 自增主鍵 |
| `agent_id` | VARCHAR(50) | NOT NULL | - | 所屬代理人 ID (外鍵 → agents.id) |
| `date` | DATE | NOT NULL | - | 績效日期 (YYYY-MM-DD) |
| `total_value` | NUMERIC(15, 2) | NOT NULL | - | 總資產價值 (現金 + 持股市值) |
| `cash_balance` | NUMERIC(15, 2) | NOT NULL | - | 現金餘額 |
| `unrealized_pnl` | NUMERIC(15, 2) | NOT NULL | 0.00 | 未實現損益 (持股浮動盈虧) |
| `realized_pnl` | NUMERIC(15, 2) | NOT NULL | 0.00 | 已實現損益 (已平倉損益) |
| `daily_return` | NUMERIC(8, 4) | NULL | - | 當日報酬率 (%) |
| `total_return` | NUMERIC(8, 4) | NULL | - | 累計報酬率 (%) |
| `win_rate` | NUMERIC(5, 2) | NULL | - | 勝率 (%) |
| `max_drawdown` | NUMERIC(8, 4) | NULL | - | 最大回撤 (%) |
| `total_trades` | INTEGER | NOT NULL | 0 | 累計交易次數 |
| `winning_trades` | INTEGER | NOT NULL | 0 | 獲利交易次數 |
| `created_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 記錄建立時間 |
| `updated_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 記錄更新時間 |

#### 約束條件

```sql
PRIMARY KEY (id)
UNIQUE (agent_id, date)  -- 每個 agent 每天只有一筆績效記錄
FOREIGN KEY (agent_id) REFERENCES agents(id)
```

#### 索引

```sql
CREATE INDEX idx_performance_agent_id ON agent_performance (agent_id);
CREATE INDEX idx_performance_date ON agent_performance (date);
```

#### 業務邏輯規則

1. **總資產計算**:
   ```python
   total_value = cash_balance + sum(holding.quantity * current_price for holding in holdings)
   ```

2. **未實現損益計算**:
   ```python
   unrealized_pnl = sum(
       (current_price - holding.average_cost) * holding.quantity
       for holding in holdings
   )
   ```

3. **累計報酬率計算**:
   ```python
   total_return = (total_value - initial_funds) / initial_funds * 100
   ```

4. **當日報酬率計算**:
   ```python
   daily_return = (today_value - yesterday_value) / yesterday_value * 100
   ```

5. **勝率計算**:
   ```python
   win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
   ```

6. **最大回撤計算**:
   - 從歷史最高點到當前的最大跌幅百分比
   - 需要計算所有歷史記錄

---

### 5. transactions (交易記錄)

**用途**: 記錄所有買賣交易明細

**表名**: `transactions`
**主鍵**: `id` (VARCHAR(50))

#### 欄位定義

| 欄位名 | 型別 | NULL | 預設值 | 說明 |
|--------|------|------|--------|------|
| `id` | VARCHAR(50) | NOT NULL | (UUID) | 交易記錄唯一識別碼 |
| `agent_id` | VARCHAR(50) | NOT NULL | - | 所屬代理人 ID (外鍵 → agents.id) |
| `session_id` | VARCHAR(50) | NULL | - | 所屬會話 ID (外鍵 → agent_sessions.id) |
| `ticker` | VARCHAR(10) | NOT NULL | - | 股票代號 |
| `company_name` | VARCHAR(200) | NULL | - | 公司名稱 |
| `action` | VARCHAR(10) | NOT NULL | - | 交易動作 (BUY/SELL) |
| `quantity` | INTEGER | NOT NULL | - | 交易股數 |
| `price` | NUMERIC(10, 2) | NOT NULL | - | 成交價格 (每股) |
| `total_amount` | NUMERIC(15, 2) | NOT NULL | - | 交易總金額 (= quantity × price) |
| `commission` | NUMERIC(10, 2) | NOT NULL | 0.00 | 手續費 |
| `status` | VARCHAR(20) | NOT NULL | "pending" | 交易狀態 |
| `execution_time` | DATETIME | NULL | - | 實際成交時間 |
| `decision_reason` | TEXT | NULL | - | 決策理由 (AI 分析結果) |
| `market_data` | JSON | NULL | - | 交易時的市場數據快照 |
| `created_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 交易建立時間 |

#### 欄位詳細說明

**action** (交易動作):
- `BUY`: 買入
- `SELL`: 賣出

**status** (交易狀態):
- `pending`: 待執行
- `executed`: 已執行
- `failed`: 失敗
- `cancelled`: 已取消

**market_data** (市場數據):
- JSON 格式儲存交易時的市場資訊
- 可能包含: 技術指標、基本面數據、市場情緒等

#### 約束條件

```sql
PRIMARY KEY (id)
CHECK (action IN ('BUY', 'SELL'))
CHECK (status IN ('pending', 'executed', 'failed', 'cancelled'))
FOREIGN KEY (agent_id) REFERENCES agents(id)
FOREIGN KEY (session_id) REFERENCES agent_sessions(id)
```

#### 索引

```sql
CREATE INDEX idx_transactions_agent_id ON transactions (agent_id);
CREATE INDEX idx_transactions_ticker ON transactions (ticker);
CREATE INDEX idx_transactions_created_at ON transactions (created_at);
CREATE INDEX idx_transactions_status ON transactions (status);
```

#### 業務邏輯規則

1. **買入規則**:
   - 檢查 `agent.current_funds` 是否足夠
   - `total_amount = quantity × price + commission`
   - 更新 `agent.current_funds -= total_amount`
   - 更新或建立 `agent_holdings` 記錄

2. **賣出規則**:
   - 檢查 `agent_holdings` 是否有足夠股數
   - `total_amount = quantity × price - commission`
   - 更新 `agent.current_funds += total_amount`
   - 更新或刪除 `agent_holdings` 記錄

3. **手續費計算** (台股規則):
   - 買入: `commission = total_amount × 0.001425` (手續費 0.1425%)
   - 賣出: `commission = total_amount × 0.001425 + total_amount × 0.003` (手續費 + 證交稅)

4. **狀態流轉**:
   - `pending` → `executed`: 交易成功執行
   - `pending` → `failed`: 交易失敗 (資金不足、持股不足等)
   - `pending` → `cancelled`: 使用者取消

---

### 6. agent_sessions (代理人執行會話)

**用途**: 記錄代理人每次執行的完整過程和結果

**表名**: `agent_sessions`
**主鍵**: `id` (VARCHAR)

#### 欄位定義

| 欄位名 | 型別 | NULL | 預設值 | 說明 |
|--------|------|------|--------|------|
| `id` | VARCHAR | NOT NULL | (UUID) | 會話唯一識別碼 |
| `agent_id` | VARCHAR | NOT NULL | - | 所屬代理人 ID (外鍵 → agents.id) |
| `mode` | VARCHAR | NOT NULL | - | 執行模式 (TRADING/REBALANCING/OBSERVATION) |
| `status` | VARCHAR | NOT NULL | "pending" | 會話狀態 |
| `start_time` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 開始時間 |
| `end_time` | DATETIME | NULL | - | 結束時間 |
| `execution_time_ms` | INTEGER | NULL | - | 執行耗時 (毫秒) |
| `initial_input` | JSON | NULL | - | 初始輸入參數 |
| `final_output` | JSON | NULL | - | 最終輸出結果 |
| `tools_called` | TEXT | NULL | - | 呼叫的工具列表 (JSON 字串) |
| `error_message` | TEXT | NULL | - | 錯誤訊息 (若有) |
| `created_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 記錄建立時間 |
| `updated_at` | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 記錄更新時間 |

#### 欄位詳細說明

**mode** (執行模式):
- `TRADING`: 交易模式
- `REBALANCING`: 再平衡模式
- `OBSERVATION`: 觀察模式

**status** (會話狀態):
- `pending`: 等待執行
- `running`: 執行中
- `completed`: 完成
- `failed`: 失敗
- `cancelled`: 已取消

**tools_called**:
- JSON 字串格式: `'["fundamental_analysis", "technical_analysis", "buy_stock"]'`
- 記錄此次會話中 AI Agent 呼叫的所有工具

**initial_input**:
- 會話啟動時的輸入參數
- 可能包含: 使用者指令、配置參數等

**final_output**:
- 會話結束時的輸出結果
- 可能包含: 分析報告、交易建議、執行摘要等

#### 約束條件

```sql
PRIMARY KEY (id)
FOREIGN KEY (agent_id) REFERENCES agents(id)
```

#### 索引

```sql
CREATE INDEX idx_sessions_agent_id ON agent_sessions (agent_id);
CREATE INDEX idx_sessions_status ON agent_sessions (status);
CREATE INDEX idx_sessions_start_time ON agent_sessions (start_time);
```

#### 業務邏輯規則

1. **會話生命週期**:
   - 建立: `status = 'pending'`, 設定 `start_time`
   - 開始執行: `status = 'running'`
   - 完成: `status = 'completed'`, 設定 `end_time`, 計算 `execution_time_ms`
   - 失敗: `status = 'failed'`, 記錄 `error_message`

2. **執行時間計算**:
   ```python
   execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
   ```

3. **工具追蹤**:
   - 每次呼叫工具時記錄到 `tools_called`
   - 用於分析、除錯和成本追蹤

---

## 關聯關係圖

```
agents (1) ──────< (N) agent_holdings
  │
  │
  ├─────< (N) agent_performance
  │
  │
  ├─────< (N) transactions
  │         │
  │         └────> (N) agent_sessions
  │
  └─────< (N) agent_sessions

ai_model_configs (1) ──────< (N) agents
                           (邏輯關聯)
```

---

## 資料完整性規則

### 級聯刪除規則

當刪除 `agents` 記錄時:
1. ✅ 自動刪除所有 `agent_holdings` (CASCADE)
2. ✅ 自動刪除所有 `agent_performance` (CASCADE)
3. ✅ 自動刪除所有 `transactions` (CASCADE)
4. ✅ 自動刪除所有 `agent_sessions` (CASCADE)

### 參照完整性

1. `agent_holdings.agent_id` 必須存在於 `agents.id`
2. `agent_performance.agent_id` 必須存在於 `agents.id`
3. `transactions.agent_id` 必須存在於 `agents.id`
4. `transactions.session_id` 必須存在於 `agent_sessions.id` (若不為 NULL)
5. `agent_sessions.agent_id` 必須存在於 `agents.id`
6. `agents.ai_model` 應該對應到 `ai_model_configs.model_key` (邏輯約束，未強制)

---

## 資料型別對應

### SQLite → Python/Pydantic

| SQLite 型別 | Python 型別 | Pydantic 型別 | 說明 |
|------------|-------------|--------------|------|
| VARCHAR(N) | str | str | 字串 |
| TEXT | str | str | 長文字 |
| INTEGER | int | int | 整數 |
| NUMERIC(M,D) | Decimal | float | 精確數值 |
| DATETIME | datetime | datetime | 日期時間 |
| DATE | date | date | 日期 |
| BOOLEAN | bool | bool | 布林值 |
| JSON | dict/list | dict/list | JSON 物件 |

### 注意事項

1. **NUMERIC 精度**:
   - 資料庫使用 `NUMERIC(15, 2)` 儲存金額
   - Python 應使用 `Decimal` 避免浮點誤差
   - API 回應可轉為 `float`

2. **JSON 欄位**:
   - `market_data`: 原生 JSON 型別
   - `investment_preferences`: TEXT 儲存 JSON 字串
   - `tools_called`: TEXT 儲存 JSON 字串
   - `initial_input`/`final_output`: 原生 JSON 型別

3. **DATETIME 處理**:
   - 所有時間均為 UTC
   - Python: `datetime.now()` (預設 UTC)
   - 顯示時需轉換為本地時區

---

## 遷移與版本控制

### Schema 變更流程

1. **提案階段**:
   - 更新此文件 (DATABASE_SCHEMA_SPECIFICATION.md)
   - 說明變更原因和影響範圍

2. **實施階段**:
   - 建立 migration 腳本
   - 在測試環境驗證
   - 更新 ORM 模型 (models.py)

3. **部署階段**:
   - 備份現有資料庫
   - 執行 migration
   - 驗證資料完整性

4. **驗證階段**:
   - 執行契約測試
   - 更新 API/Service 文件
   - 提交程式碼

### Migration 腳本命名規範

```
YYYYMMDD_HHMM_description.sql
```

範例:
```
20251109_1200_add_agent_strategy_prompt.sql
20251109_1430_change_investment_prefs_to_json.sql
```

---

## 效能優化建議

### 索引策略

**現有索引** (已建立):
- ✅ 所有外鍵欄位
- ✅ 常用查詢欄位 (status, date, ticker)
- ✅ 排序欄位 (created_at, display_order)

**建議新增索引** (如果查詢效能不佳):
- `agent_sessions(mode, status)` - 複合索引
- `transactions(agent_id, created_at)` - 複合索引
- `agent_performance(agent_id, date)` - 已有 UNIQUE 約束

### 查詢優化

1. **避免 SELECT ***:
   ```sql
   -- ❌ 不好
   SELECT * FROM agents;

   -- ✅ 好
   SELECT id, name, status FROM agents WHERE status = 'active';
   ```

2. **使用索引欄位過濾**:
   ```sql
   -- ✅ 使用索引
   SELECT * FROM transactions WHERE agent_id = 'xxx' AND status = 'executed';
   ```

3. **分頁查詢**:
   ```sql
   SELECT * FROM agent_sessions
   WHERE agent_id = 'xxx'
   ORDER BY start_time DESC
   LIMIT 20 OFFSET 0;
   ```

---

## 資料驗證規則

### 必要驗證

**agents 表**:
- `current_funds` >= 0
- `max_position_size` BETWEEN 1 AND 100
- `investment_preferences` 為有效 JSON 字串 (若不為 NULL)

**transactions 表**:
- `quantity` > 0
- `price` > 0
- `total_amount` = `quantity` × `price` ± 誤差範圍
- `commission` >= 0

**agent_holdings 表**:
- `quantity` > 0 (若為 0 應刪除記錄)
- `average_cost` > 0
- `total_cost` = `quantity` × `average_cost` ± 誤差範圍

**agent_performance 表**:
- `total_value` >= 0
- `cash_balance` >= 0
- `win_rate` BETWEEN 0 AND 100 (若不為 NULL)
- `winning_trades` <= `total_trades`

---

## 常見查詢範例

### 1. 取得代理人完整資訊 (含持倉)

```sql
SELECT
    a.*,
    COUNT(DISTINCT h.id) as holdings_count,
    SUM(h.total_cost) as total_investment
FROM agents a
LEFT JOIN agent_holdings h ON a.id = h.agent_id
WHERE a.id = ?
GROUP BY a.id;
```

### 2. 取得代理人最新績效

```sql
SELECT *
FROM agent_performance
WHERE agent_id = ?
ORDER BY date DESC
LIMIT 1;
```

### 3. 取得代理人交易歷史

```sql
SELECT
    t.*,
    s.mode as session_mode,
    s.status as session_status
FROM transactions t
LEFT JOIN agent_sessions s ON t.session_id = s.id
WHERE t.agent_id = ?
ORDER BY t.created_at DESC
LIMIT 50;
```

### 4. 統計代理人績效

```sql
SELECT
    agent_id,
    COUNT(*) as total_sessions,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_sessions,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_sessions,
    AVG(execution_time_ms) as avg_execution_time_ms
FROM agent_sessions
WHERE agent_id = ?
GROUP BY agent_id;
```

### 5. 取得所有啟用的 AI 模型

```sql
SELECT *
FROM ai_model_configs
WHERE is_enabled = 1
ORDER BY display_order, display_name;
```

---

## 附錄

### A. 完整 Schema DDL

參見 `backend/casualtrader.db` 或執行:
```bash
sqlite3 backend/casualtrader.db ".schema"
```

### B. 範例資料

```sql
-- 查看每個表的記錄數
SELECT 'agents' as table_name, COUNT(*) as count FROM agents
UNION ALL
SELECT 'ai_model_configs', COUNT(*) FROM ai_model_configs
UNION ALL
SELECT 'agent_holdings', COUNT(*) FROM agent_holdings
UNION ALL
SELECT 'agent_performance', COUNT(*) FROM agent_performance
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'agent_sessions', COUNT(*) FROM agent_sessions;
```

### C. 資料庫維護

**備份**:
```bash
sqlite3 backend/casualtrader.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"
```

**壓縮** (VACUUM):
```bash
sqlite3 backend/casualtrader.db "VACUUM;"
```

**分析** (ANALYZE):
```bash
sqlite3 backend/casualtrader.db "ANALYZE;"
```

---

## 版本歷史

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|---------|------|
| 2.0 | 2025-11-09 | 基於實際 casualtrader.db 重寫完整規格 | Claude |
| 1.0 | 2025-10-23 | 初始版本 (已過時) | - |

---

**維護者**: CasualTrader 開發團隊
**最後檢查**: 2025-11-09
**下次審查**: 每次 schema 變更後
