<script>
  /**
   * Textarea Component
   *
   * 可重用的多行文字輸入組件
   * Svelte 5 compatible - removes legacy createBubbler
   */

  /** @type {any} */
  let {
    value = $bindable(''),
    placeholder = '',
    disabled = false,
    error = '',
    label = '',
    required = false,
    rows = 4,
    id = '',
    oninput = undefined,
    onchange = undefined,
    onblur = undefined,
    onfocus = undefined,
    ...rest
  } = $props();

  let textareaId = $derived(id || `textarea-${Math.random().toString(36).substr(2, 9)}`);
</script>

<div class="w-full">
  {#if label}
    <label for={textareaId} class="mb-1 block text-sm font-medium text-gray-300">
      {label}
      {#if required}
        <span class="text-danger-400">*</span>
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
    class="form-input block w-full rounded-lg border border-gray-600 bg-gray-700 px-4 py-2 text-white placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-800 disabled:cursor-not-allowed {error
      ? 'border-red-500'
      : ''}"
    {onchange}
    {onblur}
    {onfocus}
    oninput={(e) => {
      oninput?.(e);
    }}
    {...rest}
  ></textarea>

  {#if error}
    <p class="mt-1 text-sm text-danger-400">{error}</p>
  {/if}
</div>
