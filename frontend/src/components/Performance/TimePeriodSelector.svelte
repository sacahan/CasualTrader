<script>
  /**
   * TimePeriodSelector Component
   *
   * 時間段選擇器按鈕組
   * 支援快速切換不同的時間段：1D, 1W, 1M, 3M, 1Y, all
   *
   * Svelte 5 使用 runes
   */

  // Props
  let { selectedPeriod = '1M', onperiodchange = () => {}, agentColor = '34, 197, 94' } = $props();

  // 定義可用的時間段
  const periods = [
    { value: '1D', label: '1 天', tooltip: '過去 1 天' },
    { value: '1W', label: '1 週', tooltip: '過去 7 天' },
    { value: '1M', label: '1 月', tooltip: '過去 30 天' },
    { value: '3M', label: '3 月', tooltip: '過去 90 天' },
    { value: '1Y', label: '1 年', tooltip: '過去 365 天' },
    { value: 'all', label: '全部', tooltip: '全部歷史數據' },
  ];

  /**
   * 處理時間段按鈕點擊
   * @param {string} period - 選定的時間段
   */
  function handlePeriodClick(period) {
    if (selectedPeriod !== period) {
      onperiodchange(period);
    }
  }
</script>

<div class="flex flex-wrap gap-2">
  {#each periods as period (period.value)}
    <button
      type="button"
      class="relative inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-all duration-200"
      class:selected={selectedPeriod === period.value}
      class:unselected={selectedPeriod !== period.value}
      style={selectedPeriod === period.value
        ? `background-color: rgb(${agentColor}); color: white;`
        : ''}
      onclick={() => handlePeriodClick(period.value)}
      title={period.tooltip}
    >
      {period.label}
    </button>
  {/each}
</div>

<style>
  button {
    outline: none;
  }

  button:focus {
    outline: 2px solid currentColor;
    outline-offset: 2px;
  }

  .selected {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  .unselected {
    border: 1px solid rgb(75, 85, 99);
    background-color: rgb(55, 65, 81);
    color: rgb(209, 213, 219);
  }

  .unselected:hover {
    border-color: rgb(107, 114, 128);
    background-color: rgb(75, 85, 99);
  }
</style>
