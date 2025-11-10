import { writable } from 'svelte/store';
import {
  WS_URL,
  WS_EVENT_TYPES,
  MAX_RECONNECT_ATTEMPTS,
  RECONNECT_DELAY_MS,
} from '../shared/constants.js';
import { agents } from './agents.js';
import { addNotification } from './notifications.js';

/**
 * WebSocket Store
 *
 * 管理 WebSocket 連接,處理即時事件和自動重連
 * 符合 FRONTEND_IMPLEMENTATION.md 規格
 */

// WebSocket 實例
let wsInstance = null;

// 重連計數器
let reconnectAttempts = 0;

// 重連計時器
let reconnectTimer = null;

// 連接狀態
export const connected = writable(false);

// 最後收到的訊息
export const lastMessage = writable(null);

// 事件監聽器映射 { eventType: [callbacks] }
const eventListeners = new Map();

/**
 * 連接到 WebSocket 伺服器
 */
export function connectWebSocket() {
  if (wsInstance && wsInstance.readyState === WebSocket.OPEN) {
    console.warn('WebSocket already connected');
    return;
  }

  try {
    wsInstance = new WebSocket(WS_URL);

    wsInstance.onopen = handleOpen;
    wsInstance.onmessage = handleMessage;
    wsInstance.onerror = handleError;
    wsInstance.onclose = handleClose;
  } catch (error) {
    console.error('Failed to create WebSocket:', error);
    scheduleReconnect();
  }
}

/**
 * 處理 WebSocket 連接成功
 */
function handleOpen(_event) {
  console.warn('WebSocket connected'); // 改用 console.warn 以符合 eslint 規則
  connected.set(true);
  reconnectAttempts = 0;

  addNotification({
    type: 'success',
    message: '已連接到即時更新伺服器',
  });
}

/**
 * 處理收到的訊息
 */
function handleMessage(event) {
  try {
    const data = JSON.parse(event.data);
    lastMessage.set(data);

    // 根據事件類型分發
    handleEvent(data);
  } catch (error) {
    console.error('Failed to parse WebSocket message:', error);
  }
}

/**
 * 處理 WebSocket 錯誤
 */
function handleError(event) {
  console.error('WebSocket error:', event);
  addNotification({
    type: 'error',
    message: '即時連接發生錯誤',
  });
}

/**
 * 處理 WebSocket 關閉
 */
function handleClose(event) {
  console.warn('WebSocket closed:', event.code, event.reason);
  connected.set(false);

  if (!event.wasClean) {
    addNotification({
      type: 'warning',
      message: '與伺服器的連接已中斷,正在嘗試重新連接...',
    });
    scheduleReconnect();
  }
}

/**
 * 排程重新連接
 */
function scheduleReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.error('Max reconnect attempts reached');
    addNotification({
      type: 'error',
      message: `無法重新連接到伺服器 (已嘗試 ${MAX_RECONNECT_ATTEMPTS} 次)`,
    });
    return;
  }

  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
  }

  const delay = RECONNECT_DELAY_MS * Math.pow(2, reconnectAttempts); // 指數退避
  console.warn(`Scheduling reconnect in ${delay}ms (attempt ${reconnectAttempts + 1})`);

  reconnectTimer = setTimeout(() => {
    reconnectAttempts++;
    connectWebSocket();
  }, delay);
}

/**
 * 斷開 WebSocket 連接
 */
export function disconnectWebSocket() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  if (wsInstance) {
    wsInstance.close(1000, 'Client disconnected');
    wsInstance = null;
  }

  connected.set(false);
  reconnectAttempts = 0;
}

/**
 * 發送訊息到伺服器
 */
export function sendMessage(data) {
  if (!wsInstance || wsInstance.readyState !== WebSocket.OPEN) {
    console.error('WebSocket not connected');
    return false;
  }

  try {
    wsInstance.send(JSON.stringify(data));
    return true;
  } catch (error) {
    console.error('Failed to send WebSocket message:', error);
    return false;
  }
}

/**
 * 註冊事件監聽器
 */
export function addEventListener(eventType, callback) {
  if (!eventListeners.has(eventType)) {
    eventListeners.set(eventType, []);
  }
  eventListeners.get(eventType).push(callback);

  // 返回取消註冊函數
  return () => {
    const listeners = eventListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  };
}

/**
 * 移除事件監聽器
 */
export function removeEventListener(eventType, callback) {
  const listeners = eventListeners.get(eventType);
  if (listeners) {
    const index = listeners.indexOf(callback);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  }
}

/**
 * 分發事件給監聽器
 */
