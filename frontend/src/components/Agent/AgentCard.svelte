<script>
  /**
   * AgentCard Component
   *
   * Agent 卡片組件,顯示 Agent 基本資訊、狀態和操作按鈕
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   * Svelte 5 compatible - uses callback props instead of createEventDispatcher
   * 採用 AgentCardSimple 的暗色主題和豐富視覺效果
   */

  import { onMount } from 'svelte';
  import { Button } from '../UI/index.js';
  import { AGENT_STATUS, AGENT_RUNTIME_STATUS } from '../../shared/constants.js';
  import { formatCurrency } from '../../shared/utils.js';
  import { isOpen } from '../../stores/market.js';

  // Props
  let {
    agent,
    performanceData = [],
    holdings = [],
    selected = false,
    onclick = undefined,
    onobserve = undefined,
    ontrade = undefined,
    onrebalance = undefined,
    onstop = undefined,
    onedit = undefined,
    ondelete = undefined,
  } = $props();

  // 計算資產相關數據
  // 計算總資產
  let totalAssets = $derived.by(() => {
    const portfolioValue = agent.portfolio?.total_value || 0;
    const funds = agent.current_funds || agent.initial_funds || 1000000;
    return portfolioValue > 0 ? portfolioValue : funds;
  });

  // 計算當前現金
  let currentCash = $derived.by(() => {
    const funds = agent.current_funds || agent.initial_funds || 1000000;
    return agent.portfolio?.cash || funds;
  });

  // 計算損益
  let pnl = $derived.by(() => {
    const assets =
      agent.portfolio?.total_value || agent.current_funds || agent.initial_funds || 1000000;
    const initial = agent.initial_funds || 1000000;
    return assets - initial;
  });

  // 判斷是否盈利
  let isProfit = $derived.by(() => {
    const assets =
      agent.portfolio?.total_value || agent.current_funds || agent.initial_funds || 1000000;
    const initial = agent.initial_funds || 1000000;
    return assets >= initial;
  });

  // Agent 顏色 (從設定中取得，預設為綠色)
  let agentColor = $derived(agent.color_theme || '34, 197, 94');

  // 是否可以編輯 (執行中不可編輯 - 配置鎖定)
  let isEditable = $derived(agent.runtime_status !== AGENT_RUNTIME_STATUS.RUNNING);

  // 是否可以啟動 (persistent status 為 active/inactive 且 runtime 不在執行中)
  let canStart = $derived(
    (agent.status === AGENT_STATUS.ACTIVE || agent.status === AGENT_STATUS.INACTIVE) &&
      (agent.runtime_status === AGENT_RUNTIME_STATUS.IDLE ||
        agent.runtime_status === AGENT_RUNTIME_STATUS.STOPPED ||
        !agent.runtime_status)
  );

  // 是否可以停止
  let canStop = $derived(agent.runtime_status === AGENT_RUNTIME_STATUS.RUNNING);

  // Canvas for mini chart
  let chartCanvas;
  let chartInstance;

  onMount(() => {
    if (chartCanvas && performanceData.length > 0) {
      renderMiniChart();
    }

    return () => {
      if (chartInstance) {
        chartInstance.destroy();
      }
    };
  });

  // 監聽數據變化，重新渲染圖表
  $effect(() => {
    if (chartCanvas && performanceData.length > 0) {
      renderMiniChart();
    }
  });

  function renderMiniChart() {
    // @ts-ignore - Chart.js is loaded via CDN in index.html
    if (!window.Chart || !chartCanvas) return;

    const ctx = chartCanvas.getContext('2d');

    // 準備數據
    const labels = performanceData.map((d, i) => i);
    const values = performanceData.map((d) => d.value || d.total_assets || totalAssets);

    if (chartInstance) {
      chartInstance.destroy();
    }

    // @ts-ignore - Chart.js is loaded via CDN in index.html
    chartInstance = new window.Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            data: values,
            borderColor: `rgb(${agentColor})`,
            backgroundColor: `rgba(${agentColor}, 0.1)`,
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2.5,
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: true,
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: `rgb(${agentColor})`,
            borderWidth: 1,
            callbacks: {
              label: (context) => `資產: ${formatCurrency(context.parsed.y)}`,
            },
          },
        },
        scales: {
          x: { display: false },
          y: { display: false },
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false,
        },
      },
    });
  }

  // 函數定義
  function handleClick() {
    onclick?.(agent);
  }

  function handleObserve(e) {
    e.stopPropagation();
    onobserve?.(agent, 'OBSERVATION');
  }

  function handleTrade(e) {
    e.stopPropagation();
    ontrade?.(agent, 'TRADING');
  }

  function handleRebalance(e) {
    e.stopPropagation();
    onrebalance?.(agent, 'REBALANCING');
  }

  function handleStop(e) {
    e.stopPropagation();
    onstop?.(agent);
  }

  function handleEdit(e) {
    e.stopPropagation();
    onedit?.(agent);
  }

  function handleDelete(e) {
    e.stopPropagation();
    if (confirm(`確定要刪除 Agent "${agent.name}"?\n\n此操作無法復原。`)) {
      ondelete?.(agent);
    }
  }
</script>

<div
  class="agent-card rounded-2xl border border-gray-700 bg-gray-800 p-6 shadow-lg transition-all duration-300 hover:shadow-2xl hover:scale-[1.02] cursor-pointer {selected
    ? 'ring-2 ring-primary-500'
    : ''}"
  style="border-color: rgba({agentColor}, 0.3);"
  onclick={handleClick}
  onkeydown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabindex="0"
