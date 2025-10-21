# API 參考文檔

**版本**: 1.0
**最後更新**: 2025-10-21
**狀態**: ✅ 已實施

## 概述

CasualTrader API 提供 RESTful 端點來管理和執行 AI 交易代理。

### 基礎 URL

```
http://localhost:8000/api
```

### 認證

目前無認證機制（開發環境）

---

## 端點列表

### 1. 健康檢查

#### GET /health

檢查 API 服務狀態。

**請求**:
```http
GET /api/health
```

**響應** (200 OK):
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2025-10-21T15:18:55.601Z"
}
```

---

### 2. 獲取 Agents 列表

#### GET /agents

獲取所有可用的代理列表。

**請求**:
```http
GET /api/agents
```

**響應** (200 OK):
```json
[
  {
    "id": "agent-001",
    "name": "Agent 1",
    "status": "idle",
    "created_at": "2025-10-21T10:00:00Z",
    "last_run": "2025-10-21T15:00:00Z"
  },
  {
    "id": "agent-002",
    "name": "Agent 2",
    "status": "idle",
    "created_at": "2025-10-21T10:00:00Z"
  }
]
```

---

### 3. 啟動 Agent 執行模式

#### POST /agents/{agent_id}/start

**啟動指定代理執行指定模式**（執行完後立即返回）。

**端點**: `POST /api/agents/{agent_id}/start`

**路徑參數**:
| 參數 | 類型 | 必需 | 說明 |
|------|------|------|------|
| agent_id | string | ✅ | Agent 的唯一識別符 |

**請求體**:
```json
{
  "mode": "OBSERVATION",
  "max_turns": 10
}
```

**請求體參數**:
| 參數 | 類型 | 必需 | 說明 | 默認 | 限制 |
|------|------|------|------|------|------|
| mode | enum | ✅ | 執行模式 | - | OBSERVATION \| TRADING \| REBALANCING |
| max_turns | integer | ❌ | 最大執行輪數 | null | 1-50 |

**模式說明**:
- **OBSERVATION**: 觀察市場，收集數據，無交易
- **TRADING**: 執行交易決策和下單
- **REBALANCING**: 調整投資組合比例

**響應** (200 OK):
```json
{
  "success": true,
  "session_id": "session-001",
  "agent_id": "agent-001",
  "mode": "OBSERVATION",
  "status": "COMPLETED",
  "execution_time_ms": 1523,
  "result": {
    "observations": [
      {
        "symbol": "TSLA",
        "price": 250.50,
        "change": 2.5
      }
    ]
  }
}
```

**錯誤響應**:

#### 400 Bad Request - 無效的 mode 參數
```json
{
  "detail": "Invalid mode: INVALID_MODE"
}
```

#### 404 Not Found - Agent 不存在
```json
{
  "detail": "Agent agent-999 not found"
}
```

#### 409 Conflict - Agent 已在執行中
```json
{
  "detail": "Agent agent-001 is already running"
}
```

#### 500 Internal Server Error - 執行異常
```json
{
  "detail": "Execution failed: ..."
}
```

**使用示例**:
```bash
# 執行觀察模式
curl -X POST http://localhost:8000/api/agents/agent-001/start \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "OBSERVATION"
  }'

# 執行交易模式（最多 10 輪）
curl -X POST http://localhost:8000/api/agents/agent-001/start \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "TRADING",
    "max_turns": 10
  }'
```

---

### 4. 停止 Agent 執行

#### POST /agents/{agent_id}/stop

立即停止正在執行的代理。

**端點**: `POST /api/agents/{agent_id}/stop`

**路徑參數**:
| 參數 | 類型 | 必需 | 說明 |
|------|------|------|------|
| agent_id | string | ✅ | Agent 的唯一識別符 |

**請求體**:
```json
{}
```

**響應** (200 OK):
```json
{
  "success": true,
  "agent_id": "agent-001",
  "status": "stopped",
  "session_id": "session-001"
}
```

**錯誤響應**:

#### 404 Not Found - Agent 不存在
```json
{
  "detail": "Agent agent-999 not found"
}
```

#### 400 Bad Request - Agent 未在執行
```json
{
  "detail": "Agent agent-001 is not running"
}
```

**使用示例**:
```bash
curl -X POST http://localhost:8000/api/agents/agent-001/stop \
  -H "Content-Type: application/json"
