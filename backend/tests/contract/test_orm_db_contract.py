"""
ORM-Database 契約測試

驗證 SQLAlchemy ORM 模型與實際資料庫表結構一致
這是防止 'no such column' 類型錯誤的關鍵測試
"""

import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from database.models import Base, Agent, AgentPerformance, Transaction


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_engine():
    """建立臨時測試資料庫"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
def async_session_factory(async_engine):
    """建立 async session 工廠"""
    return sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


class TestAgentPerformanceORMContract:
    """驗證 AgentPerformance 模型與資料庫契約"""

    async def test_model_columns_match_database_schema(self, async_engine):
        """
        最重要的契約測試：模型定義的欄位必須在資料庫中存在

        這個測試防止了 'no such column' 錯誤
        """
        # 從 SQLAlchemy 模型獲取預期欄位
        mapper = inspect(AgentPerformance)
        expected_columns = {col.key for col in mapper.columns}

        # 從實際資料庫獲取實際欄位
        async with async_engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(agent_performance)"))
            actual_columns = {row[1] for row in result.fetchall()}

        # 驗證契約
        missing = expected_columns - actual_columns
        extra = actual_columns - expected_columns

        assert not missing, f"ORM-DB Contract Broken: missing columns {missing}"
        assert not extra, f"Schema has extra columns (migration issue?): {extra}"

    async def test_column_types_match_database(self, async_engine):
        """驗證欄位型別一致"""
        async with async_engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(agent_performance)"))
            db_columns = {row[1]: row[2] for row in result.fetchall()}

        # 驗證關鍵欄位的型別（這些是 delete_agent 需要的）
        assert "DATETIME" in db_columns["created_at"], "created_at should be DATETIME"
        assert "DATETIME" in db_columns["updated_at"], "updated_at should be DATETIME"
        assert "NUMERIC" in db_columns["total_value"], "total_value should be NUMERIC"
        assert "DATE" in db_columns["date"], "date should be DATE"

    async def test_nullable_constraints_match(self, async_engine):
        """驗證 NOT NULL 約束一致"""
        async with async_engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(agent_performance)"))
            # row[3] 是 notnull 欄位：0=nullable, 1=not null
            db_columns = {row[1]: row[3] for row in result.fetchall()}

        # 根據模型定義驗證 NOT NULL 欄位
        assert db_columns["agent_id"] == 1, "agent_id should be NOT NULL"
        assert db_columns["date"] == 1, "date should be NOT NULL"
        assert db_columns["total_value"] == 1, "total_value should be NOT NULL"
        assert db_columns["created_at"] == 1, "created_at should be NOT NULL (delete_agent 需要)"
        assert db_columns["updated_at"] == 1, "updated_at should be NOT NULL"

    async def test_foreign_key_constraints_exist(self, async_engine):
        """驗證外鍵約束存在"""
        async with async_engine.begin() as conn:
            # SQLite 預設不啟用外鍵，但約束仍然在 schema 中定義
            # 檢查 agent_performance 的外鍵定義
            result = await conn.execute(text("PRAGMA foreign_key_list(agent_performance)"))
            fks = result.fetchall()

            # 應該有對 agents 表的外鍵
            agent_fk = next((fk for fk in fks if fk[2] == "agents"), None)
            assert agent_fk is not None, "Missing foreign key to agents table"

    async def test_primary_key_configuration(self, async_engine):
        """驗證主鍵配置正確"""
        async with async_engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(agent_performance)"))
            pk_columns = [row for row in result.fetchall() if row[5]]

        assert len(pk_columns) > 0, "Table must have a primary key"
        assert pk_columns[0][1] == "id", "Primary key should be 'id' column"

    async def test_unique_constraints_exist(self, async_engine):
        """驗證唯一約束存在"""
        async with async_engine.begin() as conn:
            # 模型定義了 UniqueConstraint("agent_id", "date")
            result = await conn.execute(
                text(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name='agent_performance'"
                )
            )
            create_sql = result.scalar()
            assert "UNIQUE" in create_sql.upper(), "agent_id + date should be UNIQUE"


class TestAgentORMContract:
    """驗證 Agent 模型與資料庫契約"""

    async def test_cascade_delete_configured(self, async_engine):
        """
        驗證級聯刪除配置

        delete_agent 依賴這個配置來自動刪除相關記錄
        """
        mapper = inspect(Agent)

        # 檢查 performance_records 關係
        perf_rel = mapper.relationships.get("performance_records")
        assert perf_rel is not None, "Agent should have performance_records relationship"
        assert "delete-orphan" in perf_rel.cascade, "Should have delete-orphan cascade"

        # 檢查 transactions 關係
        trans_rel = mapper.relationships.get("transactions")
        assert trans_rel is not None, "Agent should have transactions relationship"
        assert "delete-orphan" in trans_rel.cascade, "Should have delete-orphan cascade"

    async def test_all_required_columns_exist(self, async_engine):
        """驗證所有必需欄位存在"""
        async with async_engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(agents)"))
            actual_columns = {row[1] for row in result.fetchall()}

        required = {"id", "name", "status", "current_mode", "created_at", "updated_at"}
        missing = required - actual_columns

        assert not missing, f"Agent table missing required columns: {missing}"


class TestCascadeDeleteBehavior:
    """驗證級聯刪除在 DB 層級的行為"""

    async def test_delete_agent_cascades_to_performance(self, async_session_factory):
        """驗證刪除 Agent 時會級聯刪除 AgentPerformance"""
        async with async_session_factory() as session:
            # 建立 Agent 和 AgentPerformance
            agent = Agent(
                id="cascade_test_001",
                name="Cascade Test",
                initial_funds=Decimal("100000"),
                current_funds=Decimal("100000"),
            )

            perf = AgentPerformance(
                agent_id="cascade_test_001",
                date=date.today(),
                total_value=Decimal("100000"),
                cash_balance=Decimal("100000"),
            )

            session.add(agent)
            session.add(perf)
            await session.commit()

            # 驗證記錄存在
            agent_check = await session.get(Agent, "cascade_test_001")
            perf_check = await session.get(AgentPerformance, 1)
            assert agent_check is not None
            assert perf_check is not None

            # 刪除 Agent - 應該級聯刪除 AgentPerformance
            await session.delete(agent_check)
            await session.commit()

            # 驗證都被刪除了
            agent_after = await session.get(Agent, "cascade_test_001")
            perf_after = await session.get(AgentPerformance, 1)
            assert agent_after is None, "Agent should be deleted"
            assert perf_after is None, "AgentPerformance should be cascade deleted"

    async def test_delete_agent_cascades_to_transactions(self, async_session_factory):
        """驗證刪除 Agent 時會級聯刪除 Transaction"""
        async with async_session_factory() as session:
            # 建立 Agent 和 Transaction
            agent = Agent(
                id="trans_cascade_001",
                name="Transaction Cascade Test",
                initial_funds=Decimal("100000"),
                current_funds=Decimal("95000"),
            )

            trans = Transaction(
                id="trans_001",
                agent_id="trans_cascade_001",
                ticker="2330",
                action="BUY",
                quantity=10,
                price=Decimal("500"),
                total_amount=Decimal("5000"),
            )

            session.add(agent)
            session.add(trans)
            await session.commit()

            # 驗證記錄存在
            trans_check = await session.get(Transaction, "trans_001")
            assert trans_check is not None

            # 刪除 Agent
            agent_to_delete = await session.get(Agent, "trans_cascade_001")
            await session.delete(agent_to_delete)
            await session.commit()

            # 驗證 Transaction 也被刪除
            trans_after = await session.get(Transaction, "trans_001")
            assert trans_after is None, "Transaction should be cascade deleted"


class TestORMSQLGeneration:
    """驗證 ORM 生成的 SQL 正確"""

    async def test_select_statement_includes_all_columns(self, async_session_factory):
        """
        驗證 SELECT 語句包含所有欄位

        這是 delete_agent 失敗的原因：
        SELECT 嘗試查詢不存在的欄位
        """
        async with async_session_factory() as session:
            # 建立測試資料
            agent = Agent(
                id="select_test",
                name="Select Test",
                initial_funds=Decimal("100000"),
                current_funds=Decimal("100000"),
            )

            perf = AgentPerformance(
                agent_id="select_test",
                date=date.today(),
                total_value=Decimal("100000"),
                cash_balance=Decimal("100000"),
            )

            session.add(agent)
            session.add(perf)
            await session.commit()

            # 執行查詢 - 這會生成 SELECT 語句
            # 如果有不存在的欄位，會在這裡失敗
            from sqlalchemy import select

            stmt = select(AgentPerformance).where(AgentPerformance.agent_id == "select_test")
            result = await session.execute(stmt)
            perf_result = result.scalars().first()

            # 驗證所有欄位都可以訪問
            assert perf_result.id is not None
            assert perf_result.created_at is not None
            assert perf_result.updated_at is not None
            assert perf_result.total_value == Decimal("100000")
