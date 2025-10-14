<script>
  /**
   * AgentDetailModal Component
   *
   * Agent 詳細資訊 Modal
   * 顯示完整的 Agent 資訊、績效圖表、持倉詳情、交易歷史
   * 可以編輯 Agent 屬性和刪除 Agent
   */

  import { Button, Modal } from '../UI/index.js';
  import { PerformanceChart } from '../Chart/index.js';
  import { formatCurrency, formatDateTime } from '../../shared/utils.js';

  // Props
  let {
    agent,
    open = $bindable(false),
    performanceData = [],
    holdings = [],
    transactions = [],
    onclose = undefined,
  } = $props();

  // 計算資產相關數據
  let totalAssets = $derived(agent?.initial_funds || 1000000);
  let currentCash = $derived(agent?.initial_funds || 345020.5);
  let pnl = $derived(totalAssets - (agent?.initial_funds || 1000000));
  let pnlPercent = $derived((pnl / (agent?.initial_funds || 1000000)) * 100);
  let isProfit = $derived(pnl >= 0);

  // Agent 顏色
  let agentColor = $derived(agent?.color_theme || '34, 197, 94');

  function handleClose() {
    onclose?.();
  }
</script>

<Modal bind:open size="full" onclose={handleClose}>
  {#snippet header()}
    <div class="flex items-center justify-between w-full">
      <h2 class="text-2xl font-bold" style="color: rgb({agentColor});">
        {agent?.name || 'Agent 詳情'}
      </h2>
      <div class="flex items-center gap-2">
        <!-- 關閉按鈕 -->
        <button
          type="button"
          class="ml-2 rounded-md text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
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
    </div>
  {/snippet}

  <div class="custom-scrollbar max-h-[75vh] space-y-6 overflow-y-auto">
    <!-- 基本資訊與資產概覽 -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- 基本資訊 -->
      <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
        <h3 class="mb-3 text-lg font-semibold text-white" style="color: rgb({agentColor});">
          基本資訊
        </h3>
        <div class="space-y-3 text-sm">
          <div class="border-b border-gray-700 pb-3">
            <p class="text-gray-400">描述</p>
            <p class="mt-1 text-white">{agent.description}</p>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-gray-400">AI 模型</p>
              <p class="font-medium text-white">
                {agent?.ai_model || '未知模型'}
              </p>
            </div>
            <div>
              <p class="text-gray-400">單一持股上限</p>
              <p class="font-medium text-white">
                {agent?.max_position_size || 50}%
              </p>
            </div>
            <div>
              <p class="text-gray-400">狀態</p>
              <p class="font-medium text-white">{agent?.status || 'IDLE'}</p>
            </div>
            <div>
              <p class="text-gray-400">創建時間</p>
              <p class="font-medium text-white">{formatDateTime(agent?.created_at)}</p>
            </div>
          </div>

          <!-- 投資偏好 -->
          {#if agent?.investment_preferences}
            <div class="mt-4 border-t border-gray-700 pt-3">
              <p class="mb-2 text-gray-400">投資偏好</p>
              <div class="space-y-2 text-sm">
                {#if agent.investment_preferences && agent.investment_preferences.length > 0}
                  <div>
                    <span class="text-gray-400">偏好公司：</span>
                    <span class="ml-2 font-medium text-white">
                      {agent.investment_preferences.join(', ')}
                    </span>
                  </div>
                {/if}
                {#if agent.investment_preferences.preferred_sectors && agent.investment_preferences.preferred_sectors.length > 0}
                  <div>
                    <span class="text-gray-400">偏好產業：</span>
                    <span class="ml-2 font-medium text-white">
                      {agent.investment_preferences.preferred_sectors.join(', ')}
                    </span>
                  </div>
                {/if}
                {#if agent.investment_preferences.excluded_tickers && agent.investment_preferences.excluded_tickers.length > 0}
                  <div>
                    <span class="text-gray-400">排除股票：</span>
                    <span class="ml-2 font-medium text-white">
                      {agent.investment_preferences.excluded_tickers.join(', ')}
                    </span>
                  </div>
                {/if}
                <div>
                  <span class="text-gray-400">再平衡頻率：</span>
                  <span class="ml-2 font-medium text-white">
                    {agent.investment_preferences.rebalance_frequency || '每週'}
                  </span>
                </div>
              </div>
            </div>
          {/if}
        </div>
      </div>

      <!-- 資產概覽 -->
      <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
        <h3 class="mb-3 text-lg font-semibold text-white" style="color: rgb({agentColor});">
          資產概覽
        </h3>
        <div class="space-y-4">
          <div>
            <p class="text-sm text-gray-400">總資產</p>
            <p class="text-xl font-bold text-white">{formatCurrency(totalAssets)}</p>
          </div>
          <div>
            <p class="text-sm text-gray-400">現金餘額</p>
            <p class="text-xl font-bold text-white">{formatCurrency(currentCash)}</p>
          </div>
          <div>
            <p class="text-sm text-gray-400">總損益</p>
            <p class="text-xl font-bold" class:text-gain={isProfit} class:text-loss={!isProfit}>
              {isProfit ? '+' : ''}{formatCurrency(pnl)}
              <span class="text-sm">({pnlPercent.toFixed(2)}%)</span>
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 績效圖表 -->
    <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
      <h3 class="mb-3 text-lg font-semibold text-white" style="color: rgb({agentColor});">
        績效走勢
      </h3>
      <PerformanceChart agentId={agent?.agent_id} {performanceData} height={300} />
    </div>

    <!-- 持倉詳情 -->
    <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
      <h3 class="mb-3 text-lg font-semibold text-white" style="color: rgb({agentColor});">
        持倉詳情
      </h3>
      {#if holdings && holdings.length > 0}
        <div class="space-y-2">
          {#each holdings as holding}
            <div
              class="flex items-center justify-between rounded-lg border border-gray-700 bg-gray-900 p-3"
            >
              <div>
                <p class="font-medium text-white">{holding.symbol}</p>
                <p class="text-sm text-gray-400">{holding.name || ''}</p>
              </div>
              <div class="text-right">
                <p class="font-medium text-white">{holding.shares || 0} 股</p>
                <p class="text-sm text-gray-400">
                  成本 @ {formatCurrency(holding.avg_price || 0)}
                </p>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <p class="py-8 text-center text-gray-500">尚無持股</p>
      {/if}
    </div>

    <!-- 交易歷史 -->
    <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
      <h3 class="mb-3 text-lg font-semibold text-white" style="color: rgb({agentColor});">
        交易歷史
      </h3>
      {#if transactions && transactions.length > 0}
        <div class="custom-scrollbar max-h-64 space-y-2 overflow-y-auto">
          {#each transactions as tx}
            <div
              class="flex items-center justify-between rounded-lg border border-gray-700 bg-gray-900 p-3 text-sm"
            >
              <div>
                <span class={tx.type === 'BUY' ? 'text-green-400' : 'text-red-400'}>
                  {tx.type === 'BUY' ? '買入' : '賣出'}
                </span>
                <span class="ml-2 text-white">{tx.symbol}</span>
              </div>
              <div class="text-right">
                <p class="text-white">{tx.shares} 股 @ {formatCurrency(tx.price)}</p>
                <p class="text-xs text-gray-400">{formatDateTime(tx.timestamp)}</p>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <p class="py-8 text-center text-gray-500">尚無交易記錄</p>
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
