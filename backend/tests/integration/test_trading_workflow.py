"""
Integration Test: 交易工作流

驗證從 record_trade 到 create_transaction 的完整流程，
確保資料庫層接收到正確的 TransactionStatus 值
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.trading.tools.trading_tools import record_trade
from src.common.enums import TransactionStatus


@pytest.fixture
def mock_db_agent_service():
    """Mock agent_service，模擬資料庫交互"""
    service = AsyncMock()

    # create_transaction 應該接收正確的 TransactionStatus.EXECUTED
    service.create_transaction = AsyncMock(
        return_value=MagicMock(
            id="txn-123",
            status=TransactionStatus.EXECUTED,
        )
    )
    service.update_agent_holdings = AsyncMock(return_value=None)
    service.calculate_and_update_performance = AsyncMock(return_value=None)
    service.update_agent_funds = AsyncMock(return_value=None)

    return service


@pytest.mark.asyncio
async def test_trading_workflow_record_to_db(mock_db_agent_service):
    """驗證交易工作流從 record_trade 到資料庫"""
    # 執行 record_trade
    result = await record_trade(
        agent_service=mock_db_agent_service,
        agent_id="integration_test",
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=500.0,
        decision_reason="Integration test",
    )

    # ✅ 應該成功
    assert "✅" in result
    assert mock_db_agent_service.create_transaction.called

    # 驗證傳遞的參數包含 TransactionStatus.EXECUTED
    call_kwargs = mock_db_agent_service.create_transaction.call_args[1]
    assert call_kwargs["status"] == TransactionStatus.EXECUTED


@pytest.mark.asyncio
async def test_trading_workflow_status_validation(mock_db_agent_service):
    """驗證交易工作流中的狀態驗證"""
    # 這個調用應該通過 (使用正確的 TransactionStatus.EXECUTED)
    await record_trade(
        agent_service=mock_db_agent_service,
        agent_id="test",
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=500.0,
        decision_reason="Test",
    )

    # create_transaction 應被成功呼叫
    assert mock_db_agent_service.create_transaction.call_count == 1

    # 驗證 TransactionStatus.EXECUTED 被使用
    call_kwargs = mock_db_agent_service.create_transaction.call_args[1]
    assert call_kwargs["status"] == TransactionStatus.EXECUTED


@pytest.mark.asyncio
async def test_trading_workflow_updates_holdings_and_funds(mock_db_agent_service):
    """驗證交易後更新持股和資金"""
    await record_trade(
        agent_service=mock_db_agent_service,
        agent_id="test",
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=500.0,
        decision_reason="Test",
    )

    # 驗證所有相關的更新都被呼叫
    assert mock_db_agent_service.create_transaction.called
    assert mock_db_agent_service.update_agent_holdings.called
    assert mock_db_agent_service.update_agent_funds.called
    assert mock_db_agent_service.calculate_and_update_performance.called

    # 驗證正確的狀態被使用
    call_kwargs = mock_db_agent_service.create_transaction.call_args[1]
    assert call_kwargs["status"] == TransactionStatus.EXECUTED


@pytest.mark.asyncio
async def test_trading_workflow_multiple_transactions(mock_db_agent_service):
    """驗證多筆交易工作流"""
    # 第一筆交易 - BUY
    await record_trade(
        agent_service=mock_db_agent_service,
        agent_id="test",
        ticker="2330",
        action="BUY",
        quantity=1000,
        price=500.0,
        decision_reason="Buy signal",
    )

    # 第二筆交易 - SELL
    await record_trade(
        agent_service=mock_db_agent_service,
        agent_id="test",
        ticker="2330",
        action="SELL",
        quantity=1000,
        price=520.0,
        decision_reason="Sell signal",
    )

    # 驗證兩筆交易都被記錄
    assert mock_db_agent_service.create_transaction.call_count == 2

    # 驗證兩筆交易都使用 EXECUTED 狀態
    calls = mock_db_agent_service.create_transaction.call_args_list
    for call in calls:
        status = call.kwargs.get("status")
        assert status == TransactionStatus.EXECUTED

    # 驗證兩筆交易都使用 EXECUTED 狀態
    calls = mock_db_agent_service.create_transaction.call_args_list
    for call in calls:
        status = call.kwargs.get("status")
        assert status == TransactionStatus.EXECUTED


@pytest.mark.asyncio
async def test_trading_workflow_action_conversion(mock_db_agent_service):
    """驗證交易動作的大小寫轉換"""
    # 使用小寫輸入
    await record_trade(
        agent_service=mock_db_agent_service,
        agent_id="test",
        ticker="2330",
        action="buy",  # 小寫輸入
        quantity=1000,
        price=500.0,
        decision_reason="Test",
    )

    call_kwargs = mock_db_agent_service.create_transaction.call_args.kwargs
    # 應該被轉換為大寫
    assert call_kwargs["action"] == "BUY"
    # 應該使用正確的狀態
    assert call_kwargs["status"] == TransactionStatus.EXECUTED
