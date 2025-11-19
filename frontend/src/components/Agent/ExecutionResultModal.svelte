<script>
  /**
   * ExecutionResultModal Component
   *
   * 執行結果詳情模態視窗
   * 展示 Agent 執行後的詳細結果、交易紀錄、再平衡建議等
   *
   * Svelte 5 compatible
   */

  import { formatDateTime, formatNumber, formatCurrency } from '../../shared/utils.js';

  /** @type {any} */
  let {
    isOpen = false,
    agent = null,
    executionResult = null,
    executionDetail = null,
    error = null,
    onClose = undefined,
    onRetryLoadDetail = undefined,
    agentColor = '34, 197, 94', // RGB 色系：預設綠色
  } = $props();

  let executionTrades = $state([]);
  let statCards = $state([]);
  let isLoading = $state(true);

  $effect(() => {
    if (!isOpen) {
      executionTrades = [];
      statCards = [];
      isLoading = false;
      return;
    }

    const modeValue = executionDetail?.mode || executionResult?.mode || '--';
    const consumeValue =
      executionDetail?.execution_time_ms != null
        ? `${(executionDetail.execution_time_ms / 1000).toFixed(2)} 秒`
        : '--';
    const stats = executionDetail?.stats || {};
    const filledValue = stats.filled != null ? formatNumber(stats.filled) : '--';
    const notionalValue = stats.notional != null ? formatCurrency(stats.notional) : '--';

    statCards = [
      { label: '模式', value: modeValue },
      { label: '耗時', value: consumeValue },
      { label: '成交筆數', value: filledValue },
      { label: '名目金額', value: notionalValue },
    ];

    executionTrades = executionDetail?.trades || [];
    isLoading = !executionDetail && !error;
  });

  function handleEscapeKey(event) {
    if (event.key === 'Escape') {
      event.preventDefault();
      onClose?.();
    }
  }

  function handleOverlayClick(event) {
    if (event.target === event.currentTarget) {
      onClose?.();
    }
  }

  function handleOverlayKeydown(event) {
    if (event.target !== event.currentTarget) {
      return;
    }
    if (event.key === 'Escape' || event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClose?.();
    }
  }

  function getExecutionStatusMeta() {
    const status = executionDetail?.status?.toLowerCase();
    if (status === 'completed') {
      return { label: '執行成功', className: 'status-badge-success' };
    }
    if (status === 'failed') {
      return { label: '執行失敗', className: 'status-badge-failed' };
    }
    if (status === 'running' || status === 'pending') {
      return { label: '執行中', className: 'status-badge-running' };
    }
    if (status === 'stopped' || status === 'timeout') {
      return { label: '已停止', className: 'status-badge-stopped' };
    }

    return { label: '未知狀態', className: 'status-badge-unknown' };
  }
</script>

<svelte:window on:keydown={handleEscapeKey} />

