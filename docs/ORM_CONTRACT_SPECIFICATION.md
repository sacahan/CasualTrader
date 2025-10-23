# ORM 層契約規範 (Service-ORM-DB Layer Contract)

**版本**: 1.0
**最後更新**: 2025-10-23
**狀態**: Active

## 概述

本文件定義 CasualTrader 應用中 ORM (SQLAlchemy) 模型與資料庫架構的契約，確保兩層完全同步。

這是最關鍵的契約層級。根據 delete_agent 故障分析，ORM 模型期望的欄位與實際資料庫架構不一致，導致 SQL 生成錯誤。本文件明確定義所有模型欄位、型別、約束和級聯配置。

---

## 核心原則

1. **欄位一致性**：ORM 模型中定義的欄位必須在資料庫中存在
2. **型別一致性**：ORM 欄位型別必須與資料庫欄位型別匹配
3. **約束一致性**：NULL 約束、外鍵、主鍵、唯一性約束必須一致
4. **級聯配置**：相關記錄的刪除行為必須在 ORM 中明確配置

---

## Contract 3: ORM 模型定義

### 3.1 Agent 模型

```python
class Agent(Base):
    """代理人模型"""
    __tablename__ = "agent"

    # ✓ 主鍵
    id = Column(Integer, primary_key=True)

    # ✓ 基本資訊（不可 NULL）
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    ai_model = Column(String(50), nullable=False)
    strategy_prompt = Column(String(2000), nullable=True)

    # ✓ 配置（JSON 序列化）
    investment_preferences = Column(JSON, nullable=False)  # list[str]
    enabled_tools = Column(JSON, nullable=False)           # EnabledTools

    # ✓ 時間戳
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # ✓ 級聯關係配置（關鍵！）
    performances = relationship(
        "AgentPerformance",
        back_populates="agent",
        cascade="all, delete-orphan"  # ✓ 必須配置級聯刪除
    )
    transactions = relationship(
        "Transaction",
        back_populates="agent",
        cascade="all, delete-orphan"  # ✓ 必須配置級聯刪除
    )
    sessions = relationship(
        "Session",
        back_populates="agent",
        cascade="all, delete-orphan"  # ✓ 必須配置級聯刪除
    )
```

**資料庫架構** (SQLite):

```sql
CREATE TABLE agent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    ai_model VARCHAR(50) NOT NULL,
    strategy_prompt VARCHAR(2000),
    investment_preferences JSON NOT NULL,
    enabled_tools JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 AgentPerformance 模型 ✅

```python
class AgentPerformance(Base):
    """Agent 績效記錄"""
    __tablename__ = "agent_performance"

    # ✓ 主鍵
    id = Column(Integer, primary_key=True)

    # ✓ 外鍵（不可 NULL，帶級聯刪除）
    agent_id = Column(Integer, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False)

    # ✓ 績效數據（不可 NULL）
    date = Column(Date, nullable=False)
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    stock_value = Column(Float, nullable=False)
    dividend_received = Column(Float, nullable=False)

    # ✓ 時間戳（由遷移腳本添加）
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # ✓ 反向關係
    agent = relationship("Agent", back_populates="performances")
```

**資料庫架構** (SQLite):

```sql
CREATE TABLE agent_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_value REAL NOT NULL,
    cash_balance REAL NOT NULL,
    stock_value REAL NOT NULL,
    dividend_received REAL NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agent(id) ON DELETE CASCADE
);
```

**契約驗證** ✅ (已完成):

- [x] 欄位一致性：ORM 模型的所有欄位都在資料庫中
- [x] 型別一致性：Float ↔ REAL, DateTime ↔ DATETIME
- [x] NULL 約束：NULL 配置一致
- [x] 級聯配置：ON DELETE CASCADE 配置正確
- [x] 時間戳存在：created_at 和 updated_at 都存在

### 3.3 Transaction 模型

```python
class Transaction(Base):
    """交易記錄"""
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(Integer, ForeignKey("session.id", ondelete="CASCADE"), nullable=True)

    # 交易資訊
    symbol = Column(String(20), nullable=False)
    action = Column(String(10), nullable=False)  # 'buy' or 'sell'
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    # 費用
    commission = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)

    # 時間
    executed_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # 反向關係
    agent = relationship("Agent", back_populates="transactions")
    session = relationship("Session", back_populates="transactions")
```

### 3.4 Session 模型

```python
class Session(Base):
    """交易會話"""
    __tablename__ = "session"

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False)

    # 會話狀態
    status = Column(String(20), nullable=False)  # 'active' or 'closed'
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)

    # 績效
    initial_cash = Column(Float, nullable=False)
    final_value = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)  # Profit/Loss

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # 反向關係
    agent = relationship("Agent", back_populates="sessions")
    transactions = relationship("Transaction", back_populates="session")
```

---

## 級聯刪除契約

刪除 Agent 時，ORM 應自動刪除所有相關記錄：

```
DELETE Agent(agent_id)
  ↓ cascade
  ├─ DELETE AgentPerformance(agent_id) → N 筆績效記錄
  ├─ DELETE Transaction(agent_id) → M 筆交易記錄
  └─ DELETE Session(agent_id) → K 筆會話記錄
     ├─ 級聯刪除 Transaction(session_id) (已由 Agent 級聯)
