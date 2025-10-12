<script>
  /**
   * AgentCardSimple Component
   *
   * 簡化的 Agent 卡片組件，模仿 demo 頁面的設計
   * 顯示關鍵資訊：名稱、資產、損益、現金、簡易圖表、持股簡介
   */

  import { onMount } from 'svelte';
  import { Button } from '../UI/index.js';
  import { AGENT_STATUS } from '../../lib/constants.js';
  import { formatCurrency } from '../../lib/utils.js';

  // Props
  let {
    agent,
    performanceData = [],
    holdings = [],
    onclick = undefined,
    onstart = undefined,
    onstop = undefined,
    onedit = undefined,
    ondelete = undefined,
  } = $props();

  // 計算資產相關數據
  let totalAssets = $derived(agent.initial_funds || 1000000); // 從 API 獲取
  let currentCash = $derived(agent.initial_funds || 345020.5); // 從 API 獲取
  let pnl = $derived(totalAssets - agent.initial_funds);
  let pnlPercent = $derived((pnl / agent.initial_funds) * 100);
  let isProfit = $derived(pnl >= 0);

  // Agent 顏色 (從設定中取得，預設為綠色或橙色)
  let agentColor = $derived(agent.color || '34, 197, 94');

  // 是否可以啟動/停止
  let canStart = $derived(
    agent.status === AGENT_STATUS.IDLE || agent.status === AGENT_STATUS.STOPPED
  );
  let canStop = $derived(agent.status === AGENT_STATUS.RUNNING);

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

  function renderMiniChart() {
    if (!window.Chart || !chartCanvas) return;

    const ctx = chartCanvas.getContext('2d');

    // 準備數據
    const labels = performanceData.map((d, i) => i);
    const values = performanceData.map((d) => d.value || d.total_assets || totalAssets);

    if (chartInstance) {
      chartInstance.destroy();
    }

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

  function handleCardClick() {
    onclick?.(agent);
  }

  function handleStart(e) {
    e.stopPropagation();
    onstart?.(agent);
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
  class="agent-card rounded-2xl border border-gray-700 bg-gray-800 p-6 shadow-lg transition-all duration-300 hover:shadow-2xl hover:scale-[1.02] cursor-pointer"
  style="border-color: rgba({agentColor}, 0.3);"
  onclick={handleCardClick}
  onkeydown={(e) => e.key === 'Enter' && handleCardClick()}
  role="button"
  tabindex="0"
>
  <!-- Header: Agent 名稱、狀態和操作按鈕 -->
  <div class="mb-4 flex items-center justify-between">
    <div class="flex-1">
      <h3 class="text-xl font-bold" style="color: rgb({agentColor});">
        {agent.name}
      </h3>
      <div class="flex items-center gap-2 mt-1">
        {#if agent.status === AGENT_STATUS.RUNNING}
          <span class="status-dot status-running"></span>
          <span class="text-xs text-green-400">運行中</span>
        {:else}
          <span class="status-dot status-stopped"></span>
          <span class="text-xs text-gray-400">已停止</span>
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
    <p class="text-lg font-semibold text-white">{formatCurrency(currentCash)}</p>
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
              <span class="font-medium text-gray-300">{holding.symbol}</span>
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
  <div class="flex gap-3">
    {#if canStart}
      <Button
        variant="primary"
        size="md"
        fullWidth
        onclick={handleStart}
        style="background-color: rgb({agentColor}); border-color: rgb({agentColor});"
      >
        <svg class="mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        開始交易
      </Button>
    {/if}

    {#if canStop}
      <Button variant="secondary" size="md" fullWidth onclick={handleStop}>
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
        停止交易
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
