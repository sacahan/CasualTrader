<script>
  /**
   * Input Component
   *
   * 可重用的輸入框組件
   * Svelte 5 compatible - removes legacy createBubbler
   *
   * @typedef {Object} Props
   * @property {string} [type]
   * @property {string} [value]
   * @property {string} [placeholder]
   * @property {boolean} [disabled]
   * @property {string} [error]
   * @property {string} [label]
   * @property {boolean} [required]
   * @property {string} [id]
   * @property {Function} [oninput]
   * @property {Function} [onchange]
   * @property {Function} [onblur]
   * @property {Function} [onfocus]
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
    oninput = undefined,
    onchange = undefined,
    onblur = undefined,
    onfocus = undefined,
    ...rest
  } = $props();

  let inputId = $derived(id || `input-${Math.random().toString(36).substr(2, 9)}`);
</script>

<div class="w-full">
  {#if label}
    <label for={inputId} class="mb-1 block text-sm font-medium text-gray-300">
      {label}
      {#if required}
        <span class="text-danger-400">*</span>
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
      class="form-input block w-full rounded-lg border border-gray-600 bg-gray-700 px-4 py-2 text-white placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-800 disabled:cursor-not-allowed {error
        ? 'border-red-500'
        : ''}"
      {oninput}
      {onchange}
      {onblur}
      {onfocus}
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
      class="form-input block w-full rounded-lg border border-gray-600 bg-gray-700 px-4 py-2 text-white placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-800 disabled:cursor-not-allowed {error
        ? 'border-red-500'
        : ''}"
      oninput={(e) => {
        value = e.target.value;
        oninput?.(e);
      }}
      onchange={(e) => onchange?.(e)}
      onblur={(e) => onblur?.(e)}
      onfocus={(e) => onfocus?.(e)}
      {...rest}
    />
  {/if}

  {#if error}
    <p class="mt-1 text-sm text-danger-400">{error}</p>
  {/if}
</div>