{#if isOpen}
  {#key executionResult?.sessionId ?? 'execution-modal'}
    <div
      class="modal-overlay"
      role="button"
      aria-label="關閉執行結果視窗"
      tabindex="0"
      onclick={handleOverlayClick}
      onkeydown={handleOverlayKeydown}
    >
      <div
        class="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-label="執行結果詳情"
        style={`--agent-color-rgb: ${agentColor};`}
      >
        <div class="modal-header">
          <div>
            {#if executionResult}
              {@const statusMeta = getExecutionStatusMeta()}
              <div class="modal-title-row">
                <h4 class="modal-title">
                  {agent?.name || 'Agent'}
                </h4>
                <span class={`status-badge ${statusMeta.className}`}>{statusMeta.label}</span>
              </div>
            {/if}
            <p class="modal-subtitle pt-1">
              {executionResult?.sessionId ?? '—'}
              {#if executionResult?.completedAt}
                - {formatDateTime(executionResult.completedAt)}
              {/if}
            </p>
          </div>
          <button
            type="button"
            class="icon-button modal-close-button"
            onclick={onClose}
            aria-label="關閉視窗"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <div class="modal-body custom-scrollbar">
          {#if isLoading}
            <div class="modal-loading">
              <div class="spinner"></div>
              <p class="text-sm text-gray-300">載入詳細資料...</p>
            </div>
          {:else if error}
            <div class="alert-card alert-error">
              <div class="font-semibold">無法載入詳細資料</div>
              <p class="text-xs leading-relaxed mt-1">{error}</p>
            </div>
            {#if executionResult?.sessionId}
              <button
                type="button"
                class="expand-button mt-3"
                onclick={() => onRetryLoadDetail?.(executionResult.sessionId)}
              >
                重新載入詳細資料
              </button>
            {/if}
          {:else}
            <div class="modal-summary-block">
              <h4>
                {executionResult?.mode && executionResult.mode === 'REBALANCING'
                  ? 'AI 再平衡建議'
                  : 'AI 交易總結'}
              </h4>
              <code>{executionDetail?.final_output || '--'}</code>
            </div>
            <div class="stat-grid">
              {#if statCards.length > 0}
                {#each statCards as stat (stat.label)}
                  <div class="stat-card">
                    <p class="detail-section-title">{stat.label}</p>
                    <p class="text-lg font-semibold text-white mt-1">{stat.value}</p>
                  </div>
                {/each}
              {/if}
            </div>

            {#if executionTrades.length > 0}
              <div class="detail-section">
                <h5 class="detail-section-title">交易紀錄</h5>
                <div class="detail-list">
                  {#each executionTrades as trade, index (trade.id || `${trade.ticker || trade.symbol || 'trade'}-${index}`)}
                    <div class="trade-item">
                      <div class="trade-item-header">
                        <div class="trade-item-overview">
                          <div class="trade-item-title">
                            <span class="holding-ticker">{trade.ticker || trade.symbol || '—'}</span
                            >
                            <span
                              class={`trade-action-${
                                (trade.action || trade.type || 'BUY').toString().toLowerCase() ===
                                'sell'
                                  ? 'sell'
                                  : 'buy'
                              }`}
                            >
                              {(trade.action || trade.type || 'BUY') === 'SELL' ? '賣出' : '買入'}
                            </span>
                          </div>
                          <p class="trade-company-name">
                            {trade.company_name || trade.companyName || '—'}
                          </p>
                        </div>
                      </div>
                      <div class="trade-item-body">
                        <div class="trade-stat">
                          <span class="trade-stat-label">數量</span>
                          <span class="trade-stat-value">
                            {formatNumber(trade.quantity ?? trade.shares ?? 0)}
                          </span>
                        </div>
                        <div class="trade-stat">
                          <span class="trade-stat-label">價格</span>
                          <span class="trade-stat-value">{formatCurrency(trade.price ?? 0)}</span>
                        </div>
                        <div class="trade-stat">
                          <span class="trade-stat-label">金額</span>
                          <span class="trade-stat-value">
                            {formatCurrency(
                              trade.amount ??
                                trade.total_amount ??
                                (trade.price ?? 0) * (trade.quantity ?? trade.shares ?? 0)
                            )}
                          </span>
                        </div>
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            {#if executionResult?.error_message}
              <div class="alert-card alert-error mt-3">
                <div class="font-semibold">伺服器訊息</div>
                <p class="text-xs leading-relaxed mt-1">{executionResult.error_message}</p>
              </div>
            {/if}
          {/if}
        </div>
      </div>
    </div>
  {/key}
{/if}

<style lang="postcss">
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 50;
    padding: 1rem;
    backdrop-filter: blur(4px);
  }

  .modal-panel {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.9));
    border: 1px solid rgba(51, 65, 85, 0.5);
    border-radius: 1rem;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
    max-width: 900px;
    width: 100%;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    padding: 1.5rem;
    border-bottom: 1px solid rgba(51, 65, 85, 0.3);
    background: rgba(0, 0, 0, 0.2);
  }

  .modal-title-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .modal-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #f1f5f9;
    margin: 0;
  }

  .modal-subtitle {
    font-size: 0.875rem;
    color: #94a3b8;
    margin-top: 0.5rem;
    margin: 0;
  }

  .modal-close-button {
    flex-shrink: 0;
    color: #cbd5e1;
    transition: color 0.2s;
  }

  .modal-close-button:hover {
    color: #f1f5f9;
  }

  .modal-body {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
  }

  .modal-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1rem;
    gap: 1rem;
  }

  .modal-summary-block {
    background: linear-gradient(
      135deg,
      rgba(var(--agent-color-rgb, 34, 197, 94), 0.1),
      rgba(var(--agent-color-rgb, 34, 197, 94), 0.05)
    );
    border-left: 4px solid rgb(var(--agent-color-rgb, 34, 197, 94));
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }

  .modal-summary-block h4 {
    font-size: 0.95rem;
    font-weight: 600;
    color: rgb(var(--agent-color-rgb, 34, 197, 94));
    margin: 0 0 0.5rem 0;
  }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .stat-card {
    background: rgba(51, 65, 85, 0.4);
    border: 1px solid rgba(71, 85, 105, 0.3);
    border-radius: 0.5rem;
    padding: 1rem;
    text-align: center;
  }

  .detail-section {
    margin-bottom: 1.5rem;
  }

  .detail-section-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #cbd5e1;
    margin: 0 0 0.75rem 0;
  }

  .detail-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .trade-item {
    position: relative;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.85));
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-left: 3px solid rgba(var(--agent-color-rgb, 34, 197, 94), 0.6);
    border-radius: 0.75rem;
    padding: 1.1rem 1.25rem;
    box-shadow: 0 16px 30px rgba(8, 15, 34, 0.35);
    transition:
      transform 0.2s ease,
      border-color 0.2s ease;
  }

  .trade-item:hover {
    transform: translateY(-2px);
    border-left-color: rgba(var(--agent-color-rgb, 34, 197, 94), 0.85);
  }

  .trade-item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .trade-item-overview {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .trade-item-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .trade-company-name {
    font-size: 0.75rem;
    color: #94a3b8;
    margin: 0;
    letter-spacing: 0.01em;
  }

  .holding-ticker {
    font-weight: 600;
    color: #f1f5f9;
  }

  .trade-action-buy {
    background: rgba(34, 197, 94, 0.2);
    color: #86efac;
    padding: 0.25rem 0.75rem;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .trade-action-sell {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
    padding: 0.25rem 0.75rem;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .trade-status-badge {
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(94, 234, 212, 0.2);
    color: #67e8f9;
    padding: 0.25rem 0.75rem;
    border-radius: 0.375rem;
  }

  .trade-item-body {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.75rem;
  }

  .trade-stat {
    background: rgba(51, 65, 85, 0.35);
    border: 1px solid rgba(100, 116, 139, 0.2);
    border-radius: 0.55rem;
    padding: 0.6rem 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .trade-stat-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
  }

  .trade-stat-value {
    font-size: 0.95rem;
    font-weight: 600;
    color: #f8fafc;
  }

  .tool-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tool-chip {
    background: rgba(59, 130, 246, 0.2);
    color: #93c5fd;
    padding: 0.375rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 500;
  }

  .detail-json {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(71, 85, 105, 0.3);
    border-radius: 0.5rem;
    padding: 1rem;
    overflow-x: auto;
    font-size: 0.8rem;
    color: #cbd5e1;
    line-height: 1.4;
    margin: 0;
  }

  .alert-card {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-top: 1rem;
  }

  .alert-error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #fecaca;
  }

  .icon-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.375rem;
    transition: all 0.2s;
  }

  .icon-button:hover {
    background: rgba(148, 163, 184, 0.1);
  }

  .expand-button {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.3);
    color: #93c5fd;
    padding: 0.625rem 1.25rem;
    border-radius: 0.5rem;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    margin-top: 1rem;
  }

  .expand-button:hover {
    background: rgba(59, 130, 246, 0.3);
    border-color: rgba(59, 130, 246, 0.5);
  }

  .spinner {
    width: 2rem;
    height: 2rem;
    border: 2px solid rgba(148, 163, 184, 0.2);
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .custom-scrollbar {
    scrollbar-color: rgba(71, 85, 105, 0.5) transparent;
    scrollbar-width: thin;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }

  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }

  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(71, 85, 105, 0.5);
    border-radius: 3px;
  }

  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(71, 85, 105, 0.7);
  }
</style>
