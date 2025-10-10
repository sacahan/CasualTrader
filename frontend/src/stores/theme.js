import { writable } from 'svelte/store';

/**
 * Theme Store
 *
 * 管理應用程式主題(深色/淺色模式)
 */

// 從 localStorage 讀取保存的主題,默認為深色模式
const STORAGE_KEY = 'casualtrader-theme';
const storedTheme = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
const initialTheme = storedTheme === 'light' ? 'light' : 'dark';

// 主題狀態: 'light' | 'dark'
export const theme = writable(initialTheme);

/**
 * 切換主題
 */
export function toggleTheme() {
  theme.update((current) => {
    const newTheme = current === 'light' ? 'dark' : 'light';

    // 保存到 localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, newTheme);

      // 更新 HTML class
      if (newTheme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }

    return newTheme;
  });
}

/**
 * 設置主題
 */
export function setTheme(newTheme) {
  theme.set(newTheme);

  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, newTheme);

    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }
}

/**
 * 初始化主題(在應用啟動時調用)
 */
export function initTheme() {
  if (typeof window !== 'undefined') {
    const savedTheme = localStorage.getItem(STORAGE_KEY) || 'dark';
    setTheme(savedTheme);
  }
}
