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
  import { WS_EVENT_TYPES } from '../../shared/constants.js';
  import {
    formatCurrency,
    formatNumber,
    formatDateTime,
    extractErrorMessage,
  } from '../../shared/utils.js';
  import { isOpen } from '../../stores/market.js';
  import { addEventListener } from '../../stores/websocket.js';
  import { apiClient } from '../../shared/api.js';
  import ExecutionResultModal from './ExecutionResultModal.svelte';

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
  let isEditable = $derived(agent.status !== 'running');

  // 是否可以啟動 (status 為 idle, stopped, 或 inactive)
  let canStart = $derived(
    agent.status === 'idle' ||
      agent.status === 'stopped' ||
      agent.status === 'inactive' ||
      !agent.status
  );

  // 是否可以停止
  let canStop = $derived(agent.status === 'running');

  const statusLabelMap = {
    running: '運行中',
    idle: '待命',
    stopped: '已停止',
    inactive: '未啟動',
  };

  let statusLabel = $derived(statusLabelMap[agent.status] ?? '未知狀態');
  let statusBadgeClass = $derived(
    agent.status === 'running' ? 'status-badge-running' : 'status-badge-stopped'
  );
  let pnlPercent = $derived.by(() => {
    if (!agent.initial_funds) {
      return 0;
    }
    return (pnl / agent.initial_funds) * 100;
  });

  // 本地狀態 - 執行加載和錯誤
  let isExecuting = $state(false); // 標記 Agent 是否正在執行交易
  let executionError = $state(null); // 儲存執行錯誤訊息
  let executionResult = $state(null); // 儲存執行結果摘要（包含 success, time_ms, mode, sessionId 等）
  let executionDetail = $state(null); // 儲存執行詳細資訊（從 API 載入的完整 session 資料）
  let executionDetailError = $state(null); // 儲存載入執行詳情時的錯誤
  let isExecutionDetailLoading = $state(false); // 標記是否正在載入執行詳情
  let showExecutionModal = $state(false); // 控制執行結果 Modal 的顯示狀態
  let latestSessionId = $state(null); // 儲存最新的 session ID（用於重新開啟時載入歷史紀錄）

  // Canvas for mini chart
  let chartCanvas;
  let chartInstance;
  let detailRequestId = 0;

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
        clearExecutionDetailState();
        showExecutionModal = false;
      }
    });

    // 監聽執行完成事件：當 Agent 成功完成交易執行時觸發
    unsubscribeExecCompleted = addEventListener(
      WS_EVENT_TYPES.EXECUTION_COMPLETED,
      async (payload) => {
        // 只處理本 Agent 的事件（過濾其他 Agent 的廣播訊息）
        if (payload.agent_id === agent.agent_id) {
          // 重置執行狀態，清除舊的詳細資料
          isExecuting = false;
          clearExecutionDetailState();
          showExecutionModal = false;

          // 構建執行結果摘要物件，供 UI 顯示使用
          executionResult = {
            success: true,
            time_ms: payload.execution_time_ms,
            mode: payload.mode,
            sessionId: payload.session_id,
            output: payload.output,
            completedAt: payload.completed_at ?? new Date().toISOString(),
          };

          // 更新最新 session ID，標記有歷史紀錄可查看
          // 這讓用戶在刷新頁面後仍能查看最近的執行結果
          latestSessionId = payload.session_id;

          // 自動載入執行詳細資訊（包含交易明細、工具使用等）
          if (payload.session_id) {
            await loadExecutionDetail(payload.session_id);
          }
        }
      }
    );

    // 監聽執行失敗事件：當 Agent 執行過程中發生錯誤時觸發
    unsubscribeExecFailed = addEventListener(WS_EVENT_TYPES.EXECUTION_FAILED, async (payload) => {
      // 只處理本 Agent 的事件
      if (payload.agent_id === agent.agent_id) {
        // 標記執行結束，儲存錯誤訊息
        isExecuting = false;
        executionError = payload.error;
        clearExecutionDetailState();
        showExecutionModal = false;

        // 即使失敗也嘗試載入最新 session 資料
        // 失敗的 session 可能包含部分執行資訊，對除錯有幫助
        if (payload.session_id) {
          latestSessionId = payload.session_id;
          await loadExecutionDetail(payload.session_id);
        }
      }
    });

    unsubscribeExecStopped = addEventListener(WS_EVENT_TYPES.EXECUTION_STOPPED, (payload) => {
      if (payload.agent_id === agent.agent_id) {
        isExecuting = false;
        clearExecutionDetailState();
        showExecutionModal = false;
      }
    });

    // 載入最新的 session 紀錄（非同步執行，不阻塞 onMount）
    // 這讓組件掛載時自動顯示上次執行結果，即使頁面刷新也能查看歷史紀錄
    loadLatestSession();

    // 初始化圖表：如果有性能資料則渲染迷你圖表
    if (chartCanvas && Array.isArray(performanceData) && performanceData.length > 0) {
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

    // 確保 performanceData 是陣列
    const data = Array.isArray(performanceData) ? performanceData : [];

    // 如果沒有性能數據，停止繪製
    if (data.length === 0) {
      return;
    }

    // 銷毀舊圖表實例
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }

    const ctx = chartCanvas.getContext('2d');
    const initial = agent.initial_funds;

    // 提取資產價值（使用 portfolio_value）
    const values = data.map((d) => d.portfolio_value ?? 0);

    // 創建梯度漸層 - 對齊 createCardChart 風格
    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, `rgba(${agentColor}, 0.5)`);
    gradient.addColorStop(1, `rgba(${agentColor}, 0)`);

    // @ts-ignore - Chart.js is loaded via CDN in index.html
    chartInstance = new window.Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map((_, idx) => idx.toString()),
        datasets: [
          {
            label: '資產價值',
            data: values,
            borderColor: `rgb(${agentColor})`,
            backgroundColor: gradient,
            borderWidth: 2,
            pointRadius: 3,
            pointBackgroundColor: `rgb(${agentColor})`,
            pointBorderColor: '#fff',
            pointBorderWidth: 1,
            pointHoverRadius: 6,
            pointHoverBackgroundColor: `rgb(${agentColor})`,
            tension: 0.4,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: true,
            mode: 'index',
            intersect: false,
            callbacks: {
              title: (tooltipItems) => {
                const idx = tooltipItems[0].dataIndex;
                const d = data[idx];
                if (d?.date) {
                  try {
                    const date = new Date(d.date);
                    return `📅 ${date.getMonth() + 1}/${date.getDate()}`;
                  } catch {
                    return `資料點 ${idx}`;
                  }
                }
                return `資料點 ${idx}`;
              },
              label: (context) => {
                const totalAssetValue = context.parsed.y;
                const pnl = totalAssetValue - initial;
                const sign = pnl >= 0 ? '+' : '';
                const pnlPercent = ((pnl / initial) * 100).toFixed(2);
                return `${formatCurrency(totalAssetValue)} (${sign}${pnlPercent}%)`;
              },
            },
          },
        },
        scales: {
          x: { display: false },
          y: { display: false },
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
    executionResult = null;
    clearExecutionDetailState();
    showExecutionModal = false;
    ontrade?.(agent, 'TRADING');
  }

  function handleRebalance(e) {
    e.stopPropagation();
    executionResult = null;
    clearExecutionDetailState();
    showExecutionModal = false;
    onrebalance?.(agent, 'REBALANCING');
  }

  function handleStop(e) {
    e.stopPropagation();
    showExecutionModal = false;
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

  /**
   * 載入最新的 session 紀錄
   *
   * 功能說明：
   * - 在組件掛載時自動呼叫，檢查是否有最近的執行紀錄
   * - 只載入已完成（completed）或失敗（failed）的 session
   * - 自動載入詳細資訊並構建執行結果摘要供 UI 顯示
   *
   * 使用時機：
   * - 組件初始化時（onMount）
   * - 確保用戶刷新頁面後仍能查看最近的執行結果
   *
   * @async
   * @returns {Promise<void>}
   */
  async function loadLatestSession() {
    try {
      // 從後端獲取最新的 1 筆執行歷史紀錄
      const history = await apiClient.getExecutionHistory(agent.agent_id, 1);

      if (history && history.length > 0) {
        const latest = history[0];

        // 只使用已完成或失敗的 session（過濾掉正在執行中或其他中間狀態）
        if (latest.status === 'completed' || latest.status === 'failed') {
          // 儲存最新 session ID，用於後續查看詳情
          latestSessionId = latest.id;

          // 自動載入完整的執行詳細資訊（包含交易明細、工具使用等）
          await loadExecutionDetail(latest.id);

          // 構建 executionResult 摘要物件，用於在卡片上顯示執行結果預覽
          executionResult = {
            success: latest.status === 'completed', // 判斷執行是否成功
            time_ms: latest.execution_time_ms, // 執行耗時（毫秒）
            mode: latest.mode, // 執行模式（TRADING 或 REBALANCING）
            sessionId: latest.id, // Session 唯一識別碼
            output: latest.final_output, // 執行輸出（可能是 JSON 或純文字）
            completedAt: latest.completed_at || latest.end_time, // 完成時間戳記
          };
        }
      }
    } catch (error) {
      // 載入失敗時記錄錯誤，但不阻斷組件正常運作
      console.error(`Failed to load latest session for agent ${agent.agent_id}:`, error);
    }
  }

  /**
   * 載入指定 session 的詳細執行資訊
   *
   * 功能說明：
   * - 從後端 API 獲取完整的 session 詳細資料
   * - 包含交易明細、工具使用、再平衡計劃等完整資訊
   * - 使用請求 ID 機制防止競態條件（race condition）
   *
   * 競態條件處理：
   * - 每次呼叫都會產生新的 requestId
   * - 只有最新的請求結果會被採用，避免舊請求覆蓋新資料
   *
   * @async
   * @param {string} sessionId - Session 的唯一識別碼
   * @returns {Promise<void>}
   */
  async function loadExecutionDetail(sessionId) {
    // 如果沒有提供 sessionId，直接返回
    if (!sessionId) {
      return;
    }

    // 產生新的請求 ID，用於識別本次請求（防止舊請求覆蓋新資料）
    const requestId = ++detailRequestId;
    isExecutionDetailLoading = true;
    executionDetailError = null;

    try {
      // 從後端 API 獲取 session 的完整詳細資訊
      const detail = await apiClient.getSessionDetails(agent.agent_id, sessionId);

      // 只有當本次請求仍是最新的請求時，才更新資料
      // 這避免了「先發後至」的問題（舊請求比新請求晚回應）
      if (requestId === detailRequestId) {
        executionDetail = detail;
      }
    } catch (error) {
      // 只有當本次請求仍是最新的請求時，才更新錯誤狀態
      if (requestId === detailRequestId) {
        executionDetailError = extractErrorMessage(error);
        console.error(`Failed to load session detail for ${sessionId}:`, error);
      }
    } finally {
      // 只有當本次請求仍是最新的請求時，才標記載入完成
      if (requestId === detailRequestId) {
        isExecutionDetailLoading = false;
      }
    }
  }

  /**
   * 開啟執行結果 Modal 彈窗
   *
   * 功能說明：
   * - 顯示執行結果的詳細 Modal
   * - 優先使用最新的 session ID（支援查看歷史紀錄）
   * - 如果該 session 詳情尚未載入，則自動載入
   *
   * 優先順序：
   * 1. latestSessionId - 最新的歷史紀錄（即使頁面刷新也能保留）
   * 2. executionResult.sessionId - 當前執行的 session
   *
   * @param {Event} event - DOM 事件物件
   */
  function openExecutionModal(event) {
    // 阻止事件冒泡，避免觸發父元素的 click 事件
    event?.stopPropagation?.();

    // 顯示 Modal
    showExecutionModal = true;

    // 優先使用最新的 session ID（確保用戶總是看到最新的執行結果）
    const sessionId = latestSessionId || executionResult?.sessionId;

    // 如果有 sessionId 且該 session 的詳情尚未載入或不是當前 session，則載入詳情
    // 避免重複載入相同的資料
    if (sessionId && executionDetail?.id !== sessionId && !isExecutionDetailLoading) {
      loadExecutionDetail(sessionId);
    }
  }

  // 關閉執行結果 Modal 彈窗
  function closeExecutionModal() {
    showExecutionModal = false;
  }

  // 處理全域鍵盤事件（ESC 鍵關閉 Modal）
  function handleWindowKeydown(event) {
    if (event.key === 'Escape' && showExecutionModal) {
      closeExecutionModal();
    }
  }

  // 清除執行詳情狀態
  function clearExecutionDetailState() {
    executionDetail = null;
    executionDetailError = null;
    isExecutionDetailLoading = false;
  }
</script>

<svelte:window on:keydown={handleWindowKeydown} />

<div
  class="agent-card rounded-3xl border border-gray-800 bg-gray-900/80 p-6 shadow-2xl transition-all duration-300 cursor-pointer hover:-translate-y-1 hover:shadow-[0_40px_55px_rgba(0,0,0,0.55)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-900"
  class:selected
  style={`border-color: rgba(${agentColor}, 0.35); --agent-color-rgb: ${agentColor};`}
  onclick={handleClick}
  onkeydown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabindex="0"
>
  <div
    class="agent-card-header mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"
  >
    <div class="flex-1 min-w-0">
      <div class="flex flex-wrap items-center gap-3">
        <h3 class="text-2xl font-semibold leading-tight" style="color: rgb({agentColor});">
          {agent.name}
        </h3>
        <span class={`status-badge ${statusBadgeClass}`}>
          {statusLabel}
        </span>
      </div>
      <p class="agent-model text-base text-gray-300 mt-1">
        {agent.ai_model || '未知模型'}
      </p>
      <div class="agent-meta mt-3 flex flex-wrap items-center gap-3 text-sm text-gray-400">
        <div class="flex items-center gap-2">
          <span
            class={`status-dot ${agent.status === 'running' ? 'status-running' : 'status-stopped'}`}
          ></span>
          <span>{statusLabel}</span>
        </div>
        <span class="hidden text-gray-600 sm:inline">•</span>
        <span>模式 {agent.current_mode || '—'}</span>
      </div>
    </div>
    <div class="flex items-center gap-1 self-start opacity-80 transition-opacity hover:opacity-100">
      {#if onedit}
        <button
          type="button"
          onclick={handleEdit}
          class="icon-button"
          title="編輯 Agent"
          aria-label={`編輯 ${agent.name}`}
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
          type="button"
          onclick={handleDelete}
          class="icon-button"
          title="刪除 Agent"
          aria-label={`刪除 ${agent.name}`}
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

  <div class="metric-grid mb-6">
    <div class="metric-card">
      <p class="metric-caption">總資產</p>
      <p class="metric-value" style="color: rgb({agentColor});">
        {formatCurrency(totalAssets)}
      </p>
      <p class="metric-caption">初始資金 {formatCurrency(agent.initial_funds)}</p>
    </div>
    <div class="metric-card">
      <p class="metric-caption">總損益</p>
      <p class={`metric-value ${isProfit ? 'text-gain' : 'text-loss'}`}>
        {isProfit ? '+' : ''}{formatCurrency(pnl)}
      </p>
      <p class="metric-caption">{pnlPercent.toFixed(2)}%</p>
    </div>
  </div>

  <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
    <div class="info-card">
      <p class="text-xs text-gray-400 mb-1">持有現金</p>
      <p class="text-lg font-semibold" style="color: rgb({agentColor});">
        {formatCurrency(currentCash)}
      </p>
    </div>
    <div class="info-card">
      <p class="text-xs text-gray-400 mb-1">股票現值</p>
      <p class="text-lg font-semibold" style="color: rgb({agentColor});">
        {formatCurrency(holdingsTotalValue)}
      </p>
    </div>
  </div>

  <div class="chart-shell mb-6 h-48 w-full">
    <canvas bind:this={chartCanvas}></canvas>
  </div>

  <div class="mb-6">
    <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
      <p class="section-title">持有股數</p>
      <p class="section-subtitle">{holdings?.length ?? 0} 檔</p>
    </div>
    {#if holdings && holdings.length > 0}
      <div class="holdings-list space-y-2 max-h-32 overflow-y-auto custom-scrollbar">
        {#each holdings.slice(0, 10) as holding}
          <div class="holding-row">
            <div>
              <p class="holding-ticker">{holding.ticker}</p>
              <p class="holding-name">{holding.company_name || holding.name || '—'}</p>
            </div>
            <div class="text-right">
              <p class="holding-shares">{formatNumber(holding.shares || 0)} 股</p>
              <p class="holding-price">均價 {formatCurrency(holding.avg_price || 0)}</p>
            </div>
          </div>
        {/each}
        {#if holdings.length > 10}
          <p class="section-subtitle text-center">
            還有 {holdings.length - 10} 檔股票...
          </p>
        {/if}
      </div>
    {:else}
      <p class="empty-state">尚無持股</p>
    {/if}
  </div>

  <div class="flex flex-col gap-3" data-role="actions">
    {#if canStart}
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <button
          onclick={handleTrade}
          disabled={!$isOpen || isExecuting}
          class="mode-button group"
          style="--btn-base-color: rgb({agentColor}); --btn-light-color: rgba({agentColor}, 0.75);"
          title="交易模式：執行交易決策"
          aria-label="啟動交易模式"
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
            <span class="text-sm font-semibold">交易</span>
          </div>
        </button>

        <button
          onclick={handleRebalance}
          disabled={!$isOpen || isExecuting}
          class="mode-button group"
          style="--btn-base-color: rgb({agentColor}); --btn-light-color: rgba({agentColor}, 0.75);"
          title="再平衡模式：調整投資組合"
          aria-label="啟動再平衡模式"
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
            <span class="text-sm font-semibold">再平衡</span>
          </div>
        </button>
      </div>
    {/if}

    {#if canStop}
      <button
        onclick={handleStop}
        disabled={!$isOpen || isExecuting}
        class="stop-button group"
        style="--btn-base-color: rgba(239, 68, 68, 0.9); --btn-light-color: rgba(248, 113, 113, 0.9);"
        title="停止執行"
        aria-label="停止 Agent"
      >
        <div class="button-wrapper">
          {#if isExecuting}
            <svg
              class="animate-spin h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          {:else}
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
                d="M21 12a9 9 0 11-18 0 9 0 0118 0z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
              />
            </svg>
          {/if}
          <span class="text-sm font-semibold">停止</span>
        </div>
      </button>
    {/if}

    {#if isExecuting}
      <div class="alert-card alert-info">
        <div class="flex items-center gap-2">
          <div class="spinner"></div>
          <span>執行中...</span>
        </div>
      </div>
    {/if}

    {#if executionError}
      <div class="alert-card alert-error">
        <div class="font-semibold">執行失敗</div>
        <p class="text-xs leading-relaxed">{executionError}</p>
        <button type="button" class="expand-button mt-2" onclick={openExecutionModal}>
          查看詳情
        </button>
      </div>
    {/if}

    {#if executionResult && !executionError}
      <div class="result-summary animation-fade-in mt-3">
        <div class="result-summary-content">
          <div class="result-summary-header">
            <h4 class="font-semibold text-white text-lg">
              {executionResult.success ? '執行完成' : '執行失敗'}
            </h4>
            <span class="result-pill">{executionResult.mode || '—'}</span>
          </div>
          <p class="text-sm text-gray-300 mt-1">
            {formatDateTime(executionResult.completedAt)} (耗時 {executionResult.time_ms != null
              ? (executionResult.time_ms / 1000).toFixed(2) + ' 秒'
              : '--'})
          </p>
        </div>
        <div class="result-actions">
          <button type="button" class="expand-button" onclick={openExecutionModal}>
            查看詳情
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>

<ExecutionResultModal
  isOpen={showExecutionModal}
  {agent}
  {executionResult}
  {executionDetail}
  error={executionDetailError}
  onClose={closeExecutionModal}
  {agentColor}
/>

<style>
  .agent-card {
    position: relative;
    overflow: hidden;
    background:
      linear-gradient(
        160deg,
        rgba(var(--agent-color-rgb, 59, 130, 246), 0.4),
        rgba(15, 23, 42, 0.92)
      ),
      rgba(15, 23, 42, 0.9);
    border-radius: 1.5rem;
    border: 1px solid rgba(148, 163, 184, 0.2);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45);
  }

  .agent-card::before {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    background: radial-gradient(
      circle at top right,
      rgba(var(--agent-color-rgb, 59, 130, 246), 0.45),
      transparent 55%
    );
  }

  .agent-card.selected {
    box-shadow:
      0 0 0 2px rgba(59, 130, 246, 0.55),
      0 40px 55px rgba(0, 0, 0, 0.55);
  }

  .agent-card-header {
    position: relative;
    z-index: 1;
  }

  .text-gain {
    color: #4ade80;
  }

  .text-loss {
    color: #f87171;
  }

  .status-dot {
    width: 10px;
    height: 10px;
    border-radius: 9999px;
    display: inline-block;
  }

  .status-running {
    background-color: #22c55e;
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.8);
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

  .metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
  }

  .metric-card {
    position: relative;
    background: rgba(15, 23, 42, 0.85);
    border-radius: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.25);
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    min-height: 120px;
    z-index: 1;
  }

  .metric-card::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    pointer-events: none;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  }

  .metric-value {
    font-size: 1.9rem;
    font-weight: 700;
    line-height: 1.2;
  }

  .metric-caption {
    font-size: 0.8rem;
    color: #94a3b8;
    letter-spacing: 0.02em;
    text-transform: uppercase;
  }

  .info-card {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 1rem;
    padding: 1rem;
    min-height: 110px;
  }

  .chart-shell {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 1rem;
    padding: 1rem;
  }

  .section-title {
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #e5e7eb;
  }

  .section-subtitle {
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .empty-state {
    text-align: center;
    padding: 1rem;
    border-radius: 0.85rem;
    border: 1px dashed rgba(148, 163, 184, 0.4);
    color: #6b7280;
    background: rgba(15, 23, 42, 0.5);
  }

  .holding-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.65rem 0.75rem;
    border-radius: 0.75rem;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(75, 85, 99, 0.35);
  }

  .holding-ticker {
    font-weight: 600;
    color: #e5e7eb;
  }

  .holding-name {
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .holding-shares {
    font-family: 'JetBrains Mono', 'SFMono-Regular', ui-monospace, monospace;
    color: #f8fafc;
  }

  .holding-price {
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .icon-button {
    border: none;
    background: transparent;
    border-radius: 0.5rem;
    padding: 0.4rem;
    color: #9ca3af;
    transition: all 0.2s ease;
  }

  .icon-button:hover:not(:disabled) {
    background-color: rgba(107, 114, 128, 0.3);
    color: #fff;
  }

  .icon-button:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }

  .custom-scrollbar::-webkit-scrollbar-track {
    background: #1f2937;
  }

  .custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: #4b5563;
    border-radius: 9999px;
  }

  .mode-button {
    position: relative;
    padding: 0.75rem 1rem;
    border-radius: 0.85rem;
    font-weight: 600;
    color: #fff;
    border: none;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    background: linear-gradient(135deg, var(--btn-light-color), var(--btn-base-color));
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.35);
    overflow: hidden;
    font-size: 0.9rem;
  }

  .mode-button:not(:disabled):hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 35px rgba(0, 0, 0, 0.5);
  }

  .mode-button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .mode-button::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(110deg, transparent, rgba(255, 255, 255, 0.25), transparent);
    transform: translateX(-100%);
    transition: transform 0.6s ease;
  }

  .mode-button:not(:disabled):hover::before {
    transform: translateX(100%);
  }

  .button-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    z-index: 1;
  }

  .button-wrapper svg {
    transition: transform 0.3s ease;
  }

  .mode-button:not(:disabled):hover .button-wrapper svg {
    transform: scale(1.1);
  }

  .stop-button {
    position: relative;
    width: 100%;
    padding: 0.85rem 1rem;
    border-radius: 0.85rem;
    font-weight: 600;
    color: #fff;
    border: none;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    background: linear-gradient(135deg, var(--btn-base-color), rgba(185, 28, 28, 0.85));
    box-shadow: 0 12px 24px rgba(239, 68, 68, 0.35);
    overflow: hidden;
  }

  .stop-button:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .stop-button::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(110deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transform: translateX(-100%);
    transition: transform 0.6s ease;
  }

  .stop-button:not(:disabled):hover::before {
    transform: translateX(100%);
  }

  .alert-card {
    padding: 0.75rem 1rem;
    border-radius: 0.75rem;
    border: 1px solid transparent;
    font-size: 0.85rem;
  }

  .alert-info {
    background: rgba(59, 130, 246, 0.12);
    border-color: rgba(59, 130, 246, 0.4);
    color: #bfdbfe;
  }

  .alert-error {
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.4);
    color: #fecaca;
  }

  .spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid rgba(147, 197, 253, 0.4);
    border-top-color: #60a5fa;
    border-radius: 9999px;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .result-summary {
    background: linear-gradient(
      135deg,
      rgba(var(--agent-color-rgb, 34, 197, 94), 0.1),
      rgba(var(--agent-color-rgb, 34, 197, 94), 0.05)
    );
    border-left: 4px solid rgb(var(--agent-color-rgb, 34, 197, 94));
    border-radius: 0.85rem;
    padding: 1rem;
    transition: all 0.3s ease;
    display: flex;
    gap: 1rem;
    align-items: stretch;
  }

  .result-summary.failed {
    border-left-color: #ef4444;
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05));
  }

  .result-summary.partial {
    border-left-color: #eab308;
    background: linear-gradient(135deg, rgba(234, 179, 8, 0.1), rgba(234, 179, 8, 0.05));
  }

  .result-summary-content {
    flex: 1;
  }

  .result-summary-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .result-pill {
    padding: 0.1rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(59, 130, 246, 0.15);
    color: #bfdbfe;
  }

  .result-summary-text {
    color: #d1d5db;
    font-size: 0.9rem;
    line-height: 1.5;
    display: -webkit-box;
    line-clamp: 3;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .result-actions {
    width: 160px;
    display: flex;
    align-items: flex-end;
  }

  .result-actions .expand-button {
    margin-top: 0;
  }

  .trade-item,
  .rebalance-item {
    background: rgba(30, 41, 59, 0.9);
    border: 1px solid rgba(75, 85, 99, 0.35);
    border-radius: 0.75rem;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .trade-item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .trade-item-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .trade-status-badge {
    font-size: 0.7rem;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    background: rgba(59, 130, 246, 0.2);
    color: #bfdbfe;
    font-weight: 600;
  }

  .trade-item-body {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.35rem;
    font-size: 0.85rem;
    color: #e5e7eb;
  }

  .trade-action-buy {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .trade-action-sell {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .value-positive {
    color: #4ade80;
  }

  .value-negative {
    color: #f87171;
  }

  .progress-bar {
    background: rgba(75, 85, 99, 0.3);
    border-radius: 0.25rem;
    height: 0.5rem;
    overflow: hidden;
    margin: 0.5rem 0;
  }

  .progress-fill {
    background: linear-gradient(90deg, #22c55e, #16a34a);
    height: 100%;
    transition: width 0.5s ease;
  }

  .stat-card {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(75, 85, 99, 0.2);
    border-radius: 0.5rem;
    padding: 1rem;
    text-align: center;
  }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
  }

  .animation-fade-in {
    animation: fadeIn 0.5s ease;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .animation-slide-in {
    animation: slideIn 0.3s ease;
  }

  @keyframes slideIn {
    from {
      max-height: 0;
      opacity: 0;
    }
    to {
      max-height: 1000px;
      opacity: 1;
    }
  }

  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .status-badge-success {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
  }

  .status-badge-failed {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
  }

  .status-badge-partial {
    background: rgba(234, 179, 8, 0.2);
    color: #facc15;
  }

  .status-badge-running {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
  }

  .status-badge-stopped {
    background: rgba(156, 163, 175, 0.15);
    color: #d1d5db;
  }

  .result-detail-container {
    background: rgba(17, 24, 39, 0.85);
    border: 1px solid rgba(75, 85, 99, 0.4);
    border-radius: 0.85rem;
    padding: 1rem;
    margin-top: 1rem;
    backdrop-filter: blur(12px);
  }

  .expand-button {
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: rgba(75, 85, 99, 0.3);
    border: 1px solid rgba(75, 85, 99, 0.4);
    border-radius: 0.65rem;
    color: #d1d5db;
    font-weight: 600;
    margin-top: 0.75rem;
    transition: all 0.2s ease;
  }

  .expand-button:hover {
    background: rgba(75, 85, 99, 0.5);
  }

  .expand-button:active {
    transform: scale(0.98);
  }

  .detail-json {
    background: rgba(15, 23, 42, 0.9);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 0.5rem;
    padding: 0.75rem;
    font-size: 0.8rem;
    overflow-x: auto;
    color: #e5e7eb;
  }

  .detail-section {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(75, 85, 99, 0.35);
    border-radius: 0.85rem;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .detail-section-title {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    margin: 0;
  }

  .detail-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .tool-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tool-chip {
    padding: 0.35rem 0.75rem;
    border-radius: 9999px;
    background: rgba(59, 130, 246, 0.2);
    color: #bfdbfe;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    z-index: 50;
  }

  .modal-panel {
    width: min(900px, 100%);
    max-height: 90vh;
    border-radius: 1.25rem;
    border: 1px solid rgba(148, 163, 184, 0.3);
    background: rgba(15, 23, 42, 0.95);
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5);
    display: flex;
    flex-direction: column;
  }

  .modal-header {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid rgba(75, 85, 99, 0.5);
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
  }

  .modal-title-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .modal-title {
    font-weight: 600;
    color: #fff;
    margin: 0;
  }

  .modal-subtitle {
    margin-top: 0.35rem;
    color: #94a3b8;
    font-size: 0.85rem;
  }

  .modal-body {
    padding: 1.5rem;
    overflow-y: auto;
    gap: 1rem;
    display: flex;
    flex-direction: column;
  }

  .modal-close-button {
    color: #9ca3af;
  }

  .modal-close-button:hover {
    color: #fff;
  }

  .modal-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 2rem 0;
    color: #d1d5db;
  }
</style>
