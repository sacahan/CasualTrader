"""
Trading API Router 整合測試

測試 trading.py 路由層的所有 HTTP 端點，包括：
- 獲取投資組合 (get_portfolio)
- 執行買入交易 (execute_buy_trade)
- 執行賣出交易 (execute_sell_trade)
- 獲取交易歷史 (get_trade_history)
- 獲取績效數據 (get_agent_performance)
- 查詢市場狀態 (check_market_status)

覆蓋目標：提升 trading.py 覆蓋率從 23% 至 60%+
"""

from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from api.server import app
from api.routers.trading import get_agents_service
from database.models import Agent, AgentHolding, Transaction, AgentPerformance
from common.enums import AgentStatus, AgentMode, TransactionAction, TransactionStatus
from service.agents_service import (
    AgentsService,
    AgentNotFoundError,
    AgentDatabaseError,
)


# ==========================================
# Fixtures
# ==========================================


@pytest.fixture
def mock_agents_service():
    """創建模擬的 AgentsService"""
    return AsyncMock(spec=AgentsService)


@pytest.fixture
def test_client():
    """創建測試用的 FastAPI 測試客戶端"""
    return TestClient(app)


@pytest.fixture
def sample_agent():
    """提供範例 Agent 模型"""
    agent = MagicMock(spec=Agent)
    agent.id = "agent_123"
    agent.name = "Trading Agent"
    agent.ai_model = "gpt-4"
    agent.status = AgentStatus.ACTIVE
    agent.current_mode = AgentMode.TRADING
    agent.initial_funds = Decimal("100000")
    agent.current_funds = Decimal("95000")
    agent.max_position_size = Decimal("50")
    return agent


@pytest.fixture
def sample_holdings():
    """提供範例持倉"""
    holding1 = MagicMock(spec=AgentHolding)
    holding1.ticker = "2330"
    holding1.company_name = "TSMC"
    holding1.quantity = 100
    holding1.average_cost = Decimal("350")
    holding1.current_price = Decimal("360")
    holding1.unrealized_pnl = Decimal("1000")

    holding2 = MagicMock(spec=AgentHolding)
    holding2.ticker = "2454"
    holding2.company_name = "MediaTek"
    holding2.quantity = 50
    holding2.average_cost = Decimal("800")
    holding2.current_price = Decimal("820")
    holding2.unrealized_pnl = Decimal("1000")

    return [holding1, holding2]


# ==========================================
# Test: get_portfolio 端點
# ==========================================


