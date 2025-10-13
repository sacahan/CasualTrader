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

// AI Models
export const AI_MODELS = {
  GPT_4O: 'gpt-4o',
  GPT_4O_MINI: 'gpt-4o-mini',
  GPT_4_TURBO: 'gpt-4-turbo',
  CLAUDE_SONNET_4_5: 'claude-sonnet-4.5',
  CLAUDE_OPUS_4: 'claude-opus-4',
  GEMINI_2_5_PRO: 'gemini-2.5-pro',
  GEMINI_2_0_FLASH: 'gemini-2.0-flash',
  DEEPSEEK_V3: 'deepseek-v3',
  GROK_2: 'grok-2',
};

export const AI_MODEL_LABELS = {
  [AI_MODELS.GPT_4O]: 'GPT-4o',
  [AI_MODELS.GPT_4O_MINI]: 'GPT-4o Mini',
  [AI_MODELS.GPT_4_TURBO]: 'GPT-4 Turbo',
  [AI_MODELS.CLAUDE_SONNET_4_5]: 'Claude Sonnet 4.5',
  [AI_MODELS.CLAUDE_OPUS_4]: 'Claude Opus 4',
  [AI_MODELS.GEMINI_2_5_PRO]: 'Gemini 2.5 Pro',
  [AI_MODELS.GEMINI_2_0_FLASH]: 'Gemini 2.0 Flash',
  [AI_MODELS.DEEPSEEK_V3]: 'DeepSeek V3',
  [AI_MODELS.GROK_2]: 'Grok 2',
};

export const AI_MODEL_GROUPS = {
  OpenAI: [AI_MODELS.GPT_4O, AI_MODELS.GPT_4O_MINI, AI_MODELS.GPT_4_TURBO],
  'Anthropic Claude': [AI_MODELS.CLAUDE_SONNET_4_5, AI_MODELS.CLAUDE_OPUS_4],
  'Google Gemini': [AI_MODELS.GEMINI_2_5_PRO, AI_MODELS.GEMINI_2_0_FLASH],
  其他: [AI_MODELS.DEEPSEEK_V3, AI_MODELS.GROK_2],
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
export const DEFAULT_MAX_POSITION_SIZE = 5;
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
