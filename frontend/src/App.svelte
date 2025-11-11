<script>
  /**
   * App Component
   *
   * 主應用程式組件
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   * Svelte 5 compatible - uses runes instead of legacy APIs
   */

  import { onMount, onDestroy } from 'svelte';
  import { Navbar, NotificationToast } from './components/Layout/index.js';
  import { AgentCreationForm, AgentCard, AgentDetailModal } from './components/Agent/index.js';
  import { Button, Modal } from './components/UI/index.js';
  import {
    agents,
    selectedAgent,
    loading as agentsLoading,
    loadAgents,
    stopAgent,
    deleteAgent,
    selectAgent,
    executeAgent,
  } from './stores/agents.js';
  import {
    agentDetails,
    loadAgentDetails,
    getAgentHoldingsDerived,
  } from './stores/agentDetails.js';
  import { connectWebSocket, disconnectWebSocket } from './stores/websocket.js';
  import { loadMarketStatus, loadMarketIndices } from './stores/market.js';
  import { notifySuccess, notifyError } from './stores/notifications.js';

  // 模態視窗狀態
  let showCreateModal = $state(false);
  let showEditModal = $state(false);
  let showDetailModal = $state(false);

  // 編輯模式的 Agent
  let editingAgent = $state(null);

  onMount(async () => {
    // 連接 WebSocket
    connectWebSocket();

    // 載入初始資料
    await loadAgents();
    await loadMarketStatus();
    await loadMarketIndices();
  });

  // 當 agents 列表變化時，自動載入所有 agent 的詳細資料以顯示圖表
  $effect(() => {
    if ($agents && $agents.length > 0) {
      // 並行加載所有 agent 的詳細資料（使用新的 agentDetails store）
      Promise.all($agents.map((agent) => loadAgentDetails(agent.agent_id))).catch((error) => {
        console.error('Failed to load agent details:', error);
      });
    }
  });

  // Agent 事件處理 - updated for Svelte 5 callback props
  async function handleAgentSelect(agent) {
    selectAgent(agent.agent_id);
    await loadAgentDetails(agent.agent_id);
    showDetailModal = true;
  }

  async function handleTradeAgent(agent, mode) {
    try {
      await executeAgent(agent.agent_id, mode);
      notifySuccess(`Agent ${agent.name} 已進入${getModeName(mode)}模式`);
    } catch (error) {
      notifyError(`${getModeName(mode)}失敗: ${error.message}`);
    }
  }

  async function handleRebalanceAgent(agent, mode) {
    try {
      await executeAgent(agent.agent_id, mode);
      notifySuccess(`Agent ${agent.name} 已進入${getModeName(mode)}模式`);
    } catch (error) {
      notifyError(`${getModeName(mode)}失敗: ${error.message}`);
    }
  }

  function getModeName(mode) {
    const modes = {
      TRADING: '交易',
      REBALANCING: '再平衡',
    };
    return modes[mode] || mode;
  }

  async function handleStopAgent(agent) {
    try {
      await stopAgent(agent.agent_id);
      notifySuccess(`Agent ${agent.name} 已停止`);
    } catch (error) {
      notifyError(`停止失敗: ${error.message}`);
    }
  }

  async function handleEditAgent(agent) {
    editingAgent = agent;
    showEditModal = true;
  }

  async function handleDeleteAgent(agent) {
    if (
      !confirm(
        `確定要刪除 Agent "${agent.name}"?\n\n此操作無法復原,所有相關資料(持倉、交易記錄、策略變更)將被永久刪除。`
      )
    ) {
      return;
    }

    try {
      await deleteAgent(agent.agent_id);
      notifySuccess(`Agent ${agent.name} 已刪除`);
    } catch (error) {
      notifyError(`刪除失敗: ${error.message}`);
    }
  }

  function handleAgentCreated() {
    showCreateModal = false;
    loadAgents(); // 重新載入 agents 列表
  }

  function handleAgentUpdated() {
    showEditModal = false;
    editingAgent = null;
    loadAgents(); // 重新載入 agents 列表
  }

  function handleEditCancel() {
    showEditModal = false;
    editingAgent = null;
  }

  function handleDetailModalClose() {
    showDetailModal = false;
    selectAgent(null);
  }

  onDestroy(() => {
    // 斷開 WebSocket
    disconnectWebSocket();
  });
