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
    color: '34, 197, 94', // 預設綠色
  });

  // 預設顏色選項
  const colorOptions = [
    { label: '綠色 (穩健型)', value: '34, 197, 94' },
    { label: '橙色 (積極型)', value: '249, 115, 22' },
    { label: '藍色 (平衡型)', value: '59, 130, 246' },
    { label: '紫色 (保守型)', value: '168, 85, 247' },
    { label: '紅色 (高風險)', value: '239, 68, 68' },
    { label: '青色 (科技導向)', value: '6, 182, 212' },
  ];

  // 自定義顏色狀態
  let showColorPicker = $state(false);
  let customColor = $state('#22c55e'); // 預設為綠色的十六進位

  // 十六進位轉 RGB 字串
  function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
      : '34, 197, 94';
  }

  // RGB 字串轉十六進位
  function rgbToHex(rgb) {
    const parts = rgb.split(',').map((p) => parseInt(p.trim()));
    if (parts.length !== 3 || parts.some((p) => isNaN(p) || p < 0 || p > 255)) {
      return '#22c55e';
    }
    return (
      '#' +
      parts
        .map((p) => {
          const hex = p.toString(16);
          return hex.length === 1 ? '0' + hex : hex;
        })
        .join('')
    );
  }

  // 處理自定義顏色選擇
  function handleCustomColorChange(event) {
    customColor = event.target.value;
    formData.color = hexToRgb(customColor);
  }

  // 切換到自定義顏色模式
  function toggleColorPicker() {
    showColorPicker = !showColorPicker;
    if (showColorPicker) {
      customColor = rgbToHex(formData.color);
    }
  }

  // 表單驗證錯誤
  let errors = $state({
    name: '',
    description: '',
    initial_funds: '',
    max_position_size: '',
    color: '',
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
      color: '',
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

    // 驗證顏色格式 (R, G, B)
    if (formData.color && !/^\d{1,3},\s*\d{1,3},\s*\d{1,3}$/.test(formData.color)) {
      errors.color = '請輸入正確的 RGB 格式，例如: 34, 197, 94';
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
        description: formData.description.trim(), // 簡短描述，用於卡片顯示
        strategy_prompt: formData.description.trim(), // 完整策略指令，用於 Agent 執行
        initial_funds: parseFloat(formData.initial_funds),
        ai_model: formData.ai_model,
        color: formData.color, // 卡片顏色
        investment_preferences: {
          preferred_sectors: [],
          excluded_tickers: [],
          max_position_size: parseFloat(formData.max_position_size) / 100, // Convert percentage to decimal
          rebalance_frequency: 'weekly',
        },
      };

      const newAgent = await createAgent(agentData);

      // 重置表單
      resetForm();

      // 顯示成功通知
      notifySuccess(`Agent "${newAgent.name}" 創建成功!`);

      // 呼叫 oncreated callback (這會關閉對話框並重新載入列表)
      oncreated?.(newAgent);
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
      ai_model: 'gpt-5-mini', // 與初始值一致
      color: '34, 197, 94', // 預設綠色
    };
    errors = {
      name: '',
      description: '',
      initial_funds: '',
      max_position_size: '',
      color: '',
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
      min="1000"
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

  <!-- 卡片顏色選擇 -->
  <fieldset>
    <legend class="mb-2 block text-sm font-medium text-gray-700">
      卡片顏色
      <span class="text-red-500">*</span>
    </legend>

    <!-- 預設顏色選項 -->
    <div class="grid grid-cols-3 gap-3 mb-4">
      {#each colorOptions as option}
        <button
          type="button"
          class="flex items-center gap-2 rounded-lg border-2 p-3 transition-all hover:scale-105"
          class:border-gray-300={formData.color !== option.value && !showColorPicker}
          class:border-blue-500={formData.color === option.value && !showColorPicker}
          class:ring-2={formData.color === option.value && !showColorPicker}
          class:ring-blue-500={formData.color === option.value && !showColorPicker}
          onclick={() => {
            formData.color = option.value;
            showColorPicker = false;
          }}
        >
          <div class="h-8 w-8 rounded-full" style="background-color: rgb({option.value});"></div>
          <span class="text-sm font-medium text-gray-700">{option.label}</span>
        </button>
      {/each}
    </div>

    <!-- 自定義顏色選擇器 -->
    <div class="border-t border-gray-200 pt-4">
      <button
        type="button"
        class="flex items-center gap-2 rounded-lg border-2 p-3 transition-all hover:scale-105 w-full"
        class:border-gray-300={!showColorPicker}
        class:border-blue-500={showColorPicker}
        class:ring-2={showColorPicker}
        class:ring-blue-500={showColorPicker}
        onclick={toggleColorPicker}
      >
        <div class="h-8 w-8 rounded-full" style="background-color: rgb({formData.color});"></div>
        <span class="text-sm font-medium text-gray-700">自定義顏色</span>
        <svg
          class="ml-auto h-4 w-4 transform transition-transform"
          class:rotate-180={showColorPicker}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {#if showColorPicker}
        <div class="mt-3 space-y-3 rounded-lg bg-gray-50 p-4">
          <div class="flex items-center gap-3">
            <label for="color-picker" class="text-sm font-medium text-gray-700">選擇顏色:</label>
            <input
              id="color-picker"
              type="color"
              bind:value={customColor}
              oninput={handleCustomColorChange}
              class="h-10 w-16 rounded border border-gray-300 cursor-pointer"
            />
            <div class="flex-1">
              <span class="text-xs text-gray-500">RGB: {formData.color}</span>
            </div>
          </div>

          <div>
            <label for="rgb-input" class="text-sm font-medium text-gray-700">或直接輸入 RGB:</label>
            <input
              id="rgb-input"
              type="text"
              bind:value={formData.color}
              placeholder="34, 197, 94"
              class="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
      {/if}
    </div>

    {#if errors.color}
      <p class="mt-1 text-sm text-red-600">{errors.color}</p>
    {/if}
  </fieldset>

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
