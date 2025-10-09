"""
Phase 3 API Tests

Test suite for FastAPI backend and WebSocket functionality.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def app():
    """Create FastAPI test app."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_agent_manager():
    """Mock AgentManager for testing."""
    with patch("src.api.routers.agents.agent_manager") as mock:
        yield mock


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "CasualTrader API"


class TestAgentManagement:
    """Test agent management endpoints."""

    def test_list_agents_empty(self, client, mock_agent_manager):
        """Test listing agents when none exist."""
        mock_agent_manager.list_agents = AsyncMock(return_value=[])

        response = client.get("/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["agents"] == []

    def test_create_agent(self, client, mock_agent_manager):
        """Test creating a new agent."""
        mock_agent_manager.create_agent = AsyncMock(return_value="agent_001")
        mock_agent_manager.get_agent = AsyncMock(
            return_value={
                "id": "agent_001",
                "name": "Test Agent",
                "description": "Test Description",
                "ai_model": "gpt-4o",
                "strategy_type": "balanced",
                "strategy_prompt": "Test strategy",
                "status": "idle",
                "initial_funds": 1000000.0,
                "max_turns": 50,
                "risk_tolerance": 0.5,
                "enabled_tools": {},
                "investment_preferences": {},
                "custom_instructions": "",
            }
        )

        request_data = {
            "name": "Test Agent",
            "description": "Test Description",
            "ai_model": "gpt-4o",
            "strategy_type": "balanced",
            "strategy_prompt": "Test strategy prompt for agent",
            "color_theme": "#007bff",
            "initial_funds": 1000000.0,
            "max_turns": 50,
            "risk_tolerance": 0.5,
            "enabled_tools": {
                "fundamental_analysis": True,
                "technical_analysis": True,
                "risk_assessment": True,
                "sentiment_analysis": False,
                "web_search": True,
                "code_interpreter": False,
            },
            "investment_preferences": {
                "preferred_sectors": ["技術業"],
                "excluded_stocks": [],
                "max_position_size": 0.15,
                "rebalance_frequency": "weekly",
            },
            "custom_instructions": "",
        }

        response = client.post("/api/agents", json=request_data)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "agent_001"
        assert data["name"] == "Test Agent"

    def test_get_agent(self, client, mock_agent_manager):
        """Test getting specific agent."""
        mock_agent_manager.get_agent = AsyncMock(
            return_value={
                "id": "agent_001",
                "name": "Test Agent",
                "description": "Test",
                "ai_model": "gpt-4o",
                "strategy_type": "balanced",
                "strategy_prompt": "Test",
                "status": "idle",
                "initial_funds": 1000000.0,
                "max_turns": 50,
                "risk_tolerance": 0.5,
                "enabled_tools": {},
                "investment_preferences": {},
                "custom_instructions": "",
            }
        )

        response = client.get("/api/agents/agent_001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "agent_001"

    def test_get_agent_not_found(self, client, mock_agent_manager):
        """Test getting non-existent agent."""
        mock_agent_manager.get_agent = AsyncMock(return_value=None)

        response = client.get("/api/agents/nonexistent")
        assert response.status_code == 404

    def test_start_agent(self, client, mock_agent_manager):
        """Test starting an agent."""
        mock_agent_manager.get_agent = AsyncMock(
            return_value={
                "id": "agent_001",
                "name": "Test Agent",
                "status": "idle",
            }
        )
        mock_agent_manager.start_agent = AsyncMock()

        request_data = {
            "execution_mode": "continuous",
            "max_cycles": 100,
            "stop_on_loss_threshold": 0.15,
        }

        response = client.post("/api/agents/agent_001/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_stop_agent(self, client, mock_agent_manager):
        """Test stopping an agent."""
        mock_agent_manager.get_agent = AsyncMock(
            return_value={
                "id": "agent_001",
                "name": "Test Agent",
                "status": "running",
            }
        )
        mock_agent_manager.stop_agent = AsyncMock()

        response = client.post("/api/agents/agent_001/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"


class TestTradingEndpoints:
    """Test trading-related endpoints."""

    def test_get_portfolio(self, client):
        """Test getting agent portfolio."""
        with patch("src.api.routers.trading.agent_manager") as mock:
            mock.get_agent = AsyncMock(
                return_value={
                    "id": "agent_001",
                    "name": "Test Agent",
                }
            )
            mock.get_portfolio = AsyncMock(
                return_value={
                    "cash": 1000000.0,
                    "positions": {},
                    "total_value": 1000000.0,
                }
            )

            response = client.get("/api/trading/agents/agent_001/portfolio")
            assert response.status_code == 200
            data = response.json()
            assert "portfolio" in data
            assert data["portfolio"]["cash"] == 1000000.0

    def test_get_trades(self, client):
        """Test getting agent trades."""
        with patch("src.api.routers.trading.agent_manager") as mock:
            mock.get_agent = AsyncMock(
                return_value={
                    "id": "agent_001",
                    "name": "Test Agent",
                }
            )
            mock.get_trades = AsyncMock(return_value=[])

            response = client.get("/api/trading/agents/agent_001/trades")
            assert response.status_code == 200
            data = response.json()
            assert "trades" in data
            assert data["total"] == 0

    def test_get_strategy_changes(self, client):
        """Test getting strategy changes."""
        with patch("src.api.routers.trading.agent_manager") as mock:
            mock.get_agent = AsyncMock(
                return_value={
                    "id": "agent_001",
                    "name": "Test Agent",
                }
            )
            mock.get_strategy_changes = AsyncMock(return_value=[])

            response = client.get("/api/trading/agents/agent_001/strategies")
            assert response.status_code == 200
            data = response.json()
            assert "strategy_changes" in data

    def test_get_performance(self, client):
        """Test getting agent performance."""
        with patch("src.api.routers.trading.agent_manager") as mock:
            mock.get_agent = AsyncMock(
                return_value={
                    "id": "agent_001",
                    "name": "Test Agent",
                }
            )
            mock.get_performance = AsyncMock(
                return_value={
                    "return_rate": 0.05,
                    "win_rate": 0.6,
                    "max_drawdown": 0.02,
                }
            )

            response = client.get("/api/trading/agents/agent_001/performance")
            assert response.status_code == 200
            data = response.json()
            assert "performance" in data

    def test_get_market_status(self, client):
        """Test getting market status."""
        response = client.get("/api/trading/market/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_trading_day" in data
        assert "status" in data


class TestWebSocket:
    """Test WebSocket functionality."""

    def test_websocket_connection(self, client):
        """Test WebSocket connection establishment."""
        with client.websocket_connect("/ws") as websocket:
            # Send a test message
            websocket.send_text("test")
            # Receive echo response
            data = websocket.receive_json()
            assert data["type"] == "pong"
            assert "received" in data["data"]


@pytest.mark.asyncio
class TestWebSocketManager:
    """Test WebSocket manager functionality."""

    async def test_broadcast_agent_status(self):
        """Test broadcasting agent status."""
        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        await manager.startup()

        # Test broadcast without connections (should not error)
        await manager.broadcast_agent_status(
            agent_id="agent_001", status="running", details={"test": "data"}
        )

        await manager.shutdown()

    async def test_multiple_event_types(self):
        """Test different event broadcast types."""
        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        await manager.startup()

        # Test different broadcast methods
        await manager.broadcast_trade_execution(
            agent_id="agent_001", trade_data={"symbol": "2330", "action": "buy"}
        )

        await manager.broadcast_strategy_change(
            agent_id="agent_001", change_data={"reason": "test"}
        )

        await manager.broadcast_portfolio_update(
            agent_id="agent_001", portfolio_data={"cash": 1000000.0}
        )

        await manager.broadcast_performance_update(
            agent_id="agent_001", performance_data={"return_rate": 0.05}
        )

        await manager.broadcast_error(agent_id="agent_001", error_message="Test error")

        await manager.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
