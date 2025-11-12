<script>
  /**
   * PerformanceTrend Component
   *
   * 績效趨勢圖表
   * 展示投資組合淨值隨時間的變化
   * 使用 Chart.js 庫進行可視化
   *
   * Svelte 5 使用 runes
   */

  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';

  // Props
  let { data = [], agentColor = '34, 197, 94', height = 300 } = $props();

  let chartContainer = $state(null);
  let chart = $state(null);

  /**
   * 初始化圖表
   */
  function initChart() {
    if (!chartContainer || !data || data.length === 0) {
      return;
    }

    // 銷毀現有圖表
    if (chart) {
      chart.destroy();
    }

    // 提取數據
    const labels = data.map((d) => d.date || '');
    const values = data.map((d) => d.value || 0);

    // 建立圖表
    const ctx = chartContainer.getContext('2d');
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: '投資組合淨值',
            data: values,
            borderColor: `rgb(${agentColor})`,
            backgroundColor: `rgba(${agentColor}, 0.1)`,
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 6,
            pointBackgroundColor: `rgb(${agentColor})`,
            pointBorderColor: 'rgb(17, 24, 39)',
            pointBorderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            labels: {
              color: 'rgb(209, 213, 219)',
              font: {
                size: 12,
              },
            },
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: 'rgb(255, 255, 255)',
            bodyColor: 'rgb(209, 213, 219)',
            borderColor: `rgb(${agentColor})`,
            borderWidth: 1,
            callbacks: {
              label: function (context) {
                return `淨值: ${context.parsed.y.toFixed(2)}`;
              },
            },
          },
        },
        scales: {
          x: {
            display: true,
            grid: {
              color: 'rgba(107, 114, 128, 0.2)',
            },
            ticks: {
              color: 'rgb(156, 163, 175)',
              font: {
                size: 11,
              },
              maxTicksLimit: 6,
            },
          },
          y: {
            display: true,
            grid: {
              color: 'rgba(107, 114, 128, 0.2)',
            },
            ticks: {
              color: 'rgb(156, 163, 175)',
              font: {
                size: 11,
              },
              callback: function (value) {
                return typeof value === 'number' ? value.toFixed(0) : value;
              },
            },
          },
        },
      },
    });
  }

  // 組件掛載時初始化圖表
  onMount(() => {
    initChart();
  });

  // 監視數據變化，重新初始化圖表
  $effect(() => {
    if (data) {
      initChart();
    }
  });
</script>

<div class="rounded-lg border border-gray-700 bg-gray-900 p-6" style="height: {height + 50}px">
  {#if data && data.length > 0}
    <canvas bind:this={chartContainer} style="height: {height}px;"></canvas>
  {:else}
    <div class="flex items-center justify-center py-12">
      <p class="text-gray-400">無可用圖表數據</p>
    </div>
  {/if}
</div>

<style>
  /* Chart.js 樣式已在外部處理 */
</style>