</script>

<div class="min-h-screen bg-gray-900">
  <!-- Navbar -->
  <Navbar title="Casual Trader" />

  <!-- Main Content -->
  <main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
    <!-- Header -->
    <header class="mb-8 text-center">
      <h1 class="text-3xl font-bold text-white sm:text-4xl">AI 代理人股票交易模擬</h1>
      <p class="mt-2 text-gray-400">觀察不同 AI 交易策略的績效表現</p>
    </header>

    <!-- Control Panel -->
    <div
      class="mb-8 flex items-center justify-between rounded-2xl border border-gray-700 bg-gray-800 p-6 shadow-lg"
    >
      <p class="text-gray-300">點擊卡片查看詳細資訊，或透過設定按鈕管理 Agents。</p>
      <Button onclick={() => (showCreateModal = true)}>
        <svg class="mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          />
        </svg>
        創建新 Agent
      </Button>
    </div>

    <!-- Agent Cards Grid -->
    {#if $agentsLoading}
      <div class="flex items-center justify-center py-20">
        <div class="text-center">
          <div
            class="mb-4 inline-block h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"
          ></div>
          <p class="text-gray-400">載入中...</p>
        </div>
      </div>
    {:else if $agents.length === 0}
      <div class="rounded-2xl border border-gray-700 bg-gray-800 p-12 text-center">
        <svg
          class="mx-auto mb-4 h-16 w-16 text-gray-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
          />
        </svg>
        <h3 class="mb-2 text-xl font-semibold text-white">尚未建立 AI Agent</h3>
        <p class="mb-6 text-gray-400">開始建立您的第一個 AI 交易助手</p>
        <Button onclick={() => (showCreateModal = true)}>
          <svg class="mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
          建立 Agent
        </Button>
      </div>
    {:else}
      <div class="grid grid-cols-1 gap-8 md:grid-cols-2 xl:grid-cols-2">
        {#each $agents as agent (agent.agent_id)}
          {@const detail = $agentDetails[agent.agent_id] || {}}
          <AgentCard
            {agent}
            performanceData={detail.performance || []}
            holdings={detail.holdings || []}
            onclick={handleAgentSelect}
            onedit={handleEditAgent}
            ondelete={handleDeleteAgent}
            ontrade={handleTradeAgent}
            onrebalance={handleRebalanceAgent}
            onstop={handleStopAgent}
          />
        {/each}
      </div>
    {/if}
  </main>

  <!-- Create Agent Modal -->
  <Modal bind:open={showCreateModal} title="創建新 Agent" size="xl">
    <AgentCreationForm oncreated={handleAgentCreated} oncancel={() => (showCreateModal = false)} />
  </Modal>

  <!-- Edit Agent Modal -->
  <Modal bind:open={showEditModal} title="編輯 Agent" size="xl">
    <AgentCreationForm
      agent={editingAgent}
      onupdated={handleAgentUpdated}
      oncancel={handleEditCancel}
    />
  </Modal>

  <!-- Agent Detail Modal -->
  {#if $selectedAgent}
    {@const detail = $agentDetails[$selectedAgent.agent_id] || {}}
    <AgentDetailModal
      agent={$selectedAgent}
      bind:open={showDetailModal}
      performanceData={detail.performance || []}
      holdings={detail.holdings || []}
      transactions={detail.transactions || []}
      onclose={handleDetailModalClose}
    />
  {/if}

  <!-- Notification Toast -->
  <NotificationToast />
</div>

<style>
  /* Global styles are in app.css */
</style>
