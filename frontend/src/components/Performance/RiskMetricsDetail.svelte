<script>
  /**
   * RiskMetricsDetail Component
   *
   * 風險指標詳情面板
   * 展示詳細的風險指標：Sharpe Ratio、Sortino Ratio、Calmar Ratio、Information Ratio
   * 包含指標說明和狀態評級
   *
   * Svelte 5 使用 runes
   */

  import { formatNumber } from '../../shared/utils.js';

  // Props
  let { metrics = {} } = $props();

  // 定義風險指標配置
  const riskMetricsConfig = [
    {
      key: 'sharpe_ratio',
      label: 'Sharpe Ratio',
      description: '風險調整收益率指標（高於 1.0 為優秀）',
      thresholds: {
        excellent: 1.0,
        good: 0.5,
        poor: 0.0,
      },
    },
    {
      key: 'sortino_ratio',
      label: 'Sortino Ratio',
      description: '考慮下行風險的報酬指標（高於 1.0 為優秀）',
      thresholds: {
        excellent: 1.0,
        good: 0.5,
        poor: 0.0,
      },
    },
    {
      key: 'calmar_ratio',
      label: 'Calmar Ratio',
      description: '報酬與最大回撤的比率（高於 1.0 為優秀）',
      thresholds: {
        excellent: 1.0,
        good: 0.5,
        poor: 0.0,
      },
    },
    {
      key: 'information_ratio',
      label: 'Information Ratio',
      description: '超額報酬與超額風險的比率（高於 0.5 為優秀）',
      thresholds: {
        excellent: 0.5,
        good: 0.25,
        poor: 0.0,
      },
    },
  ];

  /**
   * 根據數值和閾值取得風險指標的評級
   * @param {number} value - 指標數值
   * @param {object} thresholds - 閾值物件
   * @returns {object} 評級物件 {status, statusText, statusColor}
   */
  function getRiskMetricStatus(value, thresholds) {
    if (value === null || value === undefined) {
      return {
        status: 'unknown',
        statusText: '無數據',
        statusColor: 'text-gray-400',
        bgColor: 'bg-gray-700 bg-opacity-20',
      };
    }

    if (value >= thresholds.excellent) {
      return {
        status: 'excellent',
        statusText: '優秀',
        statusColor: 'text-green-500',
        bgColor: 'bg-green-900 bg-opacity-20',
      };
    }

    if (value >= thresholds.good) {
      return {
        status: 'good',
        statusText: '良好',
        statusColor: 'text-blue-500',
        bgColor: 'bg-blue-900 bg-opacity-20',
      };
    }

    if (value >= thresholds.poor) {
      return {
        status: 'fair',
        statusText: '尚可',
        statusColor: 'text-yellow-500',
        bgColor: 'bg-yellow-900 bg-opacity-20',
      };
    }

    return {
      status: 'poor',
      statusText: '較差',
      statusColor: 'text-red-500',
      bgColor: 'bg-red-900 bg-opacity-20',
    };
  }

  /**
   * 格式化指標數值
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

<div class="space-y-4">
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
    {#each riskMetricsConfig as metric (metric.key)}
      {@const metricValue = metrics[metric.key]}
      {@const status = getRiskMetricStatus(metricValue, metric.thresholds)}

      <div
        class={`rounded-lg border border-gray-600 p-6 transition-all duration-200 ${status.bgColor}`}
      >
        <!-- 指標標籤 -->
        <div class="mb-3 flex items-start justify-between">
          <div>
            <p class="font-semibold text-gray-300">{metric.label}</p>
            <p class="text-xs text-gray-500">{metric.description}</p>
          </div>
        </div>

        <!-- 指標數值和評級 -->
        <div class="flex items-baseline justify-between">
          <p class={`text-2xl font-bold ${status.statusColor}`}>
            {formatMetricValue(metricValue)}
          </p>
          <span class={`text-xs font-medium ${status.statusColor}`}>
            {status.statusText}
          </span>
        </div>
      </div>
    {/each}
  </div>

  <!-- 指標說明 -->
  <div class="mt-6 rounded-lg border border-gray-700 bg-gray-800 p-4">
    <h4 class="mb-3 font-semibold text-gray-300">指標說明</h4>
    <ul class="space-y-2 text-sm text-gray-400">
      <li>
        <strong>Sharpe Ratio:</strong> 衡量每單位風險獲得的超額報酬。值越高越好（> 1.0 為優秀）。
      </li>
      <li>
        <strong>Sortino Ratio:</strong> 類似 Sharpe，但只考慮負波動率。通常高於 Sharpe Ratio（> 1.0 為優秀）。
      </li>
      <li>
        <strong>Calmar Ratio:</strong> 年化回報率與最大回撤的比率。衡量風險調整收益（> 1.0 為優秀）。
      </li>
      <li>
        <strong>Information Ratio:</strong> 超額報酬與超額風險的比率。衡量基金經理的選股能力（> 0.5 為優秀）。
      </li>
    </ul>
  </div>
</div>

<style>
  /* 響應式設計已透過 Tailwind 處理 */
</style>
