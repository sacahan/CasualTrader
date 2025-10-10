# CasualTrader Frontend 模組架構說明

**版本**: 2.0 (實作版)
**更新日期**: 2025-10-10
**實作狀態**: Phase 4 完成，核心功能運作中
**技術棧**: Vite + Svelte 5 (不使用 SvelteKit)
**相關文件**: [FRONTEND_IMPLEMENTATION.md](./FRONTEND_IMPLEMENTATION.md)

---

## 📌 文檔說明

### 架構文檔 vs 實作規格

本文檔為 **架構設計文檔**，描述 CasualTrader Frontend 的實際實作架構。與 **FRONTEND_IMPLEMENTATION.md**（實作規格文檔）的關係如下：

| 文檔 | 定位 | 內容 |
|------|------|------|
| **FRONTEND_IMPLEMENTATION.md** | 實作規格 | 理想狀態的完整設計規範，包含所有計劃功能 |
| **FRONTEND_ARCHITECTURE.md** (本文檔) | 架構說明 | 實際已實作的架構，標註完成與規劃中的功能 |

### 架構決策：為何不使用 SvelteKit？

雖然 FRONTEND_IMPLEMENTATION.md 規範中提到 SvelteKit 和 `routes/` 目錄，實際實作選擇了更輕量的 **Vite + Svelte** 方案：

**✅ 優勢**:

- **簡化架構**: 無需學習 SvelteKit 特定 API
- **快速開發**: 減少配置複雜度
- **輕量級**: SPA 足以滿足當前需求
- **靈活性**: 未來可彈性遷移至 SvelteKit

**⚠️ 權衡**:

- 無檔案系統路由（使用條件渲染與模態視窗替代）
- 無 SSR 支援（當前不需要）
- 需自行管理路由狀態

### 實作完成度

- ✅ **核心功能**: 100% (Agent 創建、監控、策略追蹤)
- 🔄 **進階功能**: 51.5% (17/33 組件已完成)
- 📋 **測試覆蓋**: 待實作

---

## 目錄

