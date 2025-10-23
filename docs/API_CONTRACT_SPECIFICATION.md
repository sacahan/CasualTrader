# API 契約規範 (Frontend-Backend Contract)

**版本**: 1.0
**最後更新**: 2025-10-22
**狀態**: Active

## 概述

本文件定義前後台之間的完整 API 契約規範，確保資料格式一致性和型別安全。涵蓋所有已實現的端點、請求/回應格式、錯誤處理和驗證規則。

## 核心原則

### 1. 資料型別契約

```typescript
// 前端期待的型別
interface Agent {
  id: string;
  name: string;
  investment_preferences: string[];  // ✅ 必須是字串陣列
  enabled_tools: EnabledTools;       // ✅ 必須是物件
  created_at: string;                // ✅ ISO 8601 格式
  // ... 其他欄位
}
```

```python
# 後端回應的型別
class AgentResponse(BaseModel):
    id: str
    name: str
    investment_preferences: list[str]  # ✅ 必須是字串列表
    enabled_tools: EnabledTools        # ✅ 必須是物件
    created_at: datetime               # ✅ 自動序列化為 ISO 格式
    # ... 其他欄位
```

### 2. 序列化規則

| 欄位 | 前端格式 | 後端格式 | 轉換規則 |
|------|----------|----------|----------|
| `investment_preferences` | `string[]` | `list[str]` | 直接對應，不進行 JSON 字串序列化 |
| `enabled_tools` | `object` | `dict` | 直接對應 |
| `created_at` / `updated_at` | `string` (ISO 8601) | `datetime` | 自動序列化為 ISO 8601 格式 |
| 數值欄位 | `number` | `float` / `int` | 直接對應 |

### 3. 通用響應格式

所有 API 響應遵循以下模式：

**成功响應** (2xx):
```json
{
  "success": true,
  "data": { /* 實際資料 */ },
  "timestamp": "2025-10-22T16:02:14Z"
}
```

**錯誤響應** (4xx, 5xx):
```json
{
  "detail": "人類可讀的錯誤訊息",
  "error_code": "ERROR_TYPE",
  "field_errors": {
    "field_name": ["錯誤詳情"]
  },
  "timestamp": "2025-10-22T16:02:14Z"
}
```

---

## 資料模型定義

### EnabledTools (工具配置)

```typescript
interface EnabledTools {
  fundamental_analysis: boolean;   // 基本面分析
  technical_analysis: boolean;     // 技術面分析
  risk_assessment: boolean;        // 風險評估
  sentiment_analysis: boolean;     // 市場情緒分析
  web_search: boolean;             // 網路搜尋
  code_interpreter: boolean;       // 程式碼解譯器
}
```

### Agent (完整模型)

```typescript
interface Agent {
  // 基本資訊
  id: string;                              // 代理人 ID (UUID)
  name: string;                            // 代理人名稱 (1-100 字)
  description: string;                     // 代理人描述 (0-500 字)
  ai_model: string;                        // 使用的 AI 模型鑰匙
  strategy_prompt: string;                 // 交易策略提示語
  color_theme: string;                     // UI 顏色 (RGB: "34, 197, 94")

  // 配置參數
  initial_funds: number;                   // 初始資金 (> 0)
  max_position_size: number;               // 最大持倉比例 (1-100%)
  max_turns: number;                       // 最大回合數 (1-30)
  enabled_tools: EnabledTools;             // 啟用工具
  investment_preferences: string[];        // 投資偏好代碼 (如 ["2330", "2454"])
  custom_instructions: string;             // 自訂指令

  // 狀態
  status: "active" | "inactive" | "error" | "suspended";  // 持久化狀態
  runtime_status?: "idle" | "running" | "stopped";        // 執行時狀態
  current_mode: string;                    // 當前交易模式

  // 財務資訊
  current_funds?: number;                  // 目前資金
  portfolio?: Portfolio;                   // 投資組合
  performance?: PerformanceMetrics;        // 績效指標

  // 時間戳
  created_at: string;                      // 建立時間 (ISO 8601)
  updated_at: string;                      // 更新時間 (ISO 8601)
}
```

### Portfolio (投資組合)

