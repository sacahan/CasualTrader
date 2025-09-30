"""
Configuration management for Market MCP Server.

This module provides configuration classes and utilities for managing
server settings, API parameters, and runtime options.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Main configuration class for the MCP Server."""

    # Server Configuration
    server_name: str = Field(default="market-mcp-server", description="MCP Server name")
    server_version: str = Field(default="0.1.0", description="Server version")

    # API Configuration
    twse_api_url: str = Field(
        default="https://mis.twse.com.tw/stock/api/getStockInfo.jsp",
        description="Taiwan Stock Exchange API URL",
    )
    api_timeout: int = Field(default=5, description="API request timeout in seconds")
    api_retries: int = Field(default=3, description="Maximum number of API retries")

    # Rate Limiting Configuration
    rate_limit_per_symbol: int = Field(
        default=30, description="Seconds between requests per symbol"
    )
    rate_limit_global_per_minute: int = Field(
        default=20, description="Global requests per minute"
    )
    rate_limit_per_second: int = Field(
        default=2, description="Requests per second limit"
    )

    # Cache Configuration
    cache_ttl: int = Field(default=30, description="Cache TTL in seconds")
    cache_maxsize: int = Field(default=1000, description="Maximum cache entries")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    log_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="Log format string",
    )

    # Development Configuration
    debug: bool = Field(default=False, description="Enable debug mode")

    class Config:
        env_prefix = "MARKET_MCP_"
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def reload_config() -> Config:
    """Reload configuration from environment."""
    global config
    config = Config()
    return config
