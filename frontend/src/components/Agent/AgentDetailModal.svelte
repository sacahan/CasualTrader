<script>
  /**
   * AgentDetailModal Component
   *
   * Agent 詳細資訊 Modal
   * 顯示完整的 Agent 資訊、績效圖表、持倉詳情、交易歷史
   * 可以編輯 Agent 屬性和刪除 Agent
   */

  import { Button, Modal } from '../UI/index.js';
  import { PerformanceChart } from '../Chart/index.js';
  import { formatCurrency, formatDateTime } from '../../lib/utils.js';
  import { AI_MODEL_LABELS } from '../../lib/constants.js';

  // Props
  let {
    agent,
    open = false,
    performanceData = [],
    holdings = [],
    transactions = [],
    onclose = undefined,
    onedit = undefined,
    ondelete = undefined,
  } = $props();

  // 計算資產相關數據
  let totalAssets = $derived(agent?.initial_funds || 1000000);
  let currentCash = $derived(agent?.initial_funds || 345020.5);
  let pnl = $derived(totalAssets - (agent?.initial_funds || 1000000));
  let pnlPercent = $derived((pnl / (agent?.initial_funds || 1000000)) * 100);
  let isProfit = $derived(pnl >= 0);

  // Agent 顏色
  let agentColor = $derived(agent?.color || '34, 197, 94');

  // 編輯模式
  let isEditing = $state(false);
  let editForm = $state({
    name: '',
    description: '',
    color: '',
    max_position_size: 15,
  });

  function handleEdit() {
    if (!agent) return;

    editForm = {
      name: agent.name,
      description: agent.description || '',
      color: agent.color || '34, 197, 94',
      max_position_size: (agent.investment_preferences?.max_position_size || 0.15) * 100,
    };
    isEditing = true;
  }

  function handleCancelEdit() {
    isEditing = false;
  }

  async function handleSaveEdit() {
    if (!agent) return;

    const updates = {
      name: editForm.name,
      description: editForm.description,
      color: editForm.color,
      investment_preferences: {
        ...agent.investment_preferences,
        max_position_size: editForm.max_position_size / 100,
      },
    };

    await onedit?.(agent, updates);
    isEditing = false;
  }

  function handleDelete() {
    if (!agent) return;

    if (confirm(`確定要刪除 Agent "${agent.name}"?\n\n此操作無法復原。`)) {
      ondelete?.(agent);
    }
  }

  function handleClose() {
    isEditing = false;
    onclose?.();
  }
</script>

