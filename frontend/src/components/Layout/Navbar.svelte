<script>
  /**
   * Navbar Component
   *
   * 導航列組件
   */

  import { connected } from "../../stores/websocket.js";
  import { isOpen } from "../../stores/market.js";

  export let title = "CasualTrader";
</script>

<nav class="border-b border-gray-200 bg-white shadow-sm">
  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    <div class="flex h-16 items-center justify-between">
      <!-- Logo & Title -->
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-500">
          <svg
            class="h-6 w-6 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
            />
          </svg>
        </div>
        <h1 class="text-xl font-bold text-gray-900">{title}</h1>
      </div>

      <!-- Status Indicators -->
      <div class="flex items-center gap-4">
        <!-- Market Status -->
        <div class="flex items-center gap-2">
          <div
            class="h-2 w-2 rounded-full {$isOpen
              ? 'bg-green-500'
              : 'bg-gray-400'}"
          />
          <span class="text-sm text-gray-600">
            {$isOpen ? "市場開盤中" : "市場已收盤"}
          </span>
        </div>

        <!-- WebSocket Connection Status -->
        <div class="flex items-center gap-2">
          <div
            class="h-2 w-2 rounded-full {$connected
              ? 'bg-green-500 animate-pulse'
              : 'bg-red-500'}"
          />
          <span class="text-sm text-gray-600">
            {$connected ? "即時連線" : "離線"}
          </span>
        </div>
      </div>
    </div>
  </div>
</nav>

<style>
  /* 樣式已通過 Tailwind CSS 處理 */
</style>
