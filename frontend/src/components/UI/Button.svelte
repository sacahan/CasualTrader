<script>
  /** @type {any} */
  let {
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    fullWidth = false,
    type = 'button',
    onclick = undefined,
    children,
    ...rest
  } = $props();

  const baseClasses =
    'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  const variantClasses = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
    secondary: 'bg-gray-600 text-white hover:bg-gray-500 focus:ring-gray-500',
    danger: 'bg-danger-500 text-white hover:bg-danger-600 focus:ring-danger-500',
    ghost: 'bg-transparent text-gray-400 hover:bg-gray-800 hover:text-white focus:ring-primary-500',
  };

  // 計算按鈕 class
  let buttonClass = $derived(
    [
      baseClasses,
      sizeClasses[size] ?? sizeClasses.md,
      variantClasses[variant] ?? variantClasses.primary,
      fullWidth && 'w-full',
      disabled && 'opacity-50 cursor-not-allowed',
      loading && 'cursor-wait',
    ]
      .filter(Boolean)
      .join(' ')
  );
</script>

<button {type} class={buttonClass} disabled={disabled || loading} {onclick} {...rest}>
  {#if loading}
    <svg
      class="animate-spin -ml-1 mr-2 h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  {/if}
  {@render children?.()}
</button>
