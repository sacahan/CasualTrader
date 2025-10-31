"""
E2E Tests Fixtures

端到端測試層級的 pytest fixtures
只模擬外部服務（資料庫、API）以確保速度和可靠性，不模擬業務邏輯
"""

import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture
async def e2e_db_session():
    """Create in-memory SQLite database session for E2E testing"""
    from src.database.models import Base

    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def e2e_trading_service(e2e_db_session):
    """Create TradingService for E2E testing with only external deps mocked"""
    from src.service.trading_service import TradingService

    service = TradingService(e2e_db_session)

    # Mock only external services, not business logic
    service.mcp_client = AsyncMock()
    service.holiday_client = AsyncMock()

    return service


@pytest.fixture
def mock_api_response():
    """Common mock responses for API calls"""
    return {
        "success": True,
        "data": {"agent_id": "test-agent", "mode": "TRADING", "result": {}},
    }