```typescript
interface Portfolio {
  cash: number;                    // 現金餘額
  total_value: number;             // 總資產價值
  positions: {                     // 持股明細
    [ticker: string]: {
      quantity: number;            // 持股數量
      avg_price: number;           // 平均買入價格
      current_price: number;       // 當前價格
      total_value: number;         // 持股總價值
      gain_loss: number;           // 損益
      gain_loss_percent: number;   // 損益百分比
    }
  };
  timestamp: string;               // 快照時間 (ISO 8601)
}
```

### Transaction (交易記錄)

```typescript
interface Transaction {
  id: string;                      // 交易紀錄 ID
  agent_id: string;                // 代理人 ID
  ticker: string;                  // 股票代號
  action: "buy" | "sell";          // 買賣動作
  quantity: number;                // 交易股數
  price: number;                   // 交易價格
  total_amount: number;            // 交易總金額
  fee: number;                     // 手續費
  timestamp: string;               // 交易時間 (ISO 8601)
  reason?: string;                 // 交易原因
}
```

### PerformanceMetrics (績效指標)

```typescript
interface PerformanceMetrics {
  total_return: number;            // 總報酬率
  annual_return: number;           // 年報酬率
  sharpe_ratio: number;            // 夏普比率
  max_drawdown: number;            // 最大回撤
  win_rate: number;                // 勝率
  total_trades: number;            // 總交易數
  winning_trades: number;          // 獲利交易數
  losing_trades: number;           // 虧損交易數
  updated_at: string;              // 更新時間 (ISO 8601)
}
```

### AIModel (AI 模型)

```typescript
interface AIModel {
  model_key: string;               // 模型唯一識別碼 (如 "gpt-4o")
  display_name: string;            // 顯示名稱
  provider: string;                // 提供商 (openai/litellm)
  group_name: string;              // 分組名稱
  model_type: string;              // 模型類型
  litellm_prefix?: string;         // LiteLLM 前綴
  full_model_name: string;         // 完整模型名稱
  max_tokens?: number;             // 最大 token 數
  cost_per_1k_tokens?: number;     // 每 1K tokens 成本
  description?: string;            // 描述
  display_order?: number;          // 顯示順序
}
```

---

## API 端點契約

### 1. Agents 管理

#### GET /api/agents - 列出所有代理人

**描述**: 獲取系統中所有 Agent 的列表

**請求**:
```
GET /api/agents
```

**回應** (200):
```json
[
  {
    "id": "agent_123",
    "name": "保守型投資者",
    "description": "低風險策略代理人",
    "ai_model": "gpt-4o-mini",
    "strategy_prompt": "採用保守投資策略...",
    "color_theme": "34, 197, 94",
    "initial_funds": 1000000,
    "current_funds": 1050000,
    "max_position_size": 50,
    "status": "active",
    "runtime_status": "idle",
    "current_mode": "OBSERVATION",
    "max_turns": 10,
    "enabled_tools": {
      "fundamental_analysis": true,
      "technical_analysis": true,
      "risk_assessment": true,
      "sentiment_analysis": false,
      "web_search": true,
      "code_interpreter": false
    },
    "investment_preferences": ["2330", "2454", "0050"],
    "custom_instructions": "優先考慮長期持有",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-10-22T15:00:00Z"
  }
]
```

**錯誤** (500):
```json
{
  "detail": "Failed to list agents",
  "error_code": "INTERNAL_ERROR"
}
```

---

#### GET /api/agents/{agent_id} - 取得單一代理人

**描述**: 根據 ID 獲取特定 Agent 的詳細資訊

**請求**:
```
GET /api/agents/agent_123
```

**路徑參數**:
- `agent_id` (string, required): Agent ID

