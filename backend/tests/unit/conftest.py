"""
Unit Tests Fixtures

單元測試層級的 pytest fixtures
所有外部依賴都應該被模擬（Mock）
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture
def mock_db_session():
    """Mock AsyncSession for database operations"""
    return AsyncMock()


@pytest.fixture
def mock_agent_config():
    """Mock Agent configuration"""
    config = MagicMock()
    config.id = "test-agent"
    config.ai_model = "gpt-4"
    config.description = "Test agent"
    config.mode = "TRADING"
    return config


@pytest.fixture
def mock_trading_agent():
    """Mock TradingAgent instance"""
    agent = AsyncMock()
    agent.agent_id = "test-agent"
    agent.is_initialized = False
    agent.initialize = AsyncMock()
    agent.run = AsyncMock(return_value={"success": True})
    agent.cleanup = AsyncMock()
    return agent
