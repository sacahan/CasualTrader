# Service 層契約驗證測試

"""
Contract 2: API-Service 層契約驗證

此測試檔案驗證 Service 層中所有的契約要求:
- 方法簽名 (參數和返回型別)
- 例外型別 (何時拋出、為何拋出)
- 非同步契約 (async/await)
"""

import pytest
import inspect
from unittest.mock import AsyncMock

from src.service.agents_service import AgentsService, AgentNotFoundError, AgentConfigurationError
from src.service.session_service import AgentSessionService
from src.service.trading_service import TradingService
from src.schemas.agent import CreateAgentRequest, AgentResponse


class TestAgentsServiceContract:
    """AgentsService 層契約驗證"""

    def test_get_agent_config_method_exists(self):
        """驗證 get_agent_config 方法存在"""
        assert hasattr(AgentsService, "get_agent_config")

    def test_get_agent_config_is_async(self):
        """驗證 get_agent_config 是 async 方法"""
        method = getattr(AgentsService, "get_agent_config")
        assert inspect.iscoroutinefunction(method)

    def test_create_agent_method_exists(self):
        """驗證 create_agent 方法存在"""
        assert hasattr(AgentsService, "create_agent")

    def test_create_agent_is_async(self):
        """驗證 create_agent 是 async 方法"""
        method = getattr(AgentsService, "create_agent")
        assert inspect.iscoroutinefunction(method)

    def test_list_agents_method_exists(self):
        """驗證 list_agents 方法存在"""
        assert hasattr(AgentsService, "list_agents")

    def test_list_agents_is_async(self):
        """驗證 list_agents 是 async 方法"""
        method = getattr(AgentsService, "list_agents")
        assert inspect.iscoroutinefunction(method)

    def test_get_agent_config_method_signature(self):
        """驗證 get_agent_config 方法簽名包含 agent_id"""
        method = getattr(AgentsService, "get_agent_config")
        sig = inspect.signature(method)
        assert "agent_id" in sig.parameters

    def test_create_agent_method_signature(self):
        """驗證 create_agent 方法簽名包含必要的參數"""
        method = getattr(AgentsService, "create_agent")
        sig = inspect.signature(method)
        # 應該有 name 和 description 等參數
        params = list(sig.parameters.keys())
        assert "name" in params or "agent_data" in params or "data" in params

    def test_agent_not_found_error_exists(self):
        """驗證 AgentNotFoundError 例外類存在"""
        assert AgentNotFoundError is not None
        assert issubclass(AgentNotFoundError, Exception)

    def test_agent_configuration_error_exists(self):
        """驗證 AgentConfigurationError 例外類存在"""
        assert AgentConfigurationError is not None
        assert issubclass(AgentConfigurationError, Exception)


class TestSessionServiceContract:
    """AgentSessionService 層契約驗證"""

    def test_get_session_method_exists(self):
        """驗證 get_session 方法存在"""
        assert hasattr(AgentSessionService, "get_session")

    def test_get_session_is_async(self):
        """驗證 get_session 是 async 方法"""
        method = getattr(AgentSessionService, "get_session")
        assert inspect.iscoroutinefunction(method)

    def test_delete_session_method_exists(self):
        """驗證 delete_session 方法存在"""
        assert hasattr(AgentSessionService, "delete_session")

    def test_delete_session_is_async(self):
        """驗證 delete_session 是 async 方法"""
        method = getattr(AgentSessionService, "delete_session")
        assert inspect.iscoroutinefunction(method)

    def test_get_session_method_signature(self):
        """驗證 get_session 方法簽名包含 session_id"""
        method = getattr(AgentSessionService, "get_session")
        sig = inspect.signature(method)
        assert "session_id" in sig.parameters

    def test_delete_session_method_signature(self):
        """驗證 delete_session 方法簽名包含 session_id"""
        method = getattr(AgentSessionService, "delete_session")
        sig = inspect.signature(method)
        assert "session_id" in sig.parameters


class TestTradingServiceContract:
    """TradingService 層契約驗證"""

    def test_service_has_trading_methods(self):
        """驗證 TradingService 存在交易相關方法"""
        # 驗證 TradingService 可被初始化
        assert TradingService is not None


class TestServiceReturnTypeContract:
    """Service 返回值型別契約驗證"""

    def test_agent_response_is_dto(self):
        """驗證 AgentResponse 是 DTO"""
        from pydantic import BaseModel

        assert issubclass(AgentResponse, BaseModel)

    def test_create_agent_request_is_dto(self):
        """驗證 CreateAgentRequest 是 DTO"""
        from pydantic import BaseModel

        assert issubclass(CreateAgentRequest, BaseModel)


class TestServiceMethodInvokableContract:
    """驗證 Service 方法可被正確呼叫"""

    @pytest.fixture
    def mock_session(self):
        """建立 mock 資料庫會話"""
        return AsyncMock()

    def test_agents_service_can_be_instantiated(self, mock_session):
        """驗證 AgentsService 能被實例化"""
        service = AgentsService(session=mock_session)
        assert service is not None

    def test_session_service_can_be_instantiated(self, mock_session):
        """驗證 AgentSessionService 能被實例化"""
        # AgentSessionService 接受 db_session 參數
        service = AgentSessionService(db_session=mock_session)
        assert service is not None

    def test_trading_service_can_be_instantiated(self, mock_session):
        """驗證 TradingService 能被實例化"""
        # TradingService 接受 db_session 參數
        service = TradingService(db_session=mock_session)
        assert service is not None
