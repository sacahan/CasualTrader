-- CasualTrader Phase 1 SQLite Database Schema
-- 支援 Agent 系統基礎架構
-- 版本: 1.0
-- 日期: 2025-10-06

-- ==========================================
-- Agent 基礎資料表
-- ==========================================

-- Agent 註冊和配置表
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,                    -- Agent 唯一 ID
    name TEXT NOT NULL,                     -- Agent 顯示名稱
    description TEXT,                       -- Agent 描述
    instructions TEXT NOT NULL,             -- Agent 完整指令 (Prompt)
    ai_model TEXT NOT NULL DEFAULT 'gpt-4o-mini', -- AI 模型選擇
    color TEXT DEFAULT '34, 197, 94',       -- UI 卡片顏色 (RGB 格式)

    -- 投資配置
    initial_funds DECIMAL(15,2) NOT NULL,   -- 初始資金
    max_position_size DECIMAL(5,2) DEFAULT 5.0, -- 最大單筆投資比例 (%)

    -- Agent 狀態
    status TEXT NOT NULL DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'error', 'suspended')),
    current_mode TEXT DEFAULT 'OBSERVATION' CHECK (current_mode IN ('TRADING', 'REBALANCING', 'STRATEGY_REVIEW', 'OBSERVATION')),

    -- 配置參數 (JSON)
    config JSON,                            -- Agent 配置參數
    investment_preferences TEXT,            -- 投資偏好
    strategy_adjustment_criteria TEXT,      -- 策略調整依據
    auto_adjust_settings JSON,              -- 自動調整設定

    -- 時間戳記
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active_at DATETIME
);

-- Agent 執行會話表 (SQLite Session 持久化)
CREATE TABLE IF NOT EXISTS agent_sessions (
    id TEXT PRIMARY KEY,                    -- Session ID
    agent_id TEXT NOT NULL,                 -- 關聯的 Agent ID
    session_type TEXT NOT NULL,             -- 會話類型
    mode TEXT NOT NULL,                     -- 執行模式

    -- 執行狀態
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'timeout')),
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    execution_time_ms INTEGER,

    -- 執行內容
    initial_input JSON,                     -- 輸入參數
    final_output JSON,                      -- 執行結果
    tools_called TEXT,                      -- 調用的工具列表 (逗號分隔)
    error_message TEXT,                     -- 錯誤訊息

    -- 追蹤資訊
    trace_data JSON,                        -- 詳細追蹤資料

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- ==========================================
-- 交易系統資料表
-- ==========================================

-- 投資組合持倉表
CREATE TABLE IF NOT EXISTS agent_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,                 -- Agent ID
    ticker TEXT NOT NULL,                   -- 股票代號
    company_name TEXT,                      -- 公司名稱

    -- 持倉資訊
    quantity INTEGER NOT NULL,              -- 持有股數
    average_cost DECIMAL(10,2) NOT NULL,    -- 平均成本
    total_cost DECIMAL(15,2) NOT NULL,      -- 總成本

    -- 時間戳記
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    UNIQUE(agent_id, ticker)
);

-- 交易記錄表
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,                    -- 交易 ID
    agent_id TEXT NOT NULL,                 -- Agent ID
    session_id TEXT,                        -- 關聯的執行會話

    -- 交易基本資訊
    ticker TEXT NOT NULL,                   -- 股票代號
    company_name TEXT,                      -- 公司名稱
    action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')), -- 交易動作

    -- 交易數量和價格
    quantity INTEGER NOT NULL,              -- 交易股數
    price DECIMAL(10,2) NOT NULL,           -- 交易價格
    total_amount DECIMAL(15,2) NOT NULL,    -- 交易總金額
    commission DECIMAL(10,2) DEFAULT 0,     -- 手續費

    -- 交易狀態
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'executed', 'failed', 'cancelled')),
    execution_time DATETIME,

    -- 決策背景
    decision_reason TEXT,                   -- 交易決策原因
    ai_model TEXT,                          -- 執行交易時使用的 AI 模型
    market_data JSON,                       -- 交易時的市場數據

    -- 時間戳記
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE SET NULL
);

-- ==========================================
-- 策略演化系統資料表
-- ==========================================

