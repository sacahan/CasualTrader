<script>
  import { createBubbler } from 'svelte/legacy';

  const bubble = createBubbler();
  

  /**
   * @typedef {Object} Props
   * @property {string} [type] - Input Component
可重用的輸入框組件
   * @property {string} [value]
   * @property {string} [placeholder]
   * @property {boolean} [disabled]
   * @property {string} [error]
   * @property {string} [label]
   * @property {boolean} [required]
   * @property {string} [id]
   */

  /** @type {Props & { [key: string]: any }} */
  let {
    type = 'text',
    value = $bindable(''),
    placeholder = '',
    disabled = false,
    error = '',
    label = '',
    required = false,
    id = '',
    ...rest
  } = $props();

  let inputId = $derived(id || `input-${Math.random().toString(36).substr(2, 9)}`);
</script>

<div class="w-full">
  {#if label}
    <label for={inputId} class="mb-1 block text-sm font-medium text-gray-700">
      {label}
      {#if required}
        <span class="text-red-500">*</span>
      {/if}
    </label>
  {/if}

  {#if type === 'text' || type === 'email' || type === 'password' || type === 'number' || type === 'tel' || type === 'url'}
    <input
      {type}
      bind:value
      {placeholder}
      {disabled}
      {required}
      id={inputId}
      class="form-input block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed {error
        ? 'border-red-500'
        : ''}"
      oninput={bubble('input')}
      onchange={bubble('change')}
      onblur={bubble('blur')}
      onfocus={bubble('focus')}
      {...rest}
    />
  {:else}
    <!-- 為其他 type 使用非綁定方式 -->
    <input
      {type}
      {value}
      {placeholder}
      {disabled}
      {required}
      id={inputId}
      class="form-input block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed {error
        ? 'border-red-500'
        : ''}"
      oninput={(e) => (value = e.target.value)}
      onchange={bubble('change')}
      onblur={bubble('blur')}
      onfocus={bubble('focus')}
      {...rest}
    />
  {/if}

  {#if error}
    <p class="mt-1 text-sm text-red-600">{error}</p>
  {/if}
</div>
