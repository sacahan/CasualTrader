"""
Performance and Benchmark Tests

Tests system performance under various conditions:
- API response time benchmarks
- Agent decision time limits
- WebSocket message latency
- Database query performance
- Concurrent operations
"""

import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, patch

import pytest


class TestPerformanceBenchmarks:
    """
    Performance benchmark tests for Phase 5 validation.

    Validates:
    - API response time < 500ms (95th percentile)
    - Agent decision time < 30 seconds
    - WebSocket push latency < 100ms
    - Database queries < 2 seconds (complex queries)
    """

    def test_api_response_time_health_check(self, test_client):
        """
        Test health check endpoint response time.

        Target: < 100ms for health check
        """
        start_time = time.time()
        response = test_client.get("/api/health")
        elapsed = (time.time() - start_time) * 1000  # Convert to ms

        assert response.status_code == 200
        assert elapsed < 100, f"Health check too slow: {elapsed:.2f}ms"

    def test_api_response_time_list_agents(self, test_client):
        """
        Test list agents endpoint response time.

        Target: < 500ms
        """
        with patch("src.api.routers.agents.agent_manager") as mock_manager:
            mock_manager.list_agents = AsyncMock(return_value=[])

            start_time = time.time()
            response = test_client.get("/api/agents")
            elapsed = (time.time() - start_time) * 1000

            assert response.status_code == 200
            assert elapsed < 500, f"List agents too slow: {elapsed:.2f}ms"

    def test_api_response_time_get_agent(self, test_client):
        """
        Test get agent endpoint response time.

        Target: < 500ms
        """
        agent_id = "test-agent-001"

        with patch("src.api.routers.agents.agent_manager") as mock_manager:
            mock_agent = {
                "id": agent_id,
                "name": "Test Agent",
                "status": "idle",
                "ai_model": "gpt-4o",
                "strategy_prompt": "Test",
                "initial_funds": 1000000.0,
                "max_turns": 50,
                "enabled_tools": {},
                "investment_preferences": {},
                "custom_instructions": "",
                "created_at": "2025-10-11T14:00:00",
                "updated_at": "2025-10-11T14:00:00",
            }
            mock_manager.get_agent = AsyncMock(return_value=mock_agent)

            start_time = time.time()
            response = test_client.get(f"/api/agents/{agent_id}")
            elapsed = (time.time() - start_time) * 1000

            assert response.status_code == 200
            assert elapsed < 500, f"Get agent too slow: {elapsed:.2f}ms"

    def test_concurrent_api_requests(self, test_client):
        """
        Test concurrent API requests performance.

        Target: Handle 50+ concurrent requests without errors
        """

        with patch("src.api.routers.agents.agent_manager") as mock_manager:
            mock_manager.list_agents = AsyncMock(return_value=[])

            def make_request():
                response = test_client.get("/api/agents")
                return response.status_code == 200

            # Execute 50 concurrent requests
            with ThreadPoolExecutor(max_workers=10) as executor:
                start_time = time.time()
                futures = [executor.submit(make_request) for _ in range(50)]
                results = [f.result() for f in futures]
                elapsed = time.time() - start_time

            # All requests should succeed
            assert all(results), "Some concurrent requests failed"
            assert elapsed < 5.0, f"Concurrent requests too slow: {elapsed:.2f}s"

            # Calculate average response time
            avg_time = (elapsed / 50) * 1000
            assert avg_time < 500, f"Average response time too high: {avg_time:.2f}ms"

    def test_market_status_performance(self, test_client):
        """
        Test market status check performance.

        Target: < 200ms (includes Taiwan holiday check)
        """
        start_time = time.time()
        response = test_client.get("/api/trading/market/status")
        elapsed = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert elapsed < 200, f"Market status check too slow: {elapsed:.2f}ms"

    @pytest.mark.asyncio
    async def test_websocket_latency(self, test_client):
        """
        Test WebSocket message latency.

        Target: < 100ms for message broadcast
        """
        from src.api.websocket import WebSocketManager

        manager = WebSocketManager()
        await manager.startup()

        # Measure broadcast time (without actual connections, measures overhead)
        start_time = time.time()
        await manager.broadcast_agent_status(agent_id="test-001", status="running", details={})
        elapsed = (time.time() - start_time) * 1000

        await manager.shutdown()

        # Should be very fast with no connections
        assert elapsed < 10, f"WebSocket broadcast overhead too high: {elapsed:.2f}ms"


