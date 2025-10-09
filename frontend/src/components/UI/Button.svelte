<script>
  /**
   * Button Component
   *
   * 可重用的按鈕組件,支援多種樣式和狀態
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   */

  export let variant = "primary"; // primary | secondary | danger | ghost
  export let size = "md"; // sm | md | lg
  export let disabled = false;
  export let loading = false;
  export let fullWidth = false;
  export let type = "button";

  // 計算按鈕 class
  $: buttonClass = [
    "btn",
    `btn-${variant}`,
    `btn-${size}`,
    fullWidth && "w-full",
    disabled && "opacity-50 cursor-not-allowed",
    loading && "cursor-wait",
  ]
    .filter(Boolean)
    .join(" ");
</script>

<button
  {type}
  class={buttonClass}
  disabled={disabled || loading}
  on:click
  {...$$restProps}
>
  {#if loading}
    <svg
      class="animate-spin -ml-1 mr-2 h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  {/if}
  <slot />
</button>

<style>
  .btn {
    @apply inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2;
  }

  /* Size variants */
  .btn-sm {
    @apply px-3 py-1.5 text-sm;
  }

  .btn-md {
    @apply px-4 py-2 text-base;
  }

  .btn-lg {
    @apply px-6 py-3 text-lg;
  }

  /* Color variants */
  .btn-primary {
    @apply bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-500;
  }

  .btn-secondary {
    @apply bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500;
  }

  .btn-danger {
    @apply bg-red-500 text-white hover:bg-red-600 focus:ring-red-500;
  }

  .btn-ghost {
    @apply bg-transparent text-primary-600 hover:bg-primary-50 focus:ring-primary-500;
  }
</style>
