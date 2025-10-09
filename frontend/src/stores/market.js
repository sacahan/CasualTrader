import { writable, derived } from 'svelte/store';
import { apiClient } from '../lib/api.js';
import { extractErrorMessage, isMarketOpen } from '../lib/utils.js';

/**
 * Market Store
 *
 * 管理市場狀態和行情資料
 * 符合 FRONTEND_IMPLEMENTATION.md 規格
 */

// 市場狀態資料
export const marketStatus = writable(null);

// 市場指數資料
export const marketIndices = writable([]);

// 股票報價快取 { symbol: quote }
export const stockQuotes = writable({});

// 載入狀態
export const loading = writable(false);

// 錯誤訊息
export const error = writable(null);

// 衍生 store: 市場是否開盤
export const isOpen = derived(marketStatus, ($marketStatus) => {
  if (!$marketStatus) return isMarketOpen(); // 使用本地判斷作為預設
  return $marketStatus.is_open || false;
});

// 衍生 store: 下次開盤時間
export const nextOpenTime = derived(marketStatus, ($marketStatus) => {
  if (!$marketStatus) return null;
  return $marketStatus.next_open_time || null;
});

/**
 * 載入市場狀態
 */
export async function loadMarketStatus() {
  loading.set(true);
  error.set(null);

  try {
    const data = await apiClient.getMarketStatus();
    marketStatus.set(data);
    return data;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to load market status:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 載入市場指數
 */
export async function loadMarketIndices() {
  loading.set(true);
  error.set(null);

  try {
    const data = await apiClient.getMarketIndices();
    marketIndices.set(data.indices || []);
    return data;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error('Failed to load market indices:', err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 載入股票報價
 */
export async function loadStockQuote(symbol) {
  loading.set(true);
  error.set(null);

  try {
    const quote = await apiClient.getStockQuote(symbol);

    // 更新快取
    stockQuotes.update((quotes) => ({
      ...quotes,
      [symbol]: quote,
    }));

    return quote;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error(`Failed to load quote for ${symbol}:`, err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 批量載入股票報價
 */
export async function loadStockQuotes(symbols) {
  const promises = symbols.map((symbol) => loadStockQuote(symbol));

  try {
    const quotes = await Promise.allSettled(promises);
    return quotes.filter((result) => result.status === 'fulfilled').map((result) => result.value);
  } catch (err) {
    console.error('Failed to load stock quotes:', err);
    throw err;
  }
}

/**
 * 從快取中取得股票報價
 */
export function getCachedQuote(symbol) {
  let quotes;
  stockQuotes.subscribe((value) => {
    quotes = value;
  })();
  return quotes[symbol] || null;
}

/**
 * 清除股票報價快取
 */
export function clearQuotesCache() {
  stockQuotes.set({});
}

/**
 * 清除錯誤訊息
 */
export function clearError() {
  error.set(null);
}

/**
 * 啟動市場資料自動刷新
 * @param {number} interval - 刷新間隔(毫秒),預設 30 秒
 */
export function startMarketDataPolling(interval = 30000) {
  // 立即載入一次
  loadMarketStatus();
  loadMarketIndices();

  // 設定定時刷新
  const timerId = setInterval(() => {
    loadMarketStatus();
    loadMarketIndices();
  }, interval);

  // 返回停止函數
  return () => {
    clearInterval(timerId);
  };
}
