-- Schema DDL for PostgreSQL (CasualTrader)

-- ai_model_configs
CREATE TABLE public.ai_model_configs (
  id               BIGSERIAL PRIMARY KEY,
  model_key        VARCHAR(100) NOT NULL UNIQUE,
  display_name     VARCHAR(200) NOT NULL,
  provider         VARCHAR(50)  NOT NULL,
  group_name       VARCHAR(50)  NOT NULL,
  model_type       VARCHAR(20)  NOT NULL,
  litellm_prefix   VARCHAR(100),
  is_enabled       BOOLEAN      NOT NULL DEFAULT TRUE,
  requires_api_key BOOLEAN      NOT NULL DEFAULT TRUE,
  api_key_env_var  VARCHAR(100),
  display_order    INTEGER      NOT NULL DEFAULT 999,
  created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  CONSTRAINT check_model_type CHECK (model_type IN ('openai','litellm'))
);
CREATE INDEX idx_ai_models_model_key     ON public.ai_model_configs (model_key);
CREATE INDEX idx_ai_models_provider      ON public.ai_model_configs (provider);
CREATE INDEX idx_ai_models_is_enabled    ON public.ai_model_configs (is_enabled);
CREATE INDEX idx_ai_models_display_order ON public.ai_model_configs (display_order);

-- agents
CREATE TABLE public.agents (
  id                      VARCHAR(50)  PRIMARY KEY,
  name                    VARCHAR(200) NOT NULL,
  description             TEXT,
  ai_model                VARCHAR(50)  NOT NULL DEFAULT 'gpt-4o-mini',
  color_theme             VARCHAR(20)  NOT NULL DEFAULT '34, 197, 94',
  initial_funds           NUMERIC(15,2) NOT NULL DEFAULT 0,
  current_funds           NUMERIC(15,2) NOT NULL DEFAULT 0,
  max_position_size       NUMERIC(5,2)  NOT NULL DEFAULT 50.00,
  status                  VARCHAR(20)  NOT NULL DEFAULT 'inactive',
  current_mode            VARCHAR(30)  NOT NULL DEFAULT 'TRADING',
  investment_preferences  TEXT,
  created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  last_active_at          TIMESTAMPTZ,
  CONSTRAINT check_agent_status CHECK (status IN ('active','inactive','error','suspended')),
  CONSTRAINT check_agent_mode   CHECK (current_mode IN ('TRADING','REBALANCING'))
);
CREATE INDEX idx_agents_status     ON public.agents (status);
CREATE INDEX idx_agents_created_at ON public.agents (created_at);

-- agent_sessions
CREATE TABLE public.agent_sessions (
  id                 VARCHAR(50) PRIMARY KEY,
  agent_id           VARCHAR(50) NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
  mode               VARCHAR(30) NOT NULL,
  status             VARCHAR(20) NOT NULL DEFAULT 'pending',
  start_time         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  end_time           TIMESTAMPTZ,
  execution_time_ms  INTEGER,
  initial_input      JSONB,
  final_output       TEXT,
  tools_called       TEXT,
  error_message      TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT check_session_status CHECK (status IN ('pending','running','completed','failed','cancelled'))
);
CREATE INDEX idx_sessions_agent_id   ON public.agent_sessions (agent_id);
CREATE INDEX idx_sessions_status     ON public.agent_sessions (status);
CREATE INDEX idx_sessions_start_time ON public.agent_sessions (start_time);
CREATE INDEX idx_sessions_created_at ON public.agent_sessions (created_at);

-- agent_holdings
CREATE TABLE public.agent_holdings (
  id            BIGSERIAL PRIMARY KEY,
  agent_id      VARCHAR(50) NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
  ticker        VARCHAR(10) NOT NULL,
  company_name  VARCHAR(200),
  quantity      INTEGER     NOT NULL,
  average_cost  NUMERIC(10,2) NOT NULL,
  total_cost    NUMERIC(15,2) NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_agent_ticker UNIQUE (agent_id, ticker)
);
CREATE INDEX idx_holdings_agent_id ON public.agent_holdings (agent_id);
CREATE INDEX idx_holdings_ticker   ON public.agent_holdings (ticker);

-- transactions
CREATE TABLE public.transactions (
  id             VARCHAR(50) PRIMARY KEY,
  agent_id       VARCHAR(50) NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
  session_id     VARCHAR(50) REFERENCES public.agent_sessions(id) ON DELETE SET NULL,
  ticker         VARCHAR(10) NOT NULL,
  company_name   VARCHAR(200),
  action         VARCHAR(10) NOT NULL,
  quantity       INTEGER     NOT NULL,
  price          NUMERIC(10,2) NOT NULL,
  total_amount   NUMERIC(15,2) NOT NULL,
  commission     NUMERIC(10,2) NOT NULL DEFAULT 0,
  status         VARCHAR(20) NOT NULL DEFAULT 'pending',
  execution_time TIMESTAMPTZ,
  decision_reason TEXT,
  market_data    JSONB,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT check_transaction_action  CHECK (action IN ('BUY','SELL')),
  CONSTRAINT check_transaction_status  CHECK (status IN ('pending','executed','failed','cancelled'))
);
CREATE INDEX idx_transactions_agent_id   ON public.transactions (agent_id);
CREATE INDEX idx_transactions_ticker     ON public.transactions (ticker);
CREATE INDEX idx_transactions_created_at ON public.transactions (created_at);
CREATE INDEX idx_transactions_status     ON public.transactions (status);

-- agent_performance
CREATE TABLE public.agent_performance (
  id                     BIGSERIAL PRIMARY KEY,
  agent_id               VARCHAR(50) NOT NULL REFERENCES public.agents(id) ON DELETE CASCADE,
  date                   DATE        NOT NULL,
  total_value            NUMERIC(15,2) NOT NULL,
  cash_balance           NUMERIC(15,2) NOT NULL,
  unrealized_pnl         NUMERIC(15,2) NOT NULL DEFAULT 0,
  realized_pnl           NUMERIC(15,2) NOT NULL DEFAULT 0,
  daily_return           NUMERIC(8,4),
  total_return           NUMERIC(8,4),
  win_rate               NUMERIC(5,2),
  max_drawdown           NUMERIC(8,4),
  sharpe_ratio           NUMERIC(8,4),
  sortino_ratio          NUMERIC(8,4),
  calmar_ratio           NUMERIC(8,4),
  total_trades           INTEGER NOT NULL DEFAULT 0,
  sell_trades_count      INTEGER NOT NULL DEFAULT 0,
  winning_trades_correct INTEGER NOT NULL DEFAULT 0,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_agent_date UNIQUE (agent_id, date)
);
CREATE INDEX idx_performance_agent_id ON public.agent_performance (agent_id);
CREATE INDEX idx_performance_date     ON public.agent_performance (date);
