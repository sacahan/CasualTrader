import { writable } from 'svelte/store';
import { generateId } from '../lib/utils.js';

/**
 * Notifications Store
 *
 * 管理全域通知訊息,支援自動消失和手動關閉
 * 符合 FRONTEND_IMPLEMENTATION.md 規格
 */

// 通知列表
export const notifications = writable([]);

/**
 * 添加通知
 * @param {Object} notification - 通知物件
 * @param {string} notification.type - 類型: success | error | warning | info
 * @param {string} notification.message - 訊息內容
 * @param {number} [notification.duration=5000] - 顯示時長(毫秒),0 表示不自動關閉
 */
export function addNotification({ type, message, duration = 5000 }) {
  const id = generateId();
  const timestamp = new Date();

  const notification = {
    id,
    type,
    message,
    timestamp,
    duration,
  };

  // 添加到列表
  notifications.update((list) => [...list, notification]);

  // 如果設定了 duration,自動移除
  if (duration > 0) {
    setTimeout(() => {
      removeNotification(id);
    }, duration);
  }

  return id;
}

/**
 * 移除通知
 */
export function removeNotification(id) {
  notifications.update((list) => list.filter((n) => n.id !== id));
}

/**
 * 清除所有通知
 */
export function clearAllNotifications() {
  notifications.set([]);
}

/**
 * 便捷方法:添加成功通知
 */
export function notifySuccess(message, duration = 3000) {
  return addNotification({ type: 'success', message, duration });
}

/**
 * 便捷方法:添加錯誤通知
 */
export function notifyError(message, duration = 0) {
  // 錯誤通知預設不自動關閉
  return addNotification({ type: 'error', message, duration });
}

/**
 * 便捷方法:添加警告通知
 */
export function notifyWarning(message, duration = 5000) {
  return addNotification({ type: 'warning', message, duration });
}

/**
 * 便捷方法:添加資訊通知
 */
export function notifyInfo(message, duration = 3000) {
  return addNotification({ type: 'info', message, duration });
}