```

**ORM 級聯配置驗證**：

```python
# ✓ 正確配置
agent = relationship("Agent", cascade="all, delete-orphan")

# ✗ 錯誤配置（缺少 delete-orphan）
agent = relationship("Agent", cascade="all")

# ✗ 錯誤配置（沒有級聯）
agent = relationship("Agent")
```

---

## ORM-DB 契約驗證測試 ✅ (已完成)

**位置**: `tests/contract/test_orm_db_contract.py`

**11 個測試，全部通過**:

1. `test_model_columns_match_database_schema`
   - 驗證 ORM 模型的所有欄位都在資料庫中存在

2. `test_column_types_match_database`
   - 驗證 ORM 欄位型別與資料庫欄位型別匹配

3. `test_nullable_constraints_match`
   - 驗證 NULL 約束一致性

4. `test_foreign_key_constraints_exist`
   - 驗證外鍵定義正確

5. `test_cascade_delete_configured`
   - 驗證級聯刪除配置正確

6. `test_delete_agent_cascades_to_performance`
   - 驗證刪除 Agent 級聯刪除 AgentPerformance

7. `test_delete_agent_cascades_to_transactions`
   - 驗證刪除 Agent 級聯刪除 Transaction

8. `test_select_statement_includes_all_columns`
   - 驗證 SELECT 查詢包含所有欄位

9. `test_primary_key_configuration`
   - 驗證主鍵配置正確

10. `test_unique_constraints_exist`
    - 驗證唯一性約束

11. `test_all_required_columns_exist`
    - 驗證所有必需欄位存在

**測試結果**:

```bash
$ pytest tests/contract/test_orm_db_contract.py -v
========================= 11 passed in 0.17s ==========================
✓ 所有欄位契約驗證通過
✓ 所有型別契約驗證通過
✓ 所有約束契約驗證通過
✓ 級聯行為驗證通過
```

---

## 故障案例：為什麼 delete_agent 失敗？

### 根本原因

```
ORM 模型定義：
  AgentPerformance.created_at ✓
  AgentPerformance.updated_at ✓

資料庫架構實際：
  agent_performance table 中缺少這兩個欄位 ✗

ORM 生成的 SQL：
  SELECT ... agent_performance.created_at, agent_performance.updated_at ...

資料庫響應：
  Error: no such column: agent_performance.created_at ✗

為什麼 Mock 測試無法發現？
  @patch("AgentsService")
  def test_delete_agent(mock_service):
      mock_service.delete.return_value = {"success": True}  # ← 假成功
      # Mock 永遠不會執行真實 SQL 查詢 ✗
```

### 防止機制

如果有此契約測試（test_model_columns_match_database_schema），問題會被立即發現：

```python
def test_model_columns_match_database_schema():
    """ORM 模型的欄位必須在資料庫中存在"""

    # 取得 ORM 模型的所有欄位
    orm_columns = {column.name for column in AgentPerformance.__table__.columns}
    # → {'id', 'agent_id', 'date', 'total_value', ..., 'created_at', 'updated_at'}

    # 查詢實際資料庫架構
    inspector = inspect(engine)
    db_columns = {col['name'] for col in inspector.get_columns('agent_performance')}
    # → {'id', 'agent_id', 'date', 'total_value', ...} (缺少時間戳)

    # 對比
    missing = orm_columns - db_columns
    if missing:
        raise AssertionError(f"資料庫缺少欄位: {missing}")
        # AssertionError: 資料庫缺少欄位: {'created_at', 'updated_at'}
```

### 修復方案 ✅ (已完成)

1. **執行遷移腳本** ✅

   ```bash
   python backend/scripts/migrate_add_timestamps.py
   ```

2. **驗證 Contract 3** ✅

   ```bash
   pytest tests/contract/test_orm_db_contract.py -v
   # 結果：11/11 通過
   ```

3. **驗證級聯刪除** ✅

   ```bash
   pytest tests/integration/test_delete_agent_integration.py -v
   # 結果：4/4 通過
   ```

---

## 實施檢查清單

### Contract 3: Service-ORM-DB 層 ✅ (已完成)

- [x] ORM 模型定義
- [x] 資料庫架構定義
- [x] 級聯配置驗證
- [x] 11 個契約測試
- [x] 資料庫遷移
- [x] 級聯刪除驗證
- [x] 文檔完成

---

## 參考資源

- **API 契約**: `API_CONTRACT_SPECIFICATION.md`
- **Service 契約**: `SERVICE_CONTRACT_SPECIFICATION.md`
- **遷移契約**: `MIGRATION_CONTRACT_SPECIFICATION.md`
- **ORM 測試**: `backend/tests/contract/test_orm_db_contract.py`
- **集成測試**: `backend/tests/integration/test_delete_agent_integration.py`
- **遷移腳本**: `backend/scripts/migrate_add_timestamps.py`

---

**版本**: 1.0
**最後更新**: 2025-10-23
**狀態**: ✅ 完成（規範 + 測試 + 驗證）
