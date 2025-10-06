# 前端實作規格 - Vite + Svelte

**版本**: 2.0
**日期**: 2025-10-06
**相關設計**: SYSTEM_DESIGN.md

---

## 📋 概述

本文檔詳述 CasualTrader AI 股票交易模擬器前端的 Vite + Svelte 實作規格，包含：

1. **Svelte 組件架構** - 現代化組件設計與狀態管理
2. **Vite 開發環境** - 快速熱重載與構建優化
3. **即時數據處理** - WebSocket 整合與響應式狀態
4. **圖表視覺化** - Chart.js 與 Svelte 整合
5. **響應式設計** - Tailwind CSS 與 Svelte 響應式系統

---

## 🎨 Svelte 組件架構

### 1. 專案結構

```
src/
├── App.svelte              # 主應用程式組件
├── main.js                 # Vite 進入點
├── app.html               # HTML 模板
├── components/            # 可重用組件
│   ├── Layout/
│   │   ├── Navbar.svelte
│   │   └── Sidebar.svelte
│   ├── Agent/
│   │   ├── AgentCard.svelte           # Agent 基礎卡片顯示
│   │   ├── AgentGrid.svelte           # Agent 網格布局
│   │   ├── AgentModal.svelte          # Agent 彈窗組件
│   │   ├── AgentCreationForm.svelte   # Agent 創建表單
│   │   ├── AgentDashboard.svelte      # Agent 監控儀表板
│   │   ├── AgentConfigEditor.svelte   # Agent 配置編輯器
│   │   ├── AgentToolsSelector.svelte  # Agent Tools 選擇器
│   │   └── AgentPerformancePanel.svelte # Agent 績效面板
│   ├── Chart/
│   │   ├── PerformanceChart.svelte
│   │   └── MarketChart.svelte
│   └── UI/
│       ├── Button.svelte
│       ├── Modal.svelte
│       └── StatusIndicator.svelte
├── routes/                # 路由頁面
│   ├── +layout.svelte
│   ├── +page.svelte       # 主儀表板
│   └── settings/
│       └── +page.svelte   # 設定頁面
├── stores/                # Svelte stores
│   ├── agents.js          # Agent 狀態管理
│   ├── websocket.js       # WebSocket 連線狀態
│   └── market.js          # 市場數據狀態
└── lib/                   # 工具函數
    ├── api.js             # API 客戶端
    ├── websocket.js       # WebSocket 管理
    └── utils.js           # 共用工具
```

### 2. 主應用程式組件 (App.svelte)

```svelte
<script>
  import { onMount } from 'svelte';
  import { agentsStore } from './stores/agents.js';
  import { websocketStore } from './stores/websocket.js';
  import Navbar from './components/Layout/Navbar.svelte';
  import AgentGrid from './components/Agent/AgentGrid.svelte';
  import MarketPanel from './components/Market/MarketPanel.svelte';
  import StatusIndicator from './components/UI/StatusIndicator.svelte';

  onMount(() => {
    // 初始化 WebSocket 連線
    websocketStore.connect();

    // 載入 Agent 數據
    agentsStore.loadAgents();
  });
</script>

<div class="app min-h-screen bg-gray-50">
  <Navbar />

  <main class="container mx-auto px-4 py-6">
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Agent 網格 - 占 3/4 寬度 -->
      <section class="lg:col-span-3">
        <AgentGrid />
      </section>

      <!-- 市場面板 - 占 1/4 寬度 -->
      <aside class="lg:col-span-1">
        <MarketPanel />
      </aside>
    </div>
  </main>

  <!-- 全域狀態指示器 -->
  <StatusIndicator />
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  }
</style>
```

### 3. Agent 卡片組件 (AgentCard.svelte)

