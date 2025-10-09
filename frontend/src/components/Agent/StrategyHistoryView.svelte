<script>
  /**
   * StrategyHistoryView Component
   *
   * 策略變更歷史視覺化組件,展示策略演進時間軸
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   */

  import { onMount } from "svelte";
  import { apiClient } from "../../lib/api.js";
  import { formatDateTime } from "../../lib/utils.js";
  import {
    CHANGE_TYPE_LABELS,
    CHANGE_TYPE_COLORS,
  } from "../../lib/constants.js";

  export let agentId;
  export let limit = 20;

  let strategyChanges = [];
  let latestStrategy = null;
  let loading = false;
  let error = null;

  onMount(async () => {
    await loadStrategyHistory();
  });

  async function loadStrategyHistory() {
    if (!agentId) return;

    loading = true;
    error = null;

    try {
      // 載入策略變更歷史
      const changesData = await apiClient.getStrategyChanges(
        agentId,
        limit,
        0,
        null,
      );
      strategyChanges = changesData.strategy_changes || [];

      // 載入最新策略
      const latestData = await apiClient.getLatestStrategy(agentId);
      latestStrategy = latestData.latest_strategy;
    } catch (err) {
      error = err.message;
      console.error("Failed to load strategy history:", err);
    } finally {
      loading = false;
    }
  }

  // 重新載入
  export function reload() {
    return loadStrategyHistory();
  }
</script>

<div class="strategy-history">
  {#if loading}
    <!-- 載入狀態 -->
    <div class="flex items-center justify-center py-8">
      <div class="text-center">
        <svg
          class="mx-auto h-8 w-8 animate-spin text-primary-500"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <p class="mt-2 text-sm text-gray-600">載入策略歷史中...</p>
      </div>
    </div>
  {:else if error}
    <!-- 錯誤狀態 -->
    <div
      class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800"
    >
      <p class="font-medium">載入失敗</p>
      <p class="mt-1">{error}</p>
    </div>
  {:else}
    <!-- 最新策略卡片 -->
    {#if latestStrategy}
      <div
        class="mb-6 rounded-lg border-2 border-primary-500 bg-primary-50 p-4"
      >
        <div class="mb-2 flex items-center gap-2">
          <svg
            class="h-5 w-5 text-primary-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
              clip-rule="evenodd"
            />
          </svg>
          <h3 class="font-semibold text-primary-900">當前策略</h3>
          <span
            class="ml-auto rounded-full px-2 py-0.5 text-xs font-medium {CHANGE_TYPE_COLORS[
              latestStrategy.change_type
            ]}"
          >
            {CHANGE_TYPE_LABELS[latestStrategy.change_type]}
          </span>
        </div>
        <p class="mb-2 text-sm text-primary-800">
          {latestStrategy.new_strategy}
        </p>
        <p class="text-xs text-primary-600">
          調整原因: {latestStrategy.reason}
        </p>
        <p class="mt-2 text-xs text-primary-500">
          更新時間: {formatDateTime(latestStrategy.changed_at)}
        </p>
      </div>
    {/if}

    <!-- 策略變更時間軸 -->
    {#if strategyChanges.length > 0}
      <div class="space-y-4">
        <h4 class="text-sm font-medium text-gray-700">策略演進歷史</h4>

        <div class="relative">
          <!-- 時間軸線 -->
          <div
            class="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"
            aria-hidden="true"
          />

          <!-- 策略變更列表 -->
          <div class="space-y-6">
            {#each strategyChanges as change, index (change.id)}
              <div class="relative flex gap-4">
                <!-- 時間軸圓點 -->
                <div class="relative z-10 flex h-8 w-8 items-center justify-center">
                  <div
                    class="h-3 w-3 rounded-full border-2 border-white {index === 0
                      ? 'bg-primary-500'
                      : 'bg-gray-400'} shadow"
                  />
                </div>

                <!-- 變更內容卡片 -->
                <div class="flex-1 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                  <div class="mb-2 flex items-start justify-between">
                    <span
                      class="rounded-full px-2 py-0.5 text-xs font-medium {CHANGE_TYPE_COLORS[
                        change.change_type
                      ]}"
                    >
                      {CHANGE_TYPE_LABELS[change.change_type]}
                    </span>
                    <span class="text-xs text-gray-500">
                      {formatDateTime(change.changed_at)}
                    </span>
                  </div>

                  <!-- 新策略 -->
                  <div class="mb-3">
                    <p class="text-sm font-medium text-gray-900">新策略:</p>
                    <p class="mt-1 text-sm text-gray-700">
                      {change.new_strategy}
                    </p>
                  </div>

                  <!-- 調整原因 -->
                  <div class="mb-3">
                    <p class="text-sm font-medium text-gray-900">調整原因:</p>
                    <p class="mt-1 text-sm text-gray-700">{change.reason}</p>
                  </div>

                  <!-- 績效指標 (如果有) -->
                  {#if change.performance_snapshot}
                    <div
                      class="mt-3 grid grid-cols-2 gap-4 rounded-md bg-gray-50 p-3 text-xs"
                    >
                      <div>
                        <span class="text-gray-600">當時總報酬:</span>
                        <span
                          class="ml-1 font-medium {change.performance_snapshot
                            .total_return >= 0
                            ? 'text-green-600'
                            : 'text-red-600'}"
                        >
                          {change.performance_snapshot.total_return?.toFixed(2) ||
                            "N/A"}%
                        </span>
                      </div>
                      <div>
                        <span class="text-gray-600">Sharpe Ratio:</span>
                        <span class="ml-1 font-medium text-gray-900">
                          {change.performance_snapshot.sharpe_ratio?.toFixed(2) ||
                            "N/A"}
                        </span>
                      </div>
                    </div>
                  {/if}

                  <!-- 舊策略 (可摺疊) -->
                  {#if change.old_strategy}
                    <details class="mt-3">
                      <summary
                        class="cursor-pointer text-xs font-medium text-gray-600 hover:text-gray-900"
                      >
                        查看舊策略
                      </summary>
                      <p class="mt-2 text-xs text-gray-600">
                        {change.old_strategy}
                      </p>
                    </details>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>
    {:else}
      <!-- 空狀態 -->
      <div class="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
        <svg
          class="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p class="mt-4 text-sm text-gray-600">尚無策略變更記錄</p>
      </div>
    {/if}
  {/if}
</div>

<style>
  /* 樣式已通過 Tailwind CSS 處理 */
</style>
