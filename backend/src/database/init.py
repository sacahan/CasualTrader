"""
Database initialization utilities for CasualTrader

Handles automatic database table creation on startup.
"""

from sqlalchemy.ext.asyncio import AsyncEngine
from common.logger import logger
from database import Base


async def ensure_tables_exist(engine: AsyncEngine) -> None:
    """
    Ensure all database tables exist.

    Creates missing tables based on the current ORM model definitions.
    Safe to call multiple times.

    Args:
        engine: SQLAlchemy async engine instance
    """
    try:
        logger.debug("Checking database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.debug("✓ Database tables verified/created")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database tables: {e}", exc_info=True)
        raise