```svelte
<script>
  import { createEventDispatcher } from 'svelte';
  import PerformanceChart from '../Chart/PerformanceChart.svelte';
  import Button from '../UI/Button.svelte';
  import StatusIndicator from '../UI/StatusIndicator.svelte';
  import { formatCurrency, formatPercentage } from '../../lib/utils.js';

  export let agent;
  export let portfolio;
  export let recentActivities = [];

  const dispatch = createEventDispatcher();

  function startAgent() {
    dispatch('start', { agentId: agent.id });
  }

  function stopAgent() {
    dispatch('stop', { agentId: agent.id });
  }

  function openSettings() {
    dispatch('settings', { agentId: agent.id });
  }

  // 模式顯示名稱
  const modeDisplayNames = {
    trading: '交易',
    rebalancing: '再平衡',
    observation: '觀察'
  };

  $: modeDisplay = modeDisplayNames[agent.current_mode] || agent.current_mode;
  $: modeColor = {
    trading: 'bg-green-500',
    rebalancing: 'bg-blue-500',
    observation: 'bg-orange-500'
  }[agent.current_mode] || 'bg-gray-500';
</script>

<div class="agent-card bg-white rounded-lg shadow-md p-6 transition-all hover:shadow-lg">
  <!-- Agent 標題欄 -->
  <div class="agent-header flex justify-between items-start mb-4">
    <div class="agent-info">
      <h3 class="text-lg font-semibold text-gray-900">{agent.name}</h3>
      <p class="text-sm text-gray-600">{agent.ai_model}</p>
    </div>
    <div class="agent-controls flex items-center gap-2">
      <span class="mode-badge px-2 py-1 rounded-full text-xs font-medium text-white {modeColor}">
        {modeDisplay}
      </span>
      <Button size="sm" variant="ghost" on:click={startAgent} title="啟動">
        ▶
      </Button>
      <Button size="sm" variant="ghost" on:click={stopAgent} title="停止">
        ⏹
      </Button>
      <Button size="sm" variant="ghost" on:click={openSettings} title="設定">
        ⚙
      </Button>
    </div>
  </div>

  <!-- 投資組合概況 -->
  <div class="portfolio-summary grid grid-cols-3 gap-4 mb-4">
    <div class="portfolio-item text-center">
      <div class="text-xs text-gray-500">總價值</div>
      <div class="text-sm font-medium">{formatCurrency(portfolio.total_value)}</div>
    </div>
    <div class="portfolio-item text-center">
      <div class="text-xs text-gray-500">報酬率</div>
      <div class="text-sm font-medium" class:text-green-600={portfolio.total_return > 0} class:text-red-600={portfolio.total_return < 0}>
        {formatPercentage(portfolio.total_return)}
      </div>
    </div>
    <div class="portfolio-item text-center">
      <div class="text-xs text-gray-500">現金</div>
      <div class="text-sm font-medium">{formatCurrency(portfolio.cash_balance)}</div>
    </div>
  </div>

  <!-- 績效圖表 -->
  <div class="chart-container mb-4">
    <PerformanceChart agentId={agent.id} data={portfolio.performance_history} />
  </div>

  <!-- 最近活動 -->
  <div class="recent-activity mb-4">
    <h4 class="text-sm font-medium text-gray-900 mb-2">最近活動</h4>
    <div class="activity-list space-y-1">
      {#each recentActivities.slice(0, 3) as activity}
        <div class="activity-item text-xs p-2 bg-gray-50 rounded">
          <div class="flex justify-between">
            <span class="text-gray-600">{activity.message}</span>
            <span class="text-gray-400">{new Date(activity.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>
      {/each}
    </div>
  </div>

  <!-- 狀態指示器 -->
  <div class="agent-status">
    <StatusIndicator status={agent.status} message={agent.status_message} />
  </div>
</div>
```

### 4. Tailwind CSS 配置

