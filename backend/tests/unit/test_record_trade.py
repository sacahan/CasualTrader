"""
Unit Test: record_trade 函數

驗證：
1. record_trade 調用 create_transaction 時使用正確的 TransactionStatus
2. 參數驗證和轉換
3. 手續費計算
"""

import pytest
from unittest.mock import AsyncMock
from src.trading.tools.trading_tools import record_trade
from src.common.enums import TransactionStatus


@pytest.fixture
def mock_agent_service():
    """Mock agent_service"""
    service = AsyncMock()
    service.create_transaction = AsyncMock(return_value=None)
    service.update_agent_holdings = AsyncMock(return_value=None)
    service.calculate_and_update_performance = AsyncMock(return_value=None)
    service.update_agent_funds = AsyncMock(return_value=None)
    return service


@pytest.mark.asyncio
async def test_record_trade_uses_executed_status(mock_agent_service):
    """驗證 record_trade 使用 TransactionStatus.EXECUTED"""
    await record_trade(
        agent_service=mock_agent_service,
        agent_id="test_agent",
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=500.0,
        decision_reason="技術突破",
    )

    # 驗證 create_transaction 被呼叫
    mock_agent_service.create_transaction.assert_called_once()

    # 取得呼叫的參數
    call_kwargs = mock_agent_service.create_transaction.call_args.kwargs

    # ✅ 驗證 status 是 TransactionStatus.EXECUTED，不是字符串
    assert call_kwargs["status"] == TransactionStatus.EXECUTED


@pytest.mark.asyncio
async def test_record_trade_calculates_commission(mock_agent_service):
    """驗證手續費計算"""
    quantity = 1000
    price = 500.0
    total_amount = quantity * price
    expected_commission = total_amount * 0.001425

    await record_trade(
        agent_service=mock_agent_service,
        agent_id="test_agent",
        ticker="2330",
        action="BUY",
        quantity=quantity,
        price=price,
        decision_reason="Test",
    )

    call_kwargs = mock_agent_service.create_transaction.call_args.kwargs

    # 驗證手續費計算
    assert call_kwargs["commission"] == pytest.approx(expected_commission, rel=1e-6)
    assert call_kwargs["total_amount"] == pytest.approx(total_amount, rel=1e-6)


@pytest.mark.asyncio
async def test_record_trade_validates_action(mock_agent_service):
    """驗證交易動作驗證"""
    with pytest.raises(ValueError, match="無效的交易動作"):
        await record_trade(
            agent_service=mock_agent_service,
            agent_id="test_agent",
            ticker="2330",
            action="INVALID",
            quantity=1000,
            price=500.0,
            decision_reason="Test",
        )

    # create_transaction 不應被呼叫
    mock_agent_service.create_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_record_trade_passes_correct_parameters(mock_agent_service):
    """驗證所有參數正確傳遞"""
    agent_id = "test_agent_123"
    ticker = "2330"
    quantity = 1000
    price = 520.0
    reason = "技術突破買進"
    company_name = "台積電"

    await record_trade(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker=ticker,
        action="BUY",
        quantity=quantity,
        price=price,
        decision_reason=reason,
        company_name=company_name,
    )

    call_kwargs = mock_agent_service.create_transaction.call_args.kwargs

    # 驗證參數
    assert call_kwargs["agent_id"] == agent_id
    assert call_kwargs["ticker"] == ticker
    assert call_kwargs["quantity"] == quantity
    assert call_kwargs["price"] == price
    assert call_kwargs["decision_reason"] == reason
    assert call_kwargs["company_name"] == company_name
    assert call_kwargs["action"] == "BUY"


@pytest.mark.asyncio
async def test_record_trade_updates_holdings(mock_agent_service):
    """驗證持股更新被呼叫"""
    await record_trade(
        agent_service=mock_agent_service,
        agent_id="test_agent",
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=500.0,
        decision_reason="Test",
    )

    # 驗證持股更新被呼叫
    mock_agent_service.update_agent_holdings.assert_called_once()
    holdings_call = mock_agent_service.update_agent_holdings.call_args.kwargs
    assert holdings_call["action"] == "BUY"
    assert holdings_call["ticker"] == "2330"


@pytest.mark.asyncio
async def test_record_trade_updates_funds(mock_agent_service):
    """驗證資金更新被呼叫"""
    quantity = 1000
    price = 500.0
    total = quantity * price
    commission = total * 0.001425

    await record_trade(
        agent_service=mock_agent_service,
        agent_id="test_agent",
        ticker="2330",
        action="BUY",
        quantity=quantity,
        price=price,
        decision_reason="Test",
    )

    # 驗證資金更新被呼叫
    mock_agent_service.update_agent_funds.assert_called_once()
    funds_call = mock_agent_service.update_agent_funds.call_args.kwargs

    # BUY 時資金應減少
    expected_change = -(total + commission)
    assert funds_call["amount_change"] == pytest.approx(expected_change, rel=1e-6)


@pytest.mark.asyncio
async def test_record_trade_handles_sell_action(mock_agent_service):
    """驗證賣出動作"""
    quantity = 1000
    price = 500.0
    total = quantity * price
    commission = total * 0.001425

    await record_trade(
        agent_service=mock_agent_service,
        agent_id="test_agent",
        ticker="2330",
        action="SELL",
        quantity=quantity,
        price=price,
        decision_reason="Test",
    )

    # 驗證參數
    call_kwargs = mock_agent_service.create_transaction.call_args.kwargs
    assert call_kwargs["action"] == "SELL"

    # SELL 時資金應增加
    funds_call = mock_agent_service.update_agent_funds.call_args.kwargs
    expected_change = total - commission
    assert funds_call["amount_change"] == pytest.approx(expected_change, rel=1e-6)


@pytest.mark.asyncio
async def test_record_trade_returns_success_message(mock_agent_service):
    """驗證返回成功消息"""
    result = await record_trade(
        agent_service=mock_agent_service,
        agent_id="test_agent",
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=500.0,
        decision_reason="Test",
    )

    assert "✅" in result
    assert "交易記錄成功" in result
    assert "2330" in result
    assert "1000" in result


@pytest.mark.asyncio
async def test_record_trade_status_not_string(mock_agent_service):
    """驗證 status 不是字符串 COMPLETED"""
    await record_trade(
        agent_service=mock_agent_service,
        agent_id="test_agent",
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=500.0,
        decision_reason="Test",
    )

    call_kwargs = mock_agent_service.create_transaction.call_args.kwargs

    # ❌ 不應該是字符串 "COMPLETED"
    assert call_kwargs["status"] != "COMPLETED"
    assert call_kwargs["status"] != "completed"

    # ✅ 應該是 TransactionStatus.EXECUTED
    assert call_kwargs["status"] == TransactionStatus.EXECUTED


@pytest.mark.asyncio
async def test_record_trade_updates_performance(mock_agent_service):
    """驗證績效指標更新被呼叫"""
    agent_id = "test_agent_123"

    await record_trade(
        agent_service=mock_agent_service,
        agent_id=agent_id,
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=500.0,
        decision_reason="Test",
    )

    # 驗證績效更新被呼叫
    mock_agent_service.calculate_and_update_performance.assert_called_once()
    perf_call = mock_agent_service.calculate_and_update_performance.call_args
    # 驗證傳入正確的 agent_id
    assert perf_call[0][0] == agent_id or perf_call.kwargs.get("agent_id") == agent_id
