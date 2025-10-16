"""
Configuration Management

Load and manage environment variables for the API server.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Server Settings
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    api_reload: bool = Field(default=True, description="Enable auto-reload")
    api_workers: int = Field(default=1, description="Number of workers")

    # CORS Settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")

    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        description="Log format string",
    )
    log_file: str = Field(default="logs/api_{time:YYYY-MM-DD}.log", description="Log file path")
    log_rotation: str = Field(default="500 MB", description="Log rotation size")
    log_retention: str = Field(default="30 days", description="Log retention period")
    log_compression: str = Field(default="zip", description="Log compression format")

    # Database Settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///casualtrader.db",
        description="Database connection URL (relative to backend directory)",
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # Agent Settings
    max_agents: int = Field(default=10, description="Maximum concurrent agent executions")
    default_ai_model: str = Field(default="gpt-5-mini", description="Default AI model")
    default_initial_capital: float = Field(default=1000000.0, description="Default initial capital")
    default_max_turns: int = Field(default=30, description="Default max turns for main agent")
    default_agent_timeout: int = Field(
        default=300,
        description="Default execution timeout for main agent (seconds), applies to all sub-agents",
    )
    default_subagent_max_turns: int = Field(
        default=15, description="Default max turns for sub-agents"
    )

    # WebSocket Settings
    ws_heartbeat_interval: int = Field(
        default=30, description="WebSocket heartbeat interval (seconds)"
    )
    ws_max_connections: int = Field(default=100, description="Maximum WebSocket connections")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=False, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")

    # Environment
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=True, description="Debug mode")

    # MCP Server Settings - Casual Market
    mcp_casual_market_command: str = Field(
        default="uvx", description="MCP Casual Market command (uvx or npx)"
    )
    mcp_casual_market_args: list[str] = Field(
        default=["casual-market-mcp"], description="MCP Casual Market arguments array"
    )
    mcp_casual_market_timeout: int = Field(
        default=10, description="MCP Casual Market API timeout (seconds)"
    )
    mcp_casual_market_retries: int = Field(default=5, description="MCP Casual Market API retries")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle JSON-like string format
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback to comma-separated
                return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("mcp_casual_market_args", mode="before")
    @classmethod
    def parse_mcp_args(cls, v: Any) -> list[str]:
        """Parse MCP args from string or list."""
        if isinstance(v, str):
            # Handle JSON-like string format
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback to single arg
                return [v]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    def setup_logging(self) -> None:
        """Configure loguru logger with settings."""
        from loguru import logger

        # Remove default handler
        logger.remove()

        # Add console handler
        logger.add(
            sink=lambda msg: print(msg, end=""),
            format=self.log_format,
            level=self.log_level,
            colorize=True,
        )

        # Add file handler if log file is specified
        if self.log_file:
            # Ensure log directory exists
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            logger.add(
                sink=self.log_file,
                format=self.log_format,
                level=self.log_level,
                rotation=self.log_rotation,
                retention=self.log_retention,
                compression=self.log_compression,
                enqueue=True,  # Async logging
            )

        logger.info(f"Logging configured: level={self.log_level}, file={self.log_file}")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    return settings


# Global settings instance
settings = get_settings()


# ==========================================
# Database Session Management
# ==========================================

# Global engine and session maker
_engine = None
_async_session_maker = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine

        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _engine


def get_session_maker():
    """Get or create async session maker."""
    global _async_session_maker
    if _async_session_maker is None:
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


async def get_db_session():
    """
    FastAPI dependency for database session.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        ```python
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            # Use db session
            pass
        ```
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_engine():
    """Close database engine."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