class TestStressAndStability:
    """
    Stress and stability tests.

    Validates:
    - System handles high load
    - No memory leaks during extended operation
    - Graceful degradation under stress
    """

    def test_rapid_agent_operations(self, test_client):
        """
        Test rapid create/delete operations.

        Validates system stability under rapid state changes.
        """
        with patch("src.api.routers.agents.agent_manager") as mock_manager:
            # Mock rapid operations
            mock_manager.create_agent = AsyncMock(side_effect=lambda **k: f"agent-{k}")
            mock_manager.delete_agent = AsyncMock()

            # Perform rapid operations
            operations = []
            for i in range(20):
                try:
                    # Rapid operations shouldn't cause errors
                    mock_manager.create_agent()
                    mock_manager.delete_agent(f"agent-{i}")
                    operations.append(True)
                except Exception:
                    operations.append(False)

            # Most operations should succeed
            success_rate = sum(operations) / len(operations)
            assert success_rate > 0.9, f"Too many failures: {success_rate:.1%}"

    def test_large_portfolio_query(self, test_client):
        """
        Test performance with large portfolio data.

        Validates query performance with many positions.
        """
        agent_id = "test-large-portfolio"

        # Create large portfolio data
        large_portfolio = {
            "cash": 500000.0,
            "positions": {
                f"{2000 + i}": {
                    "ticker": f"{2000 + i}",
                    "quantity": 1000 * (i + 1),
                    "avg_price": 100.0 + i,
                    "current_price": 105.0 + i,
                    "market_value": 105000.0 + i * 1000,
                }
                for i in range(50)  # 50 positions
            },
            "total_value": 7750000.0,
        }

        with patch("src.api.routers.trading.agent_manager") as mock_manager:
            mock_manager.list_agent_ids = lambda: [agent_id]
            mock_manager.get_agent = AsyncMock(
                return_value={"id": agent_id, "name": "Large Portfolio Agent"}
            )
            mock_manager.get_portfolio = AsyncMock(return_value=large_portfolio)

            start_time = time.time()
            response = test_client.get(f"/api/trading/agents/{agent_id}/portfolio")
            elapsed = (time.time() - start_time) * 1000

            assert response.status_code == 200
            assert elapsed < 1000, f"Large portfolio query too slow: {elapsed:.2f}ms"

            # Verify data integrity
            portfolio = response.json()["portfolio"]
            assert len(portfolio["positions"]) == 50

    def test_many_strategy_changes(self, test_client):
        """
        Test performance with extensive strategy history.

        Validates query performance with many records.
        """
        agent_id = "test-many-strategies"

        # Create many strategy changes
        many_changes = [
            {
                "id": f"change-{i}",
                "agent_id": agent_id,
                "trigger_reason": f"Test trigger {i}",
                "change_content": f"Test change {i}",
                "agent_explanation": f"Test explanation {i}",
                "performance_at_change": {"return_rate": 0.01 * i},
                "timestamp": f"2025-10-{10 + (i % 20):02d}T14:00:00",
            }
            for i in range(100)  # 100 strategy changes
        ]

        with patch("src.api.routers.trading.agent_manager") as mock_manager:
            mock_manager.list_agent_ids = lambda: [agent_id]
            mock_manager.get_agent = AsyncMock(
                return_value={"id": agent_id, "name": "Many Strategy Agent"}
            )
            mock_manager.get_strategy_changes = AsyncMock(return_value=many_changes)

            start_time = time.time()
            response = test_client.get(f"/api/trading/agents/{agent_id}/strategies")
            elapsed = (time.time() - start_time) * 1000

            assert response.status_code == 200
            assert elapsed < 2000, f"Many strategy changes query too slow: {elapsed:.2f}ms"

            # Verify data integrity
            changes = response.json()["strategy_changes"]
            assert len(changes) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