**tailwind.config.js**:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eff6ff",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
        success: {
          500: "#10b981",
          600: "#059669",
        },
        warning: {
          500: "#f59e0b",
          600: "#d97706",
        },
        danger: {
          500: "#ef4444",
          600: "#dc2626",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
```

**app.css** (全域樣式):

```css
@import "tailwindcss/base";
@import "tailwindcss/components";
@import "tailwindcss/utilities";

@layer base {
  html {
    font-family: "Inter", system-ui, sans-serif;
  }

  body {
    @apply bg-gray-50 text-gray-900;
  }
}

@layer components {
  .btn-primary {
    @apply bg-primary-500 hover:bg-primary-600 text-white font-medium py-2 px-4 rounded-lg transition-colors;
  }

  .btn-secondary {
    @apply bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition-colors;
  }

  .btn-ghost {
    @apply text-gray-500 hover:text-gray-700 hover:bg-gray-100 p-2 rounded-lg transition-colors;
  }

  .status-indicator {
    @apply inline-block w-2 h-2 rounded-full mr-2;
  }

  .status-running {
    @apply bg-success-500 animate-pulse-slow;
  }

  .status-stopped {
    @apply bg-danger-500;
  }

  .status-paused {
    @apply bg-warning-500;
  }
}
```

---

## 🔄 Svelte Stores 狀態管理

### 1. API 客戶端 (lib/api.js)

```javascript
const BASE_URL = "http://localhost:8000";

class APIClient {
  async request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;
    const config = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || "API request failed");
      }
      return await response.json();
    } catch (error) {
      console.error("API request failed:", error);
      throw error;
    }
  }

  // Agent 管理 API
  getAgents() {
    return this.request("/api/agents");
  }

  createAgent(agentData) {
    return this.request("/api/agents", {
      method: "POST",
      body: JSON.stringify(agentData),
    });
  }

  updateAgent(agentId, updates) {
    return this.request(`/api/agents/${agentId}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    });
  }

  deleteAgent(agentId) {
    return this.request(`/api/agents/${agentId}`, {
      method: "DELETE",
    });
  }

  // Agent 控制 API
  startAgent(agentId, config = {}) {
    return this.request(`/api/agents/${agentId}/start`, {
      method: "POST",
      body: JSON.stringify(config),
    });
  }

  stopAgent(agentId) {
    return this.request(`/api/agents/${agentId}/stop`, {
      method: "POST",
    });
  }

  // 投資組合 API
  getPortfolio(agentId) {
    return this.request(`/api/agents/${agentId}/portfolio`);
  }
}

export const apiClient = new APIClient();
```

### 2. WebSocket Store (stores/websocket.js)

```javascript
import { writable } from "svelte/store";

const WS_URL = "ws://localhost:8000/ws";

function createWebSocketStore() {
  const { subscribe, set, update } = writable({
    status: "disconnected", // disconnected, connecting, connected, error
    ws: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
  });

  let ws = null;
  let reconnectTimer = null;

  return {
    subscribe,

    connect() {
      if (ws && ws.readyState === WebSocket.OPEN) {
        return;
      }

      update((state) => ({ ...state, status: "connecting" }));

      try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
          console.log("WebSocket connected");
          update((state) => ({
            ...state,
            status: "connected",
            ws,
            reconnectAttempts: 0,
          }));
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error("Failed to parse WebSocket message:", error);
          }
        };

        ws.onclose = () => {
          console.log("WebSocket disconnected");
          update((state) => ({ ...state, status: "disconnected", ws: null }));
          this.attemptReconnect();
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          update((state) => ({ ...state, status: "error" }));
        };
      } catch (error) {
        console.error("Failed to create WebSocket connection:", error);
        update((state) => ({ ...state, status: "error" }));
      }
    },

    disconnect() {
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }

      if (ws) {
        ws.close();
        ws = null;
      }

      set({
        status: "disconnected",
        ws: null,
        reconnectAttempts: 0,
        maxReconnectAttempts: 5,
      });
    },

    attemptReconnect() {
      update((state) => {
        if (state.reconnectAttempts < state.maxReconnectAttempts) {
          const newAttempts = state.reconnectAttempts + 1;
          console.log(
            `Attempting to reconnect (${newAttempts}/${state.maxReconnectAttempts})...`,
          );

          reconnectTimer = setTimeout(() => {
            this.connect();
          }, 1000 * newAttempts);

          return { ...state, reconnectAttempts: newAttempts };
        } else {
          console.error("Max reconnection attempts reached");
          return { ...state, status: "error" };
        }
      });
    },

    handleMessage(data) {
      const { type, ...payload } = data;

      // 透過自定義事件分發 WebSocket 消息
      window.dispatchEvent(
        new CustomEvent(`ws:${type}`, {
          detail: payload,
        }),
      );

      // 分發通用事件
      window.dispatchEvent(
        new CustomEvent("ws:message", {
          detail: data,
        }),
      );
    },
  };
}

export const websocketStore = createWebSocketStore();
```

### 3. Agents Store (stores/agents.js)

```javascript
import { writable, derived } from "svelte/store";
import { apiClient } from "../lib/api.js";

function createAgentsStore() {
  const { subscribe, set, update } = writable([]);

  return {
    subscribe,

    async loadAgents() {
      try {
        const agents = await apiClient.getAgents();
        set(agents);
      } catch (error) {
        console.error("Failed to load agents:", error);
        set([]);
      }
    },

    async createAgent(agentData) {
      try {
        const newAgent = await apiClient.createAgent(agentData);
        update((agents) => [...agents, newAgent]);
        return newAgent;
      } catch (error) {
        console.error("Failed to create agent:", error);
        throw error;
      }
    },

    async updateAgent(agentId, updates) {
      try {
        const updatedAgent = await apiClient.updateAgent(agentId, updates);
        update((agents) =>
          agents.map((agent) => (agent.id === agentId ? updatedAgent : agent)),
        );
        return updatedAgent;
      } catch (error) {
        console.error("Failed to update agent:", error);
        throw error;
      }
    },

    async deleteAgent(agentId) {
      try {
        await apiClient.deleteAgent(agentId);
        update((agents) => agents.filter((agent) => agent.id !== agentId));
      } catch (error) {
        console.error("Failed to delete agent:", error);
        throw error;
      }
    },

    async startAgent(agentId) {
      try {
        await apiClient.startAgent(agentId);
        update((agents) =>
          agents.map((agent) =>
            agent.id === agentId ? { ...agent, status: "running" } : agent,
          ),
        );
      } catch (error) {
        console.error("Failed to start agent:", error);
        throw error;
      }
    },

    async stopAgent(agentId) {
      try {
        await apiClient.stopAgent(agentId);
        update((agents) =>
          agents.map((agent) =>
            agent.id === agentId ? { ...agent, status: "stopped" } : agent,
          ),
        );
      } catch (error) {
        console.error("Failed to stop agent:", error);
        throw error;
      }
    },
  };
}

export const agentsStore = createAgentsStore();

// 衍生 store：運行中的 Agents
export const runningAgents = derived(agentsStore, ($agents) =>
  $agents.filter((agent) => agent.status === "running"),
);
```

### 4. Vite 開發配置

**vite.config.js**:

```javascript
import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["svelte", "chart.js"],
          utils: ["./src/lib/utils.js", "./src/lib/api.js"],
        },
      },
    },
  },
});
```

**package.json** 開發腳本:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "check": "svelte-check --tsconfig ./jsconfig.json",
    "check:watch": "svelte-check --tsconfig ./jsconfig.json --watch"
  },
  "devDependencies": {
    "@sveltejs/vite-plugin-svelte": "^3.0.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "svelte": "^4.2.7",
    "svelte-check": "^3.6.0",
    "tailwindcss": "^3.3.6",
    "vite": "^5.0.8"
  },
  "dependencies": {
    "chart.js": "^4.4.0"
  }
}
```

---

## 📁 專案檔案結構

```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── App.svelte
│   ├── main.js
│   ├── app.css
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Navbar.svelte
│   │   │   └── Sidebar.svelte
│   │   ├── Agent/
│   │   │   ├── AgentCard.svelte
│   │   │   ├── AgentGrid.svelte
│   │   │   └── AgentModal.svelte
│   │   ├── Chart/
│   │   │   └── PerformanceChart.svelte
│   │   └── UI/
│   │       ├── Button.svelte
│   │       ├── Modal.svelte
│   │       └── StatusIndicator.svelte
│   ├── stores/
│   │   ├── agents.js
│   │   ├── websocket.js
│   │   └── market.js
│   └── lib/
│       ├── api.js
│       ├── websocket.js
│       └── utils.js
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── package.json
```

---

## ✅ 實作檢查清單

### Vite + Svelte 基礎設置

- [ ] 初始化 Vite + Svelte 專案
- [ ] 配置 Tailwind CSS
- [ ] 設置 ESLint 和 Prettier
- [ ] 配置開發代理服務器

### 核心組件開發

- [ ] 實作主應用程式組件 (App.svelte)
- [ ] 實作導航欄組件 (Navbar.svelte)
- [ ] 實作 Agent 卡片組件 (AgentCard.svelte)
- [ ] 實作績效圖表組件 (PerformanceChart.svelte)

### 狀態管理

- [ ] 實作 Agents Store
- [ ] 實作 WebSocket Store
- [ ] 實作市場數據 Store
- [ ] 整合即時數據更新

### API 整合

- [ ] 實作 API 客戶端
- [ ] 實作 WebSocket 連線管理
- [ ] 實作錯誤處理和重連機制
- [ ] 測試所有 API 端點

### 用戶體驗

- [ ] 實作響應式設計
- [ ] 實作載入狀態和錯誤提示
- [ ] 實作動畫和轉場效果
- [ ] 跨瀏覽器測試

### 性能優化

- [ ] 實作程式碼分割
- [ ] 優化 Bundle 大小
- [ ] 實作圖片和資源優化
- [ ] 性能測試和調優

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
