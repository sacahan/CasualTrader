<script>
  /**
   * StatusIndicator Component
   *
   * 狀態指示器組件,顯示帶顏色的狀態標籤
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   */

  import {
    AGENT_STATUS,
    AGENT_STATUS_LABELS,
    AGENT_RUNTIME_STATUS,
    AGENT_RUNTIME_STATUS_LABELS,
    AGENT_MODE_LABELS,
    AGENT_MODE_COLORS,
  } from '../../shared/constants.js';

  /**
   * @typedef {Object} Props
   * @property {any} [status] - agent persistent status
   * @property {any} [runtimeStatus] - agent runtime status
   * @property {any} [mode] - agent mode
   * @property {string} [size] - sm | md | lg
   * @property {boolean} [showDot] - 顯示圓點
   */

  /** @type {Props} */
  let { status = null, runtimeStatus = null, mode = null, size = 'md', showDot = true } = $props();

  // Size mapping
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  const dotSizeClasses = {
    sm: 'h-1.5 w-1.5',
    md: 'h-2 w-2',
    lg: 'h-2.5 w-2.5',
  };
  // 根據 status/runtimeStatus 或 mode 決定顏色和標籤
  let color = $derived(
    mode
      ? AGENT_MODE_COLORS[mode] || 'bg-gray-500'
      : runtimeStatus
        ? getRuntimeStatusColor(runtimeStatus)
        : getStatusColor(status)
  );
  let label = $derived(
    mode
      ? AGENT_MODE_LABELS[mode] || mode
      : runtimeStatus
        ? AGENT_RUNTIME_STATUS_LABELS[runtimeStatus] || runtimeStatus
        : AGENT_STATUS_LABELS[status] || status
  );

  // 函數定義 - 移到根層級以符合 eslint no-inner-declarations 規則
  function getStatusColor(status) {
    switch (status) {
      case AGENT_STATUS.ACTIVE:
        return 'bg-blue-500';
      case AGENT_STATUS.INACTIVE:
        return 'bg-gray-500';
      case AGENT_STATUS.ERROR:
        return 'bg-red-500';
      case AGENT_STATUS.SUSPENDED:
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  }

  function getRuntimeStatusColor(runtimeStatus) {
    switch (runtimeStatus) {
      case AGENT_RUNTIME_STATUS.IDLE:
        return 'bg-gray-500';
      case AGENT_RUNTIME_STATUS.RUNNING:
        return 'bg-green-500';
      case AGENT_RUNTIME_STATUS.STOPPED:
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  }
</script>

<span
  class="inline-flex items-center gap-1.5 rounded-full font-medium {sizeClasses[
    size
  ]} {color} bg-opacity-10"
  style="color: inherit"
>
  {#if showDot}
    <span class="rounded-full {dotSizeClasses[size]} {color}"></span>
  {/if}
  <span class="text-gray-900">{label}</span>
</span>

<style>
  /* 狀態指示器樣式已通過 Tailwind 處理 */
</style>