**回應** (200):
```json
{
  "id": "agent_123",
  "name": "保守型投資者",
  "description": "低風險策略代理人",
  "ai_model": "gpt-4o-mini",
  "strategy_prompt": "採用保守投資策略...",
  "color_theme": "34, 197, 94",
  "initial_funds": 1000000,
  "current_funds": 1050000,
  "max_position_size": 50,
  "status": "active",
  "runtime_status": "idle",
  "current_mode": "OBSERVATION",
  "max_turns": 10,
  "enabled_tools": { /* ... */ },
  "investment_preferences": ["2330", "2454", "0050"],
  "custom_instructions": "優先考慮長期持有",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-10-22T15:00:00Z",
  "portfolio": {
    "cash": 50000,
    "total_value": 1050000,
    "positions": {
      "2330": {
        "quantity": 100,
        "avg_price": 1000,
        "current_price": 1050,
        "total_value": 105000,
        "gain_loss": 5000,
        "gain_loss_percent": 5.0
      }
    },
    "timestamp": "2025-10-22T15:00:00Z"
  },
  "performance": {
    "total_return": 0.05,
    "annual_return": 0.15,
    "sharpe_ratio": 1.2,
    "max_drawdown": -0.08,
    "win_rate": 0.65,
    "total_trades": 20,
    "winning_trades": 13,
    "losing_trades": 7,
    "updated_at": "2025-10-22T15:00:00Z"
  }
}
```

**錯誤** (404):
```json
{
  "detail": "Agent not found",
  "error_code": "AGENT_NOT_FOUND"
}
```

---

#### POST /api/agents - 建立新代理人

**描述**: 建立一個新的交易 Agent

**請求**:
```json
{
  "name": "積極型投資者",
  "description": "高風險高報酬策略",
  "ai_model": "gpt-4o",
  "strategy_prompt": "尋求高報酬的投資機會，接受較高風險...",
  "color_theme": "239, 68, 68",
  "initial_funds": 500000,
  "max_position_size": 75,
  "max_turns": 20,
  "enabled_tools": {
    "fundamental_analysis": true,
    "technical_analysis": true,
    "risk_assessment": true,
    "sentiment_analysis": true,
    "web_search": true,
    "code_interpreter": false
  },
  "investment_preferences": ["2330", "2454", "2412"],
  "custom_instructions": "積極尋找成長型股票"
}
```

**必須欄位**:
- `name` (string, 1-100 字): 代理人名稱
- `strategy_prompt` (string, ≥10 字): 策略提示語
- `ai_model` (string): AI 模型鑰匙 (必須存在於資料庫)

**可選欄位**:
- `description` (string, ≤500 字): 代理人描述
- `color_theme` (string, RGB 格式): 預設 "34, 197, 94"
- `initial_funds` (number, > 0): 預設 1000000
- `max_position_size` (number, 1-100): 預設 50
- `max_turns` (number, 1-30): 預設 10
- `enabled_tools` (object): 預設全啟用 (除 sentiment/code_interpreter)
- `investment_preferences` (string[]): 預設空陣列
- `custom_instructions` (string): 預設空

**回應** (201):
```json
{
  "id": "agent_124",
  "name": "積極型投資者",
  "description": "高風險高報酬策略",
  "ai_model": "gpt-4o",
  "strategy_prompt": "尋求高報酬的投資機會，接受較高風險...",
  "color_theme": "239, 68, 68",
  "initial_funds": 500000,
  "current_funds": 500000,
  "max_position_size": 75,
  "max_turns": 20,
  "status": "inactive",
  "runtime_status": "idle",
  "current_mode": "OBSERVATION",
  "enabled_tools": { /* ... */ },
  "investment_preferences": ["2330", "2454", "2412"],
  "custom_instructions": "積極尋找成長型股票",
  "created_at": "2025-10-22T16:02:14Z",
  "updated_at": "2025-10-22T16:02:14Z"
}
```

**驗證錯誤** (422):
```json
{
  "detail": "Validation error",
  "field_errors": {
    "name": ["ensure this value has at least 1 characters"],
    "strategy_prompt": ["ensure this value has at least 10 characters"],
    "ai_model": ["AI model not found in database"]
  }
}
```

---

#### PUT /api/agents/{agent_id} - 更新代理人

**描述**: 更新現有 Agent 的配置

**請求**:
```json
{
  "name": "保守型投資者 v2",
  "description": "更新的描述",
  "strategy_prompt": "新的策略提示語...",
  "max_position_size": 40,
  "enabled_tools": {
    "fundamental_analysis": true,
    "technical_analysis": false,
    "risk_assessment": true,
    "sentiment_analysis": false,
    "web_search": true,
    "code_interpreter": false
  },
  "investment_preferences": ["2330", "0050"],
  "custom_instructions": "更新的自訂指令"
}
```

