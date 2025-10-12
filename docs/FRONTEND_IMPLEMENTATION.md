# 前端實作規格 - Vite + Svelte

**版本**: 2.1
**日期**: 2025-10-12
**相關設計**: SYSTEM_DESIGN.md

---

## 📋 概述

本文檔詳述 CasualTrader AI 股票交易模擬器前端的 Vite + Svelte 實作規格，包含：

1. **Svelte 組件架構** - 現代化組件設計與狀態管理
2. **Vite 開發環境** - 快速熱重載與構建優化
3. **即時數據處理** - WebSocket 整合與響應式狀態
4. **圖表視覺化** - Chart.js 與 Svelte 整合
5. **響應式設計** - Tailwind CSS 與 Svelte 響應式系統
6. **Agent 配置介面** - Prompt 驅動的 Agent 創建表單與策略演化追蹤

### Agent 配置介面特色

本專案採用 **Prompt 驅動** 的 Agent 設計理念（詳見 AGENT_IMPLEMENTATION.md），前端介面設計特點：

- **自然語言配置**: 用戶透過開放式文字輸入描述投資偏好和策略調整依據
- **即時指令預覽**: 表單自動生成並展示 Agent 實際執行指令
- **策略演化追蹤**: 完整記錄和展示 Agent 策略變更歷史
- **透明度優先**: 所有策略調整都有詳細的觸發原因、績效背景和 Agent 說明
- **簡潔直觀**: 避免複雜的參數配置，專注於投資意圖的表達
- **⚠️ 執行時鎖定**: Agent 啟動後自動鎖定配置，防止執行期間被修改影響策略一致性

---

## 🎨 Svelte 組件架構

### 1. 專案結構

```
frontend/
├── public/                # 靜態資源
│   └── vite.svg
├── src/                   # 前端源代碼
│   ├── App.svelte         # 主應用程式組件
│   ├── main.js            # Vite 進入點
│   ├── app.css           # 全域樣式
│   ├── components/        # 可重用組件
│   │   ├── Layout/        # 佈局組件
│   │   │   ├── Navbar.svelte
│   │   │   └── Sidebar.svelte
│   │   ├── Agent/         # Agent 相關組件
│   │   │   ├── AgentCard.svelte           # Agent 基礎卡片顯示
│   │   │   ├── AgentGrid.svelte           # Agent 網格布局
│   │   │   ├── AgentModal.svelte          # Agent 彈窗組件
│   │   │   ├── AgentCreationForm.svelte   # Agent 創建表單（Prompt驅動設計）
│   │   │   ├── AgentDashboard.svelte      # Agent 監控儀表板
│   │   │   ├── AgentConfigEditor.svelte   # Agent 配置編輯器
│   │   │   ├── AgentToolsSelector.svelte  # Agent Tools 選擇器
│   │   │   ├── AgentPerformancePanel.svelte # Agent 績效面板
│   │   │   ├── StrategyHistoryView.svelte # 策略變更歷史查看
│   │   │   └── StrategyChangeModal.svelte # 策略變更詳情彈窗
│   │   ├── Chart/         # 圖表組件
│   │   │   ├── PerformanceChart.svelte
│   │   │   └── MarketChart.svelte
│   │   ├── Market/        # 市場相關組件
│   │   │   ├── MarketPanel.svelte
│   │   │   └── StockQuote.svelte
│   │   └── UI/            # 基礎 UI 組件
│   │       ├── Button.svelte
│   │       ├── Modal.svelte
│   │       └── StatusIndicator.svelte
│   ├── routes/            # SvelteKit 路由頁面
│   │   ├── +layout.svelte
│   │   ├── +page.svelte   # 主儀表板
│   │   ├── agents/        # Agent 管理頁面
│   │   │   ├── +page.svelte
│   │   │   └── [id]/
│   │   │       └── +page.svelte
│   │   └── settings/      # 設定頁面
│   │       └── +page.svelte
│   ├── stores/            # Svelte stores 狀態管理
│   │   ├── agents.js      # Agent 狀態管理
│   │   ├── websocket.js   # WebSocket 連線狀態
│   │   ├── market.js      # 市場數據狀態
│   │   └── notifications.js # 通知系統
│   ├── lib/               # 前端工具函數
│   │   ├── api.js         # API 客戶端
│   │   ├── websocket.js   # WebSocket 管理
│   │   ├── utils.js       # 共用工具（含格式化函數）
│   │   └── constants.js   # 前端常數
│   └── types/             # TypeScript 類型定義
│       ├── agent.ts       # Agent 類型
│       ├── api.ts         # API 類型
│       └── websocket.ts   # WebSocket 類型
├── vite.config.js         # Vite 配置
├── tailwind.config.js     # Tailwind CSS 配置
├── postcss.config.js      # PostCSS 配置
├── package.json           # NPM 配置
└── tsconfig.json          # TypeScript 配置
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

  // 檢查 Agent 是否正在執行（鎖定設定）
  $: isRunning = agent.status === 'running' || agent.status === 'active';
  $: isConfigLocked = isRunning; // 執行中時鎖定配置

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
      <div class="flex items-center gap-2">
        <p class="text-sm text-gray-600">{agent.description}</p>
        <span class="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
          {agent.ai_model}
        </span>
      </div>
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
      <Button
        size="sm"
        variant="ghost"
        on:click={openSettings}
        disabled={isConfigLocked}
        title={isConfigLocked ? "Agent 執行中，無法修改設定" : "設定"}
        class={isConfigLocked ? "opacity-50 cursor-not-allowed" : ""}
      >
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

### 4. Agent 創建表單組件 (AgentCreationForm.svelte)

> 參考: AGENT_IMPLEMENTATION.md - 前端 Agent 配置介面

此組件提供簡潔直觀的 Agent 創建界面，採用 **Prompt 驅動** 的設計理念，讓用戶透過自然語言描述投資偏好和策略調整依據。

```svelte
<script>
  import { createEventDispatcher } from 'svelte';
  import Button from '../UI/Button.svelte';
  import { agentsStore } from '../../stores/agents.js';

  const dispatch = createEventDispatcher();

  // 表單資料
  let formData = {
    name: '',
    description: '',
    initial_funds: 1000000,
    investment_preferences: '',
    strategy_adjustment_criteria: '',
    max_position_size: 5,
    excluded_symbols: '',
    additional_instructions: ''
  };

  // 預覽生成的 Agent 指令
  let instructionsPreview = '';

  $: {
    instructionsPreview = generateInstructionsPreview(formData);
  }

  function generateInstructionsPreview(data) {
    return `You are ${data.name || '[Agent 名稱]'}, an intelligent Taiwan stock trading agent.

CORE MISSION:
${data.description || '[Agent 描述]'}

INVESTMENT PREFERENCES:
${data.investment_preferences || '[投資偏好設定]'}

STRATEGY ADJUSTMENT CRITERIA:
${data.strategy_adjustment_criteria || '[策略調整依據]'}

AVAILABLE TRADING MODES (adapt based on conditions):
- TRADING: Execute buy/sell decisions when opportunities arise
- REBALANCING: Optimize portfolio allocation and manage risk
- OBSERVATION: Monitor market and identify potential opportunities
- STRATEGY_REVIEW: Analyze performance and adjust approach

TRADING CONSTRAINTS:
- Available capital: NT$${data.initial_funds.toLocaleString()}
- Max position size: ${data.max_position_size}% per stock
- Taiwan stock market hours: 09:00-13:30 (Mon-Fri)
- Minimum trade unit: 1000 shares
${data.excluded_symbols ? `- Excluded symbols: ${data.excluded_symbols}` : ''}

${data.additional_instructions ? `\nADDITIONAL INSTRUCTIONS:\n${data.additional_instructions}` : ''}`;
  }

  async function handleSubmit() {
    try {
      // 處理排除股票列表
      const excludedList = formData.excluded_symbols
        ? formData.excluded_symbols.split(',').map(s => s.trim()).filter(Boolean)
        : [];

      const agentConfig = {
        name: formData.name,
        description: formData.description,
        initial_funds: formData.initial_funds,
        investment_preferences: formData.investment_preferences,
        strategy_adjustment_criteria: formData.strategy_adjustment_criteria,
        max_position_size: formData.max_position_size,
        excluded_symbols: excludedList,
        additional_instructions: formData.additional_instructions
      };

      await agentsStore.createAgent(agentConfig);
      dispatch('created');

      // 重置表單
      resetForm();
    } catch (error) {
      console.error('Failed to create agent:', error);
      alert('創建 Agent 失敗: ' + error.message);
    }
  }

  function resetForm() {
    formData = {
      name: '',
      description: '',
      initial_funds: 1000000,
      investment_preferences: '',
      strategy_adjustment_criteria: '',
      max_position_size: 5,
      excluded_symbols: '',
      additional_instructions: ''
    };
  }
