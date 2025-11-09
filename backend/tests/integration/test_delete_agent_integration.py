"""
Agent 刪除端到端整合測試

測試實際的資料庫級聯刪除操作，確保 delete 功能正常運作
這個測試文件確保了測試能夠發現類似 "no such column" 的問題
"""

import pytest
import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from database.models import Base, Agent, AgentPerformance, Transaction
from common.enums import TransactionAction


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_engine():
    """建立臨時測試資料庫"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # 建立所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
def async_session_factory(async_engine):
    """建立 async session 工廠"""
    return sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


class TestDeleteAgentIntegration:
    """Agent 刪除功能整合測試"""

    @pytest.mark.asyncio
    async def test_delete_agent_with_performance_records(self, async_engine, async_session_factory):
        """
        測試刪除有績效記錄的 Agent

        這個測試確保：
        1. 級聯刪除正常運作
        2. 所有相關記錄都被刪除
        3. 不會出現 "no such column" 的錯誤
        """
        async with async_session_factory() as session:
            # 建立 Agent
            agent = Agent(
                id="test_delete_agent_001",
                name="測試刪除代理",
                initial_funds=Decimal("100000"),
                current_funds=Decimal("100000"),
            )
            session.add(agent)
            await session.flush()

            # 建立績效記錄
            performance = AgentPerformance(
                agent_id="test_delete_agent_001",
                date=date.today(),
                total_value=Decimal("100000"),
                cash_balance=Decimal("100000"),
                total_trades=0,
                sell_trades_count=0,  # 修正: 賣出交易數
                winning_trades_correct=0,  # 修正: 真實獲利交易數
            )
            session.add(performance)

            # 建立交易記錄
            transaction = Transaction(
                id="trans_001",
                agent_id="test_delete_agent_001",
                ticker="2330",
                action=TransactionAction.BUY,
                quantity=10,
                price=Decimal("600.0"),
                total_amount=Decimal("6000.0"),
            )
            session.add(transaction)

            await session.commit()

            # 驗證記錄已建立
            result = await session.execute(select(Agent).where(Agent.id == "test_delete_agent_001"))
            assert result.scalars().first() is not None

            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.agent_id == "test_delete_agent_001")
            )
            assert result.scalars().first() is not None

            result = await session.execute(
                select(Transaction).where(Transaction.agent_id == "test_delete_agent_001")
            )
            assert result.scalars().first() is not None

            # 刪除 Agent（應該級聯刪除相關記錄）
            agent_to_delete = await session.get(Agent, "test_delete_agent_001")
            await session.delete(agent_to_delete)
            await session.commit()

            # 驗證 Agent 已刪除
            result = await session.execute(select(Agent).where(Agent.id == "test_delete_agent_001"))
            assert result.scalars().first() is None

            # 驗證績效記錄已級聯刪除
            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.agent_id == "test_delete_agent_001")
            )
            assert result.scalars().first() is None

            # 驗證交易記錄已級聯刪除
            result = await session.execute(
                select(Transaction).where(Transaction.agent_id == "test_delete_agent_001")
            )
            assert result.scalars().first() is None

    @pytest.mark.asyncio
    async def test_delete_agent_with_multiple_performance_records(
        self, async_engine, async_session_factory
    ):
        """
        測試刪除有多個績效記錄的 Agent

        確保級聯刪除能處理多個相關記錄
        """
        async with async_session_factory() as session:
            # 建立 Agent
            agent = Agent(
                id="test_delete_multi_agent",
                name="多記錄刪除測試",
                initial_funds=Decimal("500000"),
                current_funds=Decimal("450000"),
            )
            session.add(agent)
            await session.flush()

            # 建立多個績效記錄
            from datetime import timedelta

            today = date.today()
            for i in range(5):
                performance = AgentPerformance(
                    agent_id="test_delete_multi_agent",
                    date=today - timedelta(days=i),
                    total_value=Decimal("100000") - Decimal(i * 5000),
                    cash_balance=Decimal("50000"),
                    total_trades=i * 10,
                    sell_trades_count=i * 5,  # 修正: 賣出交易數
                    winning_trades_correct=0,  # 修正: 真實獲利交易數
                )
                session.add(performance)

            await session.commit()

            # 驗證 5 個績效記錄已建立
            result = await session.execute(
                select(AgentPerformance).where(
                    AgentPerformance.agent_id == "test_delete_multi_agent"
                )
            )
            records = result.scalars().all()
            assert len(records) == 5

            # 刪除 Agent
            agent_to_delete = await session.get(Agent, "test_delete_multi_agent")
            await session.delete(agent_to_delete)
            await session.commit()

            # 驗證所有記錄都已刪除
            result = await session.execute(
                select(AgentPerformance).where(
                    AgentPerformance.agent_id == "test_delete_multi_agent"
                )
            )
            assert len(result.scalars().all()) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_agent(self, async_session_factory):
        """
        測試刪除不存在的 Agent

        確保適當處理不存在的記錄
        """
        async with async_session_factory() as session:
            # 嘗試查詢不存在的 Agent
            result = await session.execute(select(Agent).where(Agent.id == "nonexistent_agent"))
            agent = result.scalars().first()
            assert agent is None

    @pytest.mark.asyncio
    async def test_cascade_delete_validation(self, async_engine, async_session_factory):
        """
        測試級聯刪除驗證

        確保 SQLAlchemy ORM 的級聯刪除規則正確配置
        """
        async with async_session_factory() as session:
            # 建立 Agent 和相關資料
            agent = Agent(
                id="cascade_test_agent",
                name="級聯刪除測試",
                initial_funds=Decimal("100000"),
                current_funds=Decimal("100000"),
            )

            performance = AgentPerformance(
                agent_id="cascade_test_agent",
                date=date.today(),
                total_value=Decimal("100000"),
                cash_balance=Decimal("100000"),
            )

            transaction = Transaction(
                id="cascade_trans_001",
                agent_id="cascade_test_agent",
                ticker="2330",
                action=TransactionAction.BUY,
                quantity=10,
                price=Decimal("600.0"),
                total_amount=Decimal("6000.0"),
            )

            agent.performance_records = [performance]
            agent.transactions = [transaction]

            session.add(agent)
            await session.commit()

            # 取得 agent 的關聯物件 ID
            perf_id = performance.id
            trans_id = transaction.id

            # 刪除 Agent
            agent_to_delete = await session.get(Agent, "cascade_test_agent")
            await session.delete(agent_to_delete)
            await session.commit()

            # 驗證所有關聯物件都已刪除
            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.id == perf_id)
            )
            assert result.scalars().first() is None

            result = await session.execute(select(Transaction).where(Transaction.id == trans_id))
            assert result.scalars().first() is None