```

---

## 數據模型

### Agent 對象

```typescript
interface Agent {
  id: string;              // Agent 唯一識別符
  name: string;            // Agent 名稱
  status: AgentStatus;     // 狀態：idle | running | stopped | error
  created_at: ISO8601;     // 創建時間
  last_run?: ISO8601;      // 最後運行時間
  config?: AgentConfig;    // 配置信息
}
```

### 執行結果

```typescript
interface ExecutionResult {
  success: boolean;        // 是否成功
  session_id: string;      // 會話 ID
  agent_id: string;        // Agent ID
  mode: AgentMode;         // 執行模式
  status: SessionStatus;   // 會話狀態
  execution_time_ms: number; // 執行時間（毫秒）
  result?: any;            // 執行結果數據
  error?: string;          // 錯誤信息
}
```

### 枚舉定義

#### AgentMode
```typescript
enum AgentMode {
  OBSERVATION = "OBSERVATION",
  TRADING = "TRADING",
  REBALANCING = "REBALANCING"
}
```

#### SessionStatus
```typescript
enum SessionStatus {
  PENDING = "PENDING",
  RUNNING = "RUNNING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  CANCELLED = "CANCELLED"
}
```

---

## HTTP 狀態碼

| 狀態碼 | 說明 | 常見情況 |
|--------|------|---------|
| 200 | OK | 請求成功 |
| 400 | Bad Request | 無效的請求參數 |
| 404 | Not Found | 資源不存在 |
| 409 | Conflict | 資源狀態衝突（如 Agent 已在執行） |
| 500 | Internal Server Error | 伺服器錯誤 |

---

## 常見用例

### 用例 1: 連續執行三個模式

```bash
# 1. 先執行觀察
curl -X POST http://localhost:8000/api/agents/agent-001/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "OBSERVATION"}'

# 2. 等待執行完成（響應會自動返回）

# 3. 執行交易
curl -X POST http://localhost:8000/api/agents/agent-001/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "TRADING", "max_turns": 5}'

# 4. 執行再平衡
curl -X POST http://localhost:8000/api/agents/agent-001/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "REBALANCING"}'
```

### 用例 2: 中途停止執行

```bash
# 1. 啟動長時間執行
curl -X POST http://localhost:8000/api/agents/agent-001/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "TRADING", "max_turns": 20}'

# 2. 如果需要中途停止（在另一個終端）
curl -X POST http://localhost:8000/api/agents/agent-001/stop \
  -H "Content-Type: application/json"
```

### 用例 3: 並發檢測

```bash
# 終端 1: 啟動執行
curl -X POST http://localhost:8000/api/agents/agent-001/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "TRADING"}'

# 終端 2: 嘗試同時啟動（將被拒絕）
curl -X POST http://localhost:8000/api/agents/agent-001/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "OBSERVATION"}'
# 響應: 409 Conflict - Agent already running
```

---

## 錯誤處理

所有錯誤響應都遵循以下格式：

```json
{
  "detail": "Error message describing what went wrong"
}
```

### 常見錯誤及解決方法

| 錯誤 | 原因 | 解決方法 |
|------|------|---------|
| 404 Not Found | Agent 不存在 | 檢查 Agent ID 是否正確 |
| 409 Conflict | Agent 已在執行 | 等待當前執行完成後重試 |
| 400 Bad Request | 無效的 mode 參數 | 檢查 mode 是否為有效值 |
| 500 Server Error | 伺服器異常 | 查看伺服器日誌 |

---

## 限制和配額

| 限制項 | 值 | 說明 |
|--------|-----|------|
| Max Agents | 10 | 最多 10 個並發 Agent |
| Max Turns | 50 | 單次執行最多 50 輪 |
| Request Timeout | 300s | 請求超時時間 |

---

## WebSocket 支持

WebSocket 端點用於實時監控代理執行狀態（計劃中）。

```
ws://localhost:8000/ws
```

---

## 版本歷史

### v1.0 (2025-10-21)
- ✅ 初始版本發佈
- ✅ 3 個核心端點
- ✅ 單一模式執行支持
- ✅ 完整的錯誤處理

---

## 相關文檔

- [設計概述](./DESIGN_OVERVIEW.md) - 架構和設計決策
- [實施指南](./IMPLEMENTATION_GUIDE.md) - 詳細實施步驟
- [整合測試報告](./INTEGRATION_TEST_REPORT.md) - 測試結果
- [遷移檢查清單](./MIGRATION_CHECKLIST.md) - 部署檢查清單

---

**最後更新**: 2025-10-21
**維護者**: CasualTrader Team
