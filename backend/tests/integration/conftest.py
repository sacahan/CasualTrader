"""
Integration Tests Fixtures

整合測試層級的 pytest fixtures
只模擬外部依賴（資料庫、API），不模擬業務邏輯
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
async def test_db_session():
    """Create in-memory SQLite database session for testing"""
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
def mock_mcp_client():
    """Mock MCP client for testing"""
    mock_client = AsyncMock()
    mock_client.call_tool = AsyncMock(return_value={"type": "text", "text": "Mock MCP response"})
    return mock_client


@pytest.fixture
def mock_trading_service(test_db_session):
    """Create TradingService with mocked external dependencies"""
    from src.service.trading_service import TradingService

    service = TradingService(test_db_session)

    # Mock external API calls, not business logic
    service.mcp_client = AsyncMock()
    service.holiday_client = AsyncMock()

    return service
