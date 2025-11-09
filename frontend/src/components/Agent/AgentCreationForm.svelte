<script>
  /**
   * AgentCreationForm Component
   *
   * Agent 創建表單,支援 Prompt-driven 配置
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   * Svelte 5 compatible - uses callback props instead of createEventDispatcher
   */

  import { createAgent, updateAgent } from '../../stores/agents.js';
  import { notifySuccess, notifyError } from '../../stores/notifications.js';
  import { modelOptionsForSelect, modelsLoading, loadModels } from '../../stores/models.js';
  import { Button, Input, Select, Textarea } from '../UI/index.js';
  import {
    DEFAULT_INITIAL_FUNDS,
    MIN_INITIAL_FUNDS,
    DEFAULT_MAX_POSITION_SIZE,
  } from '../../shared/constants.js';
  import { onMount } from 'svelte';

  /**
   * @typedef {Object} Props
   * @property {Function} [oncreated]
   * @property {Function} [oncancel]
   * @property {Function} [onupdated]
   * @property {Object} [agent] - 編輯模式時的 Agent 資料
   */

  /** @type {Props} */
  let {
    oncreated = undefined,
    oncancel = undefined,
    onupdated = undefined,
    agent = undefined,
  } = $props();

  // 判斷是否為編輯模式
  let isEditMode = $derived(!!agent);

  // 表單資料
  let formData = $state({
    name: '',
    description: '',
    initial_funds: DEFAULT_INITIAL_FUNDS.toString(),
    max_position_size: DEFAULT_MAX_POSITION_SIZE.toString(),
    ai_model: 'gpt-5-mini', // 默認模型,將在 onMount 中驗證
    color_theme: '34, 197, 94', // 預設綠色
    investment_preferences: '', // 偏好公司代號，以逗號分隔
  });

  // 預設顏色選項
  const colorOptions = [
    { label: '穩健型', value: '34, 197, 94' },
    { label: '積極型', value: '249, 115, 22' },
    { label: '平衡型', value: '59, 130, 246' },
    { label: '保守型', value: '168, 85, 247' },
    { label: '高風險', value: '239, 68, 68' },
    { label: '科技導向', value: '6, 182, 212' },
  ];

  // 自定義顏色狀態
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
    formData.color_theme = hexToRgb(customColor);
  }

  // 處理預設顏色選擇
  function handlePresetColorSelect(colorValue) {
    formData.color_theme = colorValue;
    // 不自動更新 customColor，讓使用者可以獨立使用兩種選擇方式
  }

  // 同步 customColor 和 formData.color_theme（避免無限迴圈）
  let lastFormDataColor = $state('');
  $effect(() => {
    // 只有當 formData.color_theme 真的改變時才處理
    if (formData.color_theme !== lastFormDataColor) {
      lastFormDataColor = formData.color_theme;

      const isPresetColor = colorOptions.some((option) => option.value === formData.color_theme);
      if (!isPresetColor) {
        // 如果當前顏色不是預設選項，則更新 customColor 以匹配
        const newHex = rgbToHex(formData.color_theme);
        if (newHex !== customColor) {
          customColor = newHex;
        }
      }
    }
  });

  // 表單驗證錯誤
  let errors = $state({
    name: '',
    description: '',
    initial_funds: '',
    max_position_size: '',
    color_theme: '',
    investment_preferences: '',
  });

  // 提交狀態
  let submitting = $state(false);

  // 驗證表單

  // 提交表單

  // 重置表單

  // 取消

  // 初始化表單資料
  function initializeFormData() {
    if (agent) {
      // 編輯模式 - 填入現有資料（agent 對象完整，無需防禦性邏輯）
      formData = {
        name: agent.name,
        description: agent.description || '',
        initial_funds: agent.initial_funds.toString(),
        max_position_size: agent.max_position_size.toString(),
        ai_model: agent.ai_model,
        color_theme: agent.color_theme,
        investment_preferences: agent.investment_preferences?.join(', ') || '',
      };

      // 在編輯模式下，同步 customColor
      //customColor = rgbToHex(formData.color_theme);
    } else {
      // 創建模式 - 使用預設值
      resetForm();
    }
  }

  // 只在 agent prop 變化時初始化表單數據
  $effect(() => {
    // 明確依賴 agent，避免因 formData 變化導致無限循環
    agent;
    initializeFormData();
  });

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
      color_theme: '',
      investment_preferences: '',
    };

    if (!formData.name.trim()) {
      errors.name = '請輸入 Agent 名稱';
      isValid = false;
    }

    if (!formData.description.trim()) {
      errors.description = '請描述您的投資偏好';
      isValid = false;
    }

    const initialFunds = parseFloat(formData.initial_funds);
    if (!isEditMode) {
      if (isNaN(initialFunds) || initialFunds <= 0) {
        errors.initial_funds = '初始資金必須大於 0';
        isValid = false;
      } else if (initialFunds < MIN_INITIAL_FUNDS) {
        errors.initial_funds = `初始資金至少需要 ${MIN_INITIAL_FUNDS.toLocaleString()} 元才能進行台股交易`;
        isValid = false;
      }
    }

    const maxPositionSize = parseFloat(formData.max_position_size);
    if (isNaN(maxPositionSize) || maxPositionSize <= 0 || maxPositionSize > 100) {
      errors.max_position_size = '單一持股比例須介於 1-100 之間';
      isValid = false;
    }

    // 驗證顏色格式 (R, G, B)
    if (formData.color_theme && !/^\d{1,3},\s*\d{1,3},\s*\d{1,3}$/.test(formData.color_theme)) {
      errors.color_theme = '請輸入正確的 RGB 格式，例如: 34, 197, 94';
      isValid = false;
    }

    // 驗證偏好公司代號格式 (可選)
    if (formData.investment_preferences.trim()) {
      const companies = formData.investment_preferences.split(',').map((c) => c.trim());
      const invalidCompanies = companies.filter((c) => !/^[A-Z0-9]{1,10}$/.test(c));
      if (invalidCompanies.length > 0) {
        errors.investment_preferences =
          '請輸入有效的股票代號 (英文數字，最多10字元)，多個代號請用逗號分隔';
        isValid = false;
      }
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
        initial_funds: parseFloat(formData.initial_funds),
        ai_model: formData.ai_model,
        color_theme: formData.color_theme, // 卡片顏色
        investment_preferences: formData.investment_preferences.trim()
          ? formData.investment_preferences.split(',').map((c) => c.trim().toUpperCase())
          : [],
        max_position_size: parseInt(formData.max_position_size), // Convert to integer percentage
      };

      if (isEditMode) {
        // 編輯模式
        const updatedAgent = await updateAgent(agent.agent_id, agentData);

        // 顯示成功通知
        notifySuccess(`Agent "${updatedAgent.name}" 更新成功!`);

        // 呼叫 onupdated callback
        onupdated?.(updatedAgent);
      } else {
        // 創建模式
        const newAgent = await createAgent(agentData);

        // 重置表單
        resetForm();

        // 顯示成功通知
        notifySuccess(`Agent "${newAgent.name}" 創建成功!`);

        // 呼叫 oncreated callback (這會關閉對話框並重新載入列表)
        oncreated?.(newAgent);
      }
    } catch (error) {
      notifyError(`${isEditMode ? '更新' : '創建'} Agent 失敗: ${error.message}`);
    } finally {
      submitting = false;
    }
  }

  function resetForm() {
    formData = {
      name: '',
      description: '',
      initial_funds: DEFAULT_INITIAL_FUNDS.toString(),
      max_position_size: DEFAULT_MAX_POSITION_SIZE.toString(),
      ai_model: 'gpt-5-mini', // 與初始值一致
      color_theme: '34, 197, 94', // 預設綠色
      investment_preferences: '', // 重置偏好公司
    };
    errors = {
      name: '',
      description: '',
      initial_funds: '',
      max_position_size: '',
      color_theme: '',
      investment_preferences: '',
    };

    // 重置 customColor 為預設綠色
    customColor = '#22c55e';
  }

  function handleCancel() {
    if (!isEditMode) {
      resetForm();
    }
    oncancel?.();
  }
