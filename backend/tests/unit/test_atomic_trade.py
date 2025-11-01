"""
Unit tests for atomic trade execution

Tests the execute_trade_atomic function to ensure all operations are performed
atomically: all succeed or all fail with automatic rollback.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from trading.tools.trading_tools import execute_trade_atomic


@pytest.mark.asyncio
async def test_execute_trade_atomic_buy_success(mock_agent_service):
    """Verify successful atomic BUY trade execution

    All operations should succeed and be committed within the transaction.
    """
    # Arrange
    agent_id = "test_agent_1"
    ticker = "2330"
    quantity = 1000
    price = 520.0

    mock_agent_service.get_agent_config = AsyncMock(return_value=MagicMock(id=agent_id))
    mock_agent_service.create_transaction = AsyncMock(return_value=MagicMock(id="txn_123"))
    mock_agent_service.update_agent_holdings = AsyncMock()
    mock_agent_service.update_agent_funds = AsyncMock()
    mock_agent_service.calculate_and_update_performance = AsyncMock()

    # Mock session context manager for transaction
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=None)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    mock_agent_service.session.begin = MagicMock(return_value=mock_session_context)

    # Act
    result = await execute_trade_atomic(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=quantity,
        price=price,
        decision_reason="Test BUY",
        company_name="TSMC",
        casual_market_mcp=None,
    )

    # Assert - Success message
    assert "✅" in result
    assert "原子操作" in result
    assert ticker in result
    assert "BUY" in result
    assert "1,000" in result  # Quantity is formatted with commas

    # Verify all operations were called
    mock_agent_service.get_agent_config.assert_called_once_with(agent_id)
    mock_agent_service.create_transaction.assert_called_once()
    mock_agent_service.update_agent_holdings.assert_called_once()
    mock_agent_service.update_agent_funds.assert_called_once()
    mock_agent_service.calculate_and_update_performance.assert_called_once()

    # Verify transaction context was used
    mock_agent_service.session.begin.assert_called_once()


@pytest.mark.asyncio
async def test_execute_trade_atomic_sell_success(mock_agent_service):
    """Verify successful atomic SELL trade execution"""
    # Arrange
    agent_id = "test_agent_1"
    ticker = "2330"
    quantity = 1000
    price = 530.0

    mock_agent_service.get_agent_config = AsyncMock(return_value=MagicMock(id=agent_id))
    mock_agent_service.create_transaction = AsyncMock(return_value=MagicMock(id="txn_456"))
    mock_agent_service.update_agent_holdings = AsyncMock()
    mock_agent_service.update_agent_funds = AsyncMock()
    mock_agent_service.calculate_and_update_performance = AsyncMock()

    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=None)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    mock_agent_service.session.begin = MagicMock(return_value=mock_session_context)

    # Act
    result = await execute_trade_atomic(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker=ticker,
        action="SELL",
        quantity=quantity,
        price=price,
        decision_reason="Test SELL",
        company_name="TSMC",
        casual_market_mcp=None,
    )

    # Assert
    assert "✅" in result
    assert "SELL" in result
    assert ticker in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_invalid_action():
    """Verify invalid action is rejected"""
    # Arrange
    mock_agent_service = MagicMock()
    agent_id = "test_agent_1"

    # Act & Assert
    result = await execute_trade_atomic(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker="2330",
        action="INVALID",  # Invalid action
        quantity=1000,
        price=520.0,
        casual_market_mcp=None,
    )

    # Should return error message
    assert "❌" in result
    assert "無效的 action" in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_invalid_quantity():
    """Verify invalid quantity is rejected

    Quantity must be positive and a multiple of 1000.
    """
    mock_agent_service = MagicMock()
    agent_id = "test_agent_1"

    # Test: negative quantity
    result = await execute_trade_atomic(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=-1000,
        price=520.0,
        casual_market_mcp=None,
    )
    assert "❌" in result
    assert "正整數" in result

    # Test: quantity not multiple of 1000
    result = await execute_trade_atomic(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=1500,  # Not a multiple of 1000
        price=520.0,
        casual_market_mcp=None,
    )
    assert "❌" in result
    assert "1000 的倍數" in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_failure_rollback(mock_agent_service):
    """Verify transaction rollback on failure

    When any operation fails, the entire transaction should be rolled back.
    """
    # Arrange
    agent_id = "test_agent_1"
    ticker = "2330"

    mock_agent_service.get_agent_config = AsyncMock(return_value=MagicMock(id=agent_id))

    # Simulate failure in update_agent_funds
    mock_agent_service.create_transaction = AsyncMock(return_value=MagicMock(id="txn_123"))
    mock_agent_service.update_agent_holdings = AsyncMock()
    mock_agent_service.update_agent_funds = AsyncMock(
        side_effect=Exception("DB Error - Fund update failed")
    )
    mock_agent_service.calculate_and_update_performance = AsyncMock()

    # Mock transaction context to simulate rollback
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=None)
    # Simulate transaction failure (exception in context)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)

    mock_agent_service.session.begin = MagicMock(return_value=mock_session_context)

    # Act
    result = await execute_trade_atomic(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=1000,
        price=520.0,
        casual_market_mcp=None,
    )

    # Assert - Error message
    assert "❌" in result
    assert "回滾" in result
    assert "恢復" in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_agent_not_found(mock_agent_service):
    """Verify error when agent not found"""
    # Arrange
    agent_id = "nonexistent_agent"

    from service.agents_service import AgentNotFoundError

    mock_agent_service.get_agent_config = AsyncMock(
        side_effect=AgentNotFoundError(f"Agent '{agent_id}' not found")
    )

    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=None)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    mock_agent_service.session.begin = MagicMock(return_value=mock_session_context)

    # Act
    result = await execute_trade_atomic(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=520.0,
        casual_market_mcp=None,
    )

    # Assert
    assert "❌" in result
    assert "回滾" in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_funds_calculation_buy(mock_agent_service):
    """Verify correct fund calculation for BUY operation

    For BUY: funds_change = -(total_amount + commission)
    """
    # Arrange
    agent_id = "test_agent_1"
    ticker = "2330"
    quantity = 1000
    price = 520.0

    mock_agent_service.get_agent_config = AsyncMock(return_value=MagicMock(id=agent_id))
    mock_agent_service.create_transaction = AsyncMock(return_value=MagicMock(id="txn_123"))
    mock_agent_service.update_agent_holdings = AsyncMock()
    mock_agent_service.update_agent_funds = AsyncMock()
    mock_agent_service.calculate_and_update_performance = AsyncMock()

    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=None)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    mock_agent_service.session.begin = MagicMock(return_value=mock_session_context)

    # Act
    await execute_trade_atomic(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=quantity,
        price=price,
        casual_market_mcp=None,
    )

    # Assert - Verify update_agent_funds was called with correct amount_change
    # For BUY with no commission from MCP, it should be -(520.0 * 1000 + 0)
    call_args = mock_agent_service.update_agent_funds.call_args
    assert call_args is not None

    amount_change = call_args.kwargs["amount_change"]
    expected_change = -(quantity * price)  # -(total_amount + 0 commission)
    assert amount_change == expected_change


@pytest.mark.asyncio
async def test_execute_trade_atomic_funds_calculation_sell(mock_agent_service):
    """Verify correct fund calculation for SELL operation

    For SELL: funds_change = total_amount - commission
    """
    # Arrange
    agent_id = "test_agent_1"
    ticker = "2330"
    quantity = 1000
    price = 530.0

    mock_agent_service.get_agent_config = AsyncMock(return_value=MagicMock(id=agent_id))
    mock_agent_service.create_transaction = AsyncMock(return_value=MagicMock(id="txn_123"))
    mock_agent_service.update_agent_holdings = AsyncMock()
    mock_agent_service.update_agent_funds = AsyncMock()
    mock_agent_service.calculate_and_update_performance = AsyncMock()

    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=None)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    mock_agent_service.session.begin = MagicMock(return_value=mock_session_context)

    # Act
    await execute_trade_atomic(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker=ticker,
        action="SELL",
        quantity=quantity,
        price=price,
        casual_market_mcp=None,
    )

    # Assert
    call_args = mock_agent_service.update_agent_funds.call_args
    assert call_args is not None

    amount_change = call_args.kwargs["amount_change"]
    expected_change = quantity * price  # total_amount - 0 commission
    assert amount_change == expected_change


@pytest.mark.asyncio
async def test_execute_trade_atomic_transaction_fields(mock_agent_service):
    """Verify all transaction fields are created correctly"""
    # Arrange
    agent_id = "test_agent_1"
    ticker = "2330"
    quantity = 1000
    price = 520.0
    reason = "Technical breakout"
    company = "TSMC"

    mock_agent_service.get_agent_config = AsyncMock(return_value=MagicMock(id=agent_id))
    mock_agent_service.create_transaction = AsyncMock(return_value=MagicMock(id="txn_123"))
    mock_agent_service.update_agent_holdings = AsyncMock()
    mock_agent_service.update_agent_funds = AsyncMock()
    mock_agent_service.calculate_and_update_performance = AsyncMock()

    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=None)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    mock_agent_service.session.begin = MagicMock(return_value=mock_session_context)

    # Act
    await execute_trade_atomic(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=quantity,
        price=price,
        decision_reason=reason,
        company_name=company,
        casual_market_mcp=None,
    )

    # Assert - Verify create_transaction was called with correct parameters
    call_args = mock_agent_service.create_transaction.call_args
    assert call_args is not None

    kwargs = call_args.kwargs
    assert kwargs["agent_id"] == agent_id
    assert kwargs["ticker"] == ticker
    assert kwargs["action"] == "BUY"
    assert kwargs["quantity"] == quantity
    assert kwargs["price"] == price
    assert kwargs["company_name"] == company
    assert kwargs["decision_reason"] == reason
    assert kwargs["status"] == "COMPLETED"


@pytest.fixture
def mock_agent_service():
    """Fixture for mock agent service"""
    return MagicMock()
