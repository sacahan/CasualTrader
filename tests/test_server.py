"""
Tests for the CasualTrader MCP Server basic functionality.

This module contains basic tests for the MCP Server architecture
and configuration management.
"""

import pytest
from unittest.mock import AsyncMock, patch

# from market_mcp.config import Config, get_config, reload_config  # Config 已被移除
from market_mcp.server import MCPServer


# class TestConfig:
#     """Test configuration management."""
#
#     # 註釋：Config 類別已被移除，直接使用環境變數
#
#     def test_config_defaults(self):
#         """Test default configuration values."""
#         config = Config()
#         assert config.server_name == "market-mcp-server"
#         assert config.server_version == "1.0.0"
#         assert config.max_concurrent_requests == 100
#         assert config.rate_limit_per_second == 10
#         assert config.rate_limit_per_symbol == 30
#         assert config.cache_ttl == 30
#         assert config.log_level == "INFO"
#         assert config.debug is False
#
#     def test_get_config(self):
#         """Test global config instance."""
#         config = get_config()
#         assert isinstance(config, Config)
#         assert config.server_name == "market-mcp-server"
#
#     def test_reload_config(self):
#         """Test configuration reload."""
#         config = reload_config()
#         assert isinstance(config, Config)


class TestMCPServer:
    """Test MCP Server basic functionality."""

    @pytest.fixture
    def server(self):
        """Create a test server instance."""
        with patch("market_mcp.server.setup_logging"):
            return MCPServer()

    def test_server_initialization(self, server):
        """Test server initialization."""
        assert server is not None
        assert hasattr(server, "config")
        assert hasattr(server, "server")
        assert hasattr(server, "logger")

    @pytest.mark.asyncio
    async def test_get_taiwan_stock_price_validation(self, server):
        """Test stock price tool input validation."""
        # Test missing symbol
        with pytest.raises(ValueError, match="Symbol is required"):
            await server._get_taiwan_stock_price({})

        # Test invalid symbol format
        with pytest.raises(ValueError, match="Symbol must be a 4-digit number"):
            await server._get_taiwan_stock_price({"symbol": "abc"})

        with pytest.raises(ValueError, match="Symbol must be a 4-digit number"):
            await server._get_taiwan_stock_price({"symbol": "12345"})

        # Test valid symbol
        result = await server._get_taiwan_stock_price({"symbol": "2330"})
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "2330" in result[0]["text"]

    @pytest.mark.asyncio
    async def test_list_tools(self, server):
        """Test tools listing."""
        # Simply verify that the server has been initialized properly
        # and has the MCP server instance
        assert server.server is not None
        assert hasattr(server.server, "request_handlers")

        # Test that the Taiwan stock price method exists
        assert hasattr(server, "_get_taiwan_stock_price")