**所有欄位為選填** - 只有提供的欄位會被更新

**回應** (200): 同 GET /api/agents/{agent_id}

**錯誤** (404): Agent not found

---

#### DELETE /api/agents/{agent_id} - 刪除代理人

**描述**: 刪除指定的 Agent

**請求**:
```
DELETE /api/agents/agent_123
```

**回應** (204): 無內容 (成功刪除)

**錯誤** (404): Agent not found

---

#### POST /api/agents/{agent_id}/mode - 切換代理人模式

**描述**: 切換 Agent 的交易模式

**請求**:
```json
{
  "mode": "TRADING"
}
```

**路徑參數**:
- `agent_id` (string, required): Agent ID

**查詢參數**:
- `mode` (string, required): 新模式 (OBSERVATION | TRADING | REBALANCING)

**回應** (200):
```json
{
  "success": true,
  "agent_id": "agent_123",
  "previous_mode": "OBSERVATION",
  "current_mode": "TRADING",
  "timestamp": "2025-10-22T16:02:14Z"
}
```

---

#### POST /api/agents/{agent_id}/reset - 重置代理人

**描述**: 重置 Agent (清除投資組合和交易歷史)

**請求**:
```
POST /api/agents/agent_123/reset
```

**回應** (200):
```json
{
  "success": true,
  "agent_id": "agent_123",
  "message": "Agent reset successfully",
  "current_funds": 1000000,
  "timestamp": "2025-10-22T16:02:14Z"
}
```

---

### 2. 代理人執行

#### POST /api/agent_execution/{agent_id}/start - 執行單一模式（非阻塞）

**描述**: 立即返回 session_id，在後台執行 Agent。狀態更新透過 WebSocket 推送。

**請求**:
```json
{
  "mode": "OBSERVATION",
  "max_turns": 5
}
```

**路徑參數**:
- `agent_id` (string, required): Agent ID

**請求欄位**:
- `mode` (string, required): 執行模式 (OBSERVATION | TRADING | REBALANCING)
- `max_turns` (number, optional): 最大輪數 (1-50)

**回應** (202 Accepted):
```json
{
  "success": true,
  "session_id": "session_abc123def456",
  "mode": "OBSERVATION",
  "message": "Agent execution started in background. Status updates will be pushed via WebSocket."
}
```

---

#### POST /api/agent_execution/{agent_id}/stop - 停止代理人執行（阻塞式）

**描述**: 停止 Agent 正在執行的任務，等待完成後返回。

**請求**:
```
POST /api/agent_execution/agent_123/stop
```

**回應** (200):
```json
{
  "success": true,
  "agent_id": "agent_123",
  "status": "stopped",
  "message": "Agent execution stopped"
}
```

---

### 3. 交易資訊

#### GET /api/trading/agents/{agent_id}/portfolio - 取得投資組合

**描述**: 獲取 Agent 的完整投資組合資訊

**請求**:
```
GET /api/trading/agents/agent_123/portfolio
```

**回應** (200):
```json
{
  "cash": 50000,
  "total_value": 1050000,
  "positions": {
    "2330": {
      "quantity": 100,
      "avg_price": 1000,
      "current_price": 1050,
      "total_value": 105000,
      "gain_loss": 5000,
      "gain_loss_percent": 5.0
    },
    "2454": {
      "quantity": 50,
      "avg_price": 500,
      "current_price": 520,
      "total_value": 26000,
      "gain_loss": 1000,
      "gain_loss_percent": 4.0
    }
  },
  "timestamp": "2025-10-22T15:00:00Z"
}
```

---

#### GET /api/trading/agents/{agent_id}/holdings - 取得持股明細

**描述**: 獲取 Agent 的所有持股明細

**回應** (200):
```json
[
  {
    "ticker": "2330",
    "quantity": 100,
    "avg_price": 1000,
    "current_price": 1050,
    "total_value": 105000,
    "gain_loss": 5000,
    "gain_loss_percent": 5.0
  },
  {
    "ticker": "2454",
    "quantity": 50,
    "avg_price": 500,
    "current_price": 520,
    "total_value": 26000,
    "gain_loss": 1000,
    "gain_loss_percent": 4.0
  }
]
```

