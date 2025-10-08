"""
Complete End-to-End API Integration Tests

This test suite validates the complete data flow:
API -> AgentManager -> TradingAgent -> DatabaseService -> Database

Tests cover:
1. Market status with actual MCP integration
2. Agent portfolio data retrieval
3. Trading history access
4. Strategy changes tracking
5. Performance metrics calculation
"""

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
def test_agent(client):
    """Create a test agent and return its ID."""
    request_payload = {
        "name": "E2E測試代理",
        "description": "完整端對端測試代理",
        "ai_model": "gpt-4o-mini",
        "strategy_type": "balanced",
        "strategy_prompt": "測試策略：用於驗證完整數據流",
        "initial_funds": 1000000.0,
        "max_turns": 50,
        "risk_tolerance": 0.5,
        "enabled_tools": {
            "fundamental_analysis": True,
            "technical_analysis": True,
            "risk_assessment": True,
        },
        "investment_preferences": {
            "preferred_sectors": ["科技", "金融"],
            "excluded_stocks": [],
            "max_position_size": 0.2,
            "rebalance_frequency": "weekly",
        },
    }

    response = client.post("/api/agents", json=request_payload)
    assert response.status_code == 201
    agent_id = response.json()["id"]

    yield agent_id

    # Cleanup: delete agent after test
    # Note: Implement delete endpoint if needed


class TestMarketStatusIntegration:
    """Test market status endpoint with MCP integration."""

    def test_market_status_returns_valid_data(self, client):
        """Test that market status returns valid structure."""
        response = client.get("/api/trading/market/status")

        assert response.status_code == 200, f"Failed: {response.text}"

        data = response.json()

        # Validate required fields
        assert "is_trading_day" in data
        assert "is_trading_hours" in data
        assert "market_open" in data
        assert "market_close" in data
        assert "current_time" in data
        assert "current_date" in data
        assert "status" in data

        # Validate types
        assert isinstance(data["is_trading_day"], bool)
        assert isinstance(data["is_trading_hours"], bool)
        assert isinstance(data["market_open"], str)
        assert isinstance(data["market_close"], str)
        assert isinstance(data["current_time"], str)
        assert isinstance(data["current_date"], str)
        assert data["status"] in [
            "open",
            "closed",
            "pre_market",
            "after_market",
            "weekend",
            "holiday",
        ]

        print(f"✅ Market status: {data['status']}")
        print(f"   Trading day: {data['is_trading_day']}")
        print(f"   Trading hours: {data['is_trading_hours']}")
        print(f"   Current time: {data['current_time']}")

    def test_market_status_weekend_detection(self, client):
        """Test that market status correctly identifies weekends."""
        response = client.get("/api/trading/market/status")
        assert response.status_code == 200

        data = response.json()

        # On weekends, should not be a trading day
        if data.get("is_weekend", False):
            assert data["is_trading_day"] is False
            assert data["status"] in ["weekend", "closed"]
            print("✅ Weekend correctly detected")

    def test_market_status_holiday_detection(self, client):
        """Test that market status correctly identifies holidays."""
        response = client.get("/api/trading/market/status")
        assert response.status_code == 200

        data = response.json()

        # On holidays, should not be a trading day
        if data.get("is_holiday", False):
            assert data["is_trading_day"] is False
            assert data["holiday_name"] is not None
            print(f"✅ Holiday detected: {data['holiday_name']}")


class TestPortfolioDataFlow:
    """Test portfolio data retrieval flow."""

    def test_get_agent_portfolio_structure(self, client, test_agent):
        """Test portfolio endpoint returns correct structure."""
        response = client.get(f"/api/trading/agents/{test_agent}/portfolio")

        assert response.status_code == 200, f"Failed: {response.text}"

        data = response.json()

        # Validate structure
        assert "agent_id" in data
        assert "portfolio" in data
        assert "timestamp" in data

        portfolio = data["portfolio"]
        assert "cash" in portfolio
        assert "holdings" in portfolio
        assert "total_value" in portfolio
        assert isinstance(portfolio["holdings"], list)

        print(f"✅ Portfolio structure valid for agent {test_agent}")
        print(f"   Cash: ${portfolio['cash']:,.2f}")
        print(f"   Total value: ${portfolio['total_value']:,.2f}")
        print(f"   Holdings: {len(portfolio['holdings'])}")

    def test_portfolio_empty_initial_state(self, client, test_agent):
        """Test that new agent has empty portfolio with initial cash."""
        response = client.get(f"/api/trading/agents/{test_agent}/portfolio")
        assert response.status_code == 200

        portfolio = response.json()["portfolio"]

        # New agent should have no holdings
        assert len(portfolio["holdings"]) == 0
        assert portfolio["cash"] == 1000000.0
        assert portfolio["total_value"] == 1000000.0

        print("✅ Initial portfolio state correct (empty holdings, full cash)")


