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
6. **Agent 配置介面** - Prompt 驅動的 Agent 創建表單與策略演化追蹤

### Agent 配置介面特色

本專案採用 **Prompt 驅動** 的 Agent 設計理念（詳見 AGENT_IMPLEMENTATION.md），前端介面設計特點：

- **自然語言配置**: 用戶透過開放式文字輸入描述投資偏好和策略調整依據
- **即時指令預覽**: 表單自動生成並展示 Agent 實際執行指令
- **策略演化追蹤**: 完整記錄和展示 Agent 策略變更歷史
- **透明度優先**: 所有策略調整都有詳細的觸發原因、績效背景和 Agent 說明
- **簡潔直觀**: 避免複雜的參數配置，專注於投資意圖的表達

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

### 5. 策略變更歷史查看組件 (StrategyHistoryView.svelte)

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
- [ ] 實作 Agent 創建表單組件 (AgentCreationForm.svelte) - Prompt 驅動設計
- [ ] 實作策略變更歷史查看組件 (StrategyHistoryView.svelte)
- [ ] 實作策略變更詳情彈窗組件 (StrategyChangeModal.svelte)
- [ ] 實作績效圖表組件 (PerformanceChart.svelte)

### 狀態管理與工具函數

- [ ] 實作 Agents Store
- [ ] 實作 WebSocket Store
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
- [ ] 跨瀏覽器測試

### 性能優化

- [ ] 實作程式碼分割
- [ ] 優化 Bundle 大小
- [ ] 實作圖片和資源優化
- [ ] 性能測試和調優

---

**文檔維護**: CasualTrader 開發團隊
**最後更新**: 2025-10-06
