<script>
  /**
   * Select Component
   *
   * 可重用的下拉選擇組件
   */

  export let value = "";
  export let options = []; // [{ value, label }]
  export let optionGroups = null; // { groupName: [options] }
  export let placeholder = "請選擇...";
  export let disabled = false;
  export let error = "";
  export let label = "";
  export let required = false;
  export let id = "";

  $: selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;
</script>

<div class="w-full">
  {#if label}
    <label
      for={selectId}
      class="mb-1 block text-sm font-medium text-gray-700"
    >
      {label}
      {#if required}
        <span class="text-red-500">*</span>
      {/if}
    </label>
  {/if}

  <select
    bind:value
    {disabled}
    {required}
    id={selectId}
    class="form-input block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed {error
      ? 'border-red-500'
      : ''}"
    on:change
    on:blur
    on:focus
    {...$$restProps}
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
    <p class="mt-1 text-sm text-red-600">{error}</p>
  {/if}
</div>
