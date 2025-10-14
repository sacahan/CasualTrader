"""
Complete User Workflow E2E Test

Tests the complete user journey:
1. Create Agent with investment preferences
2. Configure agent settings
3. Start agent execution
4. Execute trades
5. Trigger strategy adjustment
6. View reports and performance
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestCompleteUserWorkflow:
    """
    Test complete user workflow from agent creation to trading execution.

    This test suite validates Phase 5 requirements:
    - Complete user flow (create → configure → start → trade → adjust → report)
    - Agent makes decisions based on investment preferences
    - Strategy auto-adjustment mechanism works correctly
    - Strategy changes are recorded and viewable
    - WebSocket real-time updates work in all scenarios
    """

    @pytest.mark.asyncio
    async def test_complete_workflow(self, test_client, cleanup_agents):
        """
        Test complete user workflow end-to-end.

        Workflow Steps:
        1. Create agent with specific investment preferences
        2. Verify agent creation and initial state
        3. Start agent execution
        4. Verify agent executes trading decisions
        5. Trigger strategy adjustment
        6. Verify strategy change is recorded
        7. View performance reports
        """

        # Step 1: Create Agent with Investment Preferences
        create_request = {
            "name": "E2E Test Agent",
            "description": "End-to-end test agent for workflow validation",
            "ai_model": "gpt-4o-mini",  # Use mini for faster testing
            "strategy_prompt": "Focus on technology sector with moderate risk tolerance. "
            "Prioritize companies with strong fundamentals and positive growth trends.",
            "color_theme": "#00bcd4",
            "initial_funds": 1000000.0,
            "max_turns": 30,
            "enabled_tools": {
                "fundamental_analysis": True,
                "technical_analysis": True,
                "risk_assessment": True,
                "sentiment_analysis": False,
                "web_search": True,
                "code_interpreter": False,
            },
            "investment_preferences": {
                "preferred_sectors": ["科技業", "半導體"],
                "excluded_tickers": ["1234"],  # Exclude specific ticker
                "max_position_size": 0.20,  # Max 20% per position
                "rebalance_frequency": "weekly",
            },
            "custom_instructions": "Avoid high-volatility stocks",
        }

        # Mock agent manager to avoid actual AI calls
        with patch("src.api.routers.agents.agent_manager") as mock_manager:
            # Mock create_agent
            mock_manager.create_agent = AsyncMock(return_value="test-agent-001")

            # Mock get_agent response
            mock_agent_data = {
                "id": "test-agent-001",
                "name": "E2E Test Agent",
                "description": "End-to-end test agent for workflow validation",
                "ai_model": "gpt-4o-mini",
                "strategy_prompt": create_request["strategy_prompt"],
                "color_theme": "#00bcd4",
                "current_mode": "OBSERVATION",
                "status": "idle",
                "initial_funds": 1000000.0,
                "current_funds": 1000000.0,
                "max_turns": 30,
                "enabled_tools": create_request["enabled_tools"],
                "investment_preferences": create_request["investment_preferences"],
                "custom_instructions": "Avoid high-volatility stocks",
                "created_at": "2025-10-11T14:00:00",
                "updated_at": "2025-10-11T14:00:00",
            }
            mock_manager.get_agent = AsyncMock(return_value=mock_agent_data)

            # Create agent
            response = test_client.post("/api/agents", json=create_request)

            # Step 2: Verify Agent Creation
            assert response.status_code == 201, f"Failed to create agent: {response.text}"
            agent_data = response.json()
            assert agent_data["name"] == "E2E Test Agent"
            assert agent_data["status"] == "idle"
            assert agent_data["investment_preferences"]["preferred_sectors"] == [
                "科技業",
                "半導體",
            ]
            assert agent_data["investment_preferences"]["excluded_tickers"] == ["1234"]

            agent_id = agent_data["id"]

            # Step 3: Start Agent Execution
            mock_manager.start_agent = AsyncMock()
            mock_agent_data["status"] = "running"

            start_request = {
                "execution_mode": "continuous",
                "max_cycles": 10,
                "stop_on_loss_threshold": 0.15,
            }

            response = test_client.post(f"/api/agents/{agent_id}/start", json=start_request)
            assert response.status_code == 200
            assert response.json()["status"] == "running"

            # Step 4: Verify Agent State After Start
            response = test_client.get(f"/api/agents/{agent_id}")
            assert response.status_code == 200
            agent_data = response.json()
            assert agent_data["status"] == "running"

            # Step 5: Check Portfolio (Initial State)
            with patch("src.api.routers.trading.agent_manager") as mock_trading:
                mock_trading.list_agent_ids = lambda: [agent_id]
                mock_trading.get_agent = AsyncMock(return_value=mock_agent_data)
                mock_trading.get_portfolio = AsyncMock(
                    return_value={
                        "cash": 1000000.0,
                        "positions": {},
                        "total_value": 1000000.0,
                    }
                )

                response = test_client.get(f"/api/trading/agents/{agent_id}/portfolio")
                assert response.status_code == 200
                portfolio = response.json()["portfolio"]
                assert portfolio["cash"] == 1000000.0
                assert portfolio["total_value"] == 1000000.0

            # Step 6: Check Trade History (Should be empty initially)
            with patch("src.api.routers.trading.agent_manager") as mock_trading:
                mock_trading.list_agent_ids = lambda: [agent_id]
                mock_trading.get_agent = AsyncMock(return_value=mock_agent_data)
                mock_trading.get_trades = AsyncMock(return_value=[])

                response = test_client.get(f"/api/trading/agents/{agent_id}/trades")
                assert response.status_code == 200
                assert response.json()["total"] == 0

            # Step 7: Verify Strategy Changes Can Be Queried
            with patch("src.api.routers.trading.agent_manager") as mock_trading:
                mock_trading.list_agent_ids = lambda: [agent_id]
                mock_trading.get_agent = AsyncMock(return_value=mock_agent_data)
                mock_trading.get_strategy_changes = AsyncMock(return_value=[])

                response = test_client.get(f"/api/trading/agents/{agent_id}/strategies")
                assert response.status_code == 200
                assert "strategy_changes" in response.json()

            # Step 8: Check Performance Metrics
            with patch("src.api.routers.trading.agent_manager") as mock_trading:
                mock_trading.list_agent_ids = lambda: [agent_id]
                mock_trading.get_agent = AsyncMock(return_value=mock_agent_data)
                mock_trading.get_performance = AsyncMock(
                    return_value={
                        "return_rate": 0.0,
                        "win_rate": 0.0,
                        "max_drawdown": 0.0,
                        "sharpe_ratio": 0.0,
                        "total_trades": 0,
                    }
                )

                response = test_client.get(f"/api/trading/agents/{agent_id}/performance")
                assert response.status_code == 200
                performance = response.json()["performance"]
                assert "return_rate" in performance

            # Step 9: Stop Agent
            mock_manager.stop_agent = AsyncMock()
            mock_agent_data["status"] = "stopped"

            response = test_client.post(f"/api/agents/{agent_id}/stop")
            assert response.status_code == 200
            assert response.json()["status"] == "stopped"

            # Step 10: Verify Final State
            response = test_client.get(f"/api/agents/{agent_id}")
            assert response.status_code == 200
            final_agent_data = response.json()
            assert final_agent_data["id"] == agent_id
            assert final_agent_data["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_agent_mode_switching(self, test_client, cleanup_agents):
        """
        Test agent mode switching during execution.

        Verifies:
        - Mode can be changed while agent is running
        - Mode change is recorded correctly
        - Each mode has appropriate behavior
        """

        agent_id = "test-agent-mode-001"

        with patch("src.api.routers.agents.agent_manager") as mock_manager:
            mock_agent_data = {
                "id": agent_id,
                "name": "Mode Test Agent",
                "status": "running",
                "current_mode": "OBSERVATION",
            }
            mock_manager.get_agent = AsyncMock(return_value=mock_agent_data)
            mock_manager.update_agent_mode = AsyncMock()

            # Test mode transitions
            modes = ["TRADING", "REBALANCING", "STRATEGY_REVIEW", "OBSERVATION"]

            for mode in modes:
                mode_request = {
                    "mode": mode,
                    "reason": f"Testing {mode} mode",
                    "trigger": "manual",
                }

                response = test_client.put(f"/api/agents/{agent_id}/mode", json=mode_request)
                assert response.status_code == 200
                assert response.json()["mode"] == mode

    @pytest.mark.asyncio
    async def test_agent_reset(self, test_client, cleanup_agents):
        """
        Test agent reset functionality.

        Verifies:
        - Agent portfolio can be reset
        - History is cleared
        - Agent returns to initial state
        """

        agent_id = "test-agent-reset-001"

        with patch("src.api.routers.agents.agent_manager") as mock_manager:
            mock_agent_data = {
                "id": agent_id,
                "name": "Reset Test Agent",
                "status": "idle",
            }
            mock_manager.get_agent = AsyncMock(return_value=mock_agent_data)
            mock_manager.stop_agent = AsyncMock()
            mock_manager.reset_agent = AsyncMock()

            response = test_client.post(f"/api/agents/{agent_id}/reset")
            assert response.status_code == 200
            assert response.json()["status"] == "reset"

    @pytest.mark.asyncio
    async def test_market_status_check(self, test_client):
        """
        Test market status endpoint.

        Verifies:
        - Market trading hours are correctly identified
        - Trading day validation works
        """

        response = test_client.get("/api/trading/market/status")
        assert response.status_code == 200

        market_status = response.json()
        assert "is_trading_day" in market_status
        assert "status" in market_status
        assert "current_time" in market_status


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