>
  <!-- Header: Agent 名稱、狀態和操作按鈕 -->
  <div class="mb-4 flex items-center justify-between">
    <div class="flex-1">
      <h3 class="text-xl font-bold" style="color: rgb({agentColor});">
        {agent.name}
      </h3>
      <div class="text-base text-gray-500 my-3" style="color: rgb({agentColor});">
        {agent.ai_model || '未知模型'}
      </div>
      <div class="flex items-center gap-2 mt-1">
        {#if agent.runtime_status === AGENT_RUNTIME_STATUS.RUNNING}
          <span class="status-dot status-running"></span>
          <span class="text-sm text-green-400">運行中</span>
        {:else}
          <span class="status-dot status-stopped"></span>
          <span class="text-sm text-gray-400">已停止</span>
        {/if}
      </div>
    </div>

    <!-- 操作按鈕 -->
    <div class="flex items-center gap-1 opacity-70 hover:opacity-100 transition-opacity">
      {#if onedit}
        <button
          onclick={handleEdit}
          class="rounded-lg p-2 text-gray-400 hover:bg-gray-700 hover:text-white transition-colors"
          title="編輯 Agent"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            />
          </svg>
        </button>
      {/if}

      {#if ondelete}
        <button
          onclick={handleDelete}
          class="rounded-lg p-2 text-gray-400 hover:bg-red-600 hover:text-white transition-colors"
          title="刪除 Agent"
          disabled={!isEditable}
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      {/if}
    </div>
  </div>

  <!-- 資產概覽 -->
  <div class="mb-6 grid grid-cols-2 gap-4">
    <div>
      <p class="text-xs text-gray-400 mb-1">總資產</p>
      <p class="text-2xl font-bold text-white">{formatCurrency(totalAssets)}</p>
    </div>
    <div>
      <p class="text-xs text-gray-400 mb-1">總損益</p>
      <p class="text-2xl font-bold" class:text-gain={isProfit} class:text-loss={!isProfit}>
        {isProfit ? '+' : ''}{formatCurrency(pnl)}
      </p>
    </div>
  </div>

  <!-- 現金餘額 -->
  <div class="mb-4">
    <p class="text-xs text-gray-400 mb-1">持有現金</p>
    <p class="text-lg font-semibold text-white">
      {formatCurrency(currentCash)}
    </p>
  </div>

  <!-- 迷你績效圖表 -->
  <div class="mb-6 h-32">
    <canvas bind:this={chartCanvas}></canvas>
  </div>

  <!-- 持有股數簡介 -->
  <div class="mb-6">
    <p class="text-xs text-gray-400 mb-3 font-semibold">持有股數</p>
    {#if holdings && holdings.length > 0}
      <div class="space-y-2">
        {#each holdings.slice(0, 3) as holding}
          <div class="flex items-center justify-between text-sm">
            <div class="flex items-center gap-2">
              <span class="font-medium text-gray-300">{holding.ticker || holding.symbol}</span>
              <span class="text-gray-500">{holding.name || ''}</span>
            </div>
            <div class="text-right">
              <span class="text-white font-medium">{holding.shares || 0} 股</span>
              <span class="text-gray-400 text-xs ml-2"
                >@ {formatCurrency(holding.avg_price || 0)}</span
              >
            </div>
          </div>
        {/each}
        {#if holdings.length > 3}
          <p class="text-xs text-gray-500 text-center">
            還有 {holdings.length - 3} 檔股票...
          </p>
        {/if}
      </div>
    {:else}
      <p class="text-sm text-gray-500 text-center py-4">尚無持股</p>
    {/if}
  </div>

  <!-- 操作按鈕 -->
  <div class="flex gap-2 flex-col">
    <!-- 模式選擇按鈕 -->
    {#if canStart}
      <div class="grid grid-cols-3 gap-2">
        <Button
          variant="secondary"
          size="sm"
          fullWidth
          onclick={handleObserve}
          disabled={!$isOpen}
          title="觀察模式：分析市場無交易"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
          <span class="hidden sm:inline">觀察</span>
        </Button>
        <Button
          variant="secondary"
          size="sm"
          fullWidth
          onclick={handleTrade}
          disabled={!$isOpen}
          title="交易模式：執行交易決策"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <span class="hidden sm:inline">交易</span>
        </Button>
        <Button
          variant="secondary"
          size="sm"
          fullWidth
          onclick={handleRebalance}
          disabled={!$isOpen}
          title="再平衡模式：調整投資組合"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <span class="hidden sm:inline">平衡</span>
        </Button>
      </div>
    {/if}

    <!-- 停止按鈕（總是顯示當 Agent 運行中） -->
    {#if canStop}
      <Button
        variant="danger"
        size="md"
        fullWidth
        onclick={handleStop}
        disabled={!$isOpen}
        title="停止執行"
      >
        <svg class="mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
          />
        </svg>
        停止
      </Button>
    {/if}
  </div>
</div>

<style>
  .text-gain {
    color: #4ade80; /* green-400 */
  }
  .text-loss {
    color: #f87171; /* red-400 */
  }
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }
  .status-running {
    background-color: #22c55e;
    box-shadow: 0 0 8px #22c55e;
    animation: pulse 2s infinite;
  }
  .status-stopped {
    background-color: #6b7280;
  }
  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
</style>
