"""
Core MCP Server implementation for CasualTrader.

This module provides the main MCP Server class that handles the
Model Context Protocol communication and tool registration.
"""

import asyncio
from typing import Any, Dict, List
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool

from .config import get_config
from .utils.logging import setup_logging, get_logger


class MCPServer:
    """
    Main MCP Server class for CasualTrader stock price service.

    This server provides tools for querying Taiwan stock prices through
    the Model Context Protocol interface.
    """

    def __init__(self):
        """Initialize the MCP Server."""
        self.config = get_config()
        self.server = Server("market-mcp-server")
        self.logger = get_logger(__name__)

        # Setup logging
        setup_logging()
        self.logger.info("Initializing Market MCP Server")

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources."""
            return []

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="get_taiwan_stock_price",
                    description="取得台灣股票即時價格資訊",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "台灣股票代號 (4位數字，例如: 2330)",
                                "pattern": r"^[0-9]{4}$",
                            }
                        },
                        "required": ["symbol"],
                    },
                )
            ]

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[Dict[str, Any]]:
            """Handle tool calls."""
            self.logger.info(f"Tool called: {name} with arguments: {arguments}")

            if name == "get_taiwan_stock_price":
                return await self._get_taiwan_stock_price(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def _get_taiwan_stock_price(
        self, arguments: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Handle get_taiwan_stock_price tool call.

        This is a placeholder implementation for the basic architecture.
        The actual API integration will be implemented in task-002.
        """
        symbol = arguments.get("symbol")

        if not symbol:
            raise ValueError("Symbol is required")

        # Validate symbol format
        if not symbol.isdigit() or len(symbol) != 4:
            raise ValueError("Symbol must be a 4-digit number")

        self.logger.info(f"Querying stock price for symbol: {symbol}")

        # Placeholder response - will be replaced with actual API integration
        response_data = {
            "symbol": symbol,
            "company_name": f"公司 {symbol}",
            "current_price": 100.0,
            "status": "success",
            "message": "基礎架構測試回應 - API 整合將在 task-002 實作",
            "timestamp": "2025-09-30T17:00:00Z",
        }

        return [{"type": "text", "text": str(response_data)}]

    async def run(self) -> None:
        """Run the MCP server."""
        self.logger.info("Starting Market MCP Server")
        self.logger.info(f"Server version: {self.config.server_version}")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


async def main() -> None:
    """Main entry point for the MCP Server."""
    server = MCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