export function handleEvent(data) {
  // 相容後端的 "type" 字段和舊版 "event_type" 字段
  const eventType = data.type || data.event_type;
  const payload = data.payload || data;

  if (!eventType) {
    console.warn('Received message without event type:', data);
    return;
  }

  // 觸發通用監聽器
  const listeners = eventListeners.get(eventType) || [];
  listeners.forEach((callback) => {
    try {
      callback(payload);
    } catch (error) {
      console.error(`Error in event listener for ${eventType}:`, error);
    }
  });

  // 處理內建事件
  switch (eventType) {
    case WS_EVENT_TYPES.EXECUTION_STARTED:
      handleExecutionStarted(payload);
      break;
    case WS_EVENT_TYPES.EXECUTION_COMPLETED:
      handleExecutionCompleted(payload);
      break;
    case WS_EVENT_TYPES.EXECUTION_FAILED:
      handleExecutionFailed(payload);
      break;
    case WS_EVENT_TYPES.EXECUTION_STOPPED:
      handleExecutionStopped(payload);
      break;
    case WS_EVENT_TYPES.AGENT_STATUS:
      handleAgentStatusUpdate(payload);
      break;
    case WS_EVENT_TYPES.TRADE_EXECUTION:
      handleTradeExecution(payload);
      break;
    case WS_EVENT_TYPES.STRATEGY_CHANGE:
      handleStrategyChange(payload);
      break;
    case WS_EVENT_TYPES.PORTFOLIO_UPDATE:
      handlePortfolioUpdate(payload);
      break;
    case WS_EVENT_TYPES.PERFORMANCE_UPDATE:
      handlePerformanceUpdate(payload);
      break;
    case WS_EVENT_TYPES.ERROR:
      handleErrorEvent(payload);
      break;
    default:
      console.warn(`Unhandled event type: ${eventType}`, payload);
  }
}

/**
 * 處理執行開始事件
 */
function handleExecutionStarted(payload) {
  const { agent_id, session_id, mode } = payload;

  // 更新 agent 狀態為 RUNNING
  agents.update((list) =>
    list.map((agent) =>
      agent.agent_id === agent_id ? { ...agent, status: 'running', session_id } : agent
    )
  );

  addNotification({
    type: 'info',
    message: `Agent ${agent_id} 開始執行 ${mode} 模式...`,
  });

  console.warn(`[WS] Execution started for agent ${agent_id}`);
}

/**
 * 處理執行完成事件
 */
function handleExecutionCompleted(payload) {
  const { agent_id, execution_time_ms } = payload;

  // 更新 agent 狀態為 IDLE
  agents.update((list) =>
    list.map((agent) => (agent.agent_id === agent_id ? { ...agent, status: 'idle' } : agent))
  );

  addNotification({
    type: 'success',
    message: `Agent ${agent_id} 執行完成 (耗時 ${execution_time_ms}ms)`,
  });

  console.warn(`[WS] Execution completed for agent ${agent_id}`);
}

/**
 * 處理執行失敗事件
 */
function handleExecutionFailed(payload) {
  const { agent_id, error } = payload;

  // 更新 agent 狀態為 STOPPED
  agents.update((list) =>
    list.map((agent) => (agent.agent_id === agent_id ? { ...agent, status: 'stopped' } : agent))
  );

  addNotification({
    type: 'error',
    message: `Agent ${agent_id} 執行失敗: ${error}`,
  });

  console.error(`[WS] Execution failed for agent ${agent_id}:`, error);
}

/**
 * 處理執行停止事件
 */
function handleExecutionStopped(payload) {
  const { agent_id, status } = payload;

  // 更新 agent 狀態為 STOPPED
  agents.update((list) =>
    list.map((agent) => (agent.agent_id === agent_id ? { ...agent, status: 'stopped' } : agent))
  );

  addNotification({
    type: 'warning',
    message: `Agent ${agent_id} 已停止 (狀態: ${status})`,
  });

  console.warn(`[WS] Execution stopped for agent ${agent_id}`);
}

/**
 */
function handleAgentStatusUpdate(payload) {
  const { agent_id, status, current_mode } = payload;

  agents.update((list) =>
    list.map((agent) => (agent.agent_id === agent_id ? { ...agent, status, current_mode } : agent))
  );

  addNotification({
    type: 'info',
    message: `Agent ${agent_id} 狀態更新: ${status}`,
  });
}

/**
 * 處理交易執行事件
 */
function handleTradeExecution(payload) {
  const { agent_id, action, ticker, quantity, price } = payload;

  addNotification({
    type: 'success',
    message: `Agent ${agent_id} ${action === 'buy' ? '買入' : '賣出'} ${ticker} ${quantity} 股 @ ${price}`,
  });

  // 可以觸發投資組合刷新等後續操作
}

/**
 * 處理策略變更事件
 */
function handleStrategyChange(payload) {
  const { agent_id, change_type, reason } = payload;

  addNotification({
    type: 'info',
    message: `Agent ${agent_id} 策略已調整 (${change_type}): ${reason}`,
  });
}

/**
 * 處理投資組合更新事件
 */
function handlePortfolioUpdate(payload) {
  const { agent_id, total_value, cash } = payload;

  // 可以觸發投資組合資料刷新
  console.warn(`Portfolio update for ${agent_id}:`, { total_value, cash });
}

/**
 * 處理績效更新事件
 */
function handlePerformanceUpdate(payload) {
  const { agent_id, total_return, sharpe_ratio } = payload;

  console.warn(`Performance update for ${agent_id}:`, {
    total_return,
    sharpe_ratio,
  });
}

/**
 * 處理錯誤事件
 */
function handleErrorEvent(payload) {
  const { message, details } = payload;

  addNotification({
    type: 'error',
    message: `錯誤: ${message}`,
  });

  console.error('WebSocket error event:', details);
}

/**
 * 清除所有事件監聽器
 */
export function clearAllEventListeners() {
  eventListeners.clear();
}
