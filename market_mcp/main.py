#!/usr/bin/env python3
"""
Main entry point for Market MCP Server.

This module provides the main() function that serves as the entry point
for the uvx command execution.
"""

import sys
from pathlib import Path

from market_mcp.server import main as server_main
from market_mcp.utils.logging import get_logger

# Add the project root to Python path for development
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def main() -> None:
    """
    Main entry point for the MCP Server.

    This function is called when the server is started via:
    Usage examples:
    - uvx --from . market-mcp-server
    - python -m market_mcp.main
    """
    logger = get_logger(__name__)

    try:
        logger.info("Starting Market MCP Server via main() (FastMCP 模式)")
        server_main()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
