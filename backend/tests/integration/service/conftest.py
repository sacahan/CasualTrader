"""
服務集成測試 Fixtures

只 Mock 外部依賴（數據庫、API），
測試真實的服務協作
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock 數據庫 session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_agent_config() -> MagicMock:
    """Mock Agent 配置"""
    config = MagicMock()
    config.id = "test-agent"
    config.status = "INACTIVE"
    config.current_mode = "TRADING"
    return config
