<!-- @migration-task Error while migrating Svelte code: Event modifiers other than 'once' can only be used on DOM elements
https://svelte.dev/e/event_handler_invalid_component_modifier -->
<script>
  /**
   * AgentCard Component
   *
   * Agent 卡片組件,顯示 Agent 基本資訊、狀態和操作按鈕
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   */

  import { createEventDispatcher } from 'svelte';
  import { Button, StatusIndicator } from '../UI/index.js';
  import { AI_MODEL_LABELS, AGENT_STATUS } from '../../lib/constants.js';
  import { formatCurrency, formatDateTime } from '../../lib/utils.js';

  export let agent;
  export let selected = false;

  const dispatch = createEventDispatcher();

  // 卡片操作事件
  function handleClick() {
    dispatch('click', agent);
  }

  function handleStart() {
    dispatch('start', agent);
  }

  function handleStop() {
    dispatch('stop', agent);
  }

  function handleDelete() {
    dispatch('delete', agent);
  }

  // 是否可以編輯 (執行中不可編輯 - 配置鎖定)
  $: isEditable = agent.status !== AGENT_STATUS.RUNNING;

  // 是否可以啟動
  $: canStart = agent.status === AGENT_STATUS.IDLE || agent.status === AGENT_STATUS.STOPPED;

  // 是否可以停止
  $: canStop = agent.status === AGENT_STATUS.RUNNING;
</script>

<div
  class="relative rounded-lg border bg-white p-6 shadow-sm transition-all hover:shadow-md {selected
    ? 'border-primary-500 ring-2 ring-primary-500'
    : 'border-gray-200'}"
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabindex="0"
>
  <!-- 選中指示器 -->
  {#if selected}
    <div class="absolute right-4 top-4">
      <svg class="h-6 w-6 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
        <path
          fill-rule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
          clip-rule="evenodd"
        />
      </svg>
    </div>
  {/if}

  <!-- Agent 標題 -->
  <div class="mb-4">
    <h3 class="text-lg font-semibold text-gray-900">{agent.name}</h3>
    <p class="mt-1 text-sm text-gray-500">
      {AI_MODEL_LABELS[agent.ai_model] || agent.ai_model}
    </p>
  </div>

  <!-- 狀態指示器 -->
  <div class="mb-4 flex items-center gap-2">
    <StatusIndicator status={agent.status} />
    {#if agent.current_mode}
      <StatusIndicator mode={agent.current_mode} />
    {/if}
  </div>

  <!-- 投資偏好描述 -->
  <p class="mb-4 line-clamp-3 text-sm text-gray-700">
    {agent.description || '無描述'}
  </p>

  <!-- Agent 資訊 -->
  <div class="mb-4 space-y-2 text-sm">
    <div class="flex justify-between">
      <span class="text-gray-600">初始資金:</span>
      <span class="font-medium text-gray-900">
        {formatCurrency(agent.initial_funds)}
      </span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-600">單一持股上限:</span>
      <span class="font-medium text-gray-900">
        {agent.max_position_size}%
      </span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-600">創建時間:</span>
      <span class="font-medium text-gray-900">
        {formatDateTime(agent.created_at)}
      </span>
    </div>
  </div>

  <!-- 配置鎖定提示 -->
  {#if !isEditable}
    <div
      class="mb-4 flex items-center gap-2 rounded-md bg-yellow-50 px-3 py-2 text-xs text-yellow-800"
    >
      <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
        <path
          fill-rule="evenodd"
          d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
          clip-rule="evenodd"
        />
      </svg>
      <span>執行中無法編輯配置</span>
    </div>
  {/if}

  <!-- 操作按鈕 -->
  <div class="flex gap-2">
    {#if canStart}
      <Button variant="primary" size="sm" fullWidth on:click={(e) => { e.stopPropagation(); handleStart(e); }}>
        啟動
      </Button>
    {/if}

    {#if canStop}
      <Button variant="secondary" size="sm" fullWidth on:click={(e) => { e.stopPropagation(); handleStop(e); }}>
        停止
      </Button>
    {/if}

    <Button
      variant="danger"
      size="sm"
      on:click={(e) => { e.stopPropagation(); handleDelete(e); }}
      disabled={!isEditable}
    >
      刪除
    </Button>
  </div>
</div>

<style>
  /* Line clamp utility */
  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
