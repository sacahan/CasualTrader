<script>
  /**
   * AgentGrid Component
   *
   * Agent 網格佈局組件,展示多個 Agent 卡片
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   * Svelte 5 compatible - uses callback props instead of createEventDispatcher
   */

  import AgentCard from './AgentCard.svelte';

  /**
   * @typedef {Object} Props
   * @property {any} [agents]
   * @property {any} [selectedAgentId]
   * @property {boolean} [loading]
   * @property {Function} [onselect]
   * @property {Function} [onedit]
   * @property {Function} [ontrade]
   * @property {Function} [onrebalance]
   * @property {Function} [onstop]
   * @property {Function} [ondelete]
   */

  /** @type {Props} */
  let {
    agents = [],
    selectedAgentId = null,
    loading = false,
    onselect = undefined,
    onedit = undefined,
    ontrade = undefined,
    onrebalance = undefined,
    onstop = undefined,
    ondelete = undefined,
  } = $props();

  // 卡片事件處理 - forward to parent callbacks

  // 函數定義 - 移到根層級以符合 eslint no-inner-declarations 規則
  function handleCardClick(agent) {
    onselect?.(agent);
  }
  function handleEditAgent(agent) {
    onedit?.(agent);
  }
  function handleTradeAgent(agent, mode) {
    ontrade?.(agent, mode);
  }
  function handleRebalanceAgent(agent, mode) {
    onrebalance?.(agent, mode);
  }
  function handleStopAgent(agent) {
    onstop?.(agent);
  }
  function handleDeleteAgent(agent) {
    ondelete?.(agent);
  }
</script>

<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
  {#if loading}
    <!-- 載入狀態 -->
    <div class="col-span-full flex items-center justify-center py-12">
      <div class="text-center">
        <svg
          class="mx-auto h-12 w-12 animate-spin text-primary-500"
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
        <p class="mt-4 text-sm text-gray-600">載入 Agents 中...</p>
      </div>
    </div>
  {:else if agents.length === 0}
    <!-- 空狀態 -->
    <div class="col-span-full flex items-center justify-center py-12">
      <div class="text-center">
        <svg
          class="mx-auto h-16 w-16 text-gray-400"
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
        <h3 class="mt-4 text-lg font-medium text-gray-900">尚無 Agent</h3>
        <p class="mt-2 text-sm text-gray-500">點擊「創建新 Agent」開始您的 AI 交易之旅</p>
      </div>
    </div>
  {:else}
    <!-- Agent 卡片網格 -->
    {#each agents as agent (agent.agent_id)}
      <AgentCard
        {agent}
        selected={agent.agent_id === selectedAgentId}
        onclick={handleCardClick}
        onedit={handleEditAgent}
        ontrade={handleTradeAgent}
        onrebalance={handleRebalanceAgent}
        onstop={handleStopAgent}
        ondelete={handleDeleteAgent}
      />
    {/each}
  {/if}
</div>