-- 策略變更記錄表
CREATE TABLE IF NOT EXISTS strategy_changes (
    id TEXT PRIMARY KEY,                    -- 變更 ID
    agent_id TEXT NOT NULL,                 -- Agent ID

    -- 變更觸發資訊
    trigger_reason TEXT NOT NULL,           -- 觸發原因
    change_type TEXT NOT NULL CHECK (change_type IN ('auto', 'manual', 'performance_driven')),

    -- 策略內容變更
    old_strategy TEXT,                      -- 變更前策略
    new_strategy TEXT NOT NULL,             -- 變更後策略
    change_summary TEXT NOT NULL,           -- 變更摘要

    -- 績效背景資料
    performance_at_change JSON,             -- 變更時的績效狀況

    -- Agent 說明
    agent_explanation TEXT,                 -- Agent 對變更的解釋
    ai_model TEXT,                          -- 進行策略變更時使用的 AI 模型

    -- 時間戳記
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- ==========================================
-- 快取和監控資料表
-- ==========================================

-- 市場數據快取表
CREATE TABLE IF NOT EXISTS market_data_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT UNIQUE NOT NULL,         -- 快取鍵值
    cache_data JSON NOT NULL,               -- 快取數據
    expires_at DATETIME NOT NULL,           -- 過期時間
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Agent 效能指標表
CREATE TABLE IF NOT EXISTS agent_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,                 -- Agent ID
    date DATE NOT NULL,                     -- 日期

    -- 投資組合指標
    total_value DECIMAL(15,2) NOT NULL,     -- 總資產價值
    cash_balance DECIMAL(15,2) NOT NULL,    -- 現金餘額
    unrealized_pnl DECIMAL(15,2) DEFAULT 0, -- 未實現損益
    realized_pnl DECIMAL(15,2) DEFAULT 0,   -- 已實現損益

    -- 績效指標
    daily_return DECIMAL(8,4),              -- 日報酬率
    total_return DECIMAL(8,4),              -- 總報酬率
    win_rate DECIMAL(5,2),                  -- 勝率
    max_drawdown DECIMAL(8,4),              -- 最大回撤

    -- 交易統計
    total_trades INTEGER DEFAULT 0,         -- 總交易次數
    winning_trades INTEGER DEFAULT 0,       -- 獲利交易次數

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    UNIQUE(agent_id, date)
);

-- Agent 設定快取表
CREATE TABLE IF NOT EXISTS agent_config_cache (
    agent_id TEXT NOT NULL,                 -- Agent ID
    config_key TEXT NOT NULL,               -- 設定鍵值
    config_value TEXT,                      -- 設定值
    config_type TEXT DEFAULT 'string',      -- 值類型

    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (agent_id, config_key),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- ==========================================
-- 索引建立
-- ==========================================

-- Agent 相關索引
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at);

-- Session 相關索引
CREATE INDEX IF NOT EXISTS idx_sessions_agent_id ON agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON agent_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON agent_sessions(start_time);

-- 交易相關索引
CREATE INDEX IF NOT EXISTS idx_transactions_agent_id ON transactions(agent_id);
CREATE INDEX IF NOT EXISTS idx_transactions_ticker ON transactions(ticker);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);

-- 持倉相關索引
CREATE INDEX IF NOT EXISTS idx_holdings_agent_id ON agent_holdings(agent_id);
CREATE INDEX IF NOT EXISTS idx_holdings_ticker ON agent_holdings(ticker);

-- 策略變更相關索引
CREATE INDEX IF NOT EXISTS idx_strategy_changes_agent_id ON strategy_changes(agent_id);
CREATE INDEX IF NOT EXISTS idx_strategy_changes_timestamp ON strategy_changes(timestamp);

-- 績效相關索引
CREATE INDEX IF NOT EXISTS idx_performance_agent_id ON agent_performance(agent_id);
CREATE INDEX IF NOT EXISTS idx_performance_date ON agent_performance(date);

-- 快取相關索引
CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON market_data_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_key ON market_data_cache(cache_key);

-- ==========================================
-- 觸發器 (自動更新時間戳記)
-- ==========================================

-- agents 表更新觸發器
CREATE TRIGGER IF NOT EXISTS agents_updated_at
    AFTER UPDATE ON agents
BEGIN
    UPDATE agents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- agent_holdings 表更新觸發器
CREATE TRIGGER IF NOT EXISTS holdings_updated_at
    AFTER UPDATE ON agent_holdings
BEGIN
    UPDATE agent_holdings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ==========================================
-- 視圖定義
-- ==========================================

-- Agent 總覽視圖
CREATE VIEW IF NOT EXISTS agent_overview AS
SELECT
    a.id,
    a.name,
    a.status,
    a.current_mode,
    a.initial_funds,
    COUNT(DISTINCT h.ticker) as holdings_count,
    COALESCE(SUM(h.quantity * h.average_cost), 0) as total_invested,
    a.created_at,
    a.last_active_at
FROM agents a
LEFT JOIN agent_holdings h ON a.id = h.agent_id
GROUP BY a.id;

-- Agent 最新績效視圖
CREATE VIEW IF NOT EXISTS agent_latest_performance AS
SELECT
    ap.*,
    a.name as agent_name
FROM agent_performance ap
INNER JOIN (
    SELECT agent_id, MAX(date) as latest_date
    FROM agent_performance
    GROUP BY agent_id
) latest ON ap.agent_id = latest.agent_id AND ap.date = latest.latest_date
INNER JOIN agents a ON ap.agent_id = a.id;
