// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

// Agent Modes
export const AGENT_MODES = {
  TRADING: 'trading',
  REBALANCING: 'rebalancing',
  OBSERVATION: 'observation',
  STRATEGY_REVIEW: 'strategy_review',
};

export const AGENT_MODE_LABELS = {
  [AGENT_MODES.TRADING]: '交易',
  [AGENT_MODES.REBALANCING]: '再平衡',
  [AGENT_MODES.OBSERVATION]: '觀察',
  [AGENT_MODES.STRATEGY_REVIEW]: '策略檢討',
};

export const AGENT_MODE_COLORS = {
  [AGENT_MODES.TRADING]: 'bg-green-500',
  [AGENT_MODES.REBALANCING]: 'bg-blue-500',
  [AGENT_MODES.OBSERVATION]: 'bg-orange-500',
  [AGENT_MODES.STRATEGY_REVIEW]: 'bg-purple-500',
};

// Agent Status (persistent, matches backend database models)
export const AGENT_STATUS = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  ERROR: 'error',
  SUSPENDED: 'suspended',
};

// Agent Runtime Status (transient execution state)
export const AGENT_RUNTIME_STATUS = {
  IDLE: 'idle',
  RUNNING: 'running',
  STOPPED: 'stopped',
};

export const AGENT_STATUS_LABELS = {
  [AGENT_STATUS.ACTIVE]: '活躍',
  [AGENT_STATUS.INACTIVE]: '未啟用',
  [AGENT_STATUS.ERROR]: '錯誤',
  [AGENT_STATUS.SUSPENDED]: '已暫停',
};

export const AGENT_RUNTIME_STATUS_LABELS = {
  [AGENT_RUNTIME_STATUS.IDLE]: '待命',
  [AGENT_RUNTIME_STATUS.RUNNING]: '執行中',
  [AGENT_RUNTIME_STATUS.STOPPED]: '已停止',
};

// Strategy Change Types
export const CHANGE_TYPES = {
  AUTO: 'auto',
  MANUAL: 'manual',
  PERFORMANCE_DRIVEN: 'performance_driven',
};

export const CHANGE_TYPE_LABELS = {
  [CHANGE_TYPES.AUTO]: '自動調整',
  [CHANGE_TYPES.MANUAL]: '手動調整',
  [CHANGE_TYPES.PERFORMANCE_DRIVEN]: '績效驅動',
};

export const CHANGE_TYPE_COLORS = {
  [CHANGE_TYPES.AUTO]: 'bg-blue-100 text-blue-800',
  [CHANGE_TYPES.MANUAL]: 'bg-purple-100 text-purple-800',
  [CHANGE_TYPES.PERFORMANCE_DRIVEN]: 'bg-orange-100 text-orange-800',
};

// Market Hours
export const MARKET_HOURS = {
  OPEN_HOUR: 9,
  OPEN_MINUTE: 0,
  CLOSE_HOUR: 13,
  CLOSE_MINUTE: 30,
};

// Default Values
export const DEFAULT_INITIAL_FUNDS = 1000000;
export const DEFAULT_MAX_POSITION_SIZE = 50;
export const MAX_RECONNECT_ATTEMPTS = 5;
export const RECONNECT_DELAY_MS = 1000;

// WebSocket Event Types
export const WS_EVENT_TYPES = {
  AGENT_STATUS: 'agent_status',
  TRADE_EXECUTION: 'trade_execution',
  STRATEGY_CHANGE: 'strategy_change',
  PORTFOLIO_UPDATE: 'portfolio_update',
  PERFORMANCE_UPDATE: 'performance_update',
  ERROR: 'error',
};
