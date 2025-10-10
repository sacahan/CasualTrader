-- SQLite 資料庫遷移腳本: Symbol → Ticker
-- 版本: 1.0
-- 日期: 2025-10-10
-- 說明: 將 agent_holdings 和 transactions 表中的 symbol 欄位重命名為 ticker

BEGIN TRANSACTION;

-- ==========================================
-- Step 1: 備份現有表
-- ==========================================
CREATE TABLE IF NOT EXISTS agent_holdings_backup AS SELECT * FROM agent_holdings;
CREATE TABLE IF NOT EXISTS transactions_backup AS SELECT * FROM transactions;

-- ==========================================
-- Step 2: 重建 agent_holdings 表
-- ==========================================

-- 創建新表 (使用 ticker 欄位名)
CREATE TABLE agent_holdings_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    company_name TEXT,
    quantity INTEGER NOT NULL,
    average_cost DECIMAL(10,2) NOT NULL,
    total_cost DECIMAL(15,2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    UNIQUE(agent_id, ticker)
);

-- 遷移數據
INSERT INTO agent_holdings_new (id, agent_id, ticker, company_name, quantity, average_cost, total_cost, created_at, updated_at)
SELECT id, agent_id, symbol, company_name, quantity, average_cost, total_cost, created_at, updated_at
FROM agent_holdings;

-- 刪除舊表並重命名新表
DROP TABLE agent_holdings;
ALTER TABLE agent_holdings_new RENAME TO agent_holdings;

-- 重建索引
CREATE INDEX idx_holdings_agent_id ON agent_holdings(agent_id);
CREATE INDEX idx_holdings_ticker ON agent_holdings(ticker);

-- 重建觸發器
CREATE TRIGGER holdings_updated_at
    AFTER UPDATE ON agent_holdings
BEGIN
    UPDATE agent_holdings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ==========================================
-- Step 3: 重建 transactions 表
-- ==========================================

-- 創建新表 (使用 ticker 欄位名)
CREATE TABLE transactions_new (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    session_id TEXT,
    ticker TEXT NOT NULL,
    company_name TEXT,
    action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    commission DECIMAL(10,2) DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'executed', 'failed', 'cancelled')),
    execution_time DATETIME,
    decision_reason TEXT,
    ai_model TEXT,
    market_data JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE SET NULL
);

-- 遷移數據
INSERT INTO transactions_new
SELECT id, agent_id, session_id, symbol, company_name, action, quantity, price, total_amount, commission,
       status, execution_time, decision_reason, ai_model, market_data, created_at
FROM transactions;

-- 刪除舊表並重命名新表
DROP TABLE transactions;
ALTER TABLE transactions_new RENAME TO transactions;

-- 重建索引
CREATE INDEX idx_transactions_agent_id ON transactions(agent_id);
CREATE INDEX idx_transactions_ticker ON transactions(ticker);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_status ON transactions(status);

-- ==========================================
-- Step 4: 更新視圖
-- ==========================================

-- 刪除舊視圖
DROP VIEW IF EXISTS agent_overview;

-- 重建視圖 (使用 ticker)
CREATE VIEW agent_overview AS
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

COMMIT;

-- ==========================================
-- 驗證遷移結果
-- ==========================================

-- 檢查資料筆數是否一致
SELECT
    'agent_holdings' as table_name,
    (SELECT COUNT(*) FROM agent_holdings_backup) as backup_count,
    (SELECT COUNT(*) FROM agent_holdings) as current_count;

SELECT
    'transactions' as table_name,
    (SELECT COUNT(*) FROM transactions_backup) as backup_count,
    (SELECT COUNT(*) FROM transactions) as current_count;

-- ==========================================
-- 清理 (可選 - 執行前先確認)
-- ==========================================

-- 如果遷移成功且資料一致,可以執行以下命令清理備份表:
-- DROP TABLE agent_holdings_backup;
-- DROP TABLE transactions_backup;
