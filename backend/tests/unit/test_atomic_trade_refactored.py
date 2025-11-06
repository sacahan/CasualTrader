"""
Unit tests for atomic trade execution with TradingService

Tests the atomic trade functionality after refactoring:
- TradingService.execute_trade_atomic() manages the complete transaction
- All operations succeed or all rollback
- No skip_commit parameters needed
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from service.trading_service import TradingService


@pytest.mark.asyncio
async def test_trading_service_execute_trade_atomic_buy_success():
    """Verify successful atomic BUY trade execution in TradingService

    All operations should succeed and be committed within the transaction.
    """
    # Arrange
    agent_id = "test_agent_1"
    ticker = "2330"
    quantity = 1000
    price = 520.0

    # Mock db_session
    mock_db_session = AsyncMock()
    mock_session_begin = AsyncMock()
    mock_session_begin.__aenter__ = AsyncMock(return_value=None)
    mock_session_begin.__aexit__ = AsyncMock(return_value=None)
    mock_db_session.begin_nested = MagicMock(return_value=mock_session_begin)

    # Mock agents_service
    mock_agents_service = AsyncMock()
    mock_agents_service.get_agent_config = AsyncMock(
        return_value=MagicMock(
            id=agent_id,
            initial_funds=Decimal("1000000"),
            current_funds=Decimal("1000000"),
        )
    )

    # Create TradingService
    trading_service = TradingService(db_session=mock_db_session)
    trading_service.agents_service = mock_agents_service

    # Mock the private internal methods
    trading_service._create_transaction_internal = AsyncMock(return_value=MagicMock(id="txn_123"))
    trading_service._update_agent_holdings_internal = AsyncMock()
    trading_service._update_agent_funds_internal = AsyncMock()
    trading_service._calculate_and_update_performance_internal = AsyncMock()

    # Act
    result = await trading_service.execute_trade_atomic(
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=quantity,
        price=price,
        decision_reason="Test BUY",
        company_name="TSMC",
    )

    # Assert - Success
    assert result["success"] is True
    assert result["transaction_id"] == "txn_123"
    assert "成功" in result["message"]

    # Verify all internal methods were called
    trading_service._create_transaction_internal.assert_called_once()
    trading_service._update_agent_holdings_internal.assert_called_once()
    trading_service._update_agent_funds_internal.assert_called_once()
    trading_service._calculate_and_update_performance_internal.assert_called_once()

    # Verify transaction context was used
    mock_db_session.begin_nested.assert_called_once()


@pytest.mark.asyncio
async def test_trading_service_execute_trade_atomic_sell_success():
    """Verify successful atomic SELL trade execution"""
    # Arrange
    agent_id = "test_agent_1"
    ticker = "2330"
    quantity = 1000
    price = 530.0

    mock_db_session = AsyncMock()
    mock_session_begin = AsyncMock()
    mock_session_begin.__aenter__ = AsyncMock(return_value=None)
    mock_session_begin.__aexit__ = AsyncMock(return_value=None)
    mock_db_session.begin_nested = MagicMock(return_value=mock_session_begin)

    mock_agents_service = AsyncMock()
    mock_agents_service.get_agent_config = AsyncMock(
        return_value=MagicMock(
            id=agent_id,
            initial_funds=Decimal("1000000"),
            current_funds=Decimal("500000"),
        )
    )

    trading_service = TradingService(db_session=mock_db_session)
    trading_service.agents_service = mock_agents_service

    trading_service._create_transaction_internal = AsyncMock(return_value=MagicMock(id="txn_456"))
    trading_service._update_agent_holdings_internal = AsyncMock()
    trading_service._update_agent_funds_internal = AsyncMock()
    trading_service._calculate_and_update_performance_internal = AsyncMock()

    # Act
    result = await trading_service.execute_trade_atomic(
        agent_id=agent_id,
        ticker=ticker,
        action="SELL",
        quantity=quantity,
        price=price,
        decision_reason="Test SELL",
        company_name="TSMC",
    )

    # Assert - Success
    assert result["success"] is True
    assert result["transaction_id"] == "txn_456"
    assert "成功" in result["message"]

    # Verify all internal methods were called
    trading_service._create_transaction_internal.assert_called_once()
    trading_service._update_agent_holdings_internal.assert_called_once()
    trading_service._update_agent_funds_internal.assert_called_once()
    trading_service._calculate_and_update_performance_internal.assert_called_once()


@pytest.mark.asyncio
async def test_trading_service_execute_trade_atomic_invalid_action():
    """Verify invalid action is rejected"""
    agent_id = "test_agent_1"

    mock_db_session = AsyncMock()
    mock_agents_service = AsyncMock()

    trading_service = TradingService(db_session=mock_db_session)
    trading_service.agents_service = mock_agents_service

    # Act
    result = await trading_service.execute_trade_atomic(
        agent_id=agent_id,
        ticker="2330",
        action="INVALID",  # Invalid action
        quantity=1000,
        price=520.0,
    )

    # Assert - Failure
    assert result["success"] is False
    assert "error" in result
    assert "action" in result["error"].lower() or "invalid" in result["error"].lower()


@pytest.mark.asyncio
async def test_trading_service_execute_trade_atomic_invalid_quantity():
    """Verify invalid quantity is rejected"""
    agent_id = "test_agent_1"

    mock_db_session = AsyncMock()
    mock_agents_service = AsyncMock()

    trading_service = TradingService(db_session=mock_db_session)
    trading_service.agents_service = mock_agents_service

    # Act - Quantity not divisible by 1000
    result = await trading_service.execute_trade_atomic(
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=1500,  # Invalid: not divisible by 1000
        price=520.0,
    )

    # Assert - Failure
    assert result["success"] is False
    assert "error" in result
    assert "1000" in result["error"]


@pytest.mark.asyncio
async def test_trading_service_execute_trade_atomic_agent_not_found():
    """Verify agent not found case returns error without opening transaction

    Since Agent validation happens BEFORE transaction context,
    no transaction should be opened if Agent doesn't exist.
    """
    agent_id = "nonexistent_agent"

    mock_db_session = AsyncMock()
    mock_session_begin = AsyncMock()
    mock_session_begin.__aenter__ = AsyncMock(return_value=None)
    mock_session_begin.__aexit__ = AsyncMock(return_value=None)
    mock_db_session.begin_nested = MagicMock(return_value=mock_session_begin)

    mock_agents_service = AsyncMock()
    mock_agents_service.get_agent_config = AsyncMock(return_value=None)

    trading_service = TradingService(db_session=mock_db_session)
    trading_service.agents_service = mock_agents_service

    # Act
    result = await trading_service.execute_trade_atomic(
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=520.0,
    )

    # Assert - Failure and automatic rollback
    assert result["success"] is False
    assert "error" in result
    assert "不存在" in result["error"] or "not found" in result["error"].lower()

    # Since Agent validation happens BEFORE transaction, begin_nested should NOT be called
    mock_db_session.begin_nested.assert_not_called()


@pytest.mark.asyncio
async def test_trading_service_execute_trade_atomic_no_skip_commit_parameter():
    """Verify that skip_commit parameter is not needed

    This test verifies the architectural improvement: all transaction
    logic is encapsulated in execute_trade_atomic, no need for
    skip_commit pollution in internal methods.
    """
    mock_db_session = AsyncMock()
    mock_agents_service = AsyncMock()

    trading_service = TradingService(db_session=mock_db_session)
    trading_service.agents_service = mock_agents_service

    # Verify that the method signature doesn't have skip_commit
    import inspect

    sig = inspect.signature(trading_service.execute_trade_atomic)
    param_names = list(sig.parameters.keys())

    # Should NOT have skip_commit
    assert "skip_commit" not in param_names

    # Should have these core parameters
    assert "agent_id" in param_names
    assert "ticker" in param_names
    assert "action" in param_names
    assert "quantity" in param_names
    assert "price" in param_names


@pytest.mark.asyncio
async def test_trading_service_execute_trade_atomic_atomicity():
    """Verify atomicity: all succeed or all fail

    If any step fails, all changes should be rolled back.
    """
    agent_id = "test_agent_1"

    mock_db_session = AsyncMock()
    mock_session_begin = AsyncMock()
    mock_session_begin.__aenter__ = AsyncMock(return_value=None)
    mock_session_begin.__aexit__ = AsyncMock(return_value=None)
    mock_db_session.begin_nested = MagicMock(return_value=mock_session_begin)

    mock_agents_service = AsyncMock()
    mock_agents_service.get_agent_config = AsyncMock(
        return_value=MagicMock(
            id=agent_id,
            initial_funds=Decimal("1000000"),
            current_funds=Decimal("1000000"),
        )
    )

    trading_service = TradingService(db_session=mock_db_session)
    trading_service.agents_service = mock_agents_service

    # Mock: Step 1 succeeds, Step 3 fails
    trading_service._create_transaction_internal = AsyncMock(return_value=MagicMock(id="txn_123"))
    trading_service._update_agent_holdings_internal = AsyncMock()
    trading_service._update_agent_funds_internal = AsyncMock(
        side_effect=ValueError("Insufficient funds")
    )

    # Act
    result = await trading_service.execute_trade_atomic(
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=520.0,
    )

    # Assert - Failure
    assert result["success"] is False
    assert "Insufficient funds" in result["error"]

    # Verify transaction context was used and exited (for rollback)
    mock_db_session.begin_nested.assert_called_once()
    # The context manager's __aexit__ should have been called
    mock_session_begin.__aexit__.assert_called_once()
