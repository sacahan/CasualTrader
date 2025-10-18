<script>
  /**
   * Navbar Component
   *
   * 導航列組件
   */

  import { connected } from '../../stores/websocket.js';
  import { isOpen, twseIndex } from '../../stores/market.js';
  import { theme, toggleTheme } from '../../stores/theme.js';

  /**
   * @typedef {Object} Props
   * @property {string} [title]
   */

  /** @type {Props} */
  let { title = 'CasualTrader' } = $props();
</script>

<nav class="border-b border-gray-700 bg-gray-800 shadow-lg">
  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    <div class="flex h-16 items-center justify-between">
      <!-- Logo & Title -->
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600">
          <svg class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
            />
          </svg>
        </div>
        <h1 class="text-xl font-bold text-white">{title}</h1>
      </div>

      <!-- Status Indicators & Actions -->
      <div class="flex items-center gap-4">
        <!-- TWSE Index -->
        {#if $twseIndex}
          <div class="flex items-center gap-2 border-r border-gray-600 pr-4">
            <svg
              class="h-4 w-4 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
              />
            </svg>
            <div class="flex flex-col">
              <span class="text-xs text-gray-400">大盤指數</span>
              <div class="flex items-center gap-2">
                <span
                  class="text-sm font-semibold {$twseIndex.change_percent >= 0
                    ? 'text-red-400'
                    : 'text-green-400'}"
                >
                  {$twseIndex.current_value?.toLocaleString('zh-TW', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  }) || '--'}
                </span>
                <span
                  class="text-xs {$twseIndex.change_percent >= 0
                    ? 'text-red-400'
                    : 'text-green-400'}"
                >
                  {$twseIndex.change_percent >= 0 ? '▲' : '▼'}
                  {Math.abs($twseIndex.change_percent || 0).toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
        {/if}

        <!-- Market Status -->
        <div class="flex items-center gap-2">
          <div class="status-dot {$isOpen ? 'status-running' : 'bg-gray-500'}"></div>
          <span class="text-sm text-gray-300">
            {$isOpen ? '市場開盤中' : '市場已收盤'}
          </span>
        </div>

        <!-- WebSocket Connection Status -->
        <div class="flex items-center gap-2">
          <div class="status-dot {$connected ? 'status-running blinking' : 'status-stopped'}"></div>
          <span class="text-sm text-gray-300">
            {$connected ? '即時連線' : '離線'}
          </span>
        </div>

        <!-- Theme Toggle Button -->
        <button
          type="button"
          onclick={toggleTheme}
          class="rounded-lg p-2 text-gray-300 transition-colors hover:bg-gray-700 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          aria-label="切換主題"
          title={$theme === 'dark' ? '切換到淺色模式' : '切換到深色模式'}
        >
          {#if $theme === 'dark'}
            <!-- 太陽圖示 (淺色模式) -->
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
              />
            </svg>
          {:else}
            <!-- 月亮圖示 (深色模式) -->
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
              />
            </svg>
          {/if}
        </button>
      </div>
    </div>
  </div>
</nav>

<style>
  /* 樣式已通過 Tailwind CSS 處理 */
</style>