---

#### GET /api/trading/agents/{agent_id}/transactions - 取得交易歷史

**描述**: 獲取 Agent 的交易歷史記錄

**查詢參數**:
- `limit` (number, optional): 返回筆數，預設 50
- `offset` (number, optional): 分頁起點，預設 0

**回應** (200):
```json
{
  "total": 42,
  "limit": 50,
  "offset": 0,
  "transactions": [
    {
      "id": "trade_001",
      "agent_id": "agent_123",
      "ticker": "2330",
      "action": "buy",
      "quantity": 100,
      "price": 1000,
      "total_amount": 100000,
      "fee": 100,
      "timestamp": "2025-10-22T10:00:00Z",
      "reason": "Fundamental analysis positive"
    },
    {
      "id": "trade_002",
      "agent_id": "agent_123",
      "ticker": "2454",
      "action": "buy",
      "quantity": 50,
      "price": 500,
      "total_amount": 25000,
      "fee": 25,
      "timestamp": "2025-10-22T11:00:00Z",
      "reason": "Technical analysis signal"
    }
  ]
}
```

---

#### GET /api/trading/agents/{agent_id}/trades - 取得交易記錄（別名）

**描述**: 同 /transactions，提供別名端點

---

#### GET /api/trading/agents/{agent_id}/performance - 取得績效指標

**描述**: 獲取 Agent 的績效分析指標

**回應** (200):
```json
{
  "total_return": 0.05,
  "annual_return": 0.15,
  "sharpe_ratio": 1.2,
  "max_drawdown": -0.08,
  "win_rate": 0.65,
  "total_trades": 20,
  "winning_trades": 13,
  "losing_trades": 7,
  "updated_at": "2025-10-22T15:00:00Z"
}
```

---

#### GET /api/trading/market/status - 取得市場狀態

**描述**: 獲取台灣股市開盤狀態（基於交易日檢查）

**回應** (200):
```json
{
  "is_trading_day": true,
  "market_open": true,
  "current_time": "2025-10-22T09:30:00Z",
  "market_open_time": "2025-10-22T09:00:00Z",
  "market_close_time": "2025-10-22T13:30:00Z",
  "message": "Market is open"
}
```

---

#### GET /api/trading/market/quote/{ticker} - 取得股票報價

**描述**: 獲取股票即時報價（透過 MCP Server）

**路徑參數**:
- `ticker` (string, required): 股票代號 (如 "2330")

**回應** (200):
```json
{
  "ticker": "2330",
  "name": "台積電",
  "price": 1050,
  "change": 10,
  "change_percent": 0.96,
  "volume": 25000000,
  "pe_ratio": 25.5,
  "market_cap": 15000000000000,
  "timestamp": "2025-10-22T13:30:00Z"
}
```

---

#### GET /api/trading/market/indices - 取得市場指數

**描述**: 獲取市場指數資訊（透過 MCP Server）

**回應** (200):
```json
{
  "taiex": {
    "index": "TAIEX",
    "value": 20500,
    "change": 150,
    "change_percent": 0.73,
    "timestamp": "2025-10-22T13:30:00Z"
  },
  "otc": {
    "index": "OTC",
    "value": 9500,
    "change": 50,
    "change_percent": 0.53,
    "timestamp": "2025-10-22T13:30:00Z"
  }
}
```

---

### 4. AI 模型管理

#### GET /api/ai_models/available - 取得可用模型列表

**描述**: 獲取所有可用(已啟用)的 AI 模型列表，按 display_order 排序