class TestTradingHistoryDataFlow:
    """Test trading history data retrieval flow."""

    def test_get_agent_trades_structure(self, client, test_agent):
        """Test trades endpoint returns correct structure."""
        response = client.get(f"/api/trading/agents/{test_agent}/trades?limit=10")

        assert response.status_code == 200, f"Failed: {response.text}"

        data = response.json()

        # Validate structure
        assert "agent_id" in data
        assert "trades" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        assert isinstance(data["trades"], list)
        assert data["agent_id"] == test_agent
        assert data["limit"] == 10
        assert data["offset"] == 0

        print(f"✅ Trades structure valid for agent {test_agent}")
        print(f"   Total trades: {data['total']}")

    def test_trades_pagination(self, client, test_agent):
        """Test trades pagination parameters."""
        # Test with different limits and offsets
        response1 = client.get(
            f"/api/trading/agents/{test_agent}/trades?limit=5&offset=0"
        )
        assert response1.status_code == 200

        response2 = client.get(
            f"/api/trading/agents/{test_agent}/trades?limit=10&offset=5"
        )
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert data1["limit"] == 5
        assert data2["limit"] == 10
        assert data2["offset"] == 5

        print("✅ Trades pagination works correctly")

    def test_trades_empty_initial_state(self, client, test_agent):
        """Test that new agent has no trades initially."""
        response = client.get(f"/api/trading/agents/{test_agent}/trades")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0
        assert len(data["trades"]) == 0

        print("✅ Initial trades state correct (no trades)")


