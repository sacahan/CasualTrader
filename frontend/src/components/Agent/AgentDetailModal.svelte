<script>
  /**
   * AgentDetailModal Component
   *
   * Agent 詳細資訊 Modal
   * 顯示完整的 Agent 資訊、績效圖表、持倉詳情、交易歷史
   * 新增選項卡切換功能，可切換概覽和儀表板視圖
   */

  import { Modal } from '../UI/index.js';
  import { PerformanceChart, RiskMetricsCard } from '../Chart/index.js';
  import { PerformanceDashboard } from '../Performance/index.js';
  import { formatCurrency, formatDateTime, formatNumber } from '../../shared/utils.js';

  // Props
  let {
    agent,
    open = $bindable(false),
    performanceData = [],
    holdings = [],
    transactions = [],
    onclose = undefined,
  } = $props();

  // 選項卡狀態
  let selectedTab = $state('overview');

  // Agent 顏色（從設定中取得，預設為綠色）
  let agentColor = $derived(agent?.color_theme || '34, 197, 94');

  // 計算持股總市值（市場價值估計 = 後端提供的 market_value）
  // 注意：當前後端尚未集成實時行情，market_value = total_cost
  // 實時行情集成後會自動更新計算
  let holdingsTotalValue = $derived.by(() => {
    if (!holdings || holdings.length === 0) return 0;
    return holdings.reduce((sum, holding) => {
      const value = holding.market_value ?? holding.total_cost ?? 0;
      return sum + value;
    }, 0);
  });

  // 計算總資產 = 現金 + 持股市值（真實投資組合淨值）
  let totalAssets = $derived.by(() => {
    const currentFunds = agent?.current_funds ?? agent?.initial_funds ?? 0;
    return currentFunds + holdingsTotalValue;
  });

  // 計算當前現金（不含持股）
  let currentCash = $derived(agent?.current_funds ?? agent?.initial_funds ?? 0);

  // 計算損益 = 總資產 - 初始投入
  let pnl = $derived(totalAssets - (agent?.initial_funds ?? 0));

  // 計算損益率
  let pnlPercent = $derived(
    (agent?.initial_funds ?? 0) > 0 ? (pnl / (agent?.initial_funds ?? 0)) * 100 : 0
  );

  let isProfit = $derived(pnl >= 0);

  function handleClose() {
    onclose?.();
  }
</script>

