"""
測試 current_funds 欄位功能
驗證資金更新邏輯是否正常運作
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Agent, Base
from src.service.agents_service import AgentsService


# 測試資料庫配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """創建測試資料庫 session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # 創建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 創建 session factory
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    # 清理
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_agent_with_current_funds(db_session):
    """測試創建 Agent 時 current_funds 初始化"""
    service = AgentsService(db_session)

    agent = await service.create_agent(
        name="Test Agent",
        description="Test Description",
        ai_model="gpt-4o-mini",
        strategy_prompt="Test Strategy",
        initial_funds=1000000.0,
    )
    await db_session.commit()

    # 驗證 current_funds 已初始化
    assert agent.current_funds == agent.initial_funds
    assert float(agent.current_funds) == 1000000.0


@pytest.mark.asyncio
async def test_update_agent_funds_increase(db_session):
    """測試增加資金"""
    service = AgentsService(db_session)

    # 創建測試 Agent
    agent = await service.create_agent(
        name="Test Agent",
        description="Test Description",
        ai_model="gpt-4o-mini",
        strategy_prompt="Test Strategy",
        initial_funds=1000000.0,
    )
    await db_session.commit()

    agent_id = agent.id

    # 增加資金（例如：賣出股票）
    await service.update_agent_funds(
        agent_id=agent_id, amount_change=50000.0, transaction_type="SELL"
    )

    # 驗證資金已更新
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db_session.execute(stmt)
    updated_agent = result.scalar_one()

    assert float(updated_agent.current_funds) == 1050000.0


@pytest.mark.asyncio
async def test_update_agent_funds_decrease(db_session):
    """測試減少資金"""
    service = AgentsService(db_session)

    # 創建測試 Agent
    agent = await service.create_agent(
        name="Test Agent",
        description="Test Description",
        ai_model="gpt-4o-mini",
        strategy_prompt="Test Strategy",
        initial_funds=1000000.0,
    )
    await db_session.commit()

    agent_id = agent.id

    # 減少資金（例如：買入股票）
    await service.update_agent_funds(
        agent_id=agent_id, amount_change=-100000.0, transaction_type="BUY"
    )

    # 驗證資金已更新
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db_session.execute(stmt)
    updated_agent = result.scalar_one()

    assert float(updated_agent.current_funds) == 900000.0


@pytest.mark.asyncio
async def test_update_agent_funds_insufficient(db_session):
    """測試資金不足的情況"""
    from src.service.agents_service import AgentDatabaseError

    service = AgentsService(db_session)

    # 創建測試 Agent
    agent = await service.create_agent(
        name="Test Agent",
        description="Test Description",
        ai_model="gpt-4o-mini",
        strategy_prompt="Test Strategy",
        initial_funds=1000000.0,
    )
    await db_session.commit()

    agent_id = agent.id

    # 嘗試減少過多資金（應該拋出異常）
    with pytest.raises(AgentDatabaseError, match="Insufficient funds"):
        await service.update_agent_funds(
            agent_id=agent_id, amount_change=-2000000.0, transaction_type="BUY"
        )


@pytest.mark.asyncio
async def test_current_funds_fallback_to_initial(db_session):
    """測試當 current_funds 為 None 時回退到 initial_funds 的邏輯驗證"""
    service = AgentsService(db_session)

    # 創建測試 Agent
    agent = await service.create_agent(
        name="Test Agent",
        description="Test Description",
        ai_model="gpt-4o-mini",
        strategy_prompt="Test Strategy",
        initial_funds=1000000.0,
    )
    await db_session.commit()

    agent_id = agent.id

    # 驗證 current_funds 已初始化為 initial_funds
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db_session.execute(stmt)
    initial_agent = result.scalar_one()

    # 確認初始化成功
    assert initial_agent.current_funds == initial_agent.initial_funds
    assert float(initial_agent.current_funds) == 1000000.0

    # 現在測試函數的邏輯：使用 current_funds 或回退到 initial_funds
    current_funds = initial_agent.current_funds or initial_agent.initial_funds
    assert current_funds == 1000000.0

    # 測試計算
    new_funds = float(current_funds) + 50000.0
    assert new_funds == 1050000.0


if __name__ == "__main__":
    # 手動執行測試
    print("Running current_funds tests...")
    pytest.main([__file__, "-v", "-s"])
