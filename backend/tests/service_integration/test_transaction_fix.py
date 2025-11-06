"""
測試 transaction issue 修正

驗證 execute_trade_atomic 能否正確處理事務，不會拋出
「A transaction is already begun on this Session」錯誤
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from service.trading_service import TradingService
from database.models import Base, Agent
import uuid


@pytest.fixture
async def async_engine():
    """建立臨時測試資料庫"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    """建立測試 session"""
    async_session = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def sample_agent(db_session: AsyncSession):
    """建立測試用的 Agent"""
    agent = Agent(
        id=str(uuid.uuid4()),
        name="TestAgent",
        description="測試 Agent",
        ai_model="gpt-4",
        initial_funds=Decimal("1000000"),
        current_funds=Decimal("1000000"),
    )

    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    return agent


@pytest.mark.asyncio
async def test_execute_trade_atomic_no_transaction_conflict(
    db_session: AsyncSession,
    sample_agent: Agent,
):
    """
    測試: execute_trade_atomic 不會拋出 transaction conflict 錯誤

    預期: 交易成功完成，沒有「A transaction is already begun」錯誤
    """
    # Arrange
    trading_service = TradingService(db_session)
    agent_id = sample_agent.id
    ticker = "2330"
    initial_funds = sample_agent.current_funds or sample_agent.initial_funds

    # Act - 執行原子交易
    result = await trading_service.execute_trade_atomic(
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=1000,
        price=Decimal("500"),
        company_name="台積電",
        decision_reason="測試交易",
    )

    # Assert - 交易應該成功
    assert result["success"] is True, f"交易失敗: {result.get('error')}"
    assert result["transaction_id"] is not None
    assert "交易執行成功" in result["message"]

    # Verify - 檢查資料庫狀態
    await db_session.refresh(sample_agent)

    # 檢查持股被創建
    holdings = await trading_service.agents_service.get_agent_holdings(agent_id)
    assert len(holdings) > 0, "持股應該被創建"

    holding = next((h for h in holdings if h.ticker == ticker), None)
    assert holding is not None, f"應該找到 {ticker} 的持股"
    assert holding.quantity == 1000

    # 檢查交易被記錄
    transactions = await trading_service.agents_service.get_agent_transactions(agent_id)
    assert len(transactions) > 0, "交易應該被記錄"

    # 檢查資金被扣除（購買成本 + 手續費）
    cost = 1000 * 500 + (1000 * 500 * Decimal("0.001425"))
    expected_funds = initial_funds - cost
    assert sample_agent.current_funds == expected_funds, "資金應該被正確扣除"


@pytest.mark.asyncio
async def test_execute_trade_atomic_multiple_trades(
    db_session: AsyncSession,
    sample_agent: Agent,
):
    """
    測試: 連續執行多個交易，確保沒有 transaction state 衝突
    """
    # Arrange
    trading_service = TradingService(db_session)
    agent_id = sample_agent.id

    # Act - 執行多個交易
    tickers = ["2330", "2454", "3008"]
    results = []

    for i, ticker in enumerate(tickers):
        result = await trading_service.execute_trade_atomic(
            agent_id=agent_id,
            ticker=ticker,
            action="BUY",
            quantity=1000,  # 每次買 1000 股，確保資金充足
            price=Decimal("100"),  # 降低股價以減少成本
            company_name=f"公司{i+1}",
            decision_reason=f"測試交易{i+1}",
        )
        results.append(result)

    # Assert - 所有交易都應該成功
    for i, result in enumerate(results):
        assert result["success"] is True, f"交易 {i+1} 失敗: {result.get('error')}"

    # Verify - 檢查所有持股
    holdings = await trading_service.agents_service.get_agent_holdings(agent_id)
    assert len(holdings) == 3, "應該有 3 個持股"


@pytest.mark.asyncio
async def test_execute_trade_atomic_sell_transaction(
    db_session: AsyncSession,
    sample_agent: Agent,
):
    """
    測試: 賣出交易的原子性
    """
    # Arrange - 先建立持股
    trading_service = TradingService(db_session)
    agent_id = sample_agent.id
    ticker = "2330"

    # 先買進（使用較低的價格以確保資金充足）
    buy_result = await trading_service.execute_trade_atomic(
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=2000,
        price=Decimal("100"),  # 降低股價
        company_name="台積電",
        decision_reason="建立持股",
    )
    assert buy_result["success"] is True

    # Act - 賣出
    sell_result = await trading_service.execute_trade_atomic(
        agent_id=agent_id,
        ticker=ticker,
        action="SELL",
        quantity=1000,
        price=Decimal("110"),
        company_name="台積電",
        decision_reason="部分賣出",
    )

    # Assert
    assert sell_result["success"] is True

    # Verify - 持股應該被更新
    holdings = await trading_service.agents_service.get_agent_holdings(agent_id)
    holding = next((h for h in holdings if h.ticker == ticker), None)
    assert holding is not None
    assert holding.quantity == 1000  # 2000 - 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
