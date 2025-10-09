<script>
  /**
   * AgentCreationForm Component
   *
   * Agent 創建表單,支援 Prompt-driven 配置
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   */

  import { createEventDispatcher } from "svelte";
  import { createAgent } from "../../stores/agents.js";
  import { notifySuccess, notifyError } from "../../stores/notifications.js";
  import { Button, Input, Select, Textarea } from "../UI/index.js";
  import {
    AI_MODELS,
    AI_MODEL_LABELS,
    AI_MODEL_GROUPS,
    DEFAULT_INITIAL_FUNDS,
    DEFAULT_MAX_POSITION_SIZE,
  } from "../../lib/constants.js";

  const dispatch = createEventDispatcher();

  // 表單資料
  let formData = {
    name: "",
    description: "",
    initial_funds: DEFAULT_INITIAL_FUNDS,
    max_position_size: DEFAULT_MAX_POSITION_SIZE,
    ai_model: AI_MODELS.GPT_4O,
  };

  // 表單驗證錯誤
  let errors = {
    name: "",
    description: "",
    initial_funds: "",
    max_position_size: "",
  };

  // 提交狀態
  let submitting = false;

  // 驗證表單
  function validateForm() {
    let isValid = true;
    errors = {
      name: "",
      description: "",
      initial_funds: "",
      max_position_size: "",
    };

    if (!formData.name.trim()) {
      errors.name = "請輸入 Agent 名稱";
      isValid = false;
    }

    if (!formData.description.trim()) {
      errors.description = "請描述您的投資偏好";
      isValid = false;
    }

    if (formData.initial_funds <= 0) {
      errors.initial_funds = "初始資金必須大於 0";
      isValid = false;
    }

    if (
      formData.max_position_size <= 0 ||
      formData.max_position_size > 100
    ) {
      errors.max_position_size = "單一持股比例須介於 1-100 之間";
      isValid = false;
    }

    return isValid;
  }

  // 提交表單
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
      dispatch("created", newAgent);

      // 重置表單
      resetForm();
    } catch (error) {
      notifyError(`創建 Agent 失敗: ${error.message}`);
    } finally {
      submitting = false;
    }
  }

  // 重置表單
  function resetForm() {
    formData = {
      name: "",
      description: "",
      initial_funds: DEFAULT_INITIAL_FUNDS,
      max_position_size: DEFAULT_MAX_POSITION_SIZE,
      ai_model: AI_MODELS.GPT_4O,
    };
    errors = {
      name: "",
      description: "",
      initial_funds: "",
      max_position_size: "",
    };
  }

  // 取消
  function handleCancel() {
    resetForm();
    dispatch("cancel");
  }

  // 轉換 AI_MODEL_GROUPS 為 Select 組件格式
  $: aiModelOptions = Object.entries(AI_MODEL_GROUPS).reduce(
    (acc, [groupName, models]) => {
      acc[groupName] = models.map((model) => ({
        value: model,
        label: AI_MODEL_LABELS[model],
      }));
      return acc;
    },
    {},
  );
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-6">
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
    optionGroups={aiModelOptions}
  />

  <!-- 操作按鈕 -->
  <div class="flex justify-end gap-3">
    <Button variant="secondary" on:click={handleCancel} disabled={submitting}>
      取消
    </Button>
    <Button type="submit" loading={submitting}>
      {submitting ? "創建中..." : "創建 Agent"}
    </Button>
  </div>
</form>

<style>
  /* 樣式已通過 Tailwind CSS 處理 */
</style>
