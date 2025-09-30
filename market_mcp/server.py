"""
Core MCP Server implementation for CasualTrader.

This module provides the main MCP Server class that handles the
Model Context Protocol communication and tool registration.
"""

import asyncio
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool

from .tools import stock_price_tool
from .utils.logging import get_logger, setup_logging


class MCPServer:
    """
    Main MCP Server class for CasualTrader stock price service.

    This server provides tools for querying Taiwan stock prices through
    the Model Context Protocol interface.
    """

    def __init__(self):
        """Initialize the MCP Server."""
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
        async def list_resources() -> list[Resource]:
            """List available resources."""
            return []

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            tool_def = stock_price_tool.get_tool_definition()
            return [
                Tool(
                    name=tool_def["name"],
                    description=tool_def["description"],
                    inputSchema=tool_def["inputSchema"],
                )
            ]

        @self.server.call_tool()
        async def call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[dict[str, Any]]:
            """Handle tool calls."""
            self.logger.info(f"Tool called: {name} with arguments: {arguments}")

            if name == "get_taiwan_stock_price":
                return await stock_price_tool.get_taiwan_stock_price(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def run(self) -> None:
        """Run the MCP server."""
        self.logger.info("Starting Market MCP Server")
        server_version = os.getenv("MARKET_MCP_SERVER_VERSION", "1.0.0")
        self.logger.info(f"Server version: {server_version}")

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
