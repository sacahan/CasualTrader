<script>
  /**
   * KPICards Component
   *
   * 快速指標卡片網格
   * 展示 4 個主要 KPI：淨值增長、總報酬率、勝率、最大回撤
   *
   * Svelte 5 使用 runes
   */

  import { formatNumber } from '../../shared/utils.js';

  // Props
  let { metrics = {} } = $props();

  // 定義 KPI 卡片配置
  const kpiConfig = [
    {
      key: 'net_value_growth',
      label: '淨值增長',
      unit: '%',
      icon: '📈',
      description: '投資組合淨值相對於初始資本的增長率',
    },
    {
      key: 'total_return',
      label: '總報酬率',
      unit: '%',
      icon: '💰',
      description: '投資期間的總收益率',
    },
    {
      key: 'win_rate',
      label: '勝率',
      unit: '%',
      icon: '🎯',
      description: '獲利交易佔總交易的百分比',
    },
    {
      key: 'max_drawdown',
      label: '最大回撤',
      unit: '%',
      icon: '📉',
      description: '從高點到低點的最大下跌百分比',
    },
  ];

  /**
   * 判斷數值是否為正
   * @param {number} value - 數值
   * @returns {boolean} 是否為正
   */
  function isPositive(value) {
    return value > 0;
  }

  /**
   * 判斷數值是否為負
   * @param {number} value - 數值
   * @returns {boolean} 是否為負
   */
  function isNegative(value) {
    return value < 0;
  }

  /**
   * 獲取指標的顏色狀態
   * @param {number} value - 數值
   * @param {string} key - KPI 鍵
   * @returns {string} 顏色 CSS 類
   */
  function getMetricStatus(value, key) {
    // 最大回撤應該是負數，所以邏輯相反
    if (key === 'max_drawdown') {
      return isNegative(value) ? 'text-red-500' : 'text-green-500';
    }
    return isPositive(value)
      ? 'text-green-500'
      : isNegative(value)
        ? 'text-red-500'
        : 'text-gray-400';
  }

  /**
   * 獲取指標的背景顏色
   * @param {number} value - 數值
   * @param {string} key - KPI 鍵
   * @returns {string} 背景色 CSS 類
   */
  function getMetricBgStatus(value, key) {
    if (key === 'max_drawdown') {
      return isNegative(value) ? 'bg-red-900 bg-opacity-20' : 'bg-green-900 bg-opacity-20';
    }
    return isPositive(value)
      ? 'bg-green-900 bg-opacity-20'
      : isNegative(value)
        ? 'bg-red-900 bg-opacity-20'
        : 'bg-gray-700 bg-opacity-20';
  }

  /**
   * 格式化 KPI 數值
   * @param {number} value - 數值
   * @returns {string} 格式化後的數值
   */
  function formatMetricValue(value) {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    return formatNumber(value, 2);
  }
</script>

<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
  {#each kpiConfig as kpi (kpi.key)}
    <div
      class={`rounded-lg border border-gray-600 p-6 transition-all duration-200 ${getMetricBgStatus(metrics[kpi.key], kpi.key)}`}
    >
      <!-- 圖標和標籤 -->
      <div class="mb-3 flex items-center justify-between">
        <p class="text-sm font-medium text-gray-400">{kpi.label}</p>
        <span class="text-xl">{kpi.icon}</span>
      </div>

      <!-- 數值 -->
      <div class="mb-2">
        <p class={`text-3xl font-bold ${getMetricStatus(metrics[kpi.key], kpi.key)}`}>
          {formatMetricValue(metrics[kpi.key])}{kpi.unit}
        </p>
      </div>

      <!-- 描述 -->
      <p class="text-xs text-gray-500">{kpi.description}</p>
    </div>
  {/each}
</div>

<style>
  /* 可選：添加響應式媒體查詢 */
  @media (max-width: 640px) {
    :global(.grid) {
      grid-template-columns: 1fr;
    }
  }
</style>
