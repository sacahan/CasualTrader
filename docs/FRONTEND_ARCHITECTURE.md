# CasualTrader Frontend 模組架構說明

## 目錄

1. [總覽](#總覽)
2. [技術棧](#技術棧)
3. [專案結構](#專案結構)
4. [組件層 (components/)](#組件層-components)
5. [路由層 (routes/)](#路由層-routes)
6. [狀態管理 (stores/)](#狀態管理-stores)
7. [API 層 (lib/api.js)](#api-層-libapijs)
8. [WebSocket 層 (lib/websocket.js)](#websocket-層-libwebsocketjs)
9. [工具層 (lib/utils.js)](#工具層-libutilsjs)
10. [模組依賴關係](#模組依賴關係)
11. [資料流向](#資料流向)
12. [組件互動](#組件互動)

---

## 總覽

`frontend/` 目錄是 CasualTrader 的前端應用，使用 **Vite + Svelte** 構建現代化的單頁應用（SPA），提供即時、響應式的用戶界面。

### 設計理念

- **組件化設計**: 可重用的 Svelte 組件
- **響應式狀態**: Svelte Store 集中式狀態管理
- **即時通訊**: WebSocket 雙向數據流
- **視覺化優先**: Chart.js 圖表展示
- **Prompt 驅動**: Agent 配置採用自然語言輸入
- **透明度優先**: 完整展示 Agent 決策過程和策略演化

### 核心特色

- ⚡ **Vite 構建**: 極快的熱重載和構建速度
- 🎨 **Tailwind CSS**: 實用優先的 CSS 框架
- 📊 **Chart.js 整合**: 豐富的圖表視覺化
- 🔄 **即時更新**: WebSocket 推送 Agent 狀態和交易事件
- 📱 **響應式設計**: 適配桌面和移動設備
- 🤖 **AI Agent 管理**: 完整的 Agent 創建、監控和配置界面

---

## 技術棧

### 核心框架

- **Vite 5.x**: 次世代前端構建工具
- **Svelte 4.x**: 編譯型 UI 框架
- **SvelteKit**: Svelte 應用框架（可選）

### UI 和樣式

- **Tailwind CSS 3.x**: 實用優先的 CSS 框架
- **PostCSS**: CSS 後處理器
- **Chart.js**: 圖表庫

### 狀態和數據

- **Svelte Store**: 響應式狀態管理
- **WebSocket API**: 瀏覽器原生 WebSocket
- **Fetch API**: HTTP 請求

### 開發工具

- **TypeScript** (可選): 類型安全
- **ESLint**: 代碼檢查
- **Prettier**: 代碼格式化

---

## 專案結構

```text
frontend/
├── public/                # 靜態資源
│   ├── vite.svg
│   └── favicon.ico
├── src/                   # 前端源代碼
│   ├── App.svelte         # 主應用程式組件
│   ├── main.js            # Vite 進入點
│   ├── app.css            # 全域樣式（Tailwind）
│   │
│   ├── components/        # 可重用組件
│   │   ├── Layout/        # 佈局組件
│   │   │   ├── Navbar.svelte
│   │   │   ├── Sidebar.svelte
│   │   │   └── Footer.svelte
│   │   │
│   │   ├── Agent/         # Agent 相關組件
│   │   │   ├── AgentCard.svelte           # Agent 基礎卡片
│   │   │   ├── AgentGrid.svelte           # Agent 網格布局
│   │   │   ├── AgentModal.svelte          # Agent 彈窗
│   │   │   ├── AgentCreationForm.svelte   # Agent 創建表單（Prompt驅動）
│   │   │   ├── AgentDashboard.svelte      # Agent 監控儀表板
│   │   │   ├── AgentConfigEditor.svelte   # Agent 配置編輯器
│   │   │   ├── AgentToolsSelector.svelte  # Agent Tools 選擇器
│   │   │   ├── AgentPerformancePanel.svelte # Agent 績效面板
│   │   │   ├── StrategyHistoryView.svelte # 策略變更歷史
│   │   │   └── StrategyChangeModal.svelte # 策略變更詳情彈窗
│   │   │
│   │   ├── Chart/         # 圖表組件
│   │   │   ├── PerformanceChart.svelte
│   │   │   ├── MarketChart.svelte
│   │   │   └── PortfolioChart.svelte
│   │   │
│   │   ├── Market/        # 市場相關組件
│   │   │   ├── MarketPanel.svelte
│   │   │   ├── StockQuote.svelte
│   │   │   └── IndexDisplay.svelte
│   │   │
│   │   └── UI/            # 基礎 UI 組件
│   │       ├── Button.svelte
│   │       ├── Modal.svelte
│   │       ├── StatusIndicator.svelte
│   │       ├── LoadingSpinner.svelte
│   │       └── Tooltip.svelte
│   │
│   ├── routes/            # SvelteKit 路由頁面（如使用 SvelteKit）
│   │   ├── +layout.svelte
│   │   ├── +page.svelte   # 主儀表板
│   │   ├── agents/        # Agent 管理頁面
│   │   │   ├── +page.svelte
│   │   │   └── [id]/
│   │   │       └── +page.svelte
│   │   └── settings/      # 設定頁面
│   │       └── +page.svelte
│   │
│   ├── stores/            # Svelte stores 狀態管理
│   │   ├── agents.js      # Agent 狀態管理
│   │   ├── websocket.js   # WebSocket 連線狀態
│   │   ├── market.js      # 市場數據狀態
│   │   └── notifications.js # 通知系統
│   │
│   ├── lib/               # 前端工具函數
│   │   ├── api.js         # API 客戶端
│   │   ├── websocket.js   # WebSocket 管理
│   │   ├── utils.js       # 共用工具（格式化、驗證等）
│   │   └── constants.js   # 前端常數
│   │
│   └── types/             # TypeScript 類型定義（如使用 TS）
│       ├── agent.ts       # Agent 類型
│       ├── api.ts         # API 類型
│       └── websocket.ts   # WebSocket 類型
│
├── vite.config.js         # Vite 配置
├── tailwind.config.js     # Tailwind CSS 配置
├── postcss.config.js      # PostCSS 配置
├── package.json           # NPM 配置
└── tsconfig.json          # TypeScript 配置（可選）
```

---

## 組件層 (components/)

### Layout 組件

#### Navbar.svelte - 導航欄

**功能**:

- 應用標題和 Logo
- 主導航選單
- 用戶狀態顯示
- WebSocket 連線狀態指示器

**狀態依賴**:

- `websocket` store: 顯示連線狀態

#### Sidebar.svelte - 側邊欄

**功能**:

- Agent 列表快速導航
- 系統狀態摘要
- 快捷操作按鈕

**狀態依賴**:

- `agents` store: Agent 列表

---

### Agent 組件

#### AgentCard.svelte - Agent 基礎卡片

**功能**:

- 顯示 Agent 基本資訊（名稱、描述、狀態）
- 顯示當前模式和績效摘要
- 提供快速操作按鈕（啟動、停止、查看詳情）
- 狀態顏色編碼（運行中、停止、錯誤）

**Props**:

```javascript
export let agent; // Agent 資料對象
export let compact = false; // 緊湊模式
```

**事件**:

```javascript
dispatch('start', { agentId: agent.id });
dispatch('stop', { agentId: agent.id });
dispatch('view', { agentId: agent.id });
```

**狀態依賴**:

- `agents` store: 訂閱 Agent 狀態更新

---

#### AgentGrid.svelte - Agent 網格布局

**功能**:

- 響應式網格佈局展示所有 Agents
- 支援排序和篩選
- 空狀態提示

**狀態依賴**:

- `agents` store: 訂閱 Agent 列表

---

#### AgentCreationForm.svelte - Agent 創建表單（Prompt 驅動設計）

> 參考: AGENT_IMPLEMENTATION.md - 前端 Agent 配置介面

**功能**:

- **自然語言輸入**: 投資偏好和策略調整依據
- **即時指令預覽**: 顯示生成的 Agent 指令
- **模型選擇**: 下拉選單選擇 AI 模型（GPT-4o, Claude 等）
- **進階設定**: 初始資金、風險容忍度、排除股票等
- **表單驗證**: 即時驗證輸入合法性

**表單欄位**:

```javascript
// 基本資訊
let name = '';
let description = '';
let ai_model = 'gpt-4o';
let initial_funds = 1000000;

// Prompt 驅動配置
let investment_preferences = ''; // 大型文字框
let strategy_adjustment_criteria = ''; // 大型文字框

// 進階設定
let max_position_size = 20;
let excluded_symbols = '';
let additional_instructions = '';

// 工具選擇
let enabled_tools = {
  fundamental: true,
  technical: true,
  sentiment: true,
  risk: true
};
```

**即時預覽**:

```javascript
$: generatedPrompt = generateAgentPrompt({
  description,
  investment_preferences,
  strategy_adjustment_criteria,
  initial_funds,
  max_position_size,
  excluded_symbols,
  additional_instructions
});
```

**提交處理**:

```javascript
async function handleSubmit() {
  try {
    const response = await api.createAgent({
      name,
      description,
      ai_model,
      strategy_prompt: generatedPrompt,
      initial_funds,
      enabled_tools,
      investment_preferences: { text: investment_preferences },
      custom_instructions: additional_instructions
    });

    dispatch('created', { agent: response.data });
  } catch (error) {
    // 錯誤處理
  }
}
```

---

#### AgentConfigEditor.svelte - Agent 配置編輯器

> ⚠️ **重要**: 實作配置鎖定機制

**功能**:

- 編輯已創建的 Agent 配置
- **執行時鎖定**: Agent 運行時禁用編輯
- 配置鎖定橫幅提示
- 保存變更確認

**鎖定檢查**:

```javascript
$: isLocked = agent.status === 'running' || agent.status === 'active';
$: lockReason = isLocked
  ? 'Agent 執行期間無法修改配置，請先停止 Agent'
  : null;
```

**UI 控制**:

```svelte
<div class="config-editor">
  {#if isLocked}
    <div class="config-lock-banner">
      <Icon name="lock" />
      <span>{lockReason}</span>
    </div>
  {/if}

  <textarea
    bind:value={investment_preferences}
    disabled={isLocked}
    class:locked={isLocked}
  />

  <Button
    on:click={handleSave}
    disabled={isLocked}
  >
    保存變更
  </Button>
</div>
```

---

#### StrategyHistoryView.svelte - 策略變更歷史

> 參考: AGENT_IMPLEMENTATION.md - 策略變更記錄系統

**功能**:

- **時間軸視圖**: 按時間順序展示策略變更
- **變更類型標籤**: 自動調整、手動調整、績效驅動
- **觸發原因**: 清楚說明為何觸發策略調整
- **績效背景**: 變更時的報酬率、回撤、夏普比率等
- **Agent 說明**: Agent 對策略調整的解釋
- **變更內容對比**: 新舊策略的差異展示

**數據獲取**:

```javascript
import { onMount } from 'svelte';
import { api } from '$lib/api';

let strategyChanges = [];
let loading = true;

onMount(async () => {
  try {
    const response = await api.getStrategyChanges(agentId);
    strategyChanges = response.data;
  } catch (error) {
    console.error('Failed to load strategy changes:', error);
  } finally {
    loading = false;
  }
});
```

**時間軸渲染**:

```svelte
<div class="timeline">
  {#each strategyChanges as change, index}
    <div class="timeline-item">
      <div class="timeline-marker" class:first={index === 0}>
        <Icon name={change.change_type} />
      </div>

      <div class="timeline-content">
        <div class="change-header">
          <span class="change-type">{change.change_type}</span>
          <span class="change-date">{formatDate(change.timestamp)}</span>
        </div>

        <div class="trigger-reason">
          <strong>觸發原因:</strong> {change.trigger_reason}
        </div>

        <div class="performance-context">
          <div class="metric">
            <span>報酬率:</span>
            <span class:positive={change.performance_context.return_rate > 0}>
              {change.performance_context.return_rate}%
            </span>
          </div>
          <div class="metric">
            <span>最大回撤:</span>
            <span>{change.performance_context.max_drawdown}%</span>
          </div>
          <div class="metric">
            <span>夏普比率:</span>
            <span>{change.performance_context.sharpe_ratio}</span>
          </div>
        </div>

        <div class="agent-explanation">
          <strong>Agent 說明:</strong>
          <p>{change.agent_explanation}</p>
        </div>

        <Button on:click={() => showDiff(change)}>
          查看變更內容
        </Button>
      </div>
    </div>
  {/each}
</div>
```

---

#### StrategyChangeModal.svelte - 策略變更詳情彈窗

**功能**:

- 顯示策略變更的完整內容
- 新舊策略對比（diff view）
- 相關交易記錄
- 績效影響分析

---

#### AgentDashboard.svelte - Agent 監控儀表板

**功能**:

- Agent 狀態總覽
- 實時績效圖表
- 最近交易列表
- 當前持倉展示
- 模式切換控制

**狀態依賴**:

- `agents` store: Agent 狀態
- `websocket` store: 即時事件

---

#### AgentPerformancePanel.svelte - Agent 績效面板

**功能**:

- 總報酬率和年化報酬率
- 最大回撤和夏普比率
- 勝率和平均獲利
- 績效圖表（Chart.js）

---

### Chart 組件

#### PerformanceChart.svelte - 績效圖表

**功能**:

- 淨值曲線圖
- 累積報酬率
- 回撤曲線
- 基準比較（大盤指數）

**技術實作**:

```javascript
import { onMount } from 'svelte';
import Chart from 'chart.js/auto';

let chartCanvas;
let chartInstance;

onMount(() => {
  chartInstance = new Chart(chartCanvas, {
    type: 'line',
    data: {
      labels: dates,
      datasets: [{
        label: 'Portfolio Value',
        data: values,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: { mode: 'index', intersect: false }
      }
    }
  });

  return () => {
    chartInstance.destroy();
  };
});
```

---

## 路由層 (routes/)

> 如使用 SvelteKit，採用檔案系統路由

### +page.svelte - 主儀表板

**功能**:

- 所有 Agents 總覽
- 系統狀態摘要
- 市場數據展示
- 創建 Agent 按鈕

---

### agents/+page.svelte - Agent 列表頁

**功能**:

- Agent 網格佈局
- 篩選和排序
- 批量操作

---

### agents/[id]/+page.svelte - Agent 詳情頁

**功能**:

- Agent 完整資訊
- 投資組合詳情
- 交易歷史
- 策略變更歷史
- 配置編輯

**數據載入**:

```javascript
import { page } from '$app/stores';

export async function load({ params }) {
  const agentId = params.id;
  const agent = await api.getAgent(agentId);
  const portfolio = await api.getPortfolio(agentId);
  const transactions = await api.getTransactions(agentId);

  return {
    agent,
    portfolio,
    transactions
  };
}
```

---

## 狀態管理 (stores/)

### agents.js - Agent 狀態管理

**功能**:

- 管理所有 Agent 的狀態
- 提供 Agent CRUD 操作
- 訂閱 WebSocket 更新

**實作**:

```javascript
import { writable, derived } from 'svelte/store';
import { api } from '$lib/api';

function createAgentsStore() {
  const { subscribe, set, update } = writable([]);

  return {
    subscribe,

    // 載入所有 Agents
    async load() {
      const response = await api.getAgents();
      set(response.data.agents);
    },

    // 創建 Agent
    async create(agentData) {
      const response = await api.createAgent(agentData);
      update(agents => [...agents, response.data]);
      return response.data;
    },

    // 更新 Agent
    updateAgent(agentId, updates) {
      update(agents => agents.map(agent =>
        agent.id === agentId ? { ...agent, ...updates } : agent
      ));
    },

    // 刪除 Agent
    async remove(agentId) {
      await api.deleteAgent(agentId);
      update(agents => agents.filter(agent => agent.id !== agentId));
    }
  };
}

export const agents = createAgentsStore();

// Derived stores
export const runningAgents = derived(
  agents,
  $agents => $agents.filter(agent => agent.status === 'running')
);

export const agentCount = derived(agents, $agents => $agents.length);
```

---

### websocket.js - WebSocket 連線狀態

**功能**:

- 管理 WebSocket 連接
- 處理連線狀態
- 分發事件到對應的 stores

**實作**:

```javascript
import { writable } from 'svelte/store';
import { agents } from './agents';

function createWebSocketStore() {
  const { subscribe, set } = writable({
    connected: false,
    connecting: false,
    error: null
  });

  let ws = null;

  return {
    subscribe,

    connect(url = 'ws://localhost:8000/ws') {
      if (ws) return;

      set({ connected: false, connecting: true, error: null });
      ws = new WebSocket(url);

      ws.onopen = () => {
        set({ connected: true, connecting: false, error: null });
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMessage(message);
      };

      ws.onerror = (error) => {
        set({ connected: false, connecting: false, error: error.message });
      };

      ws.onclose = () => {
        set({ connected: false, connecting: false, error: null });
        ws = null;
      };
    },

    disconnect() {
      if (ws) {
        ws.close();
        ws = null;
      }
    },

    send(message) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
      }
    }
  };
}

function handleMessage(message) {
  switch (message.type) {
    case 'agent_status':
      agents.updateAgent(message.data.agent_id, {
        status: message.data.status
      });
      break;

    case 'agent_mode_change':
      agents.updateAgent(message.data.agent_id, {
        current_mode: message.data.to_mode
      });
      break;

    case 'trade_executed':
      // 更新投資組合
      break;

    case 'portfolio_update':
      // 更新投資組合數據
      break;
  }
}

export const websocket = createWebSocketStore();
```

---

### market.js - 市場數據狀態

**功能**:

- 管理市場數據（股價、指數等）
- 定期更新市場數據
- 提供市場狀態查詢

---

### notifications.js - 通知系統

**功能**:

- 管理系統通知
- 顯示成功/錯誤提示
- 自動消失的 Toast 通知

---

## API 層 (lib/api.js)

**功能**:

- 封裝所有 HTTP API 請求
- 統一錯誤處理
- 請求攔截器

**實作**:

```javascript
const API_BASE_URL = 'http://localhost:8000/api';

class ApiClient {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Agent APIs
  getAgents() {
    return this.request('/agents');
  }

  getAgent(agentId) {
    return this.request(`/agents/${agentId}`);
  }

  createAgent(agentData) {
    return this.request('/agents', {
      method: 'POST',
      body: JSON.stringify(agentData)
    });
  }

  startAgent(agentId, config = {}) {
    return this.request(`/agents/${agentId}/start`, {
      method: 'POST',
      body: JSON.stringify(config)
    });
  }

  stopAgent(agentId) {
    return this.request(`/agents/${agentId}/stop`, {
      method: 'POST'
    });
  }

  // Trading APIs
  getPortfolio(agentId) {
    return this.request(`/trading/agents/${agentId}/portfolio`);
  }

  getTransactions(agentId) {
    return this.request(`/trading/agents/${agentId}/transactions`);
  }

  // Strategy Change APIs
  getStrategyChanges(agentId) {
    return this.request(`/agents/${agentId}/strategy-changes`);
  }
}

export const api = new ApiClient();
```

---

## WebSocket 層 (lib/websocket.js)

**功能**:

- 管理 WebSocket 連接生命週期
- 自動重連機制
- 心跳檢測

**實作**:

```javascript
export class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.handlers = new Map();
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
      this.stopHeartbeat();
      this.attemptReconnect();
    };
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  on(eventType, handler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType).push(handler);
  }

  handleMessage(message) {
    const handlers = this.handlers.get(message.type) || [];
    handlers.forEach(handler => handler(message.data));
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;
      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'ping' });
    }, 30000); // 30 seconds
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
  }
}
```

---

## 工具層 (lib/utils.js)

**功能**:

- 通用工具函數
- 格式化函數
- 驗證函數

**實作**:

```javascript
// 格式化貨幣
export function formatCurrency(value, currency = 'TWD') {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: currency
  }).format(value);
}

// 格式化百分比
export function formatPercent(value, decimals = 2) {
  return `${value.toFixed(decimals)}%`;
}

// 格式化日期
export function formatDate(date, format = 'short') {
  const options = format === 'short'
    ? { year: 'numeric', month: '2-digit', day: '2-digit' }
    : { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };

  return new Intl.DateTimeFormat('zh-TW', options).format(new Date(date));
}

// 格式化數字
export function formatNumber(value, decimals = 0) {
  return new Intl.NumberFormat('zh-TW', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
}

// 計算顏色（基於值的正負）
export function getValueColor(value) {
  if (value > 0) return 'text-green-600';
  if (value < 0) return 'text-red-600';
  return 'text-gray-600';
}

// 驗證 Agent 名稱
export function validateAgentName(name) {
  return name.length >= 1 && name.length <= 100;
}

// 驗證資金金額
export function validateFunds(amount) {
  return amount >= 100000 && amount <= 10000000;
}
```

---

## 模組依賴關係

```text
App.svelte (主應用)
├── routes/ (頁面)
│   └── components/ (UI 組件)
│       ├── stores/ (狀態管理)
│       ├── lib/api.js (HTTP API)
│       └── lib/websocket.js (WebSocket)
│
stores/ (狀態管理)
├── agents.js
│   └── lib/api.js
├── websocket.js
│   └── agents.js (事件分發)
└── market.js
    └── lib/api.js

lib/
├── api.js (獨立模組)
├── websocket.js (獨立模組)
└── utils.js (獨立模組)
```

---

## 資料流向

### 用戶操作 → API 請求

```text
User Action (Button Click)
    ↓
Component Event Handler
    ↓
Store Action (agents.create())
    ↓
API Client (api.createAgent())
    ↓
HTTP Request to Backend
    ↓
Response
    ↓
Store Update
    ↓
UI Re-render
```

### WebSocket 推送 → UI 更新

```text
Backend Event (Agent Status Change)
    ↓
WebSocket Message
    ↓
WebSocket Client Handler
    ↓
Store Update (agents.updateAgent())
    ↓
Reactive UI Update (Svelte Reactivity)
```

---

## 組件互動

### Agent 創建流程

```text
1. User clicks "創建 Agent" in AgentGrid
2. Open AgentCreationForm modal
3. User fills form (investment_preferences, etc.)
4. Real-time prompt preview updates
5. User clicks "創建"
6. Form validates input
7. Call api.createAgent()
8. Backend creates agent
9. Store updates (agents.create())
10. Modal closes
11. New AgentCard appears in grid
12. WebSocket pushes agent_created event
```

### Agent 啟動流程

```text
1. User clicks "啟動" in AgentCard
2. Call api.startAgent(agentId)
3. Backend starts agent execution
4. Response confirms start
5. AgentCard status changes to "運行中"
6. WebSocket continuously pushes:
   - agent_status
   - trade_executed
   - portfolio_update
7. UI updates in real-time
```

---

## 性能優化

### Svelte 優化

- **編譯時優化**: Svelte 在構建時編譯為高效的 JavaScript
- **響應式更新**: 只更新變更的 DOM 節點
- **懶加載**: 使用動態 import 懶加載路由組件

### Vite 優化

- **熱重載**: 極快的 HMR（熱模塊替換）
- **按需編譯**: 只編譯當前使用的模組
- **Tree Shaking**: 自動移除未使用的代碼

### WebSocket 優化

- **心跳檢測**: 檢測斷線並自動重連
- **消息批處理**: 批量處理多個事件更新
- **訂閱過濾**: 只接收訂閱的 Agent 事件

---

## 測試策略

### 組件測試

- 使用 `@testing-library/svelte` 測試組件
- 測試用戶交互和事件處理
- 測試條件渲染和響應式更新

### Store 測試

- 測試 store 的 actions 和 derived stores
- 測試 API 調用和錯誤處理

### E2E 測試

- 使用 Playwright 或 Cypress
- 測試完整的用戶流程
- 測試 WebSocket 即時更新

---

## 部署建議

### 開發環境

```bash
npm run dev
# 或
vite
```

### 生產構建

```bash
npm run build
# 輸出到 dist/
```

### 靜態部署

```bash
# 部署到 Vercel, Netlify 等
npm run build
# 上傳 dist/ 目錄
```

---

## 總結

CasualTrader Frontend 採用現代化的 Vite + Svelte 架構，提供：

- ⚡ **極速開發體驗**: Vite 熱重載 + Svelte 編譯優化
- 🎨 **優雅 UI**: Tailwind CSS + 自定義組件
- 🔄 **即時響應**: WebSocket 雙向通訊 + Svelte Store 響應式狀態
- 📊 **豐富視覺化**: Chart.js 圖表整合
- 🤖 **Prompt 驅動**: 簡化 Agent 創建流程
- 📈 **透明追蹤**: 完整展示策略演化和決策過程
- 🔒 **配置保護**: 執行時配置鎖定機制

這個架構為用戶提供了直觀、高效、即時的 AI 交易模擬器體驗。