**回應** (200):
```json
{
  "total": 8,
  "models": [
    {
      "model_key": "gpt-4o",
      "display_name": "GPT-4 Turbo",
      "provider": "openai",
      "group_name": "OpenAI",
      "model_type": "openai",
      "full_model_name": "gpt-4-turbo-preview",
      "max_tokens": 128000,
      "cost_per_1k_tokens": 0.01,
      "description": "Advanced reasoning model",
      "display_order": 1
    },
    {
      "model_key": "gpt-4o-mini",
      "display_name": "GPT-4 Mini",
      "provider": "openai",
      "group_name": "OpenAI",
      "model_type": "openai",
      "full_model_name": "gpt-4-turbo-mini",
      "max_tokens": 128000,
      "cost_per_1k_tokens": 0.0001,
      "description": "Lightweight model",
      "display_order": 2
    },
    {
      "model_key": "claude-sonnet-4.5",
      "display_name": "Claude Sonnet 4.5",
      "provider": "litellm",
      "group_name": "Anthropic",
      "model_type": "litellm",
      "litellm_prefix": "claude-3.5-sonnet",
      "full_model_name": "claude-3.5-sonnet-20250514",
      "max_tokens": 200000,
      "cost_per_1k_tokens": 0.003,
      "description": "Latest Claude model",
      "display_order": 3
    }
  ]
}
```

---

#### GET /api/ai_models/available/grouped - 取得分組的模型列表

**描述**: 獲取按 group_name 分組的 AI 模型列表

**回應** (200):
```json
{
  "groups": {
    "OpenAI": [
      {
        "model_key": "gpt-4o",
        "display_name": "GPT-4 Turbo",
        /* ... 其他欄位 */
      },
      {
        "model_key": "gpt-4o-mini",
        "display_name": "GPT-4 Mini",
        /* ... 其他欄位 */
      }
    ],
    "Anthropic": [
      {
        "model_key": "claude-sonnet-4.5",
        "display_name": "Claude Sonnet 4.5",
        /* ... 其他欄位 */
      }
    ]
  }
}
```

---

#### GET /api/ai_models/{model_key} - 取得特定模型資訊

**描述**: 根據 model_key 獲取特定模型的詳細資訊

**路徑參數**:
- `model_key` (string, required): 模型鑰匙 (如 "gpt-4o")

**回應** (200): 單個模型物件

**錯誤** (404):
```json
{
  "detail": "Model not found",
  "error_code": "MODEL_NOT_FOUND"
}
```

---

#### GET /api/ai_models/ - 取得所有模型列表（含禁用）

**描述**: 獲取所有 AI 模型列表，可選包含已禁用的模型

**查詢參數**:
- `include_disabled` (boolean, optional): 是否包含已禁用的模型，預設 false

**回應** (200): 同 available，但可能包含已禁用的模型

---

## 通用錯誤代碼

| HTTP 狀態 | 錯誤代碼 | 描述 |
|-----------|--------|------|
| 400 | `BAD_REQUEST` | 請求格式錯誤 |
| 422 | `VALIDATION_ERROR` | 資料驗證失敗 |
| 404 | `NOT_FOUND` | 資源不存在 |
| 409 | `CONFLICT` | 操作衝突 |
| 500 | `INTERNAL_ERROR` | 伺服器內部錯誤 |

---

## 驗證規則

### 前端驗證

- 提交 Agent 時，`investment_preferences` 應為字串陣列
- 驗證股票代碼格式 (4 位數字 + 可選字母)
- `color_theme` 須為有效 RGB 格式：`\d{1,3},\s*\d{1,3},\s*\d{1,3}`
- `strategy_prompt` 最少 10 個字

### 後端驗證

- 接收 `investment_preferences` 為字串陣列，不進行 JSON 序列化
- 驗證每個股票代碼的有效性
- 驗證 `ai_model` 存在於資料庫
- 回應時確保格式一致性

---

## 契約測試範例