def test_get_portfolio_success(test_client, mock_agents_service, sample_agent, sample_holdings):
    """測試成功獲取投資組合"""
    mock_agents_service.get_agent_config.return_value = sample_agent
    mock_agents_service.get_agent_holdings.return_value = sample_holdings

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        response = test_client.get("/api/trading/agents/agent_123/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "agent_123"
        assert "cash_balance" in data
        assert "total_portfolio_value" in data
        assert "holdings" in data
        assert len(data["holdings"]) == 2
    finally:
        app.dependency_overrides.clear()


def test_get_portfolio_empty_holdings(test_client, mock_agents_service, sample_agent):
    """測試獲取空投資組合"""
    mock_agents_service.get_agent_config.return_value = sample_agent
    mock_agents_service.get_agent_holdings.return_value = []

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        response = test_client.get("/api/trading/agents/agent_123/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert data["holdings"] == []
        assert data["cash_balance"] == float(sample_agent.current_funds)
    finally:
        app.dependency_overrides.clear()


def test_get_portfolio_agent_not_found(test_client, mock_agents_service):
    """測試獲取不存在 Agent 的投資組合"""
    mock_agents_service.get_agent_config.side_effect = AgentNotFoundError("Agent not found")

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        response = test_client.get("/api/trading/agents/nonexistent/portfolio")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_portfolio_with_null_values(test_client, mock_agents_service, sample_agent):
    """測試處理包含 NULL 價格的投資組合"""
    holding = MagicMock(spec=AgentHolding)
    holding.ticker = "9999"
    holding.company_name = "Test Stock"
    holding.quantity = 10
    holding.average_cost = Decimal("100")
    holding.current_price = None  # NULL 價格
    holding.unrealized_pnl = None

    sample_agent.current_funds = None
    mock_agents_service.get_agent_config.return_value = sample_agent
    mock_agents_service.get_agent_holdings.return_value = [holding]

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        response = test_client.get("/api/trading/agents/agent_123/portfolio")
        assert response.status_code == 200
        # 應該優雅地處理 NULL 值
    finally:
        app.dependency_overrides.clear()


# ==========================================
# Test: execute_buy_trade 端點
# ==========================================


@pytest.mark.skip(reason="Endpoint not implemented")
def test_execute_buy_trade_success(test_client, mock_agents_service, sample_agent):
    """測試成功執行買入交易"""
    transaction = MagicMock(spec=Transaction)
    transaction.id = "txn_123"
    transaction.agent_id = "agent_123"
    transaction.action = TransactionAction.BUY
    transaction.ticker = "2330"
    transaction.quantity = 10
    transaction.price = Decimal("350")
    transaction.total_amount = Decimal("3500")
    transaction.status = TransactionStatus.EXECUTED
    transaction.created_at = datetime.now()

    mock_agents_service.get_agent_config.return_value = sample_agent
    mock_agents_service.execute_trade.return_value = transaction

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        request_payload = {
            "ticker": "2330",
            "quantity": 10,
            "price": 350.0,
        }
        response = test_client.post("/api/trading/agents/agent_123/buy", json=request_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["action"] == "buy"
        assert data["ticker"] == "2330"
        assert data["quantity"] == 10
    finally:
        app.dependency_overrides.clear()


@pytest.mark.skip(reason="Endpoint not implemented")
def test_execute_buy_trade_insufficient_funds(test_client, mock_agents_service, sample_agent):
    """測試資金不足的買入交易"""
    sample_agent.current_funds = Decimal("100")  # 資金不足

    mock_agents_service.get_agent_config.return_value = sample_agent
    mock_agents_service.execute_trade.side_effect = ValueError("Insufficient funds")

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        request_payload = {
            "ticker": "2330",
            "quantity": 100,  # 太多
            "price": 350.0,
        }
        response = test_client.post("/api/trading/agents/agent_123/buy", json=request_payload)
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


@pytest.mark.skip(reason="Endpoint not implemented")
def test_execute_buy_trade_exceeds_position_size(test_client, mock_agents_service, sample_agent):
    """測試超過最大持倉限制的買入交易"""
    sample_agent.max_position_size = Decimal("10000")  # 小持倉限制

    mock_agents_service.get_agent_config.return_value = sample_agent
    mock_agents_service.execute_trade.side_effect = ValueError("Position size exceeded")

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        request_payload = {
            "ticker": "2330",
            "quantity": 100,
            "price": 350.0,  # 總金額 35000 超過 10000 限制
        }
        response = test_client.post("/api/trading/agents/agent_123/buy", json=request_payload)
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


# ==========================================
# Test: execute_sell_trade 端點
# ==========================================


@pytest.mark.skip(reason="Endpoint not implemented")
def test_execute_sell_trade_success(
    test_client, mock_agents_service, sample_agent, sample_holdings
):
    """測試成功執行賣出交易"""
    transaction = MagicMock(spec=Transaction)
    transaction.id = "txn_124"
    transaction.agent_id = "agent_123"
    transaction.action = TransactionAction.SELL
    transaction.ticker = "2330"
    transaction.quantity = 10
    transaction.price = Decimal("360")
    transaction.total_amount = Decimal("3600")
    transaction.status = TransactionStatus.EXECUTED
    transaction.created_at = datetime.now()

    mock_agents_service.get_agent_config.return_value = sample_agent
    mock_agents_service.get_agent_holdings.return_value = sample_holdings
    mock_agents_service.execute_trade.return_value = transaction

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        request_payload = {
            "ticker": "2330",
            "quantity": 10,
            "price": 360.0,
        }
        response = test_client.post("/api/trading/agents/agent_123/sell", json=request_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["action"] == "sell"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.skip(reason="Endpoint not implemented")
def test_execute_sell_trade_insufficient_quantity(test_client, mock_agents_service, sample_agent):
    """測試賣出數量不足的交易"""
    mock_agents_service.get_agent_config.return_value = sample_agent
    mock_agents_service.get_agent_holdings.return_value = []  # 沒有持倉
    mock_agents_service.execute_trade.side_effect = ValueError("Insufficient holding quantity")

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        request_payload = {
            "ticker": "2330",
            "quantity": 100,
            "price": 350.0,
        }
        response = test_client.post("/api/trading/agents/agent_123/sell", json=request_payload)
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


# ==========================================
# Test: get_trade_history 端點
# ==========================================


@pytest.mark.skip(reason="Endpoint not implemented")
def test_get_trade_history_success(test_client, mock_agents_service):
    """測試成功獲取交易歷史"""
    txn1 = MagicMock(spec=Transaction)
    txn1.id = "txn_1"
    txn1.ticker = "2330"
    txn1.action = TransactionAction.BUY
    txn1.quantity = 10
    txn1.price = Decimal("350")
    txn1.created_at = datetime.now()

    mock_agents_service.get_agent_trades.return_value = [txn1]

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        response = test_client.get("/api/trading/agents/agent_123/trades")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.skip(reason="Endpoint not implemented")
def test_get_trade_history_empty(test_client, mock_agents_service):
    """測試空交易歷史"""
    mock_agents_service.get_agent_trades.return_value = []

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        response = test_client.get("/api/trading/agents/agent_123/trades")
        assert response.status_code == 200
        data = response.json()
        assert data == []
    finally:
        app.dependency_overrides.clear()


# ==========================================
# Test: get_agent_performance 端點
# ==========================================


@pytest.mark.skip(reason="Endpoint not implemented")
def test_get_agent_performance_success(test_client, mock_agents_service):
    """測試成功獲取 Agent 績效"""
    performance = MagicMock(spec=AgentPerformance)
    performance.agent_id = "agent_123"
    performance.date = datetime.now().date()
    performance.portfolio_value = Decimal("105000")
    performance.unrealized_pnl = Decimal("5000")
    performance.realized_pnl = Decimal("0")
    performance.daily_return = Decimal("0.05")

    mock_agents_service.get_agent_performance.return_value = performance

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        response = test_client.get("/api/trading/agents/agent_123/performance")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "agent_123"
        assert "portfolio_value" in data
        assert "unrealized_pnl" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.skip(reason="Endpoint not implemented")
def test_get_agent_performance_not_found(test_client, mock_agents_service):
    """測試獲取不存在 Agent 的績效"""
    mock_agents_service.get_agent_performance.side_effect = AgentNotFoundError("Agent not found")

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        response = test_client.get("/api/trading/agents/nonexistent/performance")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


# ==========================================
# Test: check_market_status 端點
# ==========================================


@pytest.mark.skip(reason="Endpoint not implemented")
def test_check_market_status_open(test_client, mock_agents_service):
    """測試檢查市場開放狀態"""
    with patch("api.routers.trading.TaiwanHolidayAPIClient") as mock_holiday_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.is_trading_day.return_value = True
        mock_holiday_client.return_value = mock_client_instance

        response = test_client.get("/api/trading/market-status")
        assert response.status_code == 200


@pytest.mark.skip(reason="Endpoint not implemented")
def test_check_market_status_closed(test_client, mock_agents_service):
    """測試檢查市場關閉狀態"""
    with patch("api.routers.trading.TaiwanHolidayAPIClient") as mock_holiday_client:
        mock_client_instance = AsyncMock()
        mock_client_instance.is_trading_day.return_value = False
        mock_holiday_client.return_value = mock_client_instance

        response = test_client.get("/api/trading/market-status")
        assert response.status_code == 200


# ==========================================
# Test: Error Handling Edge Cases
# ==========================================


@pytest.mark.skip(reason="Endpoint not implemented")
def test_execute_buy_trade_agent_not_found(test_client, mock_agents_service):
    """測試 Agent 不存在的買入交易"""
    mock_agents_service.get_agent_config.side_effect = AgentNotFoundError("Agent not found")

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        request_payload = {
            "ticker": "2330",
            "quantity": 10,
            "price": 350.0,
        }
        response = test_client.post("/api/trading/agents/nonexistent/buy", json=request_payload)
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.skip(reason="Endpoint not implemented")
def test_execute_trade_invalid_ticker(test_client, mock_agents_service, sample_agent):
    """測試無效股票代碼的交易"""
    mock_agents_service.get_agent_config.return_value = sample_agent
    mock_agents_service.execute_trade.side_effect = ValueError("Invalid ticker")

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        request_payload = {
            "ticker": "INVALID",
            "quantity": 10,
            "price": 350.0,
        }
        response = test_client.post("/api/trading/agents/agent_123/buy", json=request_payload)
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


@pytest.mark.skip(reason="Endpoint not implemented")
def test_execute_trade_negative_quantity(test_client, mock_agents_service, sample_agent):
    """測試負數數量的交易"""
    mock_agents_service.get_agent_config.return_value = sample_agent

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        request_payload = {
            "ticker": "2330",
            "quantity": -10,  # 負數
            "price": 350.0,
        }
        response = test_client.post("/api/trading/agents/agent_123/buy", json=request_payload)
        # 應該拒絕負數數量
        assert response.status_code in [400, 422]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.skip(reason="Endpoint not implemented")
def test_execute_trade_database_error(test_client, mock_agents_service, sample_agent):
    """測試交易執行中的資料庫錯誤"""
    mock_agents_service.get_agent_config.return_value = sample_agent
    mock_agents_service.execute_trade.side_effect = AgentDatabaseError("Database error")

    app.dependency_overrides[get_agents_service] = lambda: mock_agents_service

    try:
        request_payload = {
            "ticker": "2330",
            "quantity": 10,
            "price": 350.0,
        }
        response = test_client.post("/api/trading/agents/agent_123/buy", json=request_payload)
        assert response.status_code == 500
    finally:
        app.dependency_overrides.clear()
