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
  import { AgentCreationForm, AgentGrid, StrategyHistoryView } from './components/Agent/index.js';
  import { PerformanceChart } from './components/Chart/index.js';
  import { Button, Modal } from './components/UI/index.js';
  import {
    agents,
    selectedAgentId,
    selectedAgent,
    loading as agentsLoading,
    loadAgents,
    startAgent,
    stopAgent,
    deleteAgent,
    selectAgent,
  } from './stores/agents.js';
  import { connectWebSocket, disconnectWebSocket } from './stores/websocket.js';
  import { loadMarketStatus, startMarketDataPolling } from './stores/market.js';
  import { notifySuccess, notifyError } from './stores/notifications.js';
  import { apiClient } from './lib/api.js';

  // 模態視窗狀態
  let showCreateModal = $state(false);
  let showStrategyModal = $state(false);

  // 績效資料
  let performanceData = $state([]);

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
  async function loadPerformanceData(agentId) {
    try {
      const data = await apiClient.getPerformance(agentId);
      // 假設 API 返回的績效資料包含歷史走勢
      performanceData = data.history || [];
    } catch (error) {
      console.error('Failed to load performance data:', error);
    }
  }

  // Agent 事件處理 - updated for Svelte 5 callback props
  function handleAgentSelect(agent) {
    selectAgent(agent.agent_id);
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

  function handleShowStrategy() {
    if ($selectedAgent) {
      showStrategyModal = true;
    }
  }

  onDestroy(() => {
    // 斷開 WebSocket
    disconnectWebSocket();

    // 停止市場資料刷新
    if (stopMarketPolling) {
      stopMarketPolling();
    }
  });

  // 監聽選中的 Agent,載入績效資料
  $effect(() => {
    if ($selectedAgent) {
      loadPerformanceData($selectedAgent.agent_id);
    }
  });
</script>

<div class="min-h-screen bg-gray-900">
  <!-- Navbar -->
  <Navbar title="CasualTrader - 股票代理人交易模擬" />

  <!-- Main Content -->
  <main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
    <!-- Header & Actions -->
    <div class="mb-8 flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">我的 AI Agents</h2>
        <p class="mt-1 text-sm text-gray-400">管理您的 AI 交易助手,監控策略演進與績效表現</p>
      </div>
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

    <!-- Agent Grid -->
    <div class="mb-8">
      <AgentGrid
        agents={$agents}
        selectedAgentId={$selectedAgentId}
        loading={$agentsLoading}
        onselect={handleAgentSelect}
        onstart={handleStartAgent}
        onstop={handleStopAgent}
        ondelete={handleDeleteAgent}
      />
    </div>

    <!-- Selected Agent Details -->
    {#if $selectedAgent}
      <div class="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <!-- Performance Chart -->
        <div class="rounded-2xl border border-gray-700 bg-gray-800 p-6 shadow-lg">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-white">績效走勢</h3>
          </div>
          <PerformanceChart agentId={$selectedAgent.agent_id} {performanceData} height={350} />
        </div>

        <!-- Strategy History -->
        <div class="rounded-2xl border border-gray-700 bg-gray-800 p-6 shadow-lg">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-white">策略演進</h3>
            <Button variant="ghost" size="sm" onclick={handleShowStrategy}>查看完整歷史</Button>
          </div>
          <div class="custom-scrollbar max-h-96 overflow-y-auto">
            <StrategyHistoryView agentId={$selectedAgent.agent_id} limit={5} />
          </div>
        </div>
      </div>
    {/if}
  </main>

  <!-- Create Agent Modal -->
  <Modal bind:open={showCreateModal} title="創建新 Agent" size="lg">
    <AgentCreationForm oncreated={handleAgentCreated} oncancel={() => (showCreateModal = false)} />
  </Modal>

  <!-- Strategy History Modal -->
  <Modal bind:open={showStrategyModal} title="策略演進完整歷史" size="xl">
    <div class="max-h-[600px] overflow-y-auto">
      {#if $selectedAgent}
        <StrategyHistoryView agentId={$selectedAgent.agent_id} limit={50} />
      {/if}
    </div>
  </Modal>

  <!-- Notification Toast -->
  <NotificationToast />
</div>

<style>
  /* Global styles are in app.css */
</style>
