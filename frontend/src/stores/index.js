/**
 * Stores Index
 *
 * 統一匯出所有 stores 和相關函數
 */

// Agent Store
export {
  agents,
  selectedAgentId,
  selectedAgent,
  runningAgents,
  idleAgents,
  loading as agentsLoading,
  error as agentsError,
  loadAgents,
  loadAgent,
  createAgent,
  updateAgent,
  deleteAgent,
  startAgent,
  stopAgent,
  executeAgent,
  switchAgentMode,
  resetAgent,
  selectAgent,
  clearSelection,
  clearError as clearAgentsError,
  isAgentEditable,
} from "./agents.js";

// WebSocket Store
export {
  connected,
  lastMessage,
  connectWebSocket,
  disconnectWebSocket,
  sendMessage,
  addEventListener,
  removeEventListener,
  clearAllEventListeners,
} from "./websocket.js";

// Market Store
export {
  marketStatus,
  marketIndices,
  stockQuotes,
  isOpen,
  nextOpenTime,
  loading as marketLoading,
  error as marketError,
  loadMarketStatus,
  loadMarketIndices,
  loadStockQuote,
  loadStockQuotes,
  getCachedQuote,
  clearQuotesCache,
  clearError as clearMarketError,
  startMarketDataPolling,
} from "./market.js";

// Notifications Store
export {
  notifications,
  addNotification,
  removeNotification,
  clearAllNotifications,
  notifySuccess,
  notifyError,
  notifyWarning,
  notifyInfo,
} from "./notifications.js";
