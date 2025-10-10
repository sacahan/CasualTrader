<script>
  /**
   * AgentCreationForm Component
   *
   * Agent 創建表單,支援 Prompt-driven 配置
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   * Svelte 5 compatible - uses callback props instead of createEventDispatcher
   */

  import { createAgent } from '../../stores/agents.js';
  import { notifySuccess, notifyError } from '../../stores/notifications.js';
  import { modelOptionsForSelect, modelsLoading, loadModels } from '../../stores/models.js';
  import { Button, Input, Select, Textarea } from '../UI/index.js';
  import { DEFAULT_INITIAL_FUNDS, DEFAULT_MAX_POSITION_SIZE } from '../../lib/constants.js';
  import { onMount } from 'svelte';

  /**
   * @typedef {Object} Props
   * @property {Function} [oncreated]
   * @property {Function} [oncancel]
   */

  /** @type {Props} */
  let { oncreated = undefined, oncancel = undefined } = $props();

  // 表單資料
  let formData = $state({
    name: '',
    description: '',
    initial_funds: DEFAULT_INITIAL_FUNDS,
    max_position_size: DEFAULT_MAX_POSITION_SIZE,
    ai_model: 'gpt-5-mini', // 默認模型,將在 onMount 中驗證
  });

  // 表單驗證錯誤
  let errors = $state({
    name: '',
    description: '',
    initial_funds: '',
    max_position_size: '',
  });

  // 提交狀態
  let submitting = $state(false);

  // 驗證表單

  // 提交表單

  // 重置表單

  // 取消

  // 在組件掛載時加載模型列表
  onMount(async () => {
    await loadModels();
  });
  // 函數定義 - 移到根層級以符合 eslint no-inner-declarations 規則
  function validateForm() {
    let isValid = true;
    errors = {
      name: '',
      description: '',
      initial_funds: '',
      max_position_size: '',
    };

    if (!formData.name.trim()) {
      errors.name = '請輸入 Agent 名稱';
      isValid = false;
    }

    if (!formData.description.trim()) {
      errors.description = '請描述您的投資偏好';
      isValid = false;
    }

    if (formData.initial_funds <= 0) {
      errors.initial_funds = '初始資金必須大於 0';
      isValid = false;
    }

    if (formData.max_position_size <= 0 || formData.max_position_size > 100) {
      errors.max_position_size = '單一持股比例須介於 1-100 之間';
      isValid = false;
    }

    return isValid;
  }
  async function handleSubmit() {
    if (!validateForm()) {
      return;
    }

    submitting = true;

    try {
      const agentData = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        initial_funds: parseFloat(formData.initial_funds),
        max_position_size: parseFloat(formData.max_position_size),
        ai_model: formData.ai_model,
      };

      const newAgent = await createAgent(agentData);

      notifySuccess(`Agent "${newAgent.name}" 創建成功!`);
      oncreated?.(newAgent);

      // 重置表單
      resetForm();
    } catch (error) {
      notifyError(`創建 Agent 失敗: ${error.message}`);
    } finally {
      submitting = false;
    }
  }
  function resetForm() {
    formData = {
      name: '',
      description: '',
      initial_funds: DEFAULT_INITIAL_FUNDS,
      max_position_size: DEFAULT_MAX_POSITION_SIZE,
      ai_model: 'gpt-5-mini',
    };
    errors = {
      name: '',
      description: '',
      initial_funds: '',
      max_position_size: '',
    };
  }
  function handleCancel() {
    resetForm();
    oncancel?.();
  }
</script>

<form
  onsubmit={(e) => {
    e.preventDefault();
    handleSubmit();
  }}
  class="space-y-6"
>
  <!-- Agent 名稱 -->
  <Input
    label="Agent 名稱"
    bind:value={formData.name}
    placeholder="例如:穩健成長型 Agent"
    error={errors.name}
    required
  />

  <!-- 投資偏好描述 (Prompt-driven) -->
  <Textarea
    label="投資偏好描述"
    bind:value={formData.description}
    placeholder="請用自然語言描述您的投資目標和風險偏好。例如:
我希望穩健成長,偏好科技股和金融股,避免過度集中單一產業。
我可以接受中等風險,目標年化報酬率 10-15%。"
    rows={6}
    error={errors.description}
    required
  />

  <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
    <!-- 初始資金 -->
    <Input
      type="number"
      label="初始資金 (TWD)"
      bind:value={formData.initial_funds}
      placeholder={DEFAULT_INITIAL_FUNDS.toString()}
      min="1"
      step="1000"
      error={errors.initial_funds}
      required
    />

    <!-- 單一持股比例上限 -->
    <Input
      type="number"
      label="單一持股比例上限 (%)"
      bind:value={formData.max_position_size}
      placeholder={DEFAULT_MAX_POSITION_SIZE.toString()}
      min="1"
      max="100"
      step="1"
      error={errors.max_position_size}
      required
    />
  </div>

  <!-- AI 模型選擇 -->
  <Select
    label="AI 模型"
    bind:value={formData.ai_model}
    optionGroups={$modelOptionsForSelect}
    disabled={$modelsLoading}
  />

  <!-- 操作按鈕 -->
  <div class="flex justify-end gap-3">
    <Button variant="secondary" onclick={handleCancel} disabled={submitting}>取消</Button>
    <Button type="submit" loading={submitting}>
      {submitting ? '創建中...' : '創建 Agent'}
    </Button>
  </div>
</form>

<style>
  /* 樣式已通過 Tailwind CSS 處理 */
</style>
