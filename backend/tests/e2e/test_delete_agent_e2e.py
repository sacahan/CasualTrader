"""
Agent 刪除功能的端到端測試

測試真實的資料庫操作，確保級聯刪除正常運作
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
from database.models import Base, Agent, AgentPerformance


@pytest.fixture
async def async_db():
    """建立臨時測試資料庫"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # 建立所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 建立 Session 工廠
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    yield async_session

    await engine.dispose()


@pytest.mark.asyncio
class TestDeleteAgentE2E:
    """Agent 刪除功能端到端測試"""

    async def test_delete_agent_with_performance_records(self, async_db):
        """測試刪除有績效記錄的 Agent"""
        async with async_db() as session:
            # 建立 Agent
            agent = Agent(
                id="test_agent_001",
                name="測試代理",
                initial_funds=Decimal("100000"),
                current_funds=Decimal("100000"),
            )
            session.add(agent)
            await session.flush()

            # 建立績效記錄
            performance = AgentPerformance(
                agent_id="test_agent_001",
                date=date.today(),
                total_value=Decimal("100000"),
                cash_balance=Decimal("100000"),
            )
            session.add(performance)
            await session.commit()

            # 驗證記錄已建立
            from sqlalchemy import select

            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.agent_id == "test_agent_001")
            )
            assert result.scalars().first() is not None

            # 刪除 Agent（應該級聯刪除相關記錄）
            await session.delete(agent)
            await session.commit()

            # 驗證 Agent 已刪除
            result = await session.execute(select(Agent).where(Agent.id == "test_agent_001"))
            assert result.scalars().first() is None

            # 驗證績效記錄已級聯刪除
            result = await session.execute(
                select(AgentPerformance).where(AgentPerformance.agent_id == "test_agent_001")
            )
            assert result.scalars().first() is None

    async def test_delete_nonexistent_agent(self, async_db):
        """測試刪除不存在的 Agent"""
        async with async_db() as session:
            from sqlalchemy import select

            # 嘗試查詢不存在的 Agent
            result = await session.execute(select(Agent).where(Agent.id == "nonexistent"))
            agent = result.scalars().first()
            assert agent is None
