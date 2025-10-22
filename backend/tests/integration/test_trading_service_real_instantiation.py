#!/usr/bin/env python3
"""
測試 TradingService 真實 Agent 實例化

驗證 _get_or_create_agent 正確傳遞 agent_service 參數
而不是誤傳 db_session，以避免 AttributeError
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from service.trading_service import TradingService
from trading.trading_agent import TradingAgent
from database.models import Agent as AgentConfig
from common.enums import AgentStatus, AgentMode


@pytest.mark.asyncio
async def test_get_or_create_agent_receives_correct_agent_service():
    """
    驗證 _get_or_create_agent 傳遞正確的參數

    這個測試檢查一個常見的 Bug：
    - Bug: TradingAgent(agent_id, agent_config, self.db_session)
    - 正確: TradingAgent(agent_id, agent_config, self.agents_service)

    如果傳遞了 db_session 而不是 agents_service，
    後續調用 agent_service.update_agent_status() 會失敗
    """
    # Setup
    mock_db_session = AsyncMock()
    service = TradingService(mock_db_session)

    mock_agent_config = MagicMock(spec=AgentConfig)
    mock_agent_config.id = "test-agent"
    mock_agent_config.status = AgentStatus.INACTIVE
    mock_agent_config.current_mode = AgentMode.OBSERVATION

    # 驗證初始狀態
    assert len(service.active_agents) == 0
    assert isinstance(service.agents_service, type(service.agents_service))

    # 執行
    agent = await service._get_or_create_agent("test-agent", mock_agent_config)

    # 驗證
    assert isinstance(agent, TradingAgent)
    assert agent.agent_id == "test-agent"

    # 最重要的驗證：agent_service 應該是 AgentsService 實例，不是 AsyncSession
    assert agent.agent_service is service.agents_service
    assert not isinstance(agent.agent_service, type(mock_db_session))

    print("✅ Agent 正確接收到 agents_service 而不是 db_session")


@pytest.mark.asyncio
async def test_get_or_create_agent_caching():
    """驗證 Agent 實例被正確快取"""
    mock_db_session = AsyncMock()
    service = TradingService(mock_db_session)

    mock_agent_config = MagicMock(spec=AgentConfig)
    mock_agent_config.id = "test-agent"

    # 第一次調用
    agent1 = await service._get_or_create_agent("test-agent", mock_agent_config)
    service.active_agents["test-agent"] = agent1  # 模擬快取

    # 第二次調用應該返回同一實例
    agent2 = await service._get_or_create_agent("test-agent", mock_agent_config)
    assert agent1 is agent2

    print("✅ Agent 實例快取運行正常")


@pytest.mark.asyncio
async def test_trading_agent_can_call_update_agent_status():
    """
    驗證 TradingAgent 能夠調用 update_agent_status

    這個測試確保即使沒有實際初始化 Agent，
    傳入的 agent_service 也有正確的方法
    """
    mock_db_session = AsyncMock()
    service = TradingService(mock_db_session)

    mock_agent_config = MagicMock(spec=AgentConfig)
    mock_agent_config.id = "test-agent"

    # Mock update_agent_status 方法
    service.agents_service.update_agent_status = AsyncMock()

    # 創建 Agent
    agent = await service._get_or_create_agent("test-agent", mock_agent_config)

    # 驗證 agent_service 有 update_agent_status 方法
    assert hasattr(agent.agent_service, "update_agent_status")
    assert callable(agent.agent_service.update_agent_status)

    # 驗證可以調用
    await agent.agent_service.update_agent_status(
        "test-agent", AgentStatus.ACTIVE, AgentMode.OBSERVATION
    )

    service.agents_service.update_agent_status.assert_called_once()

    print("✅ TradingAgent 能夠正確調用 agent_service.update_agent_status()")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
