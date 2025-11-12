"""
單元測試: calculate_unrealized_pnl 方法

測試 AgentsService.calculate_unrealized_pnl 方法的功能，
包括正常情況、邊界情況和異常處理。
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from service.agents_service import AgentsService, AgentDatabaseError
from database.models import AgentHolding


@pytest.mark.asyncio
class TestCalculateUnrealizedPnL:
    """測試 calculate_unrealized_pnl 方法"""

    @pytest.fixture
    def mock_session(self):
        """創建 mock session"""
        session = AsyncMock()
        return session

    @pytest.fixture
    def agents_service(self, mock_session):
        """創建 AgentsService 實例"""
        return AgentsService(mock_session)

    async def test_no_holdings_returns_zero(self, agents_service):
        """測試：無持倉時返回 0"""
        # Arrange
        agent_id = "test-agent-001"
        with patch.object(agents_service, "get_agent_holdings", return_value=[]):
            # Act
            result = await agents_service.calculate_unrealized_pnl(agent_id)

            # Assert
            assert result == Decimal("0")

    async def test_single_holding_profit(self, agents_service):
        """測試：單一持倉獲利情況"""
        # Arrange
        agent_id = "test-agent-001"

        # 創建 mock holding
        holding = MagicMock(spec=AgentHolding)
        holding.ticker = "2330"
        holding.quantity = 1000
        holding.average_cost = Decimal("500.00")
        holding.company_name = "台積電"

        # Mock MCP Client 返回更高的價格
        mock_price_data = {
            "success": True,
            "data": {
                "symbol": "2330",
                "company_name": "台積電",
                "current_price": 550.00,  # 獲利 50 元/股
                "change": 5.0,
                "change_percent": 1.0,
            },
        }

        with patch.object(agents_service, "get_agent_holdings", return_value=[holding]):
            with patch("api.mcp_client.MCPMarketClient") as MockMCPClient:
                # 設置 async context manager
                mock_client_instance = AsyncMock()
                mock_client_instance.get_stock_price = AsyncMock(return_value=mock_price_data)
                MockMCPClient.return_value.__aenter__.return_value = mock_client_instance

                # Act
                result = await agents_service.calculate_unrealized_pnl(agent_id)

                # Assert
                expected_pnl = (Decimal("550.00") - Decimal("500.00")) * 1000
                assert result == expected_pnl
                assert result == Decimal("50000.00")

    async def test_single_holding_loss(self, agents_service):
        """測試：單一持倉虧損情況"""
        # Arrange
        agent_id = "test-agent-002"

        holding = MagicMock(spec=AgentHolding)
        holding.ticker = "2317"
        holding.quantity = 2000
        holding.average_cost = Decimal("300.00")

        # Mock MCP Client 返回較低的價格
        mock_price_data = {
            "success": True,
            "data": {
                "current_price": 280.00,  # 虧損 20 元/股
            },
        }

        with patch.object(agents_service, "get_agent_holdings", return_value=[holding]):
            with patch("api.mcp_client.MCPMarketClient") as MockMCPClient:
                mock_client_instance = AsyncMock()
                mock_client_instance.get_stock_price = AsyncMock(return_value=mock_price_data)
                MockMCPClient.return_value.__aenter__.return_value = mock_client_instance

                # Act
                result = await agents_service.calculate_unrealized_pnl(agent_id)

                # Assert
                expected_pnl = (Decimal("280.00") - Decimal("300.00")) * 2000
                assert result == expected_pnl
                assert result == Decimal("-40000.00")

    async def test_multiple_holdings_mixed(self, agents_service):
        """測試：多個持倉混合獲利和虧損"""
        # Arrange
        agent_id = "test-agent-003"

        holdings = [
            MagicMock(
                ticker="2330",
                quantity=1000,
                average_cost=Decimal("500.00"),
                spec=AgentHolding,
            ),
            MagicMock(
                ticker="2317",
                quantity=2000,
                average_cost=Decimal("300.00"),
                spec=AgentHolding,
            ),
            MagicMock(
                ticker="2454",
                quantity=500,
                average_cost=Decimal("100.00"),
                spec=AgentHolding,
            ),
        ]

        # Mock 不同股票的價格
        price_responses = {
            "2330": {"success": True, "data": {"current_price": 550.00}},  # +50
            "2317": {"success": True, "data": {"current_price": 280.00}},  # -20
            "2454": {"success": True, "data": {"current_price": 105.00}},  # +5
        }

        async def mock_get_price(ticker):
            return price_responses[ticker]

        with patch.object(agents_service, "get_agent_holdings", return_value=holdings):
            with patch("api.mcp_client.MCPMarketClient") as MockMCPClient:
                mock_client_instance = AsyncMock()
                mock_client_instance.get_stock_price = AsyncMock(side_effect=mock_get_price)
                MockMCPClient.return_value.__aenter__.return_value = mock_client_instance

                # Act
                result = await agents_service.calculate_unrealized_pnl(agent_id)

                # Assert
                # 2330: (550 - 500) * 1000 = +50,000
                # 2317: (280 - 300) * 2000 = -40,000
                # 2454: (105 - 100) * 500 = +2,500
                # Total: 50,000 - 40,000 + 2,500 = 12,500
                assert result == Decimal("12500.00")

    async def test_api_failure_for_one_stock(self, agents_service):
        """測試：部分股票 API 調用失敗"""
        # Arrange
        agent_id = "test-agent-004"

        holdings = [
            MagicMock(
                ticker="2330",
                quantity=1000,
                average_cost=Decimal("500.00"),
                spec=AgentHolding,
            ),
            MagicMock(
                ticker="2317",
                quantity=2000,
                average_cost=Decimal("300.00"),
                spec=AgentHolding,
            ),
        ]

        # Mock 一個成功，一個失敗
        price_responses = {
            "2330": {"success": True, "data": {"current_price": 550.00}},
            "2317": {"success": False, "error": "Stock not found"},
        }

        async def mock_get_price(ticker):
            return price_responses[ticker]

        with patch.object(agents_service, "get_agent_holdings", return_value=holdings):
            with patch("api.mcp_client.MCPMarketClient") as MockMCPClient:
                mock_client_instance = AsyncMock()
                mock_client_instance.get_stock_price = AsyncMock(side_effect=mock_get_price)
                MockMCPClient.return_value.__aenter__.return_value = mock_client_instance

                # Act
                result = await agents_service.calculate_unrealized_pnl(agent_id)

                # Assert
                # 只計算成功的 2330
                expected_pnl = (Decimal("550.00") - Decimal("500.00")) * 1000
                assert result == expected_pnl

    async def test_missing_current_price_in_response(self, agents_service):
        """測試：API 回應缺少 current_price 欄位"""
        # Arrange
        agent_id = "test-agent-005"

        holding = MagicMock(
            ticker="2330",
            quantity=1000,
            average_cost=Decimal("500.00"),
            spec=AgentHolding,
        )

        # Mock 缺少 current_price
        mock_price_data = {
            "success": True,
            "data": {
                "symbol": "2330",
                # current_price 缺失
            },
        }

        with patch.object(agents_service, "get_agent_holdings", return_value=[holding]):
            with patch("api.mcp_client.MCPMarketClient") as MockMCPClient:
                mock_client_instance = AsyncMock()
                mock_client_instance.get_stock_price = AsyncMock(return_value=mock_price_data)
                MockMCPClient.return_value.__aenter__.return_value = mock_client_instance

                # Act
                result = await agents_service.calculate_unrealized_pnl(agent_id)

                # Assert
                # 應該跳過該持倉，返回 0
                assert result == Decimal("0")

    async def test_api_exception_handling(self, agents_service):
        """測試：API 調用拋出異常"""
        # Arrange
        agent_id = "test-agent-006"

        holding = MagicMock(
            ticker="2330",
            quantity=1000,
            average_cost=Decimal("500.00"),
            spec=AgentHolding,
        )

        with patch.object(agents_service, "get_agent_holdings", return_value=[holding]):
            with patch("api.mcp_client.MCPMarketClient") as MockMCPClient:
                mock_client_instance = AsyncMock()
                mock_client_instance.get_stock_price = AsyncMock(
                    side_effect=Exception("Network error")
                )
                MockMCPClient.return_value.__aenter__.return_value = mock_client_instance

                # Act
                result = await agents_service.calculate_unrealized_pnl(agent_id)

                # Assert
                # 應該處理異常並返回 0
                assert result == Decimal("0")

    async def test_zero_quantity_holding(self, agents_service):
        """測試：持倉數量為 0"""
        # Arrange
        agent_id = "test-agent-007"

        holding = MagicMock(
            ticker="2330",
            quantity=0,  # 數量為 0
            average_cost=Decimal("500.00"),
            spec=AgentHolding,
        )

        mock_price_data = {
            "success": True,
            "data": {"current_price": 550.00},
        }

        with patch.object(agents_service, "get_agent_holdings", return_value=[holding]):
            with patch("api.mcp_client.MCPMarketClient") as MockMCPClient:
                mock_client_instance = AsyncMock()
                mock_client_instance.get_stock_price = AsyncMock(return_value=mock_price_data)
                MockMCPClient.return_value.__aenter__.return_value = mock_client_instance

                # Act
                result = await agents_service.calculate_unrealized_pnl(agent_id)

                # Assert
                assert result == Decimal("0")

    async def test_database_error(self, agents_service):
        """測試：資料庫查詢失敗"""
        # Arrange
        agent_id = "test-agent-008"

        with patch.object(
            agents_service,
            "get_agent_holdings",
            side_effect=Exception("Database connection error"),
        ):
            # Act & Assert
            with pytest.raises(AgentDatabaseError):
                await agents_service.calculate_unrealized_pnl(agent_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
