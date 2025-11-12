<script>
  /**
   * TradeStatistics Component
   *
   * 交易統計面板
   * 展示交易相關統計：總交易數、獲利率、平均收益等
   *
   * Svelte 5 使用 runes
   */

  import { formatNumber } from '../../shared/utils.js';

  // Props
  let { stats = {}, agentColor = '34, 197, 94' } = $props();

  /**
   * 計算虧損交易數
   */
  let losingTrades = $derived(stats.total_trades - stats.winning_trades || 0);

  /**
   * 計算虧損率
   */
  let losingRate = $derived(
    stats.total_trades > 0 ? ((losingTrades / stats.total_trades) * 100).toFixed(1) : 0
  );

  /**
   * 格式化數值
   */
  function formatStatValue(value) {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    return formatNumber(value, 2);
  }
</script>

<div class="space-y-4">
  <!-- 統計卡片網格 -->
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
    <!-- 總交易次數 -->
    <div class="rounded-lg border border-gray-600 bg-gray-700 bg-opacity-50 p-6">
      <p class="mb-2 text-sm font-medium text-gray-400">總交易次數</p>
      <p class="text-3xl font-bold" style="color: rgb({agentColor});">
        {stats.total_trades || 0}
      </p>
      <p class="mt-2 text-xs text-gray-500">所有已執行的交易</p>
    </div>

    <!-- 獲利交易 -->
    <div class="rounded-lg border border-gray-600 bg-green-900 bg-opacity-20 p-6">
      <p class="mb-2 text-sm font-medium text-gray-400">獲利交易</p>
      <p class="text-3xl font-bold text-green-500">
        {stats.winning_trades || 0}
      </p>
      <p class="mt-2 text-xs text-gray-500">
        {stats.win_rate !== null && stats.win_rate !== undefined
          ? `佔 ${formatStatValue(stats.win_rate)}%`
          : '無數據'}
      </p>
    </div>

    <!-- 虧損交易 -->
    <div class="rounded-lg border border-gray-600 bg-red-900 bg-opacity-20 p-6">
      <p class="mb-2 text-sm font-medium text-gray-400">虧損交易</p>
      <p class="text-3xl font-bold text-red-500">
        {losingTrades}
      </p>
      <p class="mt-2 text-xs text-gray-500">
        {losingRate}%
      </p>
    </div>

    <!-- 平均收益 -->
    <div class="rounded-lg border border-gray-600 bg-gray-700 bg-opacity-50 p-6">
      <p class="mb-2 text-sm font-medium text-gray-400">平均單筆收益</p>
      <p
        class="text-3xl font-bold"
        style="color: {stats.avg_return > 0 ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'}"
      >
        {formatStatValue(stats.avg_return)}%
      </p>
      <p class="mt-2 text-xs text-gray-500">平均收益率</p>
    </div>
  </div>

  <!-- 交易比例詳情 -->
  <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
    <h4 class="mb-4 font-semibold text-gray-300">交易分析</h4>

    <div class="space-y-4">
      <!-- 獲利率進度條 -->
      <div>
        <div class="mb-2 flex items-center justify-between">
          <span class="text-sm text-gray-400">獲利率</span>
          <span class="text-sm font-medium text-green-500">
            {stats.win_rate ? formatStatValue(stats.win_rate) : 0}%
          </span>
        </div>
        <div class="h-2 w-full rounded-full bg-gray-700">
          <div
            class="h-full rounded-full bg-green-500 transition-all duration-500"
            style="width: {stats.win_rate || 0}%"
          ></div>
        </div>
      </div>

      <!-- 虧損率進度條 -->
      <div>
        <div class="mb-2 flex items-center justify-between">
          <span class="text-sm text-gray-400">虧損率</span>
          <span class="text-sm font-medium text-red-500">
            {losingRate}%
          </span>
        </div>
        <div class="h-2 w-full rounded-full bg-gray-700">
          <div
            class="h-full rounded-full bg-red-500 transition-all duration-500"
            style="width: {losingRate}%"
          ></div>
        </div>
      </div>
    </div>
  </div>

  <!-- 交易統計說明 -->
  <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
    <h4 class="mb-3 font-semibold text-gray-300">統計說明</h4>
    <ul class="space-y-2 text-sm text-gray-400">
      <li>
        <strong>總交易次數:</strong> 交易系統執行的所有交易數量（買進+賣出）。
      </li>
      <li>
        <strong>獲利交易:</strong> 帶來正收益的交易數量及其佔比。
      </li>
      <li>
        <strong>虧損交易:</strong> 帶來負收益的交易數量及其佔比。
      </li>
      <li>
        <strong>平均單筆收益:</strong> 所有交易的平均收益率。
      </li>
    </ul>
  </div>
</div>

<style>
  /* 響應式設計已透過 Tailwind 處理 */
</style>
