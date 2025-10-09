<script>
  /**
   * NotificationToast Component
   *
   * 通知提示組件,顯示在畫面右上角
   */

  import { notifications, removeNotification } from "../../stores/notifications.js";

  function getTypeClasses(type) {
    switch (type) {
      case "success":
        return "bg-green-50 text-green-800 border-green-200";
      case "error":
        return "bg-red-50 text-red-800 border-red-200";
      case "warning":
        return "bg-yellow-50 text-yellow-800 border-yellow-200";
      case "info":
        return "bg-blue-50 text-blue-800 border-blue-200";
      default:
        return "bg-gray-50 text-gray-800 border-gray-200";
    }
  }

  function getTypeIcon(type) {
    switch (type) {
      case "success":
        return "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z";
      case "error":
        return "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z";
      case "warning":
        return "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z";
      case "info":
        return "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z";
      default:
        return "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z";
    }
  }
</script>

<div
  class="pointer-events-none fixed inset-0 z-50 flex flex-col items-end justify-start gap-2 p-4"
>
  {#each $notifications as notification (notification.id)}
    <div
      class="pointer-events-auto max-w-sm transform transition-all duration-300 ease-in-out"
      role="alert"
    >
      <div
        class="flex items-start gap-3 rounded-lg border p-4 shadow-lg {getTypeClasses(
          notification.type,
        )}"
      >
        <!-- Icon -->
        <svg
          class="h-5 w-5 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d={getTypeIcon(notification.type)}
          />
        </svg>

        <!-- Message -->
        <div class="flex-1 text-sm">{notification.message}</div>

        <!-- Close Button -->
        <button
          type="button"
          class="flex-shrink-0 rounded-md hover:opacity-70 focus:outline-none"
          on:click={() => removeNotification(notification.id)}
        >
          <span class="sr-only">關閉</span>
          <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  {/each}
</div>

<style>
  /* 樣式已通過 Tailwind CSS 處理 */
</style>