<Modal bind:open size="full" onclose={handleClose}>
  {#snippet header()}
    <div class="flex items-center justify-between w-full">
      <h2 class="text-2xl font-bold" style="color: rgb({agentColor});">
        {agent?.name || 'Unknown'}
      </h2>
      <button
        type="button"
        class="rounded-md text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        onclick={handleClose}
      >
        <span class="sr-only">關閉</span>
        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  {/snippet}

  <!-- 主容器：選項卡導航 + 內容 -->
  <div class="flex h-full flex-col">
    <!-- 選項卡導航 -->
    <div class="flex gap-1 border-b border-gray-700 bg-gray-900 px-6 pb-0 pt-4">
      <button
        onclick={() => (selectedTab = 'overview')}
        class={`px-4 py-2 font-medium transition-colors ${
          selectedTab === 'overview'
            ? 'border-b-2 text-white'
            : 'border-b-2 border-transparent text-gray-400 hover:text-gray-200'
        }`}
        style={selectedTab === 'overview' ? `border-color: rgb(${agentColor})` : ''}
      >
        📊 概覽
      </button>
      <button
        onclick={() => (selectedTab = 'dashboard')}
        class={`px-4 py-2 font-medium transition-colors ${
          selectedTab === 'dashboard'
            ? 'border-b-2 text-white'
            : 'border-b-2 border-transparent text-gray-400 hover:text-gray-200'
        }`}
        style={selectedTab === 'dashboard' ? `border-color: rgb(${agentColor})` : ''}
      >
        📈 儀表板
      </button>
    </div>

    <!-- 內容區域 -->
    <div class="flex-1 overflow-hidden p-6">
      {#if selectedTab === 'overview'}
        <!-- 概覽選項卡：左圖表 + 右面板 -->
        <div class="grid h-full grid-cols-1 gap-6 lg:grid-cols-[1.5fr_1fr]">
          <!-- 左側：績效圖表 -->
          <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
            <h3 class="mb-4 text-lg font-semibold text-gray-400">績效走勢</h3>
            <div class="h-full min-h-[400px]">
              <PerformanceChart {performanceData} {agentColor} height={400} />
            </div>

            <!-- 進階風險指標 -->
            {#if performanceData && performanceData.length > 0}
              <div class="mt-8">
                <RiskMetricsCard
                  metrics={performanceData[performanceData.length - 1]}
                  {agentColor}
                />
              </div>
            {/if}
          </div>

          <!-- 右側：信息面板（可滾動） -->
          <div
            class="custom-scrollbar flex max-h-[calc(100vh-180px)] flex-col gap-6 overflow-y-auto"
          >
            <!-- KPI 指標區 -->
            <div class="space-y-3 rounded-lg border border-gray-700 bg-gray-800 p-6">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-xs text-gray-400">總資產</p>
                  <p class="mt-1 text-lg font-bold text-white" style="color: rgb({agentColor});">
                    {formatCurrency(totalAssets)}
                  </p>
                </div>
                <div>
                  <p class="text-xs text-gray-400">總損益</p>
                  <p
                    class="mt-1 text-lg font-bold"
                    class:text-gain={isProfit}
                    class:text-loss={!isProfit}
                  >
                    {isProfit ? '+' : ''}{formatCurrency(pnl)}
                  </p>
                </div>
                <div>
                  <p class="text-xs text-gray-400">持有現金</p>
                  <p class="mt-1 text-lg font-bold text-white">
                    {formatCurrency(currentCash)}
                  </p>
                </div>
                <div>
                  <p class="text-xs text-gray-400">損益率</p>
                  <p
                    class="mt-1 text-lg font-bold"
                    class:text-gain={isProfit}
                    class:text-loss={!isProfit}
                  >
                    {isProfit ? '+' : ''}{pnlPercent.toFixed(2)}%
                  </p>
                </div>
              </div>
            </div>

            <!-- 持倉詳情 -->
            <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
              <h4 class="mb-3 font-semibold text-gray-400">持有股數</h4>
              {#if holdings && holdings.length > 0}
                <div class="space-y-2">
                  {#each holdings as holding}
                    <div
                      class="flex items-center justify-between rounded-md bg-gray-900 px-3 py-2 text-sm"
                    >
                      <div>
                        <p class="font-medium text-white">{holding.ticker}</p>
                        <p class="text-xs text-gray-400">{holding.name || ''}</p>
                      </div>
                      <div class="text-right">
                        <p class="text-white">{formatNumber(holding.shares || 0)} 股</p>
                        <p class="text-xs text-gray-400">
                          每股均價 {formatCurrency(holding.avg_price || 0)}
                        </p>
                      </div>
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="text-center text-sm text-gray-500">無持股</p>
              {/if}
            </div>

            <!-- 交易歷史 -->
            <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
              <h4 class="mb-3 font-semibold text-gray-400">交易歷史</h4>
              {#if transactions && transactions.length > 0}
                <div class="custom-scrollbar max-h-48 space-y-2 overflow-y-auto">
                  {#each transactions as tx}
                    <div
                      class="flex items-center justify-between rounded-md bg-gray-900 px-3 py-2 text-sm"
                    >
                      <div>
                        <div class={tx.type === 'BUY' ? 'text-green-400' : 'text-red-400'}>
                          {tx.type === 'BUY' ? '買入' : '賣出'}
                          {tx.ticker}
                        </div>
                        <p class="text-xs text-gray-400">{tx.company_name || ''}</p>
                      </div>
                      <div class="text-right">
                        <p class="text-white">
                          {formatNumber(tx.shares || 0)} 股 / {formatCurrency(tx.price)}
                        </p>
                        <p class="text-xs text-gray-400">{formatDateTime(tx.timestamp)}</p>
                      </div>
                    </div>
                  {/each}
                </div>
              {:else}
                <p class="text-center text-sm text-gray-500">無交易記錄</p>
              {/if}
            </div>

            <!-- 基本資訊（可摺疊區塊） -->
            <details class="rounded-lg border border-gray-700 bg-gray-800 p-6">
              <summary class="cursor-pointer font-semibold text-gray-400"> 基本資訊 </summary>
              <div class="mt-4 space-y-3 border-t border-gray-700 pt-4 text-sm">
                <div>
                  <p class="text-gray-400">描述</p>
                  <p class="mt-1 text-white">{agent?.description || ''}</p>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <p class="text-gray-400">AI 模型</p>
                    <p class="font-medium text-white">{agent?.ai_model || 'N/A'}</p>
                  </div>
                  <div>
                    <p class="text-gray-400">單一持股上限</p>
                    <p class="font-medium text-white">{agent?.max_position_size || 0}%</p>
                  </div>
                  <div>
                    <p class="text-gray-400">狀態</p>
                    <p class="font-medium text-white">{agent?.status || 'N/A'}</p>
                  </div>
                  <div>
                    <p class="text-gray-400">創建時間</p>
                    <p class="font-medium text-white">{formatDateTime(agent?.created_at)}</p>
                  </div>
                </div>

                {#if agent?.investment_preferences && (agent?.investment_preferences.length > 0 || agent?.investment_preferences.preferred_sectors || agent?.investment_preferences.excluded_tickers)}
                  <div class="border-t border-gray-700 pt-3">
                    <p class="mb-2 text-gray-400">投資偏好</p>
                    <div class="space-y-1 text-sm">
                      {#if agent?.investment_preferences && agent?.investment_preferences.length > 0}
                        <p class="text-white">
                          <span class="text-gray-400">偏好公司：</span>
                          {agent?.investment_preferences.join(', ')}
                        </p>
                      {/if}
                      {#if agent?.investment_preferences.preferred_sectors && agent?.investment_preferences.preferred_sectors.length > 0}
                        <p class="text-white">
                          <span class="text-gray-400">偏好產業：</span>
                          {agent?.investment_preferences.preferred_sectors.join(', ')}
                        </p>
                      {/if}
                      {#if agent?.investment_preferences.excluded_tickers && agent?.investment_preferences.excluded_tickers.length > 0}
                        <p class="text-white">
                          <span class="text-gray-400">排除股票：</span>
                          {agent?.investment_preferences.excluded_tickers.join(', ')}
                        </p>
                      {/if}
                    </div>
                  </div>
                {/if}
              </div>
            </details>
          </div>
        </div>
      {:else if selectedTab === 'dashboard'}
        <!-- 儀表板選項卡：PerformanceDashboard 組件 -->
        <div class="h-full overflow-auto">
          {#if agent?.agent_id}
            <PerformanceDashboard agentId={agent.agent_id} {agentColor} />
          {:else}
            <div class="flex items-center justify-center h-full">
              <p class="text-gray-400">無法載入儀表板：Agent ID 缺失</p>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </div>

  {#snippet footer()}
    <!-- No footer buttons needed -->
  {/snippet}
</Modal>

<style>
  .text-gain {
    color: #4ade80;
  }
  .text-loss {
    color: #f87171;
  }
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: #1f2937;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: #4b5563;
    border-radius: 10px;
  }
</style>
