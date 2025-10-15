import { writable, derived } from 'svelte/store';
import { apiClient } from '../shared/api.js';
import { extractErrorMessage } from '../shared/utils.js';

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

// 股票報價快取 { ticker: quote }
export const stockQuotes = writable({});

// 載入狀態
export const loading = writable(false);

// 錯誤訊息
export const error = writable(null);

// 衍生 store: 市場是否開盤
// 完全依賴後端 API 的市場狀態判斷（包含節假日偵測）
export const isOpen = derived(marketStatus, ($marketStatus) => {
  if (!$marketStatus) return false;
  return $marketStatus.is_trading_hours || false;
});

// 衍生 store: 市場狀態描述
export const marketStatusText = derived(marketStatus, ($marketStatus) => {
  if (!$marketStatus) return '載入中...';

  const statusMap = {
    open: '開盤中',
    pre_market: '盤前',
    after_market: '盤後',
    closed: '休市',
    weekend: '週末休市',
    holiday: `休市 - ${$marketStatus.holiday_name || '國定假日'}`,
  };

  return statusMap[$marketStatus.status] || '未知狀態';
});

// 衍生 store: 是否為節假日
export const isHoliday = derived(marketStatus, ($marketStatus) => {
  if (!$marketStatus) return false;
  return $marketStatus.is_holiday || false;
});

// 衍生 store: 是否為交易日
export const isTradingDay = derived(marketStatus, ($marketStatus) => {
  if (!$marketStatus) return false;
  return $marketStatus.is_trading_day || false;
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
export async function loadStockQuote(ticker) {
  loading.set(true);
  error.set(null);

  try {
    const quote = await apiClient.getStockQuote(ticker);

    // 更新快取
    stockQuotes.update((quotes) => ({
      ...quotes,
      [ticker]: quote,
    }));

    return quote;
  } catch (err) {
    error.set(extractErrorMessage(err));
    console.error(`Failed to load quote for ${ticker}:`, err);
    throw err;
  } finally {
    loading.set(false);
  }
}

/**
 * 批量載入股票報價
 */
export async function loadStockQuotes(tickers) {
  const promises = tickers.map((ticker) => loadStockQuote(ticker));

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
export function getCachedQuote(ticker) {
  let quotes;
  stockQuotes.subscribe((value) => {
    quotes = value;
  })();
  return quotes[ticker] || null;
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
  // TODO: 後端尚未實作 market indices 端點
  // loadMarketIndices();

  // 設定定時刷新
  const timerId = setInterval(() => {
    loadMarketStatus();
    // TODO: 後端尚未實作 market indices 端點
    // loadMarketIndices();
  }, interval);

  // 返回停止函數
  return () => {
    clearInterval(timerId);
  };
}
