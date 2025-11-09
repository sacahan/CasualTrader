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
  import { AGENT_STATUS, AGENT_RUNTIME_STATUS, WS_EVENT_TYPES } from '../../shared/constants.js';
  import { formatCurrency } from '../../shared/utils.js';
  import { isOpen } from '../../stores/market.js';
  import { addEventListener } from '../../stores/websocket.js';
  import { executionRetryManager } from '../../shared/retry.js';

  // Props
  let {
    agent,
    performanceData = [],
    holdings = [],
    selected = false,
    onclick = undefined,
    ontrade = undefined,
    onrebalance = undefined,
    onstop = undefined,
    onedit = undefined,
    ondelete = undefined,
  } = $props();

  // 計算資產相關數據
  // 計算持股總市值（基於市場價值，如果沒有則使用成本價作為估計）
  // 由於後端尚未提供實時行情，暫用 market_value = total_cost 作為估計
  // 當後端集成實時行情後，計算會自動更新
  let holdingsTotalValue = $derived.by(() => {
    if (!holdings || holdings.length === 0) return 0;
    return holdings.reduce((sum, holding) => {
      // 優先使用 market_value，否則用 total_cost（後端當前估計相同）
      const value = holding.market_value ?? holding.total_cost ?? 0;
      return sum + value;
    }, 0);
  });

  // 計算總資產 = 現金 + 持股市值
  // 這才是真實的投資組合淨值
  let totalAssets = $derived.by(() => {
    const currentFunds = agent.current_funds ?? agent.initial_funds;
    return currentFunds + holdingsTotalValue;
  });

  // 計算當前現金（不包含持股）
  let currentCash = $derived(agent.current_funds ?? agent.initial_funds);

  // 計算損益 = 總資產 - 初始投入資金
  let pnl = $derived(totalAssets - agent.initial_funds);

  // 判斷是否盈利
  let isProfit = $derived(totalAssets >= agent.initial_funds);

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

  // 本地狀態 - 執行加載和錯誤
  let isExecuting = $state(false);
  let executionError = $state(null);
  let executionResult = $state(null);
  let showRetryButton = $state(false);
  let retryCount = $state(0);

  // Canvas for mini chart
  let chartCanvas;
  let chartInstance;

  // WebSocket 事件監聽取消函數
  let unsubscribeExecStarted;
  let unsubscribeExecCompleted;
  let unsubscribeExecFailed;
  let unsubscribeExecStopped;

  onMount(() => {
    // 設置 WebSocket 事件監聽
    unsubscribeExecStarted = addEventListener(WS_EVENT_TYPES.EXECUTION_STARTED, (payload) => {
      // 只監聽本 Agent 的事件
      if (payload.agent_id === agent.agent_id) {
        isExecuting = true;
        executionError = null;
        executionResult = null;
      }
    });

    unsubscribeExecCompleted = addEventListener(WS_EVENT_TYPES.EXECUTION_COMPLETED, (payload) => {
      if (payload.agent_id === agent.agent_id) {
        isExecuting = false;
        executionResult = {
          success: true,
          time_ms: payload.execution_time_ms,
          mode: payload.mode,
        };

        // 成功時重置重試計數和狀態
        executionRetryManager.reset(agent.agent_id);
        showRetryButton = false;
        retryCount = 0;
      }
    });

    unsubscribeExecFailed = addEventListener(WS_EVENT_TYPES.EXECUTION_FAILED, (payload) => {
      if (payload.agent_id === agent.agent_id) {
        isExecuting = false;
        executionError = payload.error;

        // 更新重試計數
        const failureCount = executionRetryManager.getRetryCount(agent.agent_id) + 1;
        retryCount = failureCount;

        // 檢查是否可以重試
        if (executionRetryManager.canRetry(agent.agent_id)) {
          executionRetryManager.recordRetry(agent.agent_id, payload.error);
          showRetryButton = true;
        } else {
          // 已達最大重試次數
          showRetryButton = false;
          executionError = `執行失敗 (已重試 ${failureCount} 次): ${payload.error}`;
        }
      }
    });

    unsubscribeExecStopped = addEventListener(WS_EVENT_TYPES.EXECUTION_STOPPED, (payload) => {
      if (payload.agent_id === agent.agent_id) {
        isExecuting = false;
      }
    });

    // 初始化圖表
    if (chartCanvas && performanceData.length > 0) {
      renderMiniChart();
    }

    // 返回清理函數
    return () => {
      // 取消訂閱
      unsubscribeExecStarted?.();
      unsubscribeExecCompleted?.();
      unsubscribeExecFailed?.();
      unsubscribeExecStopped?.();

      // 銷毀圖表
      if (chartInstance) {
        chartInstance.destroy();
      }
    };
  });

  // 監聽數據變化，重新渲染圖表
  $effect(() => {
    if (chartCanvas) {
      renderMiniChart();
    }
  });

  function renderMiniChart() {
    // @ts-ignore - Chart.js is loaded via CDN in index.html
    if (!window.Chart || !chartCanvas) return;

    const ctx = chartCanvas.getContext('2d');

    // 如果沒有性能數據，生成示例數據以顯示當前資產
    // 後端提供歷史數據時，performanceData 會包含 total_value 數組
    let chartData = performanceData;
    if (!chartData || chartData.length === 0) {
      // 生成 10 個示例數據點，逐漸接近當前資產
      const current = totalAssets;
      const initial = agent.initial_funds;
      chartData = Array.from({ length: 10 }, (_, i) => ({
        total_value: initial + (current - initial) * (i / 9),
        date: new Date(Date.now() - (10 - i) * 24 * 60 * 60 * 1000).toLocaleDateString(),
      }));
    }

    // 準備數據 - 優先使用 total_value（來自後端），否則使用 value（舊格式）
    const labels = chartData.map((d) => {
      // 如果有日期，提取月日；否則使用索引
      if (d.date) {
        try {
          const date = new Date(d.date);
          return `${date.getMonth() + 1}/${date.getDate()}`;
        } catch {
          return d.date;
        }
      }
      return '';
    });

    const values = chartData.map((d) => d.total_value ?? totalAssets);

    if (chartInstance) {
      chartInstance.destroy();
    }

    // 設置 canvas 的正確尺寸以適應容器
    // 獲取容器寬度
    const container = chartCanvas.parentElement;
    if (container) {
      const rect = container.getBoundingClientRect();
      const containerWidth = rect.width;

      // 設置 canvas 的顯示尺寸（CSS）
      chartCanvas.style.width = '100%';
      chartCanvas.style.height = '100%';

      // 設置 canvas 的內部尺寸（像素）
      // 使用 2:1 寬高比（基於 aspectRatio: 2.5，實際應用時會變成約 2:1）
      chartCanvas.width = containerWidth * (window.devicePixelRatio || 1);
      chartCanvas.height = 128 * (window.devicePixelRatio || 1);
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
        responsive: false,
        maintainAspectRatio: false,
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

  function handleTrade(e) {
    e.stopPropagation();
    showRetryButton = false;
    executionResult = null;
    ontrade?.(agent, 'TRADING');
  }

  function handleRebalance(e) {
    e.stopPropagation();
    showRetryButton = false;
    executionResult = null;
    onrebalance?.(agent, 'REBALANCING');
  }

  function handleRetry(e) {
    e.stopPropagation();
    // 根據最後失敗的模式重試（暫時使用 TRADING 作為預設）
    // 實際實現需要記住上一次的模式
    const lastMode = agent.current_mode || 'TRADING';
    showRetryButton = false;
    executionError = null;
    ontrade?.(agent, lastMode);
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
  <div class="mb-6 h-32 w-full">
    <canvas bind:this={chartCanvas}></canvas>
  </div>

  <!-- 持有股數簡介 -->
  <div class="mb-6">
    <p class="text-xs text-gray-400 mb-3 font-semibold">持有股數</p>
    {#if holdings && holdings.length > 0}
      <div class="space-y-2 max-h-32 overflow-y-auto custom-scrollbar">
        {#each holdings.slice(0, 3) as holding}
          <div class="flex justify-between items-center text-sm bg-gray-700/50 p-2 rounded-md">
            <div>
              <div class="font-bold text-white">{holding.ticker}</div>
              <div class="text-xs text-gray-400">{holding.company_name || holding.name || ''}</div>
            </div>
            <div class="text-right">
              <div class="font-mono text-white">{holding.quantity || 0} 股</div>
              <div class="text-xs text-gray-400">@ {formatCurrency(holding.average_cost || 0)}</div>
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
      <div class="grid grid-cols-2 gap-3">
        <!-- 交易按鈕 -->
        <button
          onclick={handleTrade}
          disabled={!$isOpen || isExecuting}
          class="mode-button group"
          style="--btn-base-color: rgb({agentColor}); --btn-light-color: rgba({agentColor}, 0.8);"
          title="交易模式：執行交易決策"
        >
          <div class="button-wrapper">
            <svg
              class="h-5 w-5 transition-transform duration-300 group-hover:scale-110"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <span class="hidden sm:inline text-sm font-semibold">交易</span>
          </div>
        </button>

        <!-- 平衡按鈕 -->
        <button
          onclick={handleRebalance}
          disabled={!$isOpen || isExecuting}
          class="mode-button group"
          style="--btn-base-color: rgb({agentColor}); --btn-light-color: rgba({agentColor}, 0.8);"
          title="再平衡模式：調整投資組合"
        >
          <div class="button-wrapper">
            <svg
              class="h-5 w-5 transition-transform duration-300 group-hover:scale-110"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <span class="hidden sm:inline text-sm font-semibold">平衡</span>
          </div>
        </button>
      </div>
    {/if}

    <!-- 停止按鈕（總是顯示當 Agent 運行中） -->
    {#if canStop}
      <Button
        variant="danger"
        size="md"
        fullWidth
        onclick={handleStop}
        disabled={!$isOpen || isExecuting}
        loading={isExecuting}
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

    <!-- 執行狀態提示 -->
    {#if isExecuting}
      <div class="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
        <div class="flex items-center gap-2">
          <div
            class="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"
          ></div>
          <span>執行中...</span>
        </div>
      </div>
    {/if}

    {#if executionError}
      <div class="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
        <div class="font-semibold">
          執行失敗{retryCount > 0
            ? ` (重試 ${retryCount}/${executionRetryManager.maxRetries})`
            : ''}
        </div>
        <div class="text-xs mt-1">{executionError}</div>
        {#if showRetryButton}
          <button
            type="button"
            onclick={handleRetry}
            class="mt-2 px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition-colors"
          >
            重試
          </button>
        {/if}
      </div>
    {/if}

    {#if executionResult && executionResult.success}
      <div class="mt-2 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-800">
        <div class="font-semibold">✓ 執行完成</div>
        <div class="text-xs mt-1">
          {executionResult.mode} 模式 (耗時 {executionResult.time_ms}ms)
        </div>
      </div>
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

  /* 模式按鈕美化樣式 - 使用動態agentColor */
  .mode-button {
    position: relative;
    padding: 0.75rem 1rem;
    border-radius: 0.75rem;
    font-weight: 600;
    color: white;
    border: none;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    /* 使用動態顏色變數，base色到深色的漸層 */
    background: linear-gradient(135deg, var(--btn-light-color) 0%, var(--btn-base-color) 100%);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    overflow: hidden;
    font-size: 0.875rem;
  }

  .mode-button:not(:disabled) {
    transform-origin: center;
  }

  .mode-button:not(:disabled):hover {
    transform: scale(1.05);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
  }

  .mode-button:not(:disabled):active {
    transform: scale(0.95);
    animation: buttonPulse 0.4s ease-out;
  }

  .mode-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .mode-button:focus {
    outline: none;
    /* 使用 --btn-base-color 進行focus ring */
    box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.2);
  }

  /* 光澤效果 - hover時增加 */
  .mode-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s ease;
    z-index: 1;
  }

  .mode-button:not(:disabled):hover::before {
    left: 100%;
  }

  /* 按鈕內容包裝 */
  .button-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.375rem;
    position: relative;
    z-index: 10;
  }

  .button-wrapper svg {
    transition: transform 0.3s ease;
  }

  .mode-button:not(:disabled):hover .button-wrapper svg {
    transform: scale(1.1) rotate(5deg);
  }

  .mode-button:not(:disabled):active .button-wrapper svg {
    transform: scale(0.95);
  }

  /* 執行中的脈衝動畫 */
  @keyframes buttonPulse {
    0% {
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    50% {
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6);
    }
    100% {
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
  }
</style>