class TestStrategyChangesDataFlow:
    """Test strategy changes data retrieval flow."""

    def test_get_strategy_changes_structure(self, client, test_agent):
        """Test strategy changes endpoint returns correct structure."""
        response = client.get(f"/api/trading/agents/{test_agent}/strategies?limit=10")

        assert response.status_code == 200, f"Failed: {response.text}"

        data = response.json()

        # Validate structure
        assert "agent_id" in data
        assert "strategy_changes" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        assert isinstance(data["strategy_changes"], list)
        assert data["agent_id"] == test_agent

        print(f"✅ Strategy changes structure valid for agent {test_agent}")
        print(f"   Total changes: {data['total']}")

    def test_strategy_changes_pagination(self, client, test_agent):
        """Test strategy changes pagination."""
        response = client.get(
            f"/api/trading/agents/{test_agent}/strategies?limit=20&offset=0"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["limit"] == 20
        assert data["offset"] == 0

        print("✅ Strategy changes pagination works")

    def test_strategy_changes_empty_initial(self, client, test_agent):
        """Test that new agent has no strategy changes."""
        response = client.get(f"/api/trading/agents/{test_agent}/strategies")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0

        print("✅ Initial strategy changes state correct (no changes)")


class TestPerformanceMetricsDataFlow:
    """Test performance metrics data retrieval flow."""

    def test_get_agent_performance_structure(self, client, test_agent):
        """Test performance endpoint returns correct structure."""
        response = client.get(f"/api/trading/agents/{test_agent}/performance")

        assert response.status_code == 200, f"Failed: {response.text}"

        data = response.json()

        # Validate structure
        assert "agent_id" in data
        assert "performance" in data
        assert "timestamp" in data

        performance = data["performance"]
        assert "initial_funds" in performance
        assert "current_funds" in performance
        assert "total_return" in performance
        assert "total_return_percent" in performance

        print(f"✅ Performance structure valid for agent {test_agent}")
        print(f"   Initial: ${performance['initial_funds']:,.2f}")
        print(f"   Current: ${performance['current_funds']:,.2f}")
        print(f"   Return: {performance['total_return_percent']:.2f}%")

    def test_performance_initial_state(self, client, test_agent):
        """Test that new agent has zero returns initially."""
        response = client.get(f"/api/trading/agents/{test_agent}/performance")
        assert response.status_code == 200

        performance = response.json()["performance"]

        # New agent should have no returns
        assert performance["initial_funds"] == 1000000.0
        assert performance["current_funds"] == 1000000.0
        assert performance["total_return"] == 0.0
        assert performance["total_return_percent"] == 0.0

        print("✅ Initial performance state correct (zero returns)")


class TestCompleteDataFlowIntegration:
    """Test complete data flow across all endpoints."""

    def test_agent_lifecycle_data_flow(self, client):
        """
        Test complete agent lifecycle data flow:
        1. Create agent
        2. Check initial state
        3. Verify all endpoints work
        4. Ensure data consistency
        """
        # 1. Create agent
        create_response = client.post(
            "/api/agents",
            json={
                "name": "完整測試代理",
                "description": "完整生命週期測試代理",
                "ai_model": "gpt-4o-mini",
                "strategy_type": "balanced",
                "strategy_prompt": "完整生命週期測試策略",
                "initial_funds": 500000.0,
                "risk_tolerance": 0.5,
                "enabled_tools": {
                    "fundamental_analysis": True,
                    "technical_analysis": True,
                },
                "investment_preferences": {
                    "preferred_sectors": ["科技"],
                    "excluded_stocks": [],
                    "max_position_size": 0.2,
                    "rebalance_frequency": "weekly",
                },
            },
        )
        assert create_response.status_code == 201, f"Failed: {create_response.text}"
        agent_id = create_response.json()["id"]

        print(f"\n✅ Step 1: Agent created with ID {agent_id}")

        # 2. Get agent details
        agent_response = client.get(f"/api/agents/{agent_id}")
        assert agent_response.status_code == 200
        print("✅ Step 2: Agent details retrieved")

        # 3. Check portfolio
        portfolio_response = client.get(f"/api/trading/agents/{agent_id}/portfolio")
        assert portfolio_response.status_code == 200
        portfolio = portfolio_response.json()["portfolio"]
        assert portfolio["cash"] == 500000.0
        print("✅ Step 3: Portfolio data consistent")

        # 4. Check trades
        trades_response = client.get(f"/api/trading/agents/{agent_id}/trades")
        assert trades_response.status_code == 200
        assert trades_response.json()["total"] == 0
        print("✅ Step 4: Trades data consistent")

        # 5. Check strategies
        strategies_response = client.get(f"/api/trading/agents/{agent_id}/strategies")
        assert strategies_response.status_code == 200
        assert strategies_response.json()["total"] == 0
        print("✅ Step 5: Strategy changes data consistent")

        # 6. Check performance
        performance_response = client.get(f"/api/trading/agents/{agent_id}/performance")
        assert performance_response.status_code == 200
        perf = performance_response.json()["performance"]
        assert perf["initial_funds"] == 500000.0
        assert perf["current_funds"] == 500000.0
        print("✅ Step 6: Performance data consistent")

        print(f"\n✅ Complete data flow validated for agent {agent_id}")


class TestErrorHandling:
    """Test error handling across all endpoints."""

    def test_portfolio_nonexistent_agent(self, client):
        """Test portfolio endpoint with nonexistent agent."""
        response = client.get("/api/trading/agents/nonexistent-id/portfolio")
        assert response.status_code == 404

    def test_trades_nonexistent_agent(self, client):
        """Test trades endpoint with nonexistent agent."""
        response = client.get("/api/trading/agents/nonexistent-id/trades")
        assert response.status_code == 404

    def test_strategies_nonexistent_agent(self, client):
        """Test strategies endpoint with nonexistent agent."""
        response = client.get("/api/trading/agents/nonexistent-id/strategies")
        assert response.status_code == 404

    def test_performance_nonexistent_agent(self, client):
        """Test performance endpoint with nonexistent agent."""
        response = client.get("/api/trading/agents/nonexistent-id/performance")
        assert response.status_code == 404

    def test_invalid_pagination_parameters(self, client, test_agent):
        """Test trades endpoint with invalid pagination."""
        # Negative limit should be rejected
        response = client.get(f"/api/trading/agents/{test_agent}/trades?limit=-1")
        assert response.status_code == 422

        # Limit too large should be rejected
        response = client.get(f"/api/trading/agents/{test_agent}/trades?limit=10000")
        assert response.status_code == 422

        print("✅ Invalid pagination parameters properly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