<Modal bind:open size="full" onclose={handleClose}>
  <div slot="header" class="flex items-center justify-between">
    <h2 class="text-2xl font-bold" style="color: rgb({agentColor});">
      {agent?.name || 'Agent 詳情'}
    </h2>
    {#if !isEditing}
      <div class="flex gap-2">
        <Button variant="ghost" size="sm" onclick={handleEdit}>
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
            />
          </svg>
          編輯
        </Button>
        <Button variant="danger" size="sm" onclick={handleDelete}>
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
          刪除
        </Button>
      </div>
    {/if}
  </div>

  <div class="custom-scrollbar max-h-[70vh] space-y-6 overflow-y-auto p-6">
    {#if isEditing}
      <!-- 編輯表單 -->
      <div class="space-y-4">
        <div>
          <label for="edit-name" class="mb-2 block text-sm font-medium text-gray-300">
            Agent 名稱
          </label>
          <input
            id="edit-name"
            type="text"
            bind:value={editForm.name}
            class="w-full rounded-lg border border-gray-600 bg-gray-700 p-3 text-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label for="edit-description" class="mb-2 block text-sm font-medium text-gray-300">
            描述
          </label>
          <textarea
            id="edit-description"
            bind:value={editForm.description}
            rows="3"
            class="w-full rounded-lg border border-gray-600 bg-gray-700 p-3 text-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          ></textarea>
        </div>

        <div>
          <label for="edit-color" class="mb-2 block text-sm font-medium text-gray-300">
            卡片顏色 (R, G, B)
          </label>
          <input
            id="edit-color"
            type="text"
            bind:value={editForm.color}
            placeholder="例如：34, 197, 94"
            class="w-full rounded-lg border border-gray-600 bg-gray-700 p-3 text-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p class="mt-1 text-xs text-gray-400">
            預設顏色：綠色 (34, 197, 94)、橙色 (249, 115, 22)、藍色 (59, 130, 246)
          </p>
        </div>

        <div>
          <label for="edit-max-position" class="mb-2 block text-sm font-medium text-gray-300">
            單一持股上限 (%)
          </label>
          <input
            id="edit-max-position"
            type="number"
            min="5"
            max="100"
            bind:value={editForm.max_position_size}
            class="w-full rounded-lg border border-gray-600 bg-gray-700 p-3 text-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div class="flex gap-3 pt-4">
          <Button variant="primary" fullWidth onclick={handleSaveEdit}>儲存變更</Button>
          <Button variant="secondary" fullWidth onclick={handleCancelEdit}>取消</Button>
        </div>
      </div>
    {:else}
      <!-- 詳細資訊顯示 -->

      <!-- 基本資訊 -->
      <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
        <h3 class="mb-3 text-lg font-semibold text-white">基本資訊</h3>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-gray-400">AI 模型</p>
            <p class="font-medium text-white">
              {AI_MODEL_LABELS[agent?.ai_model] || agent?.ai_model}
            </p>
          </div>
          <div>
            <p class="text-gray-400">狀態</p>
            <p class="font-medium text-white">{agent?.status || 'IDLE'}</p>
          </div>
          <div>
            <p class="text-gray-400">創建時間</p>
            <p class="font-medium text-white">{formatDateTime(agent?.created_at)}</p>
          </div>
          <div>
            <p class="text-gray-400">單一持股上限</p>
            <p class="font-medium text-white">
              {((agent?.investment_preferences?.max_position_size || 0.15) * 100).toFixed(0)}%
            </p>
          </div>
        </div>
        {#if agent?.description}
          <div class="mt-3 border-t border-gray-700 pt-3">
            <p class="text-gray-400">描述</p>
            <p class="mt-1 text-white">{agent.description}</p>
          </div>
        {/if}
      </div>

      <!-- 資產概覽 -->
      <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
        <h3 class="mb-3 text-lg font-semibold text-white">資產概覽</h3>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <p class="text-sm text-gray-400">總資產</p>
            <p class="text-xl font-bold text-white">{formatCurrency(totalAssets)}</p>
          </div>
          <div>
            <p class="text-sm text-gray-400">現金餘額</p>
            <p class="text-xl font-bold text-white">{formatCurrency(currentCash)}</p>
          </div>
          <div>
            <p class="text-sm text-gray-400">總損益</p>
            <p class="text-xl font-bold" class:text-gain={isProfit} class:text-loss={!isProfit}>
              {isProfit ? '+' : ''}{formatCurrency(pnl)}
              <span class="text-sm">({pnlPercent.toFixed(2)}%)</span>
            </p>
          </div>
        </div>
      </div>

      <!-- 績效圖表 -->
      <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
        <h3 class="mb-3 text-lg font-semibold text-white">績效走勢</h3>
        <PerformanceChart agentId={agent?.agent_id} {performanceData} height={300} />
      </div>

      <!-- 持倉詳情 -->
      <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
        <h3 class="mb-3 text-lg font-semibold text-white">持倉詳情</h3>
        {#if holdings && holdings.length > 0}
          <div class="space-y-2">
            {#each holdings as holding}
              <div
                class="flex items-center justify-between rounded-lg border border-gray-700 bg-gray-900 p-3"
              >
                <div>
                  <p class="font-medium text-white">{holding.symbol}</p>
                  <p class="text-sm text-gray-400">{holding.name || ''}</p>
                </div>
                <div class="text-right">
                  <p class="font-medium text-white">{holding.shares || 0} 股</p>
                  <p class="text-sm text-gray-400">
                    成本 @ {formatCurrency(holding.avg_price || 0)}
                  </p>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="py-8 text-center text-gray-500">尚無持股</p>
        {/if}
      </div>

      <!-- 交易歷史 -->
      <div class="rounded-lg border border-gray-700 bg-gray-800 p-4">
        <h3 class="mb-3 text-lg font-semibold text-white">交易歷史</h3>
        {#if transactions && transactions.length > 0}
          <div class="custom-scrollbar max-h-64 space-y-2 overflow-y-auto">
            {#each transactions as tx}
              <div
                class="flex items-center justify-between rounded-lg border border-gray-700 bg-gray-900 p-3 text-sm"
              >
                <div>
                  <span class={tx.type === 'BUY' ? 'text-green-400' : 'text-red-400'}>
                    {tx.type === 'BUY' ? '買入' : '賣出'}
                  </span>
                  <span class="ml-2 text-white">{tx.symbol}</span>
                </div>
                <div class="text-right">
                  <p class="text-white">{tx.shares} 股 @ {formatCurrency(tx.price)}</p>
                  <p class="text-xs text-gray-400">{formatDateTime(tx.timestamp)}</p>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="py-8 text-center text-gray-500">尚無交易記錄</p>
        {/if}
      </div>
    {/if}
  </div>
</Modal>

<style>
  .text-gain {
    color: #4ade80;
  }
  .text-loss {
    color: #f87171;
  }
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: #1f2937;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: #4b5563;
    border-radius: 10px;
  }
</style>