</script>

<form class="agent-creation-form bg-white rounded-lg shadow-md p-6" on:submit|preventDefault={handleSubmit}>
  <h2 class="text-2xl font-bold text-gray-900 mb-6">創建 Trading Agent</h2>

  <!-- 基本資訊區塊 -->
  <div class="basic-info mb-6 space-y-4">
    <h3 class="text-lg font-semibold text-gray-800 mb-3">基本資訊</h3>

    <div class="input-group">
      <label class="block text-sm font-medium text-gray-700 mb-2">Agent 名稱 *</label>
      <input
        type="text"
        bind:value={formData.name}
        placeholder="例如：穩健成長投資顧問"
        class="form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        required
      />
    </div>

    <div class="input-group">
      <label class="block text-sm font-medium text-gray-700 mb-2">Agent 描述 *</label>
      <textarea
        bind:value={formData.description}
        placeholder="簡短描述這個 Agent 的投資目標和特色"
        class="form-textarea w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        rows="3"
        required
      />
    </div>

    <div class="input-group">
      <label class="block text-sm font-medium text-gray-700 mb-2">AI 模型 *</label>
      <select
        bind:value={formData.ai_model}
        class="form-select w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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
      <p class="text-xs text-gray-500 mt-1">選擇用於投資決策的 AI 模型，不同模型具有不同的推理風格與成本</p>
    </div>

    <div class="input-group">
      <label class="block text-sm font-medium text-gray-700 mb-2">初始資金 (NT$) *</label>
      <input
        type="number"
        bind:value={formData.initial_funds}
        min="100000"
        step="10000"
        class="form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        required
      />
    </div>
  </div>

  <!-- 核心投資設定區塊 -->
  <div class="investment-settings mb-6 space-y-4">
    <h3 class="text-lg font-semibold text-gray-800 mb-3">核心投資設定</h3>

    <div class="input-group">
      <label class="block text-sm font-medium text-gray-700 mb-2">投資偏好 *</label>
      <textarea
        bind:value={formData.investment_preferences}
        placeholder="用自然語言描述投資偏好。

範例：
'我偏好穩健成長的大型股，主要關注半導體和金融股，風險承受度中等，希望長期持有優質企業，避免過度頻繁交易。'"
        class="form-textarea strategy-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        rows="6"
        required
      />
      <p class="text-xs text-gray-500 mt-1">描述您的投資風格、偏好產業、風險承受度等</p>
    </div>

    <div class="input-group">
      <label class="block text-sm font-medium text-gray-700 mb-2">策略調整依據 *</label>
      <textarea
        bind:value={formData.strategy_adjustment_criteria}
        placeholder="說明何時以及如何調整投資策略。

範例：
'當連續三天虧損超過2%時，轉為保守觀察模式；當發現技術突破信號且基本面支撐時，可以增加部位；每週檢討一次績效，若月報酬率低於大盤2%以上，考慮調整選股邏輯。'"
        class="form-textarea strategy-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        rows="6"
        required
      />
      <p class="text-xs text-gray-500 mt-1">定義觸發策略調整的條件和調整方向</p>
    </div>
  </div>

  <!-- 進階設定區塊 -->
  <div class="advanced-settings mb-6 space-y-4">
    <h3 class="text-lg font-semibold text-gray-800 mb-3">進階設定（可選）</h3>

    <div class="input-group">
      <label class="block text-sm font-medium text-gray-700 mb-2">單股最大部位 (%)</label>
      <input
        type="number"
        bind:value={formData.max_position_size}
        min="1"
        max="20"
        step="0.5"
        class="form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
      />
      <p class="text-xs text-gray-500 mt-1">單一股票占投資組合的最大比例</p>
    </div>

    <div class="input-group">
      <label class="block text-sm font-medium text-gray-700 mb-2">排除股票代碼</label>
      <input
        type="text"
        bind:value={formData.excluded_symbols}
        placeholder="例如: 2498,2328"
        class="form-input w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
      />
      <p class="text-xs text-gray-500 mt-1">不希望投資的股票代碼，用逗號分隔</p>
    </div>

    <div class="input-group">
      <label class="block text-sm font-medium text-gray-700 mb-2">額外指令</label>
      <textarea
        bind:value={formData.additional_instructions}
        placeholder="任何額外的投資限制或特殊要求"
        class="form-textarea w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        rows="3"
      />
    </div>
  </div>

  <!-- Agent 指令預覽區塊 -->
  <div class="preview-section mb-6">
    <h3 class="text-lg font-semibold text-gray-800 mb-3">Agent 指令預覽</h3>
    <div class="preview-content bg-gray-50 p-4 rounded-lg border border-gray-200">
      <pre class="text-xs text-gray-700 whitespace-pre-wrap font-mono">{instructionsPreview}</pre>
    </div>
    <p class="text-xs text-gray-500 mt-2">這是系統將為您的 Agent 生成的實際指令</p>
  </div>

  <!-- 操作按鈕 -->
  <div class="form-actions flex justify-end gap-3">
    <Button variant="secondary" on:click={resetForm}>
      重置
    </Button>
    <Button type="submit" variant="primary">
      創建 Trading Agent
    </Button>
  </div>
</form>

<style>
  .strategy-input {
    font-family: 'Inter', system-ui, sans-serif;
    line-height: 1.6;
  }

  .preview-content pre {
    max-height: 400px;
    overflow-y: auto;
  }
