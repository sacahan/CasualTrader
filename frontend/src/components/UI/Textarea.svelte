<script>
  /**
   * Textarea Component
   *
   * 可重用的多行文字輸入組件
   */

  export let value = "";
  export let placeholder = "";
  export let disabled = false;
  export let error = "";
  export let label = "";
  export let required = false;
  export let rows = 4;
  export let id = "";

  $: textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
</script>

<div class="w-full">
  {#if label}
    <label
      for={textareaId}
      class="mb-1 block text-sm font-medium text-gray-700"
    >
      {label}
      {#if required}
        <span class="text-red-500">*</span>
      {/if}
    </label>
  {/if}

  <textarea
    bind:value
    {placeholder}
    {disabled}
    {required}
    {rows}
    id={textareaId}
    class="form-input block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed {error
      ? 'border-red-500'
      : ''}"
    on:input
    on:change
    on:blur
    on:focus
    {...$$restProps}
  />

  {#if error}
    <p class="mt-1 text-sm text-red-600">{error}</p>
  {/if}
</div>
