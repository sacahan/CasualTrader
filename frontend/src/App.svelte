<script>
  /**
   * App Component
   *
   * 主應用程式組件
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   */

  import { onMount, onDestroy } from "svelte";
  import { Navbar, NotificationToast } from "./components/Layout/index.js";
  import {
    AgentCreationForm,
    AgentCard,
    AgentGrid,
    StrategyHistoryView,
  } from "./components/Agent/index.js";
  import { PerformanceChart } from "./components/Chart/index.js";
  import { Button, Modal } from "./components/UI/index.js";
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
  } from "./stores/agents.js";
  import {
    connectWebSocket,
    disconnectWebSocket,
  } from "./stores/websocket.js";
  import {
    loadMarketStatus,
    startMarketDataPolling,
  } from "./stores/market.js";
  import { notifySuccess, notifyError } from "./stores/notifications.js";
  import { apiClient } from "./lib/api.js";

  // 模態視窗狀態
  let showCreateModal = false;
  let showStrategyModal = false;

  // 績效資料
  let performanceData = [];

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

  onDestroy(() => {
    // 斷開 WebSocket
    disconnectWebSocket();

    // 停止市場資料刷新
    if (stopMarketPolling) {
      stopMarketPolling();
    }
  });

  // 監聽選中的 Agent,載入績效資料
  $: if ($selectedAgent) {
    loadPerformanceData($selectedAgent.agent_id);
  }

  async function loadPerformanceData(agentId) {
    try {
      const data = await apiClient.getPerformance(agentId);
      // 假設 API 返回的績效資料包含歷史走勢
      performanceData = data.history || [];
    } catch (error) {
      console.error("Failed to load performance data:", error);
    }
  }

  // Agent 事件處理
  function handleAgentSelect(event) {
    selectAgent(event.detail.agent_id);
  }

  async function handleStartAgent(event) {
    try {
      await startAgent(event.detail.agent_id);
      notifySuccess(`Agent ${event.detail.name} 已啟動`);
    } catch (error) {
      notifyError(`啟動失敗: ${error.message}`);
    }
  }

  async function handleStopAgent(event) {
    try {
      await stopAgent(event.detail.agent_id);
      notifySuccess(`Agent ${event.detail.name} 已停止`);
    } catch (error) {
      notifyError(`停止失敗: ${error.message}`);
    }
  }

  async function handleDeleteAgent(event) {
    if (
      !confirm(
        `確定要刪除 Agent "${event.detail.name}"?\n\n此操作無法復原,所有相關資料(持倉、交易記錄、策略變更)將被永久刪除。`,
      )
    ) {
      return;
    }

    try {
      await deleteAgent(event.detail.agent_id);
      notifySuccess(`Agent ${event.detail.name} 已刪除`);
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
</script>

<div class="min-h-screen bg-gray-50">
  <!-- Navbar -->
  <Navbar title="CasualTrader - AI 股票交易模擬器" />

  <!-- Main Content -->
  <main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
    <!-- Header & Actions -->
    <div class="mb-8 flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">我的 AI Agents</h2>
        <p class="mt-1 text-sm text-gray-600">
          管理您的 AI 交易助手,監控策略演進與績效表現
        </p>
      </div>
      <Button on:click={() => (showCreateModal = true)}>
        <svg
          class="mr-2 h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
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
        on:select={handleAgentSelect}
        on:start={handleStartAgent}
        on:stop={handleStopAgent}
        on:delete={handleDeleteAgent}
      />
    </div>

    <!-- Selected Agent Details -->
    {#if $selectedAgent}
      <div class="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <!-- Performance Chart -->
        <div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">績效走勢</h3>
          </div>
          <PerformanceChart
            agentId={$selectedAgent.agent_id}
            {performanceData}
            height={350}
          />
        </div>

        <!-- Strategy History -->
        <div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">策略演進</h3>
            <Button
              variant="ghost"
              size="sm"
              on:click={handleShowStrategy}
            >
              查看完整歷史
            </Button>
          </div>
          <div class="max-h-96 overflow-y-auto">
            <StrategyHistoryView
              agentId={$selectedAgent.agent_id}
              limit={5}
            />
          </div>
        </div>
      </div>
    {/if}
  </main>

  <!-- Create Agent Modal -->
  <Modal
    bind:open={showCreateModal}
    title="創建新 Agent"
    size="lg"
  >
    <AgentCreationForm
      on:created={handleAgentCreated}
      on:cancel={() => (showCreateModal = false)}
    />
  </Modal>

  <!-- Strategy History Modal -->
  <Modal
    bind:open={showStrategyModal}
    title="策略演進完整歷史"
    size="xl"
  >
    <div class="max-h-[600px] overflow-y-auto">
      {#if $selectedAgent}
        <StrategyHistoryView
          agentId={$selectedAgent.agent_id}
          limit={50}
        />
      {/if}
    </div>
  </Modal>

  <!-- Notification Toast -->
  <NotificationToast />
</div>

<style>
  /* Global styles are in app.css */
</style>