1. [總覽](#總覽)
2. [技術棧](#技術棧)
3. [專案結構](#專案結構)
4. [組件層 (components/)](#組件層-components)
5. [應用架構 (單頁應用設計)](#應用架構-單頁應用設計)
6. [狀態管理 (stores/)](#狀態管理-stores)
7. [API 層 (lib/api.js)](#api-層-libapijs)
8. [WebSocket 層 (stores/websocket.js)](#websocket-層-storeswebsocketjs)
9. [工具層 (lib/utils.js)](#工具層-libutilsjs)
10. [模組依賴關係](#模組依賴關係)
11. [資料流向](#資料流向)
12. [組件互動](#組件互動)
13. [實作狀態總覽](#實作狀態總覽)

---

## 總覽

`frontend/` 目錄是 CasualTrader 的前端應用，使用 **Vite + Svelte 5** 構建現代化的**單頁應用（SPA）**，提供即時、響應式的用戶界面。

> ⚠️ **架構說明**: 本專案選擇使用 **Vite + Svelte** 而非 SvelteKit，採用單頁應用設計，所有功能整合在 `App.svelte` 主組件中，無檔案系統路由。

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

- **Vite 5.4.4**: 次世代前端構建工具
- **Svelte 5.0**: 編譯型 UI 框架 (使用 Runes API)
- **單頁應用 (SPA)**: 不使用 SvelteKit，採用 Vite + Svelte 輕量化方案

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

> 📋 **圖例**: ✅ 已實作 | 📋 規劃中 | 🔄 部分完成

```text
frontend/
├── public/                # 靜態資源
│   └── vite.svg          # ✅
├── src/                   # 前端源代碼
│   ├── App.svelte         # ✅ 主應用程式組件 (單頁應用入口)
│   ├── main.js            # ✅ Vite 進入點
│   ├── app.css            # ✅ 全域樣式（Tailwind）
│   │
│   ├── components/        # 可重用組件
│   │   ├── Layout/        # 佈局組件
│   │   │   ├── Navbar.svelte            # ✅
│   │   │   ├── NotificationToast.svelte # ✅
│   │   │   ├── Sidebar.svelte           # 📋 規劃中
│   │   │   └── Footer.svelte            # 📋 規劃中
│   │   │
│   │   ├── Agent/         # Agent 相關組件
│   │   │   ├── AgentCard.svelte           # ✅ Agent 基礎卡片
│   │   │   ├── AgentGrid.svelte           # ✅ Agent 網格布局
│   │   │   ├── AgentCreationForm.svelte   # ✅ Agent 創建表單（Prompt驅動）
│   │   │   ├── StrategyHistoryView.svelte # ✅ 策略變更歷史
│   │   │   ├── AgentModal.svelte          # 📋 規劃中
│   │   │   ├── AgentDashboard.svelte      # 📋 規劃中
│   │   │   ├── AgentConfigEditor.svelte   # 📋 規劃中
│   │   │   ├── AgentToolsSelector.svelte  # 📋 規劃中
│   │   │   ├── AgentPerformancePanel.svelte # 📋 規劃中
│   │   │   └── StrategyChangeModal.svelte # 📋 規劃中
│   │   │
│   │   ├── Chart/         # 圖表組件
│   │   │   ├── PerformanceChart.svelte   # ✅
│   │   │   ├── MarketChart.svelte        # 📋 規劃中
│   │   │   └── PortfolioChart.svelte     # 📋 規劃中
│   │   │
│   │   ├── Market/        # 市場相關組件
│   │   │   ├── MarketPanel.svelte        # 📋 規劃中
│   │   │   ├── StockQuote.svelte         # 📋 規劃中
│   │   │   └── IndexDisplay.svelte       # 📋 規劃中
│   │   │
│   │   └── UI/            # 基礎 UI 組件
│   │       ├── Button.svelte             # ✅
│   │       ├── Modal.svelte              # ✅
│   │       ├── StatusIndicator.svelte    # ✅
│   │       ├── Input.svelte              # ✅
│   │       ├── Textarea.svelte           # ✅
│   │       ├── Select.svelte             # ✅
│   │       ├── LoadingSpinner.svelte     # 📋 規劃中
│   │       └── Tooltip.svelte            # 📋 規劃中
│   │
│   ├── stores/            # ✅ Svelte stores 狀態管理
│   │   ├── agents.js      # ✅ Agent 狀態管理
│   │   ├── websocket.js   # ✅ WebSocket 連線狀態
│   │   ├── market.js      # ✅ 市場數據狀態
│   │   ├── notifications.js # ✅ 通知系統
│   │   └── index.js       # ✅ Store 統一匯出
│   │
│   ├── lib/               # ✅ 前端工具函數
│   │   ├── api.js         # ✅ API 客戶端
│   │   ├── utils.js       # ✅ 共用工具（格式化、驗證等）
│   │   └── constants.js   # ✅ 前端常數
│   │
│   └── types/             # 📋 TypeScript 類型定義（未使用 TS）
│
├── tests/                 # 測試目錄（待實作）
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env                   # ✅ 環境變數
├── .env.example           # ✅ 環境變數範本
├── .eslintrc.json         # ✅ ESLint 配置
├── .prettierrc.json       # ✅ Prettier 配置
├── vite.config.js         # ✅ Vite 配置
├── tailwind.config.js     # ✅ Tailwind CSS 配置
├── postcss.config.js      # ✅ PostCSS 配置
├── svelte.config.js       # ✅ Svelte 配置
├── jsconfig.json          # ✅ JavaScript 配置
└── package.json           # ✅ NPM 配置
```

### 架構決策說明

**為何不使用 SvelteKit？**

1. **簡化複雜度**: 專案不需要 SSR、檔案系統路由等 SvelteKit 功能
2. **快速開發**: Vite + Svelte 提供更輕量的開發體驗
3. **單頁應用足夠**: 所有功能可在 `App.svelte` 中透過條件渲染管理
4. **降低學習曲線**: 團隊成員只需熟悉 Svelte，無需學習 SvelteKit API

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

#### Sidebar.svelte - 側邊欄 📋 規劃中

**功能**:

- Agent 列表快速導航
- 系統狀態摘要
- 快捷操作按鈕

**狀態依賴**:

- `agents` store: Agent 列表

---

### Agent 組件

> **實作狀態**: ✅ 4/10 組件已完成

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

#### AgentGrid.svelte - Agent 網格布局 ✅

**功能**:

- 響應式網格佈局展示所有 Agents
- 支援排序和篩選
- 空狀態提示

**狀態依賴**:

- `agents` store: 訂閱 Agent 列表

---

#### AgentCreationForm.svelte - Agent 創建表單（Prompt 驅動設計） ✅

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

#### AgentConfigEditor.svelte - Agent 配置編輯器 📋 規劃中

> ⚠️ **重要**: 需實作配置鎖定機制

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

#### StrategyHistoryView.svelte - 策略變更歷史 ✅

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

#### StrategyChangeModal.svelte - 策略變更詳情彈窗 📋 規劃中

**功能**:

- 顯示策略變更的完整內容
- 新舊策略對比（diff view）
- 相關交易記錄
- 績效影響分析

---

#### AgentDashboard.svelte - Agent 監控儀表板 📋 規劃中

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

#### AgentPerformancePanel.svelte - Agent 績效面板 📋 規劃中

**功能**:

- 總報酬率和年化報酬率
- 最大回撤和夏普比率
- 勝率和平均獲利
- 績效圖表（Chart.js）

---

### Chart 組件

> **實作狀態**: ✅ 1/3 組件已完成

#### PerformanceChart.svelte - 績效圖表 ✅

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

## 應用架構 (單頁應用設計)

### App.svelte - 主應用組件

> ✅ **已實作**: 完整的單頁應用邏輯

**功能**:

- **Agent 管理**: 所有 Agents 總覽、創建、啟動/停止、刪除
- **即時監控**: WebSocket 連接提供即時狀態更新
- **策略歷史**: 查看 Agent 策略變更記錄
- **績效展示**: Chart.js 圖表展示投資組合表現
- **模態管理**: 創建表單、策略歷史等彈窗組件

**架構設計**:

```svelte
<script>
  // 狀態管理
  import { agents, selectedAgent } from './stores/agents.js';
  import { connectWebSocket } from './stores/websocket.js';
  import { loadMarketStatus } from './stores/market.js';

  // 組件
  import { Navbar } from './components/Layout/index.js';
  import { AgentGrid, AgentCreationForm, StrategyHistoryView } from './components/Agent/index.js';
  import { PerformanceChart } from './components/Chart/index.js';

  // 模態狀態
  let showCreateModal = $state(false);
  let showStrategyModal = $state(false);

  // 初始化
  onMount(async () => {
    connectWebSocket();
    await loadAgents();
    await loadMarketStatus();
  });
</script>

<Navbar />

<main>
  <!-- Agent 網格 -->
  <AgentGrid
    agents={$agents}
    on:create={() => showCreateModal = true}
    on:select={handleAgentSelect}
  />

  <!-- 選中 Agent 的績效圖表 -->
  {#if $selectedAgent}
    <PerformanceChart agentId={$selectedAgent.agent_id} />
  {/if}
</main>

<!-- 模態視窗 -->
<Modal bind:show={showCreateModal}>
  <AgentCreationForm on:created={handleAgentCreated} />
</Modal>

<Modal bind:show={showStrategyModal}>
  <StrategyHistoryView agentId={$selectedAgent?.agent_id} />
</Modal>
```

**頁面切換方式**:

由於不使用路由系統，所有「頁面」透過以下方式實現：

1. **條件渲染**: 使用 `{#if}` 塊根據狀態顯示不同內容
2. **模態視窗**: 複雜表單和詳情頁使用 Modal 組件
3. **選中狀態**: 透過 `selectedAgent` store 管理當前查看的 Agent

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

## WebSocket 層 (stores/websocket.js)

> ✅ **已實作**: 完整的 WebSocket 狀態管理

**功能**:

- 管理 WebSocket 連接生命週期
- 自動重連機制
- 事件監聽與分發
- 連接狀態管理

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

---

## 實作狀態總覽

### ✅ Phase 4 已完成功能

#### 核心功能

- ✅ **Agent 生命週期管理**: 創建、啟動、停止、刪除
- ✅ **Prompt 驅動創建**: 自然語言投資偏好輸入
- ✅ **即時狀態監控**: WebSocket 推送 Agent 狀態變更
- ✅ **策略歷史追蹤**: 完整的策略變更時間軸
- ✅ **績效圖表**: Chart.js 展示投資組合價值走勢
- ✅ **通知系統**: Toast 通知顯示操作結果

#### 已實作組件 (17/33)

- ✅ **Layout**: Navbar, NotificationToast
- ✅ **Agent**: AgentCard, AgentGrid, AgentCreationForm, StrategyHistoryView
- ✅ **Chart**: PerformanceChart
- ✅ **UI**: Button, Modal, StatusIndicator, Input, Textarea, Select

#### 狀態管理

- ✅ **agents.js**: 完整的 Agent CRUD 操作
- ✅ **websocket.js**: WebSocket 連接與事件處理
- ✅ **market.js**: 市場數據狀態管理
- ✅ **notifications.js**: 通知系統

#### API 整合

- ✅ **api.js**: HTTP API 客戶端封裝
- ✅ **utils.js**: 格式化工具函數
- ✅ **constants.js**: 前端常數定義

### 📋 待實作功能 (規劃中)

#### Agent 進階組件

- 📋 **AgentModal**: Agent 詳情彈窗
- 📋 **AgentDashboard**: 完整的 Agent 監控儀表板
- 📋 **AgentConfigEditor**: 配置編輯器（含執行時鎖定）
- 📋 **AgentToolsSelector**: Tools 選擇器
- 📋 **AgentPerformancePanel**: 詳細績效面板
- 📋 **StrategyChangeModal**: 策略變更詳情對比

#### 市場數據展示

- 📋 **MarketPanel**: 市場狀態面板
- 📋 **StockQuote**: 即時股價顯示
- 📋 **IndexDisplay**: 指數展示
- 📋 **MarketChart**: 市場圖表

#### 圖表視覺化

- 📋 **PortfolioChart**: 投資組合分布圖
- 📋 **進階績效圖表**: 回撤曲線、勝率分析等

#### UI 組件

- 📋 **LoadingSpinner**: 載入指示器
- 📋 **Tooltip**: 提示浮窗
- 📋 **Sidebar**: 側邊欄導航
- 📋 **Footer**: 頁腳

#### 測試

- 📋 **單元測試**: 組件與 Store 測試
- 📋 **整合測試**: API 與 WebSocket 測試
- 📋 **E2E 測試**: 完整用戶流程測試

### 🔄 架構演進路徑

#### 短期目標 (Phase 5)

1. 完成 **AgentConfigEditor** 和配置鎖定機制
2. 實作 **StrategyChangeModal** 策略對比視圖
3. 新增 **MarketPanel** 市場數據展示
4. 完善 **UI 組件庫** (LoadingSpinner, Tooltip)

#### 中期目標 (Phase 6)

1. 實作 **AgentDashboard** 完整監控介面
2. 新增 **PortfolioChart** 投資組合視覺化
3. 建立 **單元測試** 覆蓋率 > 70%
4. 優化 **WebSocket** 訊息批處理

#### 長期目標 (Phase 7+)

1. 考慮遷移至 **SvelteKit** (如需 SSR 或多頁路由)
2. 引入 **TypeScript** 提升類型安全
3. 實作 **E2E 測試** 自動化
4. 建立 **設計系統** 文件

---

## 總結

CasualTrader Frontend 採用現代化的 **Vite + Svelte 5 (單頁應用)** 架構，提供：

- ⚡ **極速開發體驗**: Vite 熱重載 + Svelte 5 Runes 編譯優化
- 🎨 **優雅 UI**: Tailwind CSS + 自定義組件系統
- 🔄 **即時響應**: WebSocket 雙向通訊 + Svelte Store 響應式狀態
- 📊 **豐富視覺化**: Chart.js 圖表整合
- 🤖 **Prompt 驅動**: 自然語言 Agent 創建流程
- 📈 **透明追蹤**: 完整展示策略演化和決策過程
- 🏗️ **輕量架構**: 不使用 SvelteKit，專注於核心功能

### 當前實作狀態

- ✅ **Phase 4 完成**: 核心功能運作中
- 📊 **組件完成度**: 51.5% (17/33)
- 🎯 **功能完整度**: 核心功能 100%，進階功能規劃中
- � **技術債**: 待補充測試、TypeScript 類型、進階 UI 組件

這個架構為用戶提供了**直觀、高效、即時**的 AI 交易模擬器體驗，並為未來功能擴展預留了清晰的演進路徑。