</style>
```

### 5. Agent 配置編輯器組件 (AgentConfigEditor.svelte)

> ⚠️ **重要**: 此組件實作配置鎖定機制，防止執行中的 Agent 被修改

此組件用於編輯已創建的 Agent 配置，並強制執行配置鎖定規則。

```svelte
<script>
  import { createEventDispatcher } from 'svelte';
  import { agentsStore } from '../../stores/agents.js';
  import Button from '../UI/Button.svelte';
  import Modal from '../UI/Modal.svelte';

  export let agent;
  export let show = false;

  const dispatch = createEventDispatcher();

  // 檢查配置是否被鎖定
  $: isRunning = agent.status === 'running' || agent.status === 'active';
  $: isConfigLocked = isRunning || agent.config_locked;

  // 編輯表單資料
  let editFormData = { ...agent };

  // 當 agent 變更時更新表單
  $: if (agent) {
    editFormData = { ...agent };
  }

  async function handleSave() {
    // 雙重檢查鎖定狀態
    if (isConfigLocked) {
      alert('⚠️ 無法儲存：Agent 正在執行中，配置已鎖定。請先停止 Agent。');
      return;
    }

    try {
      await agentsStore.updateAgent(agent.id, editFormData);
      dispatch('saved');
      dispatch('close');
    } catch (error) {
      alert(`儲存失敗：${error.message}`);
    }
  }

  function handleCancel() {
    dispatch('close');
  }

  async function handleStopAgent() {
    if (confirm('確定要停止 Agent 執行嗎？停止後才能修改配置。')) {
      try {
        await agentsStore.stopAgent(agent.id);
        // Agent 停止後會自動解鎖，可以繼續編輯
      } catch (error) {
        alert(`停止失敗：${error.message}`);
      }
    }
  }
</script>

