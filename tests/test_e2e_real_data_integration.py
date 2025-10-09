"""
End-to-End 測試 - 真實資料整合測試
測試所有模擬資料函數都已改為使用真實資料源

包含：
1. MCP Client 真實資料測試
2. Portfolio Queries 資料庫整合測試
3. 完整交易流程測試（含資料庫寫入）
"""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.agents.functions.portfolio_queries import PortfolioQueries
from src.agents.integrations.mcp_client import get_mcp_client
from src.database.models import (
    Agent,
    AgentHolding,
    Base,
    Transaction,
    TransactionAction,
    TransactionStatus,
)

# ==========================================
# 測試配置
# ==========================================


@pytest.fixture
async def db_engine():
    """創建測試資料庫引擎"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # 創建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """創建測試資料庫會話"""
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest.fixture
async def mcp_client():
    """創建 MCP 客戶端"""
    client = get_mcp_client()
    await client.initialize()
    yield client
    await client.close()


@pytest.fixture
async def test_agent(db_session: AsyncSession):
    """創建測試 Agent"""
    agent_state = Agent(
        id="test_agent_001",
        name="Test Trading Agent",
        instructions="Test trading instructions for automated trading",
        status="active",
        current_mode="TRADING",
        initial_funds=Decimal("1000000.0"),
        config={
            "risk_tolerance": 0.5,
            "max_position_size": 0.2,
        },
    )

    db_session.add(agent_state)
    await db_session.commit()
    await db_session.refresh(agent_state)

    return agent_state


# ==========================================
# MCP Client 真實資料測試
# ==========================================


class TestMCPClientRealData:
    """測試 MCP Client 使用真實資料源"""

    @pytest.mark.asyncio
    async def test_get_stock_price_real_data(self, mcp_client):
        """測試獲取真實股價數據"""
        # 測試台積電股價
        result = await mcp_client.get_stock_price("2330")

        # 驗證返回數據結構
        assert "symbol" in result
        assert result["symbol"] == "2330"
        assert "current_price" in result
        assert "company_name" in result
        assert "volume" in result
        assert "last_update" in result

        # 驗證價格為合理數值（台積電股價應在 100-2000 之間）
        assert 100 < result["current_price"] < 2000

        # 驗證數據來源
        assert "data_source" in result
        print(f"✅ Stock price data source: {result.get('data_source', 'MCP')}")

    @pytest.mark.asyncio
    async def test_get_company_profile_real_data(self, mcp_client):
        """測試獲取真實公司資料"""
        result = await mcp_client.get_company_profile("2330")

        assert "symbol" in result
        assert "company_name" in result
        assert "industry" in result
        assert "sector" in result

        # 驗證台積電公司名稱（包含 Taiwan Semiconductor）
        company_name_upper = result["company_name"].upper()
        assert (
            "台積電" in result["company_name"]
            or "TSMC" in company_name_upper
            or "TAIWAN SEMICONDUCTOR" in company_name_upper
        )

        print(f"✅ Company: {result['company_name']}, Industry: {result['industry']}")

    @pytest.mark.asyncio
    async def test_get_income_statement_real_data(self, mcp_client):
        """測試獲取真實損益表數據"""
        result = await mcp_client.get_income_statement("2330")

        assert "symbol" in result
        assert "revenue" in result
        assert "net_income" in result

        # 驗證營收為合理數值（台積電年營收應為正數）
        assert result["revenue"] > 0

        print(
            f"✅ Revenue: {result['revenue']:,.0f}, Net Income: {result['net_income']:,.0f}"
        )

    @pytest.mark.asyncio
    async def test_check_trading_day(self, mcp_client):
        """測試檢查交易日"""
        # 測試週末（非交易日）
        result_weekend = await mcp_client.check_trading_day("2025-10-11")  # 週六
        assert result_weekend["is_weekend"] is True
        assert result_weekend["is_trading_day"] is False

        # 測試國慶日（非交易日）
        result_holiday = await mcp_client.check_trading_day("2025-10-10")
        assert result_holiday["is_holiday"] is True
        assert result_holiday["is_trading_day"] is False

        # 測試一般工作日（交易日）
        result_trading = await mcp_client.check_trading_day("2025-10-09")
        # 注意：這裡可能是交易日也可能不是，取決於實際日期
        assert "is_trading_day" in result_trading

        print("✅ Trading day check works correctly")


# ==========================================
# Portfolio Queries 資料庫整合測試
# ==========================================


class TestPortfolioQueriesDatabase:
    """測試 Portfolio Queries 使用真實資料庫"""

    @pytest.mark.asyncio
    async def test_get_cash_balance_from_db(
        self, db_session: AsyncSession, test_agent, mcp_client
    ):
        """測試從資料庫獲取現金餘額"""
        portfolio_queries = PortfolioQueries(db_session, mcp_client)

        # 獲取現金餘額
        cash = await portfolio_queries._get_cash_balance(
            test_agent.id, test_agent.initial_funds
        )

        # 應該等於初始資金（尚無交易）
        assert cash == 1000000.0

        print(f"✅ Cash balance from DB: {cash:,.2f}")

    @pytest.mark.asyncio
    async def test_get_positions_from_db(
        self, db_session: AsyncSession, test_agent, mcp_client
    ):
        """測試從資料庫獲取持倉"""
        # 創建測試持倉
        holding = AgentHolding(
            agent_id=test_agent.id,
            symbol="2330",
            company_name="TSMC",
            quantity=1000,
            average_cost=Decimal("580.0"),
            total_cost=Decimal("580000.0"),
        )
        db_session.add(holding)
        await db_session.commit()

        # 查詢持倉
        portfolio_queries = PortfolioQueries(db_session, mcp_client)
        positions = await portfolio_queries._get_positions_data(test_agent.id)

        assert len(positions) == 1
        assert positions[0]["symbol"] == "2330"
        assert positions[0]["quantity"] == 1000

        print(f"✅ Positions from DB: {len(positions)} position(s)")

    @pytest.mark.asyncio
    async def test_portfolio_summary_from_db(
        self, db_session: AsyncSession, test_agent, mcp_client
    ):
        """測試獲取完整投資組合摘要"""
        # 創建測試持倉
        holding1 = AgentHolding(
            agent_id=test_agent.id,
            symbol="2330",
            company_name="TSMC",
            quantity=1000,
            average_cost=Decimal("580.0"),
            total_cost=Decimal("580000.0"),
        )
        holding2 = AgentHolding(
            agent_id=test_agent.id,
            symbol="2317",
            company_name="Hon Hai",
            quantity=2000,
            average_cost=Decimal("120.0"),
            total_cost=Decimal("240000.0"),
        )
        db_session.add_all([holding1, holding2])
        await db_session.commit()

        # 獲取投資組合摘要
        portfolio_queries = PortfolioQueries(db_session, mcp_client)
        summary = await portfolio_queries.get_portfolio_summary(test_agent.id)

        # 驗證摘要數據
        assert summary["agent_id"] == test_agent.id
        assert summary["num_positions"] == 2
        assert "total_market_value" in summary
        assert "unrealized_pnl" in summary
        assert "cash_balance" in summary

        # 驗證現金餘額（沒有 Transaction 記錄時，應為初始資金）
        # 注意：持倉是直接創建的，沒有通過交易記錄，所以不會扣除現金
        assert summary["cash_balance"] == 1000000.0

        print(
            f"✅ Portfolio summary: {summary['num_positions']} positions, "
            f"Total value: {summary['total_value']:,.2f}"
        )


# ==========================================
# 完整交易流程測試（含資料庫寫入）
# ==========================================


class TestCompleteTradeFlow:
    """測試完整的交易流程，包含資料庫寫入"""

    @pytest.mark.asyncio
    async def test_buy_trade_with_db_write(
        self, db_session: AsyncSession, test_agent, mcp_client
    ):
        """測試買入交易並寫入資料庫"""
        # 執行買入交易
        trade_result = await mcp_client.execute_buy(
            symbol="2330", quantity=1000, price=590.0
        )

        # 驗證交易結果
        assert trade_result["action"] == "buy"
        assert trade_result["symbol"] == "2330"
        assert trade_result["quantity"] == 1000

        # 寫入資料庫
        action_map = {"buy": TransactionAction.BUY, "sell": TransactionAction.SELL}
        qty = trade_result["quantity"]
        price = trade_result["price"]
        trade = Transaction(
            agent_id=test_agent.id,
            symbol=trade_result["symbol"],
            action=action_map[trade_result["action"]],
            quantity=qty,
            price=Decimal(str(price)),
            total_amount=Decimal(str(qty * price)),
            commission=Decimal(str(trade_result["fee"])),
            status=TransactionStatus.EXECUTED,
            execution_time=datetime.now(),
            created_at=datetime.now(),
        )
        db_session.add(trade)

        # 更新或創建持倉
        stmt = select(AgentHolding).where(
            AgentHolding.agent_id == test_agent.id, AgentHolding.symbol == "2330"
        )
        result = await db_session.execute(stmt)
        holding = result.scalar_one_or_none()

        if holding:
            # 更新現有持倉
            old_total = float(holding.total_cost)
            new_cost = trade_result["quantity"] * trade_result["price"]
            new_quantity = holding.quantity + trade_result["quantity"]
            new_total = old_total + new_cost
            holding.quantity = new_quantity
            holding.average_cost = Decimal(str(new_total / new_quantity))
            holding.total_cost = Decimal(str(new_total))
        else:
            # 創建新持倉
            qty = trade_result["quantity"]
            price = trade_result["price"]
            holding = AgentHolding(
                agent_id=test_agent.id,
                symbol="2330",
                company_name="TSMC",
                quantity=qty,
                average_cost=Decimal(str(price)),
                total_cost=Decimal(str(qty * price)),
            )
            db_session.add(holding)

        await db_session.commit()

        # 驗證資料庫記錄
        stmt = select(Transaction).where(Transaction.agent_id == test_agent.id)
        result = await db_session.execute(stmt)
        trades = result.scalars().all()
        assert len(trades) == 1

        stmt = select(AgentHolding).where(AgentHolding.agent_id == test_agent.id)
        result = await db_session.execute(stmt)
        holdings = result.scalars().all()
        assert len(holdings) == 1
        assert holdings[0].quantity == 1000

        print("✅ Buy trade executed and saved to DB")

    @pytest.mark.asyncio
    async def test_sell_trade_with_db_write(
        self, db_session: AsyncSession, test_agent, mcp_client
    ):
        """測試賣出交易並寫入資料庫"""
        # 先創建持倉
        holding = AgentHolding(
            agent_id=test_agent.id,
            symbol="2330",
            company_name="TSMC",
            quantity=2000,
            average_cost=Decimal("580.0"),
            total_cost=Decimal("1160000.0"),
        )
        db_session.add(holding)
        await db_session.commit()

        # 執行賣出交易
        trade_result = await mcp_client.execute_sell(
            symbol="2330", quantity=1000, price=595.0
        )

        # 驗證交易結果
        assert trade_result["action"] == "sell"
        assert trade_result["symbol"] == "2330"
        assert trade_result["quantity"] == 1000

        # 寫入交易記錄
        action_map = {"buy": TransactionAction.BUY, "sell": TransactionAction.SELL}
        qty = trade_result["quantity"]
        price = trade_result["price"]
        trade = Transaction(
            agent_id=test_agent.id,
            symbol=trade_result["symbol"],
            action=action_map[trade_result["action"]],
            quantity=qty,
            price=Decimal(str(price)),
            total_amount=Decimal(str(qty * price)),
            commission=Decimal(str(trade_result["fee"])),
            status=TransactionStatus.EXECUTED,
            execution_time=datetime.now(),
            created_at=datetime.now(),
        )
        db_session.add(trade)

        # 更新持倉
        await db_session.refresh(holding)
        holding.quantity -= trade_result["quantity"]

        await db_session.commit()

        # 驗證持倉更新
        await db_session.refresh(holding)
        assert holding.quantity == 1000  # 2000 - 1000 = 1000

        print("✅ Sell trade executed and saved to DB")

    @pytest.mark.asyncio
    async def test_complete_e2e_flow(
        self, db_session: AsyncSession, test_agent, mcp_client
    ):
        """
        完整的 End-to-End 流程測試
        1. 創建 Agent
        2. 執行多筆買入交易
        3. 執行賣出交易
        4. 查詢投資組合
        5. 計算績效指標
        """
        portfolio_queries = PortfolioQueries(db_session, mcp_client)

        # Step 1: 檢查初始狀態
        initial_summary = await portfolio_queries.get_portfolio_summary(test_agent.id)
        assert initial_summary["cash_balance"] == 1000000.0
        assert initial_summary["num_positions"] == 0

        print(f"✅ Initial cash: {initial_summary['cash_balance']:,.2f}")

        # Step 2: 執行第一筆買入（台積電）
        trade1 = await mcp_client.execute_buy(symbol="2330", quantity=1000, price=590.0)

        db_trade1 = Transaction(
            agent_id=test_agent.id,
            symbol="2330",
            action=TransactionAction.BUY,
            quantity=1000,
            price=Decimal("590.0"),
            total_amount=Decimal("590000.0"),
            commission=Decimal(str(trade1["fee"])),
            status=TransactionStatus.EXECUTED,
            execution_time=datetime.now(),
            created_at=datetime.now(),
        )
        db_session.add(db_trade1)

        holding1 = AgentHolding(
            agent_id=test_agent.id,
            symbol="2330",
            company_name="TSMC",
            quantity=1000,
            average_cost=Decimal("590.0"),
            total_cost=Decimal("590000.0"),
        )
        db_session.add(holding1)
        await db_session.commit()

        print("✅ Buy 1000 shares of 2330 at 590.0")

        # Step 3: 執行第二筆買入（鴻海）
        trade2 = await mcp_client.execute_buy(symbol="2317", quantity=2000, price=120.0)

        db_trade2 = Transaction(
            agent_id=test_agent.id,
            symbol="2317",
            action=TransactionAction.BUY,
            quantity=2000,
            price=Decimal("120.0"),
            total_amount=Decimal("240000.0"),
            commission=Decimal(str(trade2["fee"])),
            status=TransactionStatus.EXECUTED,
            execution_time=datetime.now(),
            created_at=datetime.now(),
        )
        db_session.add(db_trade2)

        holding2 = AgentHolding(
            agent_id=test_agent.id,
            symbol="2317",
            company_name="Hon Hai",
            quantity=2000,
            average_cost=Decimal("120.0"),
            total_cost=Decimal("240000.0"),
        )
        db_session.add(holding2)
        await db_session.commit()

        print("✅ Buy 2000 shares of 2317 at 120.0")

        # Step 4: 查詢投資組合
        portfolio = await portfolio_queries.get_portfolio_summary(test_agent.id)

        assert portfolio["num_positions"] == 2
        # 現金 = 1,000,000 - 590,000 - 240,000 - 手續費 ≈ 168,817
        expected_cash = 1000000.0 - (1000 * 590.0) - (2000 * 120.0)
        assert abs(portfolio["cash_balance"] - expected_cash) < 2000  # 允許手續費誤差

        print(f"✅ Portfolio has {portfolio['num_positions']} positions")
        print(f"   Cash balance: {portfolio['cash_balance']:,.2f}")
        print(f"   Total value: {portfolio['total_value']:,.2f}")

        # Step 5: 執行賣出交易
        await db_session.refresh(holding1)
        trade3 = await mcp_client.execute_sell(symbol="2330", quantity=500, price=600.0)

        db_trade3 = Transaction(
            agent_id=test_agent.id,
            symbol="2330",
            action=TransactionAction.SELL,
            quantity=500,
            price=Decimal("600.0"),
            total_amount=Decimal("300000.0"),
            commission=Decimal(str(trade3["fee"])),
            status=TransactionStatus.EXECUTED,
            execution_time=datetime.now(),
            created_at=datetime.now(),
        )
        db_session.add(db_trade3)

        # Update holding
        holding1.quantity -= 500
        old_total = float(holding1.total_cost)
        sold_cost = 500 * float(holding1.average_cost)
        holding1.total_cost = Decimal(str(old_total - sold_cost))
        await db_session.commit()

        print("✅ Sell 500 shares of 2330 at 600.0")

        # Step 6: 查詢最終狀態和績效
        final_summary = await portfolio_queries.get_portfolio_summary(test_agent.id)
        # TODO: Implement get_performance_metrics and get_trade_history methods
        # performance = await portfolio_queries.get_performance_metrics(test_agent.id)

        # 驗證持倉
        assert final_summary["num_positions"] == 2  # 仍有2個持倉（台積電剩500股）

        # 驗證基本資料
        assert final_summary["cash_balance"] > 0
        assert final_summary["total_value"] > 0

        print("✅ Final summary:")
        print(f"   Cash balance: {final_summary['cash_balance']:,.2f}")
        print(f"   Total value: {final_summary['total_value']:,.2f}")
        print(f"   Positions: {final_summary['num_positions']}")

        # 整合測試通過
        print("\n🎉 Complete E2E test PASSED!")


# ==========================================
# 運行測試
# ==========================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
