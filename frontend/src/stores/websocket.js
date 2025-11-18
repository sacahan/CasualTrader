import { writable } from 'svelte/store';
import {
  WS_URL,
  WS_EVENT_TYPES,
  MAX_RECONNECT_ATTEMPTS,
  RECONNECT_DELAY_MS,
} from '../shared/constants.js';
import { agents } from './agents.js';
import { refreshAgentDetails } from './agentDetails.js';
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
    default:
      console.warn(`Unhandled event type: ${eventType}`, payload);
  }
}

/**
 * 處理執行開始事件
 */
function handleExecutionStarted(payload) {
  const { agent_id, session_id } = payload;

  // 更新 agent 狀態為 RUNNING
  agents.update((list) =>
    list.map((agent) =>
      agent.agent_id === agent_id ? { ...agent, status: 'running', session_id } : agent
    )
  );

  // addNotification({
  //   type: 'info',
  //   message: `Agent ${agent_id} 開始執行 ${mode} 模式...`,
  // });

  console.warn(`[WS] Execution started for agent ${agent_id}`);
}

/**
 * 處理執行完成事件
 */
function handleExecutionCompleted(payload) {
  const { agent_id, execution_time_ms, financial_data } = payload;

  // 如果有財務數據，立即更新 agent 的財務狀態
  if (financial_data) {
    agents.update((list) =>
      list.map((agent) =>
        agent.agent_id === agent_id
          ? {
              ...agent,
              status: 'idle',
              current_funds: financial_data.current_funds,
              // 可選：也可以儲存其他財務數據供顯示
              total_portfolio_value: financial_data.total_portfolio_value,
              holdings_value: financial_data.holdings_value,
            }
          : agent
      )
    );
  } else {
    // 如果沒有財務數據，只更新狀態
    agents.update((list) =>
      list.map((agent) => (agent.agent_id === agent_id ? { ...agent, status: 'idle' } : agent))
    );
  }

  addNotification({
    type: 'success',
    message: `Agent ${agent_id} 執行完成 (耗時 ${execution_time_ms}ms)`,
  });

  console.warn(`[WS] Execution completed for agent ${agent_id}`, financial_data);

  // 如果沒有財務數據，則需要重新載入完整的 agent 數據
  if (!financial_data) {
    import('./agents.js').then(({ loadAgent }) => {
      loadAgent(agent_id).catch((error) => {
        console.error(`Failed to reload agent ${agent_id}:`, error);
      });
    });
  }

  // 非同步刷新詳細數據：性能、持股、交易紀錄
  refreshAgentDetails(agent_id).catch((error) => {
    console.error(`Failed to refresh details for agent ${agent_id}:`, error);
  });
}

/**
 * 處理執行失敗事件
 */
function handleExecutionFailed(payload) {
  const { agent_id, error, financial_data } = payload;

  // 如果有財務數據，更新財務狀態和執行狀態
  if (financial_data) {
    agents.update((list) =>
      list.map((agent) =>
        agent.agent_id === agent_id
          ? {
              ...agent,
              status: 'stopped',
              current_funds: financial_data.current_funds,
              total_portfolio_value: financial_data.total_portfolio_value,
              holdings_value: financial_data.holdings_value,
            }
          : agent
      )
    );
  } else {
    // 如果沒有財務數據，只更新狀態
    agents.update((list) =>
      list.map((agent) => (agent.agent_id === agent_id ? { ...agent, status: 'stopped' } : agent))
    );
  }

  addNotification({
    type: 'error',
    message: `Agent ${agent_id} 執行失敗: ${error}`,
  });

  console.error(`[WS] Execution failed for agent ${agent_id}:`, error, financial_data);

  // 如果沒有財務數據，則需要重新載入
  if (!financial_data) {
    import('./agents.js').then(({ loadAgent }) => {
      loadAgent(agent_id).catch((err) => {
        console.error(`Failed to reload agent ${agent_id}:`, err);
      });
    });
  }

  // 非同步刷新詳細數據以反映最新狀態
  refreshAgentDetails(agent_id).catch((err) => {
    console.error(`Failed to refresh details for agent ${agent_id} after failure:`, err);
  });
}

/**
 * 處理執行停止事件
 */
function handleExecutionStopped(payload) {
  const { agent_id, status, financial_data } = payload;

  // 如果有財務數據，更新財務狀態和執行狀態
  if (financial_data) {
    agents.update((list) =>
      list.map((agent) =>
        agent.agent_id === agent_id
          ? {
              ...agent,
              status: 'stopped',
              current_funds: financial_data.current_funds,
              total_portfolio_value: financial_data.total_portfolio_value,
              holdings_value: financial_data.holdings_value,
            }
          : agent
      )
    );
  } else {
    // 如果沒有財務數據，只更新狀態
    agents.update((list) =>
      list.map((agent) => (agent.agent_id === agent_id ? { ...agent, status: 'stopped' } : agent))
    );
  }

  addNotification({
    type: 'warning',
    message: `Agent ${agent_id} 已停止 (狀態: ${status})`,
  });

  console.warn(`[WS] Execution stopped for agent ${agent_id}`, financial_data);

  // 如果沒有財務數據，則需要重新載入
  if (!financial_data) {
    import('./agents.js').then(({ loadAgent }) => {
      loadAgent(agent_id).catch((err) => {
        console.error(`Failed to reload agent ${agent_id}:`, err);
      });
    });
  }

  // 非同步刷新詳細數據以反映最新狀態
  refreshAgentDetails(agent_id).catch((error) => {
    console.error(`Failed to refresh details for agent ${agent_id} after stop:`, error);
  });
}

/**
 * 處理代理狀態更新事件
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
 * 清除所有事件監聽器
 */
export function clearAllEventListeners() {
  eventListeners.clear();
}
