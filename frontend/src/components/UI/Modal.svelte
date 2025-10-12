<script>
  /**
   * Modal Component
   *
   * 模態對話框組件,支援關閉按鈕和背景點擊關閉
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   * Svelte 5 compatible - uses callback props instead of createEventDispatcher
   */

  import { onMount, onDestroy } from 'svelte';

  /**
   * @typedef {Object} Props
   * @property {boolean} [open]
   * @property {string} [title]
   * @property {string} [size] - sm | md | lg | xl | full
   * @property {boolean} [closeOnBackdrop]
   * @property {Function} [onclose]
   * @property {import('svelte').Snippet} [header]
   * @property {import('svelte').Snippet} [children]
   * @property {import('svelte').Snippet} [footer]
   */

  /** @type {Props} */
  let {
    open = $bindable(false),
    title = '',
    size = 'md',
    closeOnBackdrop = true,
    onclose = undefined,
    header,
    children,
    footer,
  } = $props();

  // 按 ESC 關閉

  // 函數定義 - 移到根層級以符合 eslint no-inner-declarations 規則
  function handleKeydown(event) {
    if (event.key === 'Escape' && open) {
      close();
    }
  }
  function close() {
    open = false;
    onclose?.();
  }
  function handleBackdropClick(event) {
    if (closeOnBackdrop && event.target === event.currentTarget) {
      close();
    }
  }

  onMount(() => {
    document.addEventListener('keydown', handleKeydown);
  });

  onDestroy(() => {
    document.removeEventListener('keydown', handleKeydown);
  });

  // Size class mapping
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-2xl',
    full: 'max-w-7xl w-full',
  };
</script>

{#if open}
  <div
    class="fixed inset-0 z-50 overflow-y-auto"
    aria-labelledby="modal-title"
    role="dialog"
    aria-modal="true"
  >
    <!-- Backdrop -->
    <div
      class="fixed inset-0 bg-black bg-opacity-75 backdrop-blur-sm transition-opacity"
      onclick={handleBackdropClick}
      onkeydown={handleKeydown}
      role="button"
      tabindex="0"
    ></div>

    <!-- Modal container -->
    <div class="flex min-h-full items-center justify-center p-4">
      <div
        class="relative w-full {sizeClasses[
          size
        ]} transform overflow-hidden rounded-2xl border border-gray-700 bg-gray-900 shadow-xl transition-all"
      >
        <!-- Header -->
        {#if title || header}
          <div class="flex items-center justify-between border-b border-gray-700 px-6 py-4">
            {#if header}
              {@render header?.()}
            {:else}
              <div class="flex-1">
                <h3 class="text-lg font-semibold text-white" id="modal-title">
                  {title}
                </h3>
              </div>
            {/if}
            {#if !header}
              <button
                type="button"
                class="ml-4 rounded-md text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                onclick={close}
              >
                <span class="sr-only">關閉</span>
                <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            {/if}
          </div>
        {/if}

        <!-- Body -->
        <div class="px-6 py-4">
          {@render children?.()}
        </div>

        <!-- Footer -->
        {#if footer}
          <div class="flex items-center justify-end gap-3 border-t border-gray-700 px-6 py-4">
            {@render footer?.()}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  /* 進入/離開動畫可以使用 Svelte transitions */
</style>
