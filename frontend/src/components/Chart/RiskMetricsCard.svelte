<script>
  /**
   * RiskMetricsCard Component
   *
   * 展示進階風險指標的卡片組件
   * 包括: Sharpe Ratio, Sortino Ratio, Calmar Ratio
   */

  /**
   * @typedef {Object} RiskMetricsProps
   * @property {any} [metrics]
   * @property {string} [agentColor]
   */

  /** @type {RiskMetricsProps} */
  let {
    metrics = { sharpe_ratio: 0, sortino_ratio: 0, calmar_ratio: 0 },
    agentColor = '34, 197, 94',
  } = $props();

  // 格式化函數
  function formatRatio(value) {
    if (value === null || value === undefined) {
      return '—';
    }
    return value.toFixed(2);
  }

  // 判斷指標好壞
  function getRatioStatus(value) {
    if (value === null || value === undefined) {
      return 'neutral';
    }
    if (value > 1) return 'good'; // 越高越好
    if (value > 0) return 'fair';
    return 'poor';
  }

  function getStatusColor(status) {
    switch (status) {
      case 'good':
        return '#10b981'; // 綠色
      case 'fair':
        return '#f59e0b'; // 黃色
      case 'poor':
        return '#ef4444'; // 紅色
      default:
        return '#9ca3af'; // 灰色
    }
  }

  function getStatusLabel(status) {
    switch (status) {
      case 'good':
        return '優秀';
      case 'fair':
        return '中等';
      case 'poor':
        return '較差';
      default:
        return '無數據';
    }
  }
</script>

<div class="risk-metrics-card">
  <div class="card-header">
    <h3>進階風險指標</h3>
    <span class="last-updated"
      >{metrics.date ? new Date(metrics.date).toLocaleDateString('zh-TW') : '—'}</span
    >
  </div>

  <div class="metrics-grid">
    <!-- Sharpe Ratio -->
    <div class="metric-item">
      <div class="metric-label">
        <span class="label-name">夏普比率</span>
        <span class="label-description">風險調整後的報酬</span>
      </div>
      <div
        class="metric-value"
        style="color: {getStatusColor(getRatioStatus(metrics.sharpe_ratio))}"
      >
        {formatRatio(metrics.sharpe_ratio)}
      </div>
      <div class="metric-status">
        {getStatusLabel(getRatioStatus(metrics.sharpe_ratio))}
      </div>
      <div class="metric-info">
        <small>推薦值 > 1.0</small>
      </div>
    </div>

    <!-- Sortino Ratio -->
    <div class="metric-item">
      <div class="metric-label">
        <span class="label-name">索提諾比率</span>
        <span class="label-description">下行風險調整比率</span>
      </div>
      <div
        class="metric-value"
        style="color: {getStatusColor(getRatioStatus(metrics.sortino_ratio))}"
      >
        {formatRatio(metrics.sortino_ratio)}
      </div>
      <div class="metric-status">
        {getStatusLabel(getRatioStatus(metrics.sortino_ratio))}
      </div>
      <div class="metric-info">
        <small>推薦值 > 1.0</small>
      </div>
    </div>

    <!-- Calmar Ratio -->
    <div class="metric-item">
      <div class="metric-label">
        <span class="label-name">卡瑪比率</span>
        <span class="label-description">報酬 / 最大回撤</span>
      </div>
      <div
        class="metric-value"
        style="color: {getStatusColor(getRatioStatus(metrics.calmar_ratio))}"
      >
        {formatRatio(metrics.calmar_ratio)}
      </div>
      <div class="metric-status">
        {getStatusLabel(getRatioStatus(metrics.calmar_ratio))}
      </div>
      <div class="metric-info">
        <small>推薦值 > 1.0</small>
      </div>
    </div>
  </div>

  <div class="card-footer">
    <small class="note">
      ℹ️ 比率越高表示風險調整後的報酬越好。數據需要至少 20 個交易日才能計算。
    </small>
  </div>
</div>

<style>
  .risk-metrics-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    border-bottom: 2px solid #f3f4f6;
    padding-bottom: 12px;
  }

  .card-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
  }

  .last-updated {
    font-size: 12px;
    color: #9ca3af;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 12px;
  }

  .metric-item {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 12px;
    text-align: center;
  }

  .metric-item:hover {
    background: #f3f4f6;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
  }

  .metric-label {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 8px;
  }

  .label-name {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
  }

  .label-description {
    font-size: 11px;
    color: #9ca3af;
  }

  .metric-value {
    font-size: 24px;
    font-weight: 700;
    margin: 8px 0;
    font-family: 'Courier New', monospace;
  }

  .metric-status {
    font-size: 12px;
    font-weight: 500;
    color: #6b7280;
    margin-bottom: 4px;
  }

  .metric-info {
    font-size: 11px;
    color: #9ca3af;
    border-top: 1px solid #e5e7eb;
    padding-top: 6px;
    margin-top: 6px;
  }

  .card-footer {
    text-align: center;
    padding-top: 12px;
    border-top: 1px solid #e5e7eb;
  }

  .note {
    color: #9ca3af;
    display: block;
    line-height: 1.4;
  }

  @media (max-width: 768px) {
    .metrics-grid {
      grid-template-columns: 1fr;
    }

    .metric-value {
      font-size: 20px;
    }
  }
</style>
