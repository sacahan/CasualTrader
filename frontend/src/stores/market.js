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
  return $marketStatus.is_open || false;
});

// 衍生 store: 市場狀態描述
export const marketStatusText = derived(marketStatus, ($marketStatus) => {
  if (!$marketStatus) return '載入中...';

  // 根據後端 API 實際回傳的欄位判斷狀態
  if ($marketStatus.is_holiday) {
    return `休市 - ${$marketStatus.holiday_name || '國定假日'}`;
  }

  if ($marketStatus.is_weekend) {
    return '週末休市';
  }

  if (!$marketStatus.is_trading_day) {
    return '休市';
  }

  if ($marketStatus.is_open) {
    return '開盤中';
  }

  // 是交易日但未開盤，判斷是盤前還是盤後
  const currentTime = $marketStatus.current_time || '';
  if (currentTime && currentTime < '09:00:00') {
    return '盤前';
  }

  if (currentTime && currentTime > '13:30:00') {
    return '盤後';
  }

  return '休市';
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

// 衍生 store: 發行量加權指數（大盤指數）
export const twseIndex = derived(marketIndices, ($marketIndices) => {
  if (!$marketIndices || $marketIndices.length === 0) return null;

  // 從指數列表中找到"發行量加權股價指數"
  const index = $marketIndices.find((idx) => idx['指數'] === '發行量加權股價指數');

  if (!index) return null;

  // 將資料轉換為前端易用的格式
  return {
    index_name: index['指數'],
    current_value: parseFloat(index['收盤指數']),
    change: index['漲跌'] === '+' ? parseFloat(index['漲跌點數']) : -parseFloat(index['漲跌點數']),
    change_percent: parseFloat(index['漲跌百分比']),
    date: index['日期'],
  };
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
    const result = await apiClient.getMarketIndices();
    // 後端回傳格式: { success: true, data: { 日期, 指數, 收盤指數, ... }, tool: "index_info" }
    // 轉換為陣列格式以便 twseIndex 衍生 store 處理
    const indicesArray = result.data ? [result.data] : [];
    marketIndices.set(indicesArray);
    return result;
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
  let quotes = {};
  const unsubscribe = stockQuotes.subscribe((value) => {
    quotes = value;
  });
  unsubscribe();
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
