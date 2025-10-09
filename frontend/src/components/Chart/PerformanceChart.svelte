<script>
  import { run } from 'svelte/legacy';

  /**
   * PerformanceChart Component
   *
   * 績效走勢圖表組件,使用 Chart.js 展示 Agent 績效
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   */

  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';

  /**
   * @typedef {Object} Props
   * @property {any} agentId
   * @property {any} [performanceData] - { date, portfolio_value, total_return }
   * @property {number} [height]
   */

  /** @type {Props} */
  let { agentId, performanceData = [], height = 300 } = $props();

  let canvas = $state();
  let chart = $state(null);


  onMount(() => {
    initChart();
  });

  onDestroy(() => {
    if (chart) {
      chart.destroy();
    }
  });

  function initChart() {
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: '投資組合價值 (TWD)',
            data: [],
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            yAxisID: 'y',
          },
          {
            label: '總報酬率 (%)',
            data: [],
            borderColor: 'rgb(16, 185, 129)',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            position: 'top',
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                if (context.parsed.y !== null) {
                  if (context.datasetIndex === 0) {
                    // 投資組合價值
                    label += new Intl.NumberFormat('zh-TW', {
                      style: 'currency',
                      currency: 'TWD',
                      minimumFractionDigits: 0,
                    }).format(context.parsed.y);
                  } else {
                    // 總報酬率
                    label += context.parsed.y.toFixed(2) + '%';
                  }
                }
                return label;
              },
            },
          },
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: '日期',
            },
          },
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
              display: true,
              text: '投資組合價值 (TWD)',
            },
            ticks: {
              callback: function (value) {
                return new Intl.NumberFormat('zh-TW', {
                  style: 'currency',
                  currency: 'TWD',
                  minimumFractionDigits: 0,
                }).format(value);
              },
            },
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
              display: true,
              text: '總報酬率 (%)',
            },
            grid: {
              drawOnChartArea: false,
            },
            ticks: {
              callback: function (value) {
                return value.toFixed(2) + '%';
              },
            },
          },
        },
      },
    });

    if (performanceData && performanceData.length > 0) {
      updateChart(performanceData);
    }
  }

  function updateChart(data) {
    if (!chart || !data) return;

    const labels = data.map((item) => new Date(item.date).toLocaleDateString('zh-TW'));
    const portfolioValues = data.map((item) => item.portfolio_value);
    const totalReturns = data.map((item) => item.total_return);

    chart.data.labels = labels;
    chart.data.datasets[0].data = portfolioValues;
    chart.data.datasets[1].data = totalReturns;

    chart.update();
  }
  // 當 performanceData 更新時重繪圖表
  run(() => {
    if (chart && performanceData) {
      updateChart(performanceData);
    }
  });
</script>

<div class="performance-chart" style="height: {height}px">
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .performance-chart {
    position: relative;
    width: 100%;
  }
</style>
