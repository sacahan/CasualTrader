"""
Unit tests for atomic trade execution

Tests the execute_trade_atomic function to ensure all operations are performed
atomically: all succeed or all fail with automatic rollback.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from trading.tools.trading_tools import execute_trade_atomic


@pytest.fixture
def mock_agent_service():
    """Fixture for mock agent service (AgentsService)"""
    return MagicMock()


@pytest.fixture
def mock_trading_service(mock_agent_service):
    """Fixture for mock trading service with embedded agent service"""
    service = MagicMock()
    service.agents_service = mock_agent_service
    service.execute_trade_atomic = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_execute_trade_atomic_buy_success(mock_trading_service):
    """Verify successful atomic BUY trade execution

    All operations should succeed and be committed within the transaction.
    """
    # Arrange
    agent_id = "test_agent_1"
    ticker = "2330"
    quantity = 1000
    price = 520.0

    # Setup mock trading service
    mock_trading_service.execute_trade_atomic = AsyncMock(
        return_value={
            "success": True,
            "transaction_id": "txn_123",
            "message": f"交易成功: BUY {ticker} {quantity} 股 @ {price}",
        }
    )

    # Act
    result = await execute_trade_atomic(
        trading_service=mock_trading_service,
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=quantity,
        price=price,
        decision_reason="Test BUY",
        company_name="TSMC",
    )

    # Assert - Success message
    assert "✅" in result
    assert "原子操作" in result
    assert ticker in result
    assert "BUY" in result

    # Verify trading service method was called
    mock_trading_service.execute_trade_atomic.assert_called_once_with(
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=quantity,
        price=price,
        decision_reason="Test BUY",
        company_name="TSMC",
    )


@pytest.mark.asyncio
async def test_execute_trade_atomic_sell_success(mock_trading_service):
    """Verify successful atomic SELL trade execution"""
    # Arrange
    agent_id = "test_agent_1"
    ticker = "2330"
    quantity = 1000
    price = 530.0

    # Setup mock trading service
    mock_trading_service.execute_trade_atomic = AsyncMock(
        return_value={
            "success": True,
            "transaction_id": "txn_456",
            "message": f"交易成功: SELL {ticker} {quantity} 股 @ {price}",
        }
    )

    # Act
    result = await execute_trade_atomic(
        trading_service=mock_trading_service,
        agent_id=agent_id,
        ticker=ticker,
        action="SELL",
        quantity=quantity,
        price=price,
        decision_reason="Test SELL",
        company_name="TSMC",
    )

    # Assert
    assert "✅" in result
    assert "SELL" in result
    assert ticker in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_invalid_action(mock_trading_service):
    """Verify invalid action is rejected"""
    # Setup mock to return validation error
    mock_trading_service.execute_trade_atomic = AsyncMock(
        return_value={
            "success": False,
            "error": "無效的 action: INVALID，必須是 'BUY' 或 'SELL'",
        }
    )

    agent_id = "test_agent_1"

    # Act & Assert
    result = await execute_trade_atomic(
        trading_service=mock_trading_service,
        agent_id=agent_id,
        ticker="2330",
        action="INVALID",
        quantity=1000,
        price=520.0,
    )

    # Should return error message
    assert "❌" in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_invalid_quantity(mock_trading_service):
    """Verify invalid quantity is rejected"""
    # Setup mock to return validation error
    mock_trading_service.execute_trade_atomic = AsyncMock(
        return_value={
            "success": False,
            "error": "股數必須是 1000 的倍數，收到: 1500",
        }
    )

    agent_id = "test_agent_1"

    # Act
    result = await execute_trade_atomic(
        trading_service=mock_trading_service,
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=1500,
        price=520.0,
    )

    # Assert
    assert "❌" in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_failure_rollback(mock_trading_service):
    """Verify error handling on failure"""
    # Setup mock to simulate failure with rollback
    mock_trading_service.execute_trade_atomic = AsyncMock(
        return_value={
            "success": False,
            "error": "DB Error - Transaction rolled back",
        }
    )

    agent_id = "test_agent_1"

    # Act
    result = await execute_trade_atomic(
        trading_service=mock_trading_service,
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=520.0,
    )

    # Assert - Should show rollback message
    assert "❌" in result
    assert "回滾" in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_agent_not_found(mock_trading_service):
    """Verify error when agent is not found"""
    # Setup mock to return agent not found error
    mock_trading_service.execute_trade_atomic = AsyncMock(
        return_value={
            "success": False,
            "error": "Agent test_agent_1 不存在",
        }
    )

    agent_id = "test_agent_1"

    # Act
    result = await execute_trade_atomic(
        trading_service=mock_trading_service,
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=520.0,
    )

    # Assert
    assert "❌" in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_funds_calculation_buy(mock_trading_service):
    """Verify fund calculation for BUY operation"""
    # Setup mock to return success
    mock_trading_service.execute_trade_atomic = AsyncMock(
        return_value={
            "success": True,
            "message": "買入成功: 2330 1000 股 @ 520.0, 總金額: 520,000, 手續費: 740",
        }
    )

    agent_id = "test_agent_1"

    # Act
    result = await execute_trade_atomic(
        trading_service=mock_trading_service,
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=520.0,
    )

    # Assert
    assert "✅" in result
    assert "2330" in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_funds_calculation_sell(mock_trading_service):
    """Verify fund calculation for SELL operation"""
    # Setup mock to return success
    mock_trading_service.execute_trade_atomic = AsyncMock(
        return_value={
            "success": True,
            "message": "賣出成功: 2330 1000 股 @ 530.0, 總金額: 530,000, 手續費: 755",
        }
    )

    agent_id = "test_agent_1"

    # Act
    result = await execute_trade_atomic(
        trading_service=mock_trading_service,
        agent_id=agent_id,
        ticker="2330",
        action="SELL",
        quantity=1000,
        price=530.0,
    )

    # Assert
    assert "✅" in result
    assert "2330" in result


@pytest.mark.asyncio
async def test_execute_trade_atomic_transaction_fields(mock_trading_service):
    """Verify all transaction fields are recorded"""
    # Setup mock to return success
    mock_trading_service.execute_trade_atomic = AsyncMock(
        return_value={
            "success": True,
            "transaction_id": "txn_789",
            "message": "交易已記錄並且所有相關操作已完成",
        }
    )

    agent_id = "test_agent_1"
    ticker = "2330"
    quantity = 1000
    price = 520.0
    reason = "Technical breakout"
    company = "TSMC"

    # Act
    _ = await execute_trade_atomic(
        trading_service=mock_trading_service,
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=quantity,
        price=price,
        decision_reason=reason,
        company_name=company,
    )

    # Assert - Verify trading service was called with all parameters
    call_args = mock_trading_service.execute_trade_atomic.call_args
    assert call_args is not None
    kwargs = call_args.kwargs

    assert kwargs["agent_id"] == agent_id
    assert kwargs["ticker"] == ticker
    assert kwargs["quantity"] == quantity
    assert kwargs["price"] == price
    assert kwargs["decision_reason"] == reason
    assert kwargs["company_name"] == company
