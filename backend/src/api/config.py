"""
Configuration Management

Load and manage environment variables for the API server.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @staticmethod
    def _strip_wrapping_quotes(value: Any) -> Any:
        """Remove leading and trailing quotes from string values."""
        if isinstance(value, str):
            trimmed = value.strip()
            if len(trimmed) >= 2 and (
                (trimmed.startswith('"') and trimmed.endswith('"'))
                or (trimmed.startswith("'") and trimmed.endswith("'"))
            ):
                return trimmed[1:-1]
            return trimmed
        return value

    @model_validator(mode="before")
    @classmethod
    def sanitize_string_fields(cls, data: Any) -> Any:
        """Normalize string values loaded from environment variables."""
        if isinstance(data, dict):
            return {key: cls._strip_wrapping_quotes(value) for key, value in data.items()}
        return data

    # API Server Settings
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")

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
        default="postgresql+asyncpg://cstrader_user:2Ts9zM2%@sacahan-ubunto:5432/cstrader",
        description="Database connection URL",
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    database_pool_size: int = Field(default=5, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, description="Database max overflow connections")
    database_pool_timeout: int = Field(default=30, description="Database pool timeout (seconds)")
    database_pool_recycle: int = Field(
        default=3600, description="Database pool recycle time (seconds)"
    )

    # Agent Settings
    max_agents: int = Field(default=10, description="Maximum concurrent agent executions")
    default_ai_model: str = Field(default="gpt-5-mini", description="Default AI model")
    default_initial_capital: float = Field(default=1000000.0, description="Default initial capital")
    default_max_turns: int = Field(default=30, description="Default max turns for main agent")
    default_agent_timeout: int = Field(
        default=300,
        description="Default execution timeout for main agent (seconds), applies to all sub-agents",
    )

    # WebSocket Settings
    ws_heartbeat_interval: int = Field(
        default=30, description="WebSocket heartbeat interval (seconds)"
    )
    ws_max_connections: int = Field(default=100, description="Maximum WebSocket connections")

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

    @field_validator("database_url", mode="before")
    @classmethod
    def set_database_url(cls, v: Any) -> str:
        """Validate database URL."""
        if v:  # If explicitly set via env var
            return v
        # Default PostgreSQL connection
        return "postgresql+asyncpg://cstrader_user:2Ts9zM2%@sacahan-ubunto:5432/cstrader"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle empty string
            if not v or v.strip() == "":
                return ["http://localhost:3000", "http://localhost:5173"]

            # Handle JSON-like string format
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback to comma-separated
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if v else ["http://localhost:3000", "http://localhost:5173"]

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
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            # asyncpg-specific optimizations
            connect_args={
                "timeout": 10,  # Connection timeout
                "command_timeout": 10,  # Command timeout
                "max_cached_statement_lifetime": 300,  # Cache statements for 5 minutes
                "max_cacheable_statement_size": 15000,  # Cache statements up to 15KB
                "server_settings": {
                    "application_name": "casualtrader_backend",
                },
            },
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
    session = session_maker()
    try:
        yield session
    except Exception:
        # Only rollback if session is active; close() will handle cleanup automatically
        await session.rollback()
        raise
    finally:
        # close() will handle any pending transaction; explicit rollback not needed
        await session.close()


async def close_db_engine():
    """Close database engine."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