### 後端 (Python/pytest)

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_agents_response_schema():
    """驗證代理人列表回應符合契約"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/agents")
        assert response.status_code == 200

        agents = response.json()
        assert isinstance(agents, list)

        for agent in agents:
            # 驗證必填欄位
            assert isinstance(agent["id"], str)
            assert isinstance(agent["name"], str)
            assert isinstance(agent["investment_preferences"], list)
            assert all(isinstance(p, str) for p in agent["investment_preferences"])
            assert isinstance(agent["enabled_tools"], dict)
            assert "created_at" in agent
            assert "updated_at" in agent


@pytest.mark.asyncio
async def test_create_agent_validates_input():
    """驗證建立代理人的輸入驗證"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 缺少必填欄位
        response = await client.post("/api/agents", json={"name": "test"})
        assert response.status_code == 422

        # strategy_prompt 過短
        response = await client.post("/api/agents", json={
            "name": "test",
            "strategy_prompt": "short",
            "ai_model": "gpt-4o"
        })
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_agent_crud_lifecycle():
    """驗證代理人 CRUD 完整周期"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create
        create_resp = await client.post("/api/agents", json={
            "name": "Test Agent",
            "strategy_prompt": "This is a test strategy",
            "ai_model": "gpt-4o-mini",
            "investment_preferences": ["2330", "2454"]
        })
        assert create_resp.status_code == 201
        agent = create_resp.json()
        agent_id = agent["id"]
        assert agent["investment_preferences"] == ["2330", "2454"]

        # Read
        get_resp = await client.get(f"/api/agents/{agent_id}")
        assert get_resp.status_code == 200
        retrieved = get_resp.json()
        assert retrieved["id"] == agent_id
        assert retrieved["investment_preferences"] == ["2330", "2454"]

        # Update
        update_resp = await client.put(f"/api/agents/{agent_id}", json={
            "name": "Updated Agent",
            "investment_preferences": ["0050"]
        })
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["name"] == "Updated Agent"
        assert updated["investment_preferences"] == ["0050"]

        # Delete
        delete_resp = await client.delete(f"/api/agents/{agent_id}")
        assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_portfolio_data_integrity():
    """驗證投資組合資料完整性"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/trading/agents/agent_123/portfolio")
        assert response.status_code == 200

        portfolio = response.json()
        assert "cash" in portfolio
        assert "total_value" in portfolio
        assert "positions" in portfolio
        assert "timestamp" in portfolio

        # 驗證持股資料結構
        for ticker, position in portfolio["positions"].items():
            assert isinstance(ticker, str)
            assert all(k in position for k in [
                "quantity", "avg_price", "current_price",
                "total_value", "gain_loss", "gain_loss_percent"
            ])
```

### 前端 (TypeScript/Jest)

```typescript
describe('API Contract Validation', () => {
  it('should receive agent with correct investment_preferences format', async () => {
    const response = await fetch('/api/agents/agent_123');
    const agent = await response.json();

    expect(Array.isArray(agent.investment_preferences)).toBe(true);
    expect(agent.investment_preferences.every((p: unknown) => typeof p === 'string')).toBe(true);
  });

  it('should receive enabled_tools as object not string', async () => {
    const response = await fetch('/api/agents');
    const agents = await response.json();

    agents.forEach((agent: any) => {
      expect(typeof agent.enabled_tools).toBe('object');
      expect(agent.enabled_tools).not.toBeNull();
      expect(typeof agent.enabled_tools.fundamental_analysis).toBe('boolean');
    });
  });

  it('should parse timestamps as ISO 8601 strings', async () => {
    const response = await fetch('/api/agents/agent_123');
    const agent = await response.json();

    const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$/;
    expect(isoRegex.test(agent.created_at)).toBe(true);
    expect(isoRegex.test(agent.updated_at)).toBe(true);
  });

  it('should handle CRUD operations maintaining data contracts', async () => {
    // Create
    const createResp = await fetch('/api/agents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Test Agent',
        strategy_prompt: 'This is a test strategy that is long enough',
        ai_model: 'gpt-4o-mini',
        investment_preferences: ['2330', '2454']
      })
    });
    const created = await createResp.json();

    // Verify response format
    expect(Array.isArray(created.investment_preferences)).toBe(true);
    expect(typeof created.enabled_tools).toBe('object');

    const agentId = created.id;

    // Update
    const updateResp = await fetch(`/api/agents/${agentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        investment_preferences: ['0050']
      })
    });
    const updated = await updateResp.json();
    expect(updated.investment_preferences).toEqual(['0050']);

    // Delete
    await fetch(`/api/agents/${agentId}`, { method: 'DELETE' });
  });
});
```

---

## 維護原則

1. **契約先行**: 修改 API 前先更新本契約文件
2. **版本管理**: 重大變更時更新版本號並記錄
3. **自動測試**: 每次變更都執行契約測試
4. **文件同步**: 實作與本文件必須保持同步
5. **向後相容性**: 避免破壞性變更，若必要則提供遷移路徑

---

## 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 1.0 | 2025-10-22 | 初始版本，包含所有實現的端點 |
