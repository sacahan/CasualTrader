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
  import {
    AgentCreationForm,
    AgentCardSimple,
    AgentDetailModal,
  } from './components/Agent/index.js';
  import { Button, Modal } from './components/UI/index.js';
  import {
    agents,
    selectedAgent,
    loading as agentsLoading,
    loadAgents,
    startAgent,
    stopAgent,
    deleteAgent,
    updateAgent,
    selectAgent,
  } from './stores/agents.js';
  import { connectWebSocket, disconnectWebSocket } from './stores/websocket.js';
  import { loadMarketStatus, startMarketDataPolling } from './stores/market.js';
  import { notifySuccess, notifyError } from './stores/notifications.js';
  import { apiClient } from './shared/api.js';

  // 模態視窗狀態
  let showCreateModal = $state(false);
  let showEditModal = $state(false);
  let showDetailModal = $state(false);

  // 編輯模式的 Agent
  let editingAgent = $state(null);

  // 每個 Agent 的詳細資料
  let agentPerformanceData = $state({});
  let agentHoldings = $state({});
  let agentTransactions = $state({});

  // 市場資料刷新定時器
  let stopMarketPolling = null;

  onMount(async () => {
    // 連接 WebSocket
    connectWebSocket();

    // 載入初始資料
    await loadAgents();
    await loadMarketStatus();

    // 啟動市場資料定時刷新
    stopMarketPolling = startMarketDataPolling(30000); // 30 秒刷新一次
  });

  // 函數定義 - 移到根層級以符合 eslint no-inner-declarations 規則
  async function loadAgentDetails(agentId) {
    try {
      // 載入績效資料
      const perfData = await apiClient.getPerformance(agentId);
      agentPerformanceData[agentId] = perfData.history || [];

      // 載入持倉資料
      const holdingsData = await apiClient.getHoldings(agentId);
      agentHoldings[agentId] = holdingsData || [];

      // 載入交易歷史
      const txData = await apiClient.getTransactions(agentId);
      agentTransactions[agentId] = txData || [];
    } catch (error) {
      console.error('Failed to load agent details:', error);
    }
  }

  // Agent 事件處理 - updated for Svelte 5 callback props
  async function handleAgentSelect(agent) {
    selectAgent(agent.agent_id);
    await loadAgentDetails(agent.agent_id);
    showDetailModal = true;
  }

  async function handleStartAgent(agent) {
    try {
      await startAgent(agent.agent_id);
      notifySuccess(`Agent ${agent.name} 已啟動`);
    } catch (error) {
      notifyError(`啟動失敗: ${error.message}`);
    }
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

  async function handleAgentEdit(agent, updates) {
    try {
      await updateAgent(agent.agent_id, updates);
      notifySuccess(`Agent ${agent.name} 已更新`);
      await loadAgents(); // 重新載入列表
    } catch (error) {
      notifyError(`更新失敗: ${error.message}`);
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

    // 停止市場資料刷新
    if (stopMarketPolling) {
      stopMarketPolling();
    }
  });
</script>

<div class="min-h-screen bg-gray-900">
  <!-- Navbar -->
  <Navbar title="AI 股票交易模擬器" />

  <!-- Main Content -->
  <main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
    <!-- Header -->
    <header class="mb-8 text-center">
      <h1 class="text-3xl font-bold text-white sm:text-4xl">AI 股票交易模擬器</h1>
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
          <AgentCardSimple
            {agent}
            performanceData={agentPerformanceData[agent.agent_id] || []}
            holdings={agentHoldings[agent.agent_id] || []}
            onclick={handleAgentSelect}
            onstart={handleStartAgent}
            onstop={handleStopAgent}
            onedit={handleEditAgent}
            ondelete={handleDeleteAgent}
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
    <AgentDetailModal
      agent={$selectedAgent}
      bind:open={showDetailModal}
      performanceData={agentPerformanceData[$selectedAgent.agent_id] || []}
      holdings={agentHoldings[$selectedAgent.agent_id] || []}
      transactions={agentTransactions[$selectedAgent.agent_id] || []}
      onclose={handleDetailModalClose}
      onedit={handleAgentEdit}
      ondelete={handleDeleteAgent}
    />
  {/if}

  <!-- Notification Toast -->
  <NotificationToast />
</div>

<style>
  /* Global styles are in app.css */
</style>
