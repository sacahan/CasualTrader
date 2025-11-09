"""
測試服務間的協作

驗證：
1. 服務之間的依賴注入是否正確
2. 參數類型是否符合預期
3. 服務方法是否能正確調用
"""

import sys
from pathlib import Path

import pytest

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from service.trading_service import TradingService
from service.agents_service import AgentsService


@pytest.mark.asyncio
async def test_trading_service_creates_agents_service(mock_db_session):
    """驗證 TradingService 創建真實的 AgentsService"""
    service = TradingService(mock_db_session)

    assert isinstance(service.agents_service, AgentsService)
    assert service.agents_service.session is mock_db_session


@pytest.mark.asyncio
async def test_trading_agent_receives_agents_service(mock_db_session, mock_agent_config):
    """驗證 TradingAgent 接收到 AgentsService 而不是 AsyncSession"""
    service = TradingService(mock_db_session)

    agent = await service._get_or_create_agent("test-agent", mock_agent_config)

    # 核心驗證 - agent 應該持有 AgentsService，不是 AsyncSession
    assert isinstance(agent.agent_service, AgentsService)
    assert agent.agent_service is service.agents_service
    assert not isinstance(agent.agent_service, type(mock_db_session))


@pytest.mark.asyncio
async def test_get_or_create_agent_caching(mock_db_session, mock_agent_config):
    """驗證 Agent 實例快取機制"""
    service = TradingService(mock_db_session)

    # 第一次調用 - 創建 Agent
    agent1 = await service._get_or_create_agent("test-agent", mock_agent_config)
    assert "test-agent" in service.active_agents

    # 第二次調用 - 返回同一個實例
    agent2 = await service._get_or_create_agent("test-agent", mock_agent_config)
    assert agent1 is agent2


@pytest.mark.asyncio
async def test_type_validation_catches_wrong_service_type(mock_db_session, mock_agent_config):
    """驗證類型檢查捕捉錯誤的服務類型"""
    service = TradingService(mock_db_session)

    # 破壞 agent_service 類型 - 故意傳入錯誤類型
    service.agents_service = mock_db_session

    # 應該拋出 TypeError
    with pytest.raises(TypeError, match="agents_service must be AgentsService"):
        await service._get_or_create_agent("test-agent", mock_agent_config)


@pytest.mark.asyncio
async def test_agent_can_access_service_methods(mock_db_session, mock_agent_config):
    """驗證 Agent 能夠訪問服務方法（不拋出 AttributeError）"""
    service = TradingService(mock_db_session)

    agent = await service._get_or_create_agent("test-agent", mock_agent_config)

    # 驗證 agent 的 agent_service 有正確的方法簽名
    # 不會拋出 AttributeError: 'AsyncSession' object has no attribute 'update_agent_status'
    assert hasattr(agent.agent_service, "update_agent_status")
    assert hasattr(agent.agent_service, "get_agent_config")
    assert callable(agent.agent_service.update_agent_status)
    assert callable(agent.agent_service.get_agent_config)