{#if show}
  <Modal on:close={handleCancel}>
    <div class="agent-config-editor">
      <div class="header mb-6">
        <h2 class="text-2xl font-bold text-gray-900">編輯 Agent 配置</h2>
        <p class="text-sm text-gray-600 mt-1">{agent.name}</p>
      </div>

      <!-- 配置鎖定警告橫幅 -->
      {#if isConfigLocked}
        <div class="config-lock-banner bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div class="flex items-start gap-3">
            <span class="text-yellow-600 text-2xl">🔒</span>
            <div class="flex-1">
              <h4 class="text-sm font-semibold text-yellow-800 mb-2">配置已鎖定</h4>
              <p class="text-sm text-yellow-700 mb-3">
                Agent 目前正在執行交易策略，為確保策略一致性，所有配置已被鎖定。
                若需修改配置，請先停止 Agent 執行。
              </p>
              <Button
                variant="warning"
                size="sm"
                on:click={handleStopAgent}
              >
                停止 Agent 並解鎖配置
              </Button>
            </div>
          </div>
        </div>
      {/if}

      <!-- 配置表單 -->
      <form class="config-form space-y-6" on:submit|preventDefault={handleSave}>

        <!-- 基本資訊 -->
        <div class="section">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">基本資訊</h3>

          <div class="input-group mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Agent 名稱</label>
            <input
              type="text"
              bind:value={editFormData.name}
              disabled={isConfigLocked}
              class="form-input w-full px-4 py-2 border border-gray-300 rounded-lg"
              class:opacity-50={isConfigLocked}
              class:cursor-not-allowed={isConfigLocked}
            />
          </div>

          <div class="input-group mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">描述</label>
            <textarea
              bind:value={editFormData.description}
              disabled={isConfigLocked}
              class="form-textarea w-full px-4 py-2 border border-gray-300 rounded-lg"
              class:opacity-50={isConfigLocked}
              class:cursor-not-allowed={isConfigLocked}
              rows="3"
            />
          </div>
        </div>

        <!-- 投資策略配置 -->
        <div class="section">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">投資策略配置</h3>

          <div class="input-group mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">投資偏好</label>
            <textarea
              bind:value={editFormData.investment_preferences}
              disabled={isConfigLocked}
              class="form-textarea w-full px-4 py-2 border border-gray-300 rounded-lg"
              class:opacity-50={isConfigLocked}
              class:cursor-not-allowed={isConfigLocked}
              rows="6"
            />
          </div>

          <div class="input-group mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">策略調整依據</label>
            <textarea
              bind:value={editFormData.strategy_adjustment_criteria}
              disabled={isConfigLocked}
              class="form-textarea w-full px-4 py-2 border border-gray-300 rounded-lg"
              class:opacity-50={isConfigLocked}
              class:cursor-not-allowed={isConfigLocked}
              rows="6"
            />
          </div>
        </div>

        <!-- 風險控制 -->
        <div class="section">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">風險控制</h3>

          <div class="input-group mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              單股最大部位 (%)
            </label>
            <input
              type="number"
              bind:value={editFormData.max_position_size}
              disabled={isConfigLocked}
              min="1"
              max="20"
              step="0.5"
              class="form-input w-full px-4 py-2 border border-gray-300 rounded-lg"
              class:opacity-50={isConfigLocked}
              class:cursor-not-allowed={isConfigLocked}
            />
          </div>

          <div class="input-group mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              排除股票代碼
            </label>
            <input
              type="text"
              bind:value={editFormData.excluded_symbols}
              disabled={isConfigLocked}
              placeholder="例如: 2498,2328"
              class="form-input w-full px-4 py-2 border border-gray-300 rounded-lg"
              class:opacity-50={isConfigLocked}
              class:cursor-not-allowed={isConfigLocked}
            />
          </div>
        </div>

        <!-- 操作按鈕 -->
        <div class="form-actions flex justify-end gap-3 pt-6 border-t border-gray-200">
          <Button variant="secondary" on:click={handleCancel}>
            取消
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={isConfigLocked}
            title={isConfigLocked ? "配置已鎖定，無法儲存" : "儲存變更"}
          >
            {isConfigLocked ? '🔒 配置已鎖定' : '儲存變更'}
          </Button>
        </div>
      </form>

      <!-- 只讀模式提示 -->
      {#if isConfigLocked}
        <div class="readonly-notice mt-4 text-center">
          <p class="text-xs text-gray-500">
            💡 提示：您可以查看所有配置內容，但無法修改。
          </p>
        </div>
      {/if}
    </div>
  </Modal>
{/if}

<style>
  .config-lock-banner {
    animation: slideDown 0.3s ease-out;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .form-input:disabled,
  .form-textarea:disabled {
    background-color: #f9fafb;
  }
</style>
```

### 6. 策略變更歷史查看組件 (StrategyHistoryView.svelte)

> 參考: AGENT_IMPLEMENTATION.md - 策略變更記錄系統

此組件展示 Agent 策略演化的完整歷史記錄，包括變更原因、內容和績效影響。

```svelte
<script>
  import { onMount } from 'svelte';
  import { formatCurrency, formatPercentage, formatDateTime } from '../../lib/utils.js';
  import Button from '../UI/Button.svelte';
  import Modal from '../UI/Modal.svelte';

  export let agentId;

  let changes = [];
  let selectedChange = null;
  let loading = true;
  let showDetailModal = false;

  onMount(async () => {
    await loadStrategyChanges();
  });

  async function loadStrategyChanges() {
    loading = true;
    try {
      const response = await fetch(`/api/agents/${agentId}/strategy-changes`);
      if (response.ok) {
        changes = await response.json();
      }
    } catch (error) {
      console.error('Failed to load strategy changes:', error);
    } finally {
      loading = false;
    }
  }

  function openDetailModal(change) {
    selectedChange = change;
    showDetailModal = true;
  }

  function closeDetailModal() {
    showDetailModal = false;
    selectedChange = null;
  }

  // 變更類型顯示名稱
  const changeTypeLabels = {
    auto: '自動調整',
    manual: '手動調整',
    performance_driven: '績效驅動'
  };

  // 變更類型顏色
  const changeTypeColors = {
    auto: 'bg-blue-100 text-blue-800',
    manual: 'bg-purple-100 text-purple-800',
    performance_driven: 'bg-orange-100 text-orange-800'
  };
</script>

<div class="strategy-history-container bg-white rounded-lg shadow-md p-6">
  <div class="header flex justify-between items-center mb-6">
    <h2 class="text-xl font-bold text-gray-900">策略演化歷史</h2>
    <Button size="sm" variant="ghost" on:click={loadStrategyChanges}>
      🔄 重新載入
    </Button>
  </div>

  {#if loading}
    <div class="loading text-center py-8">
      <div class="spinner animate-spin inline-block w-8 h-8 border-4 border-gray-200 border-t-primary-500 rounded-full"></div>
      <p class="text-gray-600 mt-2">載入策略變更記錄...</p>
    </div>
  {:else if changes.length === 0}
    <div class="empty-state text-center py-8">
      <p class="text-gray-500">尚無策略變更記錄</p>
    </div>
  {:else}
    <div class="changes-timeline space-y-4">
      {#each changes as change, index}
        <div class="change-card border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
             on:click={() => openDetailModal(change)}>

          <!-- 變更標題列 -->
          <div class="change-header flex justify-between items-start mb-3">
            <div class="change-info flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="change-type-badge px-2 py-1 rounded-full text-xs font-medium {changeTypeColors[change.change_type]}">
                  {changeTypeLabels[change.change_type]}
                </span>
                <span class="text-sm text-gray-500">{formatDateTime(change.timestamp)}</span>
              </div>
              <h3 class="text-base font-semibold text-gray-900">{change.change_summary}</h3>
            </div>
            <div class="timeline-indicator flex flex-col items-center">
              <div class="timeline-dot w-3 h-3 bg-primary-500 rounded-full"></div>
              {#if index < changes.length - 1}
                <div class="timeline-line w-0.5 h-full bg-gray-200 mt-2"></div>
              {/if}
            </div>
          </div>

          <!-- 觸發原因 -->
          <div class="trigger-reason mb-3">
            <p class="text-sm text-gray-600">
              <span class="font-medium">觸發原因：</span>
              {change.trigger_reason}
            </p>
          </div>

          <!-- 績效背景（如果有） -->
          {#if change.performance_at_change}
            <div class="performance-context grid grid-cols-3 gap-2 mb-3 p-3 bg-gray-50 rounded">
              <div class="metric text-center">
                <div class="text-xs text-gray-500">報酬率</div>
                <div class="text-sm font-medium"
                     class:text-green-600={change.performance_at_change.total_return > 0}
                     class:text-red-600={change.performance_at_change.total_return < 0}>
                  {formatPercentage(change.performance_at_change.total_return)}
                </div>
              </div>
              <div class="metric text-center">
                <div class="text-xs text-gray-500">回撤</div>
                <div class="text-sm font-medium text-red-600">
                  {formatPercentage(change.performance_at_change.drawdown)}
                </div>
              </div>
              <div class="metric text-center">
                <div class="text-xs text-gray-500">夏普比率</div>
                <div class="text-sm font-medium">
                  {change.performance_at_change.sharpe_ratio?.toFixed(2) || 'N/A'}
                </div>
              </div>
            </div>
          {/if}

          <!-- Agent 說明摘要 -->
          {#if change.agent_explanation}
            <div class="agent-explanation text-sm text-gray-700 italic border-l-4 border-primary-200 pl-3 py-1">
              {change.agent_explanation.substring(0, 150)}{change.agent_explanation.length > 150 ? '...' : ''}
            </div>
          {/if}

          <!-- 查看詳情按鈕 -->
          <div class="action-footer mt-3 pt-3 border-t border-gray-100">
            <button class="text-sm text-primary-600 hover:text-primary-700 font-medium">
              查看完整變更內容 →
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- 策略變更詳情彈窗 -->
{#if showDetailModal && selectedChange}
  <Modal on:close={closeDetailModal}>
    <div class="strategy-detail-modal">
      <h2 class="text-2xl font-bold text-gray-900 mb-4">策略變更詳情</h2>

      <!-- 基本資訊 -->
      <div class="detail-section mb-6">
        <h3 class="text-lg font-semibold text-gray-800 mb-3">基本資訊</h3>
        <div class="info-grid grid grid-cols-2 gap-4">
          <div>
            <span class="text-sm text-gray-500">變更時間：</span>
            <span class="text-sm font-medium">{formatDateTime(selectedChange.timestamp)}</span>
          </div>
          <div>
            <span class="text-sm text-gray-500">變更類型：</span>
            <span class="px-2 py-1 rounded text-xs font-medium {changeTypeColors[selectedChange.change_type]}">
              {changeTypeLabels[selectedChange.change_type]}
            </span>
          </div>
        </div>
      </div>

      <!-- 觸發原因 -->
      <div class="detail-section mb-6">
        <h3 class="text-lg font-semibold text-gray-800 mb-3">觸發原因</h3>
        <p class="text-sm text-gray-700">{selectedChange.trigger_reason}</p>
      </div>

      <!-- Agent 說明 -->
      {#if selectedChange.agent_explanation}
        <div class="detail-section mb-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-3">Agent 說明</h3>
          <div class="explanation-box bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p class="text-sm text-gray-700 whitespace-pre-wrap">{selectedChange.agent_explanation}</p>
          </div>
        </div>
      {/if}

      <!-- 策略內容變更 -->
      <div class="detail-section mb-6">
        <h3 class="text-lg font-semibold text-gray-800 mb-3">策略內容變更</h3>
        <div class="strategy-diff space-y-4">
          {#if selectedChange.old_strategy}
            <div class="old-strategy">
              <h4 class="text-sm font-medium text-gray-700 mb-2">變更前策略（摘要）：</h4>
              <pre class="text-xs bg-red-50 border border-red-200 rounded p-3 overflow-x-auto whitespace-pre-wrap font-mono">
{selectedChange.old_strategy.substring(selectedChange.old_strategy.length - 500)}
              </pre>
            </div>
          {/if}
          <div class="new-strategy">
            <h4 class="text-sm font-medium text-gray-700 mb-2">新增策略內容：</h4>
            <pre class="text-xs bg-green-50 border border-green-200 rounded p-3 overflow-x-auto whitespace-pre-wrap font-mono">
{selectedChange.new_strategy.substring(selectedChange.new_strategy.length - 500)}
            </pre>
          </div>
        </div>
      </div>

      <!-- 績效背景 -->
      {#if selectedChange.performance_at_change}
        <div class="detail-section mb-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-3">當時績效狀況</h3>
          <div class="performance-grid grid grid-cols-3 gap-4">
            <div class="metric-card bg-gray-50 rounded-lg p-3 text-center">
              <div class="text-xs text-gray-500 mb-1">總報酬率</div>
              <div class="text-lg font-bold"
                   class:text-green-600={selectedChange.performance_at_change.total_return > 0}
                   class:text-red-600={selectedChange.performance_at_change.total_return < 0}>
                {formatPercentage(selectedChange.performance_at_change.total_return)}
              </div>
            </div>
            <div class="metric-card bg-gray-50 rounded-lg p-3 text-center">
              <div class="text-xs text-gray-500 mb-1">最大回撤</div>
              <div class="text-lg font-bold text-red-600">
                {formatPercentage(selectedChange.performance_at_change.drawdown)}
              </div>
            </div>
            <div class="metric-card bg-gray-50 rounded-lg p-3 text-center">
              <div class="text-xs text-gray-500 mb-1">夏普比率</div>
              <div class="text-lg font-bold text-gray-900">
                {selectedChange.performance_at_change.sharpe_ratio?.toFixed(2) || 'N/A'}
              </div>
            </div>
          </div>
        </div>
      {/if}

      <!-- 關閉按鈕 -->
      <div class="modal-footer flex justify-end pt-4 border-t border-gray-200">
        <Button variant="primary" on:click={closeDetailModal}>
          關閉
        </Button>
      </div>
    </div>
  </Modal>
{/if}

<style>
  .timeline-line {
    min-height: 20px;
  }

  .explanation-box {
    max-height: 200px;
    overflow-y: auto;
  }

  pre {
    max-height: 300px;
  }
</style>
```

---

## 🤖 Agent 管理介面設計

> 本節對應 AGENT_IMPLEMENTATION.md 中定義的前端 Agent 配置介面

### 設計理念

Agent 管理介面採用 **Prompt 驅動** 的設計理念，讓用戶透過自然語言描述投資策略，而非複雜的參數配置。主要特色：

1. **簡化創建流程**: 專注於投資意圖的表達，避免技術細節
2. **即時預覽**: 用戶可以看到生成的 Agent 指令
3. **策略演化追蹤**: 完整記錄 Agent 的策略調整歷史
4. **透明化決策**: 展示策略變更的原因、內容和效果

### Agent 創建流程

1. **基本資訊輸入** → Agent 名稱、描述、初始資金
2. **投資偏好設定** → 用自然語言描述投資風格和偏好
3. **策略調整依據** → 定義何時及如何調整策略
4. **進階設定（可選）** → 部位限制、排除股票等
5. **預覽與確認** → 檢視生成的 Agent 指令
6. **創建 Agent** → 提交到後端並開始運行

### 策略演化追蹤

策略變更歷史介面提供：

- **時間軸視圖**: 按時間順序展示所有策略變更
- **變更類型標籤**: 自動調整、手動調整、績效驅動
- **觸發原因說明**: 清楚說明為何觸發策略調整
- **績效背景資訊**: 變更時的報酬率、回撤、夏普比率等
- **Agent 說明**: Agent 自己對策略調整的解釋
- **變更內容對比**: 新舊策略的差異展示

### 用戶體驗考量

- **文字輸入優先**: 使用大型文字框而非下拉選單
- **範例提示**: 提供清楚的輸入範例
- **即時反饋**: 表單驗證和預覽更新
- **視覺層次**: 清晰的資訊架構和視覺層次
- **響應式設計**: 適配各種螢幕尺寸

### ⚠️ Agent 執行時配置鎖定機制

**設計目的**：防止 Agent 執行交易策略期間被修改配置，確保策略一致性和執行完整性。

#### 鎖定規則

1. **啟動時自動鎖定**
   - Agent 狀態變更為 `running` 或 `active` 時，自動鎖定所有配置
   - 前端介面禁用所有編輯按鈕和表單輸入

2. **鎖定範圍**
   - 投資偏好設定（investment_preferences）
   - 策略調整依據（strategy_adjustment_criteria）
   - 初始資金設定（initial_funds）
   - 最大部位設定（max_position_size）
   - 排除股票列表（excluded_symbols）
   - 其他所有核心配置

3. **允許的操作**
   - ✅ 查看 Agent 配置和狀態
   - ✅ 監控 Agent 執行歷史和績效
   - ✅ 查看策略變更記錄
   - ✅ 停止 Agent 執行
   - ❌ 修改任何配置參數
   - ❌ 更新投資策略內容

4. **解鎖條件**
   - Agent 狀態變更為 `stopped` 或 `idle`
   - 用戶主動停止 Agent 執行
   - Agent 執行完成或發生錯誤

#### 前端實作要點

```svelte
<script>
  // 檢查 Agent 執行狀態
  $: isRunning = agent.status === 'running' || agent.status === 'active';
  $: isConfigLocked = isRunning;

  // 顯示鎖定提示
  $: lockMessage = isConfigLocked
    ? "⚠️ Agent 執行中，配置已鎖定。請先停止 Agent 才能修改設定。"
    : null;

  function handleConfigEdit() {
    if (isConfigLocked) {
      alert("Agent 執行中無法修改配置，請先停止 Agent。");
      return;
    }
    // 開啟編輯介面
  }
</script>

<!-- 配置編輯按鈕 -->
<Button
  on:click={handleConfigEdit}
  disabled={isConfigLocked}
  title={isConfigLocked ? "Agent 執行中，無法修改" : "編輯配置"}
>
  編輯配置
</Button>

<!-- 鎖定狀態提示 -->
{#if isConfigLocked}
  <div class="config-lock-banner bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
    <div class="flex items-start gap-3">
      <span class="text-yellow-600 text-xl">🔒</span>
      <div>
        <h4 class="text-sm font-semibold text-yellow-800 mb-1">配置已鎖定</h4>
        <p class="text-sm text-yellow-700">
          {lockMessage}
        </p>
      </div>
    </div>
  </div>
{/if}

<!-- 表單輸入禁用 -->
<input
  type="text"
  bind:value={config.investment_preferences}
  disabled={isConfigLocked}
  class:opacity-50={isConfigLocked}
  class:cursor-not-allowed={isConfigLocked}
/>
```

#### 使用者提示設計

1. **視覺提示**
   - 鎖定時顯示 🔒 圖標
   - 禁用的按鈕和輸入框半透明顯示
   - 使用黃色警告橫幅提示鎖定狀態

2. **互動提示**
   - 滑鼠懸停時顯示 tooltip 說明鎖定原因
   - 嘗試編輯時彈出提示對話框
   - 提供「停止 Agent」快捷操作按鈕

3. **狀態指示**
   - Agent 卡片上顯示執行狀態徽章
   - 配置頁面頂部顯示鎖定橫幅
   - 編輯按鈕旁顯示鎖定圖標

#### 例外情況處理

1. **緊急停止**
   - 即使在鎖定狀態，仍可執行「停止 Agent」操作
   - 停止後立即解鎖配置

2. **只讀查看**
   - 鎖定期間可以查看所有配置內容
   - 支援複製配置內容用於參考

3. **策略自主調整**
   - Agent 自主策略調整不受鎖定影響
   - Agent 透過 `record_strategy_change` 工具更新策略
   - 前端實時同步顯示策略變更記錄

---

## 🎨 UI 重構與顏色系統

### Agent 卡片簡化設計

基於 demo.html 設計理念，對 Agent 展示進行了全面重構：

#### AgentCardSimple 組件

創建了新的簡化卡片組件 (`AgentCardSimple.svelte`)，取代原有複雜設計：

**顯示內容**：

1. **Agent 名稱和狀態** - 彩色名稱 + 運行狀態指示器（綠色脈動/灰色靜止）
2. **資產概覽** - 總資產金額、總損益（綠色為正/紅色為負）
3. **現金餘額** - 當前可用現金
4. **迷你績效圖表** - Chart.js 渲染，響應式設計，懸停顯示詳細資料
5. **持有股數簡介** - 顯示前 3 檔持股，包含股票代號、名稱、股數、平均成本
6. **操作按鈕** - 開始交易/停止交易，按鈕顏色與 Agent 主題色一致

**特色功能**：

- 點擊卡片打開詳情 Modal
- 懸停效果：放大和陰影效果
- 顏色主題：每個 Agent 可設定獨特顏色
- 狀態指示：運行中的 Agent 有脈動動畫

#### AgentDetailModal 組件

新增詳細資訊 Modal (`AgentDetailModal.svelte`)：

**功能區塊**：

1. **基本資訊** - AI 模型、狀態、創建時間、單一持股上限、描述
2. **資產概覽** - 總資產、現金餘額、總損益（含百分比）
3. **績效圖表** - 完整的歷史績效走勢
4. **持倉詳情** - 所有持股的完整列表
5. **交易歷史** - 所有買入/賣出記錄
6. **編輯功能** - 可修改名稱、描述、顏色、單一持股上限
7. **刪除功能** - 確認對話框防止誤操作

### Agent 顏色系統

#### 資料庫層實作

**新增欄位**：

- `agents` 表添加 `color` 欄位 (VARCHAR(20))
- 預設值：`"34, 197, 94"` (綠色)
- 格式：RGB 格式，例如 `"34, 197, 94"`

**遷移版本**：`1.4.0` - `AddAgentColorMigration`

#### API 支援

更新的資料模型：

```javascript
// CreateAgentRequest & UpdateAgentRequest
color: string = Field(
  default="34, 197, 94",
  pattern=r"^\d{1,3},\s*\d{1,3},\s*\d{1,3}$",
  description="UI 卡片顏色 (RGB 格式)"
)
```

#### 預設顏色配置

| 顏色 | RGB 值 | 類型 | 說明 |
|------|--------|------|------|
| 🟢 綠色 | 34, 197, 94 | 穩健型 | 預設顏色，價值投資策略 |
| 🟠 橙色 | 249, 115, 22 | 積極型 | 高成長、高風險策略 |
| 🔵 藍色 | 59, 130, 246 | 平衡型 | 均衡配置策略 |
| 🟣 紫色 | 168, 85, 247 | 保守型 | 低風險、穩定收益策略 |
| 🔴 紅色 | 239, 68, 68 | 高風險 | 宏觀交易、投機策略 |
| 🔷 青色 | 6, 182, 212 | 科技導向 | 科技股、創新投資策略 |

#### 顏色選擇功能

**在 AgentCreationForm 中**：

- 6 種預設顏色選項（視覺化圓形色塊）
- 自定義顏色選擇器（Color Picker + RGB 手動輸入）
- 十六進位 ↔ RGB 格式轉換
- 摺疊式自定義區域

**在 AgentDetailModal 中**：

- 編輯模式下可修改顏色
- 即時預覽更新

#### 智慧配色

系統提供智慧配色腳本 (`scripts/assign_agent_colors.py`)：

```bash
# 自動智慧配色
python scripts/assign_agent_colors.py

# 列出現有配色
python scripts/assign_agent_colors.py --list
```

**智慧配色規則**：

- 根據 Agent 名稱和描述中的關鍵字自動分配顏色
- 例如：「巴菲特」→ 綠色，「索羅斯」→ 紅色，「科技」→ 青色

### Modal 系統優化

#### 全寬支援

Modal 組件新增 `size="full"` 選項：

```javascript
const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-7xl w-full', // 新增
};
```

#### Agent 卡片操作按鈕

AgentCardSimple 新增操作按鈕：

- **編輯按鈕**：鉛筆圖標，點擊進入詳細編輯模式
- **刪除按鈕**：垃圾桶圖標，支援刪除確認對話框
- **半透明懸停效果**：避免干擾主要內容

### API 擴充

新增交易記錄 API：

```javascript
// frontend/src/lib/api.js
getTransactions(agentId, limit = 50, offset = 0) {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  return this.request(`/api/trading/agents/${agentId}/transactions?${params}`);
}
```

### App.svelte 重構

**主要變更**：

1. **簡化組件結構** - 移除 `AgentGrid`，直接使用 `AgentCardSimple`
2. **優化狀態管理** - 使用對象存儲 `agentPerformanceData`、`agentHoldings`、`agentTransactions`
3. **按需載入** - 點擊卡片時才載入詳細資料
4. **事件處理優化**：

```javascript
// 新的事件處理函數
async function handleAgentSelect(agent) {
  selectAgent(agent.agent_id);
  await loadAgentDetails(agent.agent_id);
  showDetailModal = true;
}

async function handleAgentEdit(agent, updates) {
  await updateAgent(agent.agent_id, updates);
  notifySuccess(`Agent ${agent.name} 已更新`);
  await loadAgents();
}

function handleDetailModalClose() {
  showDetailModal = false;
  selectAgent(null);
}
```

### 使用者體驗改進

#### 資訊層級清晰

- **首頁**：快速瀏覽所有 Agent 的關鍵指標
- **詳情 Modal**：深入查看單一 Agent 的完整資訊

#### 視覺設計

- **顏色差異化**：不同 Agent 使用不同顏色，易於區分
- **動畫效果**：運行中的 Agent 有脈動動畫，立即識別狀態
- **響應式設計**：適配桌面和移動設備

#### 操作便捷性

- **一鍵操作**：開始/停止交易按鈕在卡片上
- **快速編輯**：點擊卡片 → 詳情 Modal → 編輯按鈕
- **防誤操作**：刪除前需確認

### 遷移管理

使用統一的遷移腳本：

```bash
# 執行顏色欄位遷移
./scripts/db_migrate.sh up 1.4.0

# 檢查遷移狀態
./scripts/db_migrate.sh status

# 為現有 Agent 分配顏色
python scripts/assign_agent_colors.py
```

---

## 🎨 Tailwind CSS 設計系統

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

  // 策略變更 API
  getStrategyChanges(agentId, limit = 50, offset = 0, changeType = null) {
    const params = new URLSearchParams({ limit, offset });
    if (changeType) params.append('change_type', changeType);
    return this.request(`/api/agents/${agentId}/strategy-changes?${params}`);
  }

  getLatestStrategy(agentId) {
    return this.request(`/api/agents/${agentId}/strategy-changes/latest`);
  }

  recordStrategyChange(agentId, changeData) {
    return this.request(`/api/agents/${agentId}/strategy-changes`, {
      method: "POST",
      body: JSON.stringify(changeData),
    });
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

### 3. 工具函數 (lib/utils.js)

提供前端通用的格式化和工具函數。

```javascript
// 貨幣格式化
export function formatCurrency(value) {
  if (value === null || value === undefined) return 'N/A';
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: 'TWD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
}

// 百分比格式化
export function formatPercentage(value, decimals = 2) {
  if (value === null || value === undefined) return 'N/A';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

// 日期時間格式化
export function formatDateTime(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(date);
}

// 日期格式化（不含時間）
export function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(date);
}

// 時間格式化（不含日期）
export function formatTime(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('zh-TW', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(date);
}

// 數字格式化（千分位）
export function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined) return 'N/A';
  return new Intl.NumberFormat('zh-TW', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
}

// 相對時間格式化（例如：2小時前）
export function formatRelativeTime(dateString) {
  if (!dateString) return 'N/A';

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) return `${diffDays} 天前`;
  if (diffHours > 0) return `${diffHours} 小時前`;
  if (diffMins > 0) return `${diffMins} 分鐘前`;
  return '剛剛';
}

// 檢查是否為台股交易時間
export function isMarketOpen() {
  const now = new Date();
  const day = now.getDay(); // 0 = 週日, 6 = 週六
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const timeInMinutes = hours * 60 + minutes;

  // 週一到週五
  if (day >= 1 && day <= 5) {
    // 09:00 - 13:30
    return timeInMinutes >= 540 && timeInMinutes <= 810;
  }

  return false;
}

// 取得下一個交易日開盤時間
export function getNextMarketOpen() {
  const now = new Date();
  const day = now.getDay();
  const hours = now.getHours();
  const minutes = now.getMinutes();

  // 如果是週末，返回下週一 09:00
  if (day === 0) { // 週日
    const next = new Date(now);
    next.setDate(next.getDate() + 1);
    next.setHours(9, 0, 0, 0);
    return next;
  }
  if (day === 6) { // 週六
    const next = new Date(now);
    next.setDate(next.getDate() + 2);
    next.setHours(9, 0, 0, 0);
    return next;
  }

  // 如果已經收盤，返回明天 09:00
  if (hours >= 13 && minutes >= 30) {
    const next = new Date(now);
    next.setDate(next.getDate() + 1);
    next.setHours(9, 0, 0, 0);
    return next;
  }

  // 否則返回今天 09:00
  const next = new Date(now);
  next.setHours(9, 0, 0, 0);
  return next;
}
```

### 4. Agents Store (stores/agents.js)

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
        // 檢查 Agent 是否正在執行（配置鎖定檢查）
        const currentAgent = await this.getAgent(agentId);
        if (currentAgent && (currentAgent.status === 'running' || currentAgent.status === 'active')) {
          throw new Error('無法更新配置：Agent 正在執行中。請先停止 Agent 才能修改配置。');
        }

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

    async getAgent(agentId) {
      try {
        let targetAgent = null;
        update((agents) => {
          targetAgent = agents.find(agent => agent.id === agentId);
          return agents;
        });
        return targetAgent;
      } catch (error) {
        console.error("Failed to get agent:", error);
        return null;
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
            agent.id === agentId
              ? {
                  ...agent,
                  status: "running",
                  config_locked: true, // 標記配置已鎖定
                  started_at: new Date().toISOString()
                }
              : agent,
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
            agent.id === agentId
              ? {
                  ...agent,
                  status: "stopped",
                  config_locked: false, // 解鎖配置
                  stopped_at: new Date().toISOString()
                }
              : agent,
          ),
        );
      } catch (error) {
        console.error("Failed to stop agent:", error);
        throw error;
      }
    },

    // 檢查 Agent 配置是否被鎖定
    isConfigLocked(agentId) {
      let locked = false;
      update((agents) => {
        const agent = agents.find(a => a.id === agentId);
        if (agent) {
          locked = agent.config_locked ||
                   agent.status === 'running' ||
                   agent.status === 'active';
        }
        return agents;
      });
      return locked;
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

**環境變數配置 (.env.example)**:

```bash
# API 端點配置
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# 功能開關
VITE_ENABLE_STRATEGY_TRACKING=true
VITE_ENABLE_AGENT_TOOLS=true

# 開發模式
VITE_DEV_MODE=true
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

> **注意**: 完整的專案結構定義請參閱 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
> 本節僅列出前端系統的完整檔案結構。

### 前端應用結構

```
frontend/                          # 前端應用根目錄
├── public/                        # 靜態資源
│   └── vite.svg
├── src/                           # 前端源代碼
│   ├── App.svelte                 # 主應用程式組件
│   ├── main.js                    # Vite 進入點
│   ├── app.css                    # 全域樣式
│   ├── components/                # 可重用組件
│   │   ├── Layout/                # 佈局組件
│   │   │   ├── Navbar.svelte
│   │   │   └── Sidebar.svelte
│   │   ├── Agent/                 # Agent 相關組件
│   │   │   ├── AgentCard.svelte
│   │   │   ├── AgentGrid.svelte
│   │   │   ├── AgentModal.svelte
│   │   │   ├── AgentCreationForm.svelte
│   │   │   ├── AgentDashboard.svelte
│   │   │   ├── AgentConfigEditor.svelte
│   │   │   ├── AgentToolsSelector.svelte
│   │   │   └── AgentPerformancePanel.svelte
│   │   ├── Chart/                 # 圖表組件
│   │   │   ├── PerformanceChart.svelte
│   │   │   └── MarketChart.svelte
│   │   ├── Market/                # 市場相關組件
│   │   │   ├── MarketPanel.svelte
│   │   │   └── StockQuote.svelte
│   │   └── UI/                    # 基礎 UI 組件
│   │       ├── Button.svelte
│   │       ├── Modal.svelte
│   │       └── StatusIndicator.svelte
│   ├── routes/                    # SvelteKit 路由頁面
│   │   ├── +layout.svelte
│   │   ├── +page.svelte           # 主儀表板
│   │   ├── agents/                # Agent 管理頁面
│   │   │   ├── +page.svelte
│   │   │   └── [id]/
│   │   │       └── +page.svelte
│   │   └── settings/              # 設定頁面
│   │       └── +page.svelte
│   ├── stores/                    # Svelte stores 狀態管理
│   │   ├── agents.js              # Agent 狀態管理
│   │   ├── websocket.js           # WebSocket 連線狀態
│   │   ├── market.js              # 市場數據狀態
│   │   └── notifications.js       # 通知系統
│   ├── lib/                       # 前端工具函數
│   │   ├── api.js                 # API 客戶端
│   │   ├── websocket.js           # WebSocket 管理
│   │   ├── utils.js               # 共用工具
│   │   └── constants.js           # 前端常數
│   └── types/                     # TypeScript 類型定義
│       ├── agent.ts               # Agent 類型
│       ├── api.ts                 # API 類型
│       └── websocket.ts           # WebSocket 類型
├── vite.config.js                 # Vite 配置
├── tailwind.config.js             # Tailwind CSS 配置
├── postcss.config.js              # PostCSS 配置
├── package.json                   # NPM 配置
└── tsconfig.json                  # TypeScript 配置

tests/frontend/                    # 前端測試 (與主專案 tests/ 目錄整合)
├── unit/                          # 單元測試
│   ├── components/                # 組件測試
│   │   ├── Agent/
│   │   │   ├── AgentCard.test.js
│   │   │   ├── AgentDashboard.test.js
│   │   │   ├── AgentCreationForm.test.js
│   │   │   ├── StrategyHistoryView.test.js
│   │   │   └── AgentConfigEditor.test.js
│   │   ├── Chart/
│   │   │   └── PerformanceChart.test.js
│   │   └── UI/
│   │       ├── Button.test.js
│   │       └── Modal.test.js
│   ├── stores/                    # Store 測試
│   │   ├── agents.test.js
│   │   ├── websocket.test.js
│   │   └── market.test.js
│   └── lib/                       # 工具函數測試
│       ├── api.test.js
│       ├── websocket.test.js
│       └── utils.test.js
├── integration/                   # 整合測試
│   ├── api-integration.test.js    # API 整合測試
│   ├── websocket-flow.test.js     # WebSocket 流程測試
│   └── agent-workflow.test.js     # Agent 工作流程測試
└── e2e/                           # 端到端測試
    ├── agent-management.test.js   # Agent 管理流程
    ├── trading-simulation.test.js # 交易模擬流程
    └── dashboard-functionality.test.js # 儀表板功能測試
```

---

## 🧪 Agent 組件測試策略

### AgentCreationForm 測試重點

```javascript
// tests/frontend/unit/components/Agent/AgentCreationForm.test.js
import { render, fireEvent, waitFor } from '@testing-library/svelte';
import AgentCreationForm from '../../../../src/components/Agent/AgentCreationForm.svelte';

describe('AgentCreationForm', () => {
  test('即時生成指令預覽', async () => {
    const { getByRole, getByText } = render(AgentCreationForm);

    const nameInput = getByRole('textbox', { name: /agent 名稱/i });
    await fireEvent.input(nameInput, { target: { value: '測試 Agent' } });

    // 驗證預覽區域更新
    await waitFor(() => {
      expect(getByText(/You are 測試 Agent/)).toBeInTheDocument();
    });
  });

  test('表單驗證：必填欄位', async () => {
    const { getByRole, getByText } = render(AgentCreationForm);

    const submitButton = getByRole('button', { name: /創建/i });
    await fireEvent.click(submitButton);

    // 驗證錯誤訊息
    await waitFor(() => {
      expect(getByText(/請填寫/)).toBeInTheDocument();
    });
  });

  test('成功創建 Agent', async () => {
    const mockCreate = jest.fn();
    const { getByRole } = render(AgentCreationForm, {
      props: { onCreate: mockCreate }
    });

    // 填寫表單...
    const submitButton = getByRole('button', { name: /創建/i });
    await fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalled();
    });
  });
});
```

### StrategyHistoryView 測試重點

```javascript
// tests/frontend/unit/components/Agent/StrategyHistoryView.test.js
import { render, fireEvent, waitFor } from '@testing-library/svelte';
import StrategyHistoryView from '../../../../src/components/Agent/StrategyHistoryView.svelte';

describe('StrategyHistoryView', () => {
  const mockChanges = [
    {
      id: '1',
      timestamp: '2025-10-06T10:00:00Z',
      trigger_reason: '連續虧損',
      change_type: 'auto',
      change_summary: '啟動防禦模式',
      performance_at_change: {
        total_return: -2.5,
        drawdown: -3.2,
        sharpe_ratio: 0.8
      }
    }
  ];

  test('顯示策略變更列表', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockChanges)
      })
    );

    const { getByText } = render(StrategyHistoryView, {
      props: { agentId: 'test-agent-1' }
    });

    await waitFor(() => {
      expect(getByText('啟動防禦模式')).toBeInTheDocument();
      expect(getByText('連續虧損')).toBeInTheDocument();
    });
  });

  test('開啟變更詳情彈窗', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockChanges)
      })
    );

    const { getByText, queryByRole } = render(StrategyHistoryView, {
      props: { agentId: 'test-agent-1' }
    });

    await waitFor(() => {
      expect(getByText('啟動防禦模式')).toBeInTheDocument();
    });

    // 點擊變更卡片
    const changeCard = getByText('啟動防禦模式').closest('.change-card');
    await fireEvent.click(changeCard);

    // 驗證彈窗開啟
    await waitFor(() => {
      expect(queryByRole('dialog')).toBeInTheDocument();
    });
  });
});
```

### 整合測試

```javascript
// tests/frontend/integration/agent-workflow.test.js
import { render, fireEvent, waitFor } from '@testing-library/svelte';

describe('Agent 創建與策略追蹤工作流程', () => {
  test('完整流程：創建 -> 運行 -> 策略調整 -> 查看歷史', async () => {
    // 1. 創建 Agent
    // 2. 啟動 Agent
    // 3. 模擬策略調整事件
    // 4. 查看策略變更歷史
    // 詳細測試實作...
  });
});
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
  - [ ] 實作執行狀態檢測邏輯 (isRunning)
  - [ ] 實作配置鎖定狀態顯示 (isConfigLocked)
  - [ ] 禁用執行中 Agent 的設定按鈕
- [ ] 實作 Agent 創建表單組件 (AgentCreationForm.svelte) - Prompt 驅動設計
- [ ] 實作 Agent 配置編輯器組件 (AgentConfigEditor.svelte)
  - [ ] 實作配置鎖定檢查邏輯
  - [ ] 實作鎖定狀態警告橫幅
  - [ ] 禁用執行中 Agent 的所有輸入欄位
  - [ ] 實作「停止 Agent 並解鎖配置」功能
  - [ ] 實作雙重確認機制防止誤修改
- [ ] 實作策略變更歷史查看組件 (StrategyHistoryView.svelte)
- [ ] 實作策略變更詳情彈窗組件 (StrategyChangeModal.svelte)
- [ ] 實作績效圖表組件 (PerformanceChart.svelte)

### 狀態管理與工具函數

- [ ] 實作 Agents Store
  - [ ] 實作 `updateAgent` 配置鎖定檢查
  - [ ] 實作 `startAgent` 自動鎖定配置邏輯
  - [ ] 實作 `stopAgent` 自動解鎖配置邏輯
  - [ ] 實作 `isConfigLocked` 輔助方法
  - [ ] 在狀態中追蹤 `config_locked` 標記
- [ ] 實作 WebSocket Store
  - [ ] 監聽 Agent 狀態變更事件
  - [ ] 即時更新配置鎖定狀態
- [ ] 實作市場數據 Store
- [ ] 實作工具函數庫 (格式化、時間處理等)
- [ ] 整合即時數據更新

### API 整合

- [ ] 實作 API 客戶端
- [ ] 實作策略變更 API 端點整合
- [ ] 實作 WebSocket 連線管理
- [ ] 實作錯誤處理和重連機制
- [ ] 測試所有 API 端點（包括策略變更相關）

### 用戶體驗

- [ ] 實作響應式設計
- [ ] 實作載入狀態和錯誤提示
- [ ] 實作動畫和轉場效果
- [ ] Agent 創建表單的輸入驗證和即時預覽
- [ ] 策略變更歷史的時間軸視圖
- [ ] **配置鎖定使用者體驗**
  - [ ] 鎖定狀態視覺提示 (🔒 圖標、半透明等)
  - [ ] 滑鼠懸停 tooltip 說明鎖定原因
  - [ ] 嘗試編輯時的友善錯誤提示
  - [ ] 提供「停止 Agent」快捷操作
  - [ ] 配置鎖定警告橫幅動畫效果
- [ ] 跨瀏覽器測試

### 性能優化

- [ ] 實作程式碼分割
- [ ] 優化 Bundle 大小
- [ ] 實作圖片和資源優化
- [ ] 性能測試和調優

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-12
