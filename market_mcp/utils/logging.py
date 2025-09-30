"""
Logging utilities for CasualTrader MCP Server.

This module provides structured logging using loguru with configuration
support for different environments and output formats.
"""

import sys
from typing import Optional
from loguru import logger

from ..config import get_config


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> None:
    """
    Setup logging configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        format_string: Custom log format string
    """
    config = get_config()

    # Use provided values or fall back to config
    log_level = level or config.log_level
    log_format = format_string or config.log_format
    log_path = log_file or config.log_file

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format=log_format,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler if specified
    if log_path:
        logger.add(
            log_path,
            level=log_level,
            format=log_format,
            rotation="1 day",
            retention="7 days",
            compression="gzip",
            backtrace=True,
            diagnose=True,
        )

    logger.info(f"Logging initialized - Level: {log_level}")
    if log_path:
        logger.info(f"Log file: {log_path}")


def get_logger(name: str):
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logger.bind(name=name)
