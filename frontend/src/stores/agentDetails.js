import { writable, derived, get } from 'svelte/store';
import { apiClient } from '../shared/api.js';
import { extractErrorMessage } from '../shared/utils.js';

/**
 * Agent Details Store
 *
 * 管理 Agent 的詳細數據（績效、持股、交易紀錄等）
 * 支持按需加載和實時更新
 * 符合 FRONTEND_IMPLEMENTATION.md 規格
 */

// Agent 詳細數據映射: { agent_id: { performance, holdings, transactions, lastUpdated } }
export const agentDetails = writable({});

// 載入狀態映射: { agent_id: boolean }
export const detailsLoading = writable({});

// 錯誤狀態映射: { agent_id: string | null }
export const detailsError = writable({});

/**
 * 獲取特定 Agent 的詳細數據
 * 並行獲取 performance (歷史時間序列)、holdings、transactions
 *
 * @param {string} agentId - Agent ID
 * @returns {Promise<{performance: Array, holdings: Array, transactions: Array}>}
 *          performance 包含時間序列的歷史績效數據，用於圖表顯示
 */
export async function loadAgentDetails(agentId) {
  if (!agentId) return;

  // 設置加載狀態
  detailsLoading.update((state) => ({ ...state, [agentId]: true }));
  detailsError.update((state) => ({ ...state, [agentId]: null }));

  try {
    const [performance, holdings, transactions] = await Promise.all([
      apiClient.getPerformanceHistory(agentId, 30, 'asc').catch((err) => {
        console.error(`Failed to fetch performance history for ${agentId}:`, err);
        return null;
      }),
      apiClient.getHoldings(agentId).catch((err) => {
        console.error(`Failed to fetch holdings for ${agentId}:`, err);
        return null;
      }),
      apiClient.getTransactions(agentId, 50, 0).catch((err) => {
        console.error(`Failed to fetch transactions for ${agentId}:`, err);
        return null;
      }),
    ]);

    // 更新詳細數據
    // 注意：後端返回的 transactions 是一個包含 { transactions: [...] } 的對象
    const transactionsArray = transactions?.transactions || transactions || [];

    // 轉換 holdings 欄位格式
    const holdingsFormatted = (holdings || []).map((holding) => ({
      ticker: holding.ticker,
      name: holding.company_name,
      shares: holding.quantity,
      avg_price: holding.average_cost,
      total_cost: holding.total_cost,
      market_value: holding.market_value,
    }));

    // 轉換 transactions 欄位格式
    const transactionsFormatted = (Array.isArray(transactionsArray) ? transactionsArray : []).map(
      (tx) => ({
        id: tx.id,
        ticker: tx.ticker,
        company_name: tx.company_name,
        type: tx.action === 'BUY' ? 'BUY' : 'SELL',
        shares: tx.quantity,
        price: tx.price,
        total_amount: tx.total_amount,
        commission: tx.commission,
        timestamp: tx.execution_time || tx.created_at,
        status: tx.status,
      })
    );

    agentDetails.update((details) => ({
      ...details,
      [agentId]: {
        performance: Array.isArray(performance) ? performance : [],
        holdings: holdingsFormatted,
        transactions: transactionsFormatted,
        lastUpdated: new Date().toISOString(),
      },
    }));

    return { performance, holdings, transactions };
  } catch (error) {
    const errorMessage = extractErrorMessage(error);
    console.error(`Failed to load details for agent ${agentId}:`, error);
    detailsError.update((state) => ({
      ...state,
      [agentId]: errorMessage,
    }));
    throw error;
  } finally {
    // 清除加載狀態
    detailsLoading.update((state) => ({ ...state, [agentId]: false }));
  }
}

/**
 * 刷新特定 Agent 的詳細數據
 * 別名：用於執行後的數據刷新（WebSocket 事件後）
 *
 * @param {string} agentId - Agent ID
 */
export async function refreshAgentDetails(agentId) {
  await loadAgentDetails(agentId);
}

/**
 * 批量刷新多個 Agent 的詳細數據
 *
 * @param {string[]} agentIds - Agent ID 數組
 */
export async function refreshMultipleAgentDetails(agentIds) {
  await Promise.all(agentIds.map((id) => loadAgentDetails(id)));
}

/**
 * 衍生 store：獲取特定 Agent 的詳細數據
 *
 * @param {string} agentId - Agent ID
 */
export function getAgentDetailsDerived(agentId) {
  return derived(agentDetails, ($details) => $details[agentId] || {});
}

/**
 * 獲取特定 Agent 的性能數據衍生 store
 *
 * @param {string} agentId - Agent ID
 */
export function getAgentPerformanceDerived(agentId) {
  return derived(agentDetails, ($details) => $details[agentId]?.performance || {});
}

/**
 * 獲取特定 Agent 的持股數據衍生 store
 *
 * @param {string} agentId - Agent ID
 */
export function getAgentHoldingsDerived(agentId) {
  return derived(agentDetails, ($details) => $details[agentId]?.holdings || []);
}

/**
 * 獲取特定 Agent 的交易紀錄衍生 store
 *
 * @param {string} agentId - Agent ID
 */
export function getAgentTransactionsDerived(agentId) {
  return derived(agentDetails, ($details) => $details[agentId]?.transactions || []);
}

/**
 * 清除特定 Agent 的詳細數據
 *
 * @param {string} agentId - Agent ID
 */
export function clearAgentDetails(agentId) {
  agentDetails.update((details) => {
    const newDetails = { ...details };
    delete newDetails[agentId];
    return newDetails;
  });

  detailsLoading.update((state) => {
    const newState = { ...state };
    delete newState[agentId];
    return newState;
  });

  detailsError.update((state) => {
    const newState = { ...state };
    delete newState[agentId];
    return newState;
  });
}

/**
 * 清除所有 Agent 的詳細數據
 */
export function clearAllAgentDetails() {
  agentDetails.set({});
  detailsLoading.set({});
  detailsError.set({});
}

/**
 * 獲取特定 Agent 詳細數據的同步值
 * 用於在事件處理器中快速存取
 *
 * @param {string} agentId - Agent ID
 * @returns {Object}
 */
export function getAgentDetailsSync(agentId) {
  const details = get(agentDetails);
  return details[agentId] || {};
}

/**
 * 檢查特定 Agent 的詳細數據是否已加載
 *
 * @param {string} agentId - Agent ID
 * @returns {boolean}
 */
export function isAgentDetailsLoaded(agentId) {
  return !!get(agentDetails)[agentId];
}