</script>

<form
  onsubmit={(e) => {
    e.preventDefault();
    handleSubmit();
  }}
  class="w-full max-w-full space-y-6"
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
      disabled={isEditMode}
      required
    />
    {#if isEditMode}
      <p class="mt-1 text-sm text-gray-500">編輯模式下無法修改初始資金</p>
    {/if}

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

  <!-- 偏好公司代號 -->
  <Input
    label="偏好公司代號"
    bind:value={formData.investment_preferences}
    placeholder="例如: 2330, 2454, 0050 (多個代號請用逗號分隔)"
    error={errors.investment_preferences}
    help="可選欄位：輸入您偏好投資的股票代號，系統會優先考慮這些標的"
  />

  <!-- 卡片顏色選擇 -->
  <fieldset>
    <legend class="mb-2 block text-sm font-medium text-gray-300">
      卡片顏色
      <span class="text-red-500">*</span>
    </legend>

    <!-- 預設顏色選項 -->
    <div class="grid grid-cols-3 gap-3 mb-4">
      {#each colorOptions as option}
        <button
          type="button"
          class="flex items-center gap-2 rounded-lg border-2 p-3 transition-all hover:scale-105"
          class:border-gray-300={formData.color_theme !== option.value}
          class:border-blue-500={formData.color_theme === option.value}
          class:ring-2={formData.color_theme === option.value}
          class:ring-blue-500={formData.color_theme === option.value}
          onclick={() => handlePresetColorSelect(option.value)}
        >
          <div class="h-8 w-8 rounded-full" style="background-color: rgb({option.value});"></div>
          <span class="text-sm font-medium text-gray-300">{option.label}</span>
        </button>
      {/each}
    </div>

    <!-- 自定義顏色選擇器 -->
    <div class="border-t border-gray-200 pt-4">
      <div class="flex items-center gap-3 rounded-lg border-2 border-gray-300 p-3">
        <input
          id="color-picker"
          type="color"
          bind:value={customColor}
          oninput={handleCustomColorChange}
          class="h-8 w-8 rounded border border-gray-300 cursor-pointer"
          title="選擇自定義顏色"
        />
        <div
          class="h-8 w-8 rounded-full"
          style="background-color: rgb({formData.color_theme});"
        ></div>
        <span class="text-sm font-medium text-gray-300">自定義顏色</span>
      </div>
    </div>

    {#if errors.color_theme}
      <p class="mt-1 text-sm text-red-600">{errors.color_theme}</p>
    {/if}
  </fieldset>

  <!-- 操作按鈕 -->
  <div class="flex justify-end gap-3">
    <Button variant="secondary" onclick={handleCancel} disabled={submitting}>取消</Button>
    <Button type="submit" loading={submitting}>
      {#if isEditMode}
        {submitting ? '更新中...' : '更新 Agent'}
      {:else}
        {submitting ? '創建中...' : '創建 Agent'}
      {/if}
    </Button>
  </div>
</form>

<style>
  /* 樣式已通過 Tailwind CSS 處理 */
</style>
