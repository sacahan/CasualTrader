<script>
  /**
   * Select Component
   *
   * 可重用的下拉選擇組件
   * Svelte 5 compatible - removes legacy createBubbler
   *
   * @typedef {Object} Props
   * @property {string} [value]
   * @property {any} [options] - [{ value, label }]
   * @property {any} [optionGroups] - { groupName: [options] }
   * @property {string} [placeholder]
   * @property {boolean} [disabled]
   * @property {string} [error]
   * @property {string} [label]
   * @property {boolean} [required]
   * @property {string} [id]
   * @property {Function} [onchange]
   * @property {Function} [onblur]
   * @property {Function} [onfocus]
   */

  /** @type {Props & { [key: string]: any }} */
  let {
    value = $bindable(''),
    options = [],
    optionGroups = null,
    placeholder = '請選擇...',
    disabled = false,
    error = '',
    label = '',
    required = false,
    id = '',
    onchange = undefined,
    onblur = undefined,
    onfocus = undefined,
    ...rest
  } = $props();

  let selectId = $derived(id || `select-${Math.random().toString(36).substr(2, 9)}`);
</script>

<div class="w-full">
  {#if label}
    <label for={selectId} class="mb-1 block text-sm font-medium text-gray-300">
      {label}
      {#if required}
        <span class="text-danger-400">*</span>
      {/if}
    </label>
  {/if}

  <select
    bind:value
    {disabled}
    {required}
    id={selectId}
    class="form-input block w-full rounded-lg border border-gray-600 bg-gray-700 px-4 py-2 text-white focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-800 disabled:cursor-not-allowed {error
      ? 'border-red-500'
      : ''}"
    {onchange}
    {onblur}
    {onfocus}
    {...rest}
  >
    {#if placeholder}
      <option value="" disabled selected={!value}>{placeholder}</option>
    {/if}

    {#if optionGroups}
      {#each Object.entries(optionGroups) as [groupName, groupOptions]}
        <optgroup label={groupName}>
          {#each groupOptions as option}
            <option value={option.value || option}>
              {option.label || option}
            </option>
          {/each}
        </optgroup>
      {/each}
    {:else}
      {#each options as option}
        <option value={option.value || option}>
          {option.label || option}
        </option>
      {/each}
    {/if}
  </select>

  {#if error}
    <p class="mt-1 text-sm text-danger-400">{error}</p>
  {/if}
</div>
