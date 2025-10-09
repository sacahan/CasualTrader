<script>
  /**
   * Modal Component
   *
   * 模態對話框組件,支援關閉按鈕和背景點擊關閉
   * 符合 FRONTEND_IMPLEMENTATION.md 規格
   */

  import { createEventDispatcher, onMount, onDestroy } from "svelte";

  export let open = false;
  export let title = "";
  export let size = "md"; // sm | md | lg | xl
  export let closeOnBackdrop = true;

  const dispatch = createEventDispatcher();

  // 按 ESC 關閉
  function handleKeydown(event) {
    if (event.key === "Escape" && open) {
      close();
    }
  }

  function close() {
    open = false;
    dispatch("close");
  }

  function handleBackdropClick(event) {
    if (closeOnBackdrop && event.target === event.currentTarget) {
      close();
    }
  }

  onMount(() => {
    document.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    document.removeEventListener("keydown", handleKeydown);
  });

  // Size class mapping
  const sizeClasses = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
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
      class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
      on:click={handleBackdropClick}
      on:keydown={handleKeydown}
      role="button"
      tabindex="0"
    />

    <!-- Modal container -->
    <div class="flex min-h-full items-center justify-center p-4">
      <div
        class="relative w-full {sizeClasses[
          size
        ]} transform overflow-hidden rounded-lg bg-white shadow-xl transition-all"
      >
        <!-- Header -->
        {#if title || $$slots.header}
          <div
            class="flex items-center justify-between border-b border-gray-200 px-6 py-4"
          >
            <div class="flex-1">
              {#if $$slots.header}
                <slot name="header" />
              {:else}
                <h3 class="text-lg font-semibold text-gray-900" id="modal-title">
                  {title}
                </h3>
              {/if}
            </div>
            <button
              type="button"
              class="ml-4 rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
              on:click={close}
            >
              <span class="sr-only">關閉</span>
              <svg
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        {/if}

        <!-- Body -->
        <div class="px-6 py-4">
          <slot />
        </div>

        <!-- Footer -->
        {#if $$slots.footer}
          <div
            class="flex items-center justify-end gap-3 border-t border-gray-200 px-6 py-4"
          >
            <slot name="footer" />
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  /* 進入/離開動畫可以使用 Svelte transitions */
</style>
