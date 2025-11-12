<script>
  /**
   * PerformanceDashboard Component
   *
   * 性能儀表板主容器
   * 整合所有儀表板組件，管理時間段狀態和數據加載
   *
   * Features:
   * - 時間段篩選 (1D/1W/1M/3M/1Y/all)
   * - KPI 快速指標卡片
   * - 風險指標詳情面板
   * - 績效趨勢圖表
   * - 交易統計
   * - 完整的數據加載和錯誤處理
   *
   * Svelte 5 使用 runes
   */

  import { onMount } from 'svelte';
  import TimePeriodSelector from './TimePeriodSelector.svelte';
  import KPICards from './KPICards.svelte';
  import RiskMetricsDetail from './RiskMetricsDetail.svelte';
  import PerformanceTrend from './PerformanceTrend.svelte';
  import TradeStatistics from './TradeStatistics.svelte';

  // Props
  let { agentId, agentColor = '34, 197, 94' } = $props();

  // 狀態
  let selectedPeriod = $state('1M');
  let dashboardData = $state(null);
  let loading = $state(false);
  let error = $state(null);

  /**
   * 取得儀表板數據
   * @async
   * @param {string} period - 時間段 (1D|1W|1M|3M|1Y|all)
   */
  async function fetchDashboardData(period) {
    loading = true;
    error = null;

    try {
      const response = await fetch(
        `/api/trading/agents/${agentId}/dashboard?time_period=${period}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      dashboardData = data;
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      error = `無法載入儀表板數據: ${err.message}`;
      dashboardData = null;
    } finally {
      loading = false;
    }
  }

  /**
   * 處理時間段改變
   * @param {string} newPeriod - 新的時間段
   */
  function handlePeriodChange(newPeriod) {
    selectedPeriod = newPeriod;
    fetchDashboardData(newPeriod);
  }

  // 組件掛載時取得初始數據
  onMount(() => {
    fetchDashboardData(selectedPeriod);
  });

  // 衍生狀態：判斷是否有數據
  let hasData = $derived(dashboardData !== null && dashboardData !== undefined);
</script>

<div class="space-y-6 rounded-lg border border-gray-700 bg-gray-800 p-6">
  <!-- 標題 -->
  <div class="flex items-center justify-between">
    <h2 class="text-2xl font-bold" style="color: rgb({agentColor});">性能儀表板</h2>
  </div>

  <!-- 時間段選擇器 -->
  <div class="border-b border-gray-700 pb-6">
    <TimePeriodSelector {selectedPeriod} onperiodchange={handlePeriodChange} {agentColor} />
  </div>

  <!-- 加載狀態 -->
  {#if loading}
    <div class="flex items-center justify-center py-12">
      <div class="text-center">
        <div
          class="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-gray-600 border-t-current"
          style="border-top-color: rgb({agentColor});"
        ></div>
        <p class="text-gray-400">載入中...</p>
      </div>
    </div>
  {:else if error}
    <!-- 錯誤狀態 -->
    <div class="rounded-lg border border-red-500 bg-red-50 p-4">
      <div class="flex items-start">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
        <div class="ml-3">
          <p class="text-sm font-medium text-red-800">{error}</p>
        </div>
      </div>
    </div>
  {:else if hasData}
    <!-- 儀表板內容 -->
    <div class="space-y-6">
      <!-- KPI 快速指標卡片 -->
      <section>
        <h3 class="mb-4 text-lg font-semibold text-gray-300">快速指標</h3>
        <KPICards metrics={dashboardData.kpi} {agentColor} />
      </section>

      <!-- 績效趨勢圖表 -->
      <section>
        <h3 class="mb-4 text-lg font-semibold text-gray-300">績效趨勢</h3>
        <PerformanceTrend data={dashboardData.performance_data} {agentColor} height={300} />
      </section>

      <!-- 風險指標詳情 -->
      <section>
        <h3 class="mb-4 text-lg font-semibold text-gray-300">風險指標</h3>
        <RiskMetricsDetail metrics={dashboardData.risk_metrics} {agentColor} />
      </section>

      <!-- 交易統計 -->
      <section>
        <h3 class="mb-4 text-lg font-semibold text-gray-300">交易統計</h3>
        <TradeStatistics stats={dashboardData.trade_stats} {agentColor} />
      </section>
    </div>
  {:else}
    <!-- 空狀態 -->
    <div class="flex flex-col items-center justify-center py-12">
      <svg
        class="mb-4 h-12 w-12 text-gray-600"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      <p class="text-gray-400">無可用數據</p>
    </div>
  {/if}
</div>

<style>
  /* 可選：添加全局樣式 */
</style>
