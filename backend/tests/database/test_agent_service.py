"""
測試 Agent 資料庫服務層

驗證 AgentDatabaseService 的 CRUD 操作和錯誤處理
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.database.agent_service import (
    AgentDatabaseService,
    AgentNotFoundError,
    AgentConfigurationError,
    AgentDatabaseError,
)
from src.database.models import Agent, AgentMode, AgentStatus


# ==========================================
# Fixtures
# ==========================================


@pytest.fixture
def mock_session():
    """創建 mock AsyncSession"""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def sample_agent():
    """創建範例 Agent"""
    return Agent(
        id="test-agent-001",
        name="Test Agent",
        instructions="Test instructions for agent behavior",
        ai_model="gpt-4o-mini",
        initial_funds=1000000.0,
        status=AgentStatus.ACTIVE,
        current_mode=AgentMode.OBSERVATION,
        investment_preferences=json.dumps(
            {
                "enabled_tools": {
                    "fundamental_analysis": True,
                    "technical_analysis": True,
                },
                "risk_tolerance": "moderate",
                "max_single_position": 10.0,
            }
        ),
    )


@pytest.fixture
def agent_service(mock_session):
    """創建 AgentDatabaseService 實例"""
    return AgentDatabaseService(mock_session)


# ==========================================
# Test Query Operations
# ==========================================


@pytest.mark.asyncio
async def test_get_agent_config_success(agent_service, mock_session, sample_agent):
    """
    測試成功載入 Agent 配置

    驗證：
    1. 正確查詢資料庫
    2. 返回正確的 Agent 實例
    3. 驗證配置欄位
    """
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_agent
    mock_session.execute.return_value = mock_result

    # Act
    agent = await agent_service.get_agent_config("test-agent-001")

    # Assert
    assert agent == sample_agent
    assert agent.id == "test-agent-001"
    assert agent.name == "Test Agent"
    assert agent.ai_model == "gpt-4o-mini"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_agent_config_not_found(agent_service, mock_session):
    """
    測試 Agent 不存在的情況

    驗證：
    1. 當 Agent 不存在時拋出 AgentNotFoundError
    2. 錯誤訊息包含 agent_id
    """
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act & Assert
    with pytest.raises(AgentNotFoundError) as exc_info:
        await agent_service.get_agent_config("non-existent-agent")

    assert "non-existent-agent" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_agent_config_invalid_configuration(agent_service, mock_session, sample_agent):
    """
    測試配置驗證失敗

    驗證：
    1. 當必要欄位缺失時拋出 AgentConfigurationError
    2. 驗證各個必要欄位（name, instructions, ai_model）
    """
    # Arrange - 移除必要欄位
    sample_agent.name = None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_agent
    mock_session.execute.return_value = mock_result

    # Act & Assert
    with pytest.raises(AgentConfigurationError) as exc_info:
        await agent_service.get_agent_config("test-agent-001")

    assert "name is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_agent_config_database_error(agent_service, mock_session):
    """
    測試資料庫操作失敗

    驗證：
    1. 當資料庫錯誤時拋出 AgentDatabaseError
    2. 錯誤訊息有意義
    """
    # Arrange
    mock_session.execute.side_effect = SQLAlchemyError("Database connection failed")

    # Act & Assert
    with pytest.raises(AgentDatabaseError) as exc_info:
        await agent_service.get_agent_config("test-agent-001")

    assert "Failed to load agent config" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_active_agents_success(agent_service, mock_session, sample_agent):
    """
    測試取得 ACTIVE 狀態 Agents

    驗證：
    1. 只返回 ACTIVE 狀態的 Agents
    2. 返回列表格式正確
    """
    # Arrange
    agents = [sample_agent]
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = agents
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    result = await agent_service.list_active_agents()

    # Assert
    assert len(result) == 1
    assert result[0].status == AgentStatus.ACTIVE


@pytest.mark.asyncio
async def test_list_agents_by_status(agent_service, mock_session, sample_agent):
    """
    測試按狀態取得 Agents

    驗證：
    1. 正確過濾指定狀態
    2. 支援各種 AgentStatus
    """
    # Arrange
    sample_agent.status = AgentStatus.SUSPENDED
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [sample_agent]
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    # Act
    result = await agent_service.list_agents_by_status(AgentStatus.SUSPENDED)

    # Assert
    assert len(result) == 1
    assert result[0].status == AgentStatus.SUSPENDED


# ==========================================
# Test Update Operations
# ==========================================


@pytest.mark.asyncio
async def test_update_agent_status_success(agent_service, mock_session, sample_agent):
    """
    測試更新 Agent 狀態

    驗證：
    1. 狀態更新成功
    2. 模式可選更新
    3. 正確 commit 變更
    """
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_agent
    mock_session.execute.return_value = mock_result

    # Act
    await agent_service.update_agent_status(
        "test-agent-001", AgentStatus.SUSPENDED, AgentMode.TRADING
    )

    # Assert
    assert sample_agent.status == AgentStatus.SUSPENDED
    assert sample_agent.current_mode == AgentMode.TRADING
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_agent_status_not_found(agent_service, mock_session):
    """
    測試更新不存在的 Agent

    驗證：
    1. 拋出 AgentNotFoundError
    2. 不執行 commit
    """
    # Arrange
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Act & Assert
    with pytest.raises(AgentNotFoundError):
        await agent_service.update_agent_status("non-existent", AgentStatus.SUSPENDED)

    mock_session.commit.assert_not_called()


# ==========================================
# Test Validation and Parsing
# ==========================================


def test_validate_agent_config_success(agent_service, sample_agent):
    """
    測試配置驗證成功

    驗證：
    1. 有效配置不拋出異常
    2. 驗證所有必要欄位
    """
    # Act & Assert - 不應拋出異常
    agent_service._validate_agent_config(sample_agent)


def test_validate_agent_config_missing_fields(agent_service, sample_agent):
    """
    測試缺少必要欄位

    驗證：
    1. name 缺失時拋出錯誤
    2. instructions 缺失時拋出錯誤
    3. ai_model 缺失時拋出錯誤
    """
    # Test missing name
    sample_agent.name = None
    with pytest.raises(AgentConfigurationError, match="name is required"):
        agent_service._validate_agent_config(sample_agent)

    # Test missing instructions
    sample_agent.name = "Test Agent"
    sample_agent.instructions = None
    with pytest.raises(AgentConfigurationError, match="instructions are required"):
        agent_service._validate_agent_config(sample_agent)

    # Test missing ai_model
    sample_agent.instructions = "Test"
    sample_agent.ai_model = None
    with pytest.raises(AgentConfigurationError, match="AI model is required"):
        agent_service._validate_agent_config(sample_agent)


def test_validate_agent_config_invalid_json(agent_service, sample_agent):
    """
    測試無效的 JSON 配置

    驗證：
    1. 當 investment_preferences 不是有效 JSON 時拋出錯誤
    2. 錯誤訊息包含 JSON 解析錯誤資訊
    """
    # Arrange
    sample_agent.investment_preferences = "invalid json {}"

    # Act & Assert
    with pytest.raises(AgentConfigurationError, match="Invalid investment_preferences"):
        agent_service._validate_agent_config(sample_agent)


def test_parse_investment_preferences_success(agent_service, sample_agent):
    """
    測試解析投資偏好成功

    驗證：
    1. 正確解析 JSON 字串
    2. 返回正確的字典結構
    """
    # Act
    preferences = agent_service.parse_investment_preferences(sample_agent)

    # Assert
    assert isinstance(preferences, dict)
    assert "enabled_tools" in preferences
    assert "risk_tolerance" in preferences
    assert preferences["risk_tolerance"] == "moderate"


def test_parse_investment_preferences_empty(agent_service, sample_agent):
    """
    測試空的投資偏好

    驗證：
    1. 當 investment_preferences 為 None 時返回預設值
    2. 預設值包含必要欄位
    """
    # Arrange
    sample_agent.investment_preferences = None

    # Act
    preferences = agent_service.parse_investment_preferences(sample_agent)

    # Assert
    assert isinstance(preferences, dict)
    assert "enabled_tools" in preferences
    assert "risk_tolerance" in preferences
    assert preferences["risk_tolerance"] == "moderate"


def test_parse_investment_preferences_invalid_json(agent_service, sample_agent):
    """
    測試無效 JSON 返回預設值

    驗證：
    1. 當 JSON 解析失敗時返回預設值
    2. 記錄警告日誌（可選）
    """
    # Arrange
    sample_agent.investment_preferences = "not valid json"

    # Act
    preferences = agent_service.parse_investment_preferences(sample_agent)

    # Assert - 應返回預設值
    assert isinstance(preferences, dict)
    assert "enabled_tools" in preferences


def test_get_default_preferences(agent_service):
    """
    測試預設投資偏好

    驗證：
    1. 返回完整的預設配置
    2. 包含所有必要的工具開關
    3. 包含風險參數
    """
    # Act
    defaults = agent_service._get_default_preferences()

    # Assert
    assert "enabled_tools" in defaults
    assert "risk_tolerance" in defaults
    assert "max_single_position" in defaults
    assert "stop_loss_percent" in defaults
    assert "take_profit_percent" in defaults

    # 驗證工具開關
    tools = defaults["enabled_tools"]
    assert tools["fundamental_analysis"] is True
    assert tools["technical_analysis"] is True
    assert tools["risk_assessment"] is True


# ==========================================
# Test Context Manager
# ==========================================


@pytest.mark.asyncio
async def test_context_manager_success(mock_session):
    """
    測試異步上下文管理器正常使用

    驗證：
    1. 正常退出時關閉 session
    2. 不執行 rollback
    """
    # Act
    async with AgentDatabaseService(mock_session):
        pass  # Service 創建成功

    # Assert
    mock_session.close.assert_called_once()
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_context_manager_with_exception(mock_session):
    """
    測試異步上下文管理器異常處理

    驗證：
    1. 發生異常時執行 rollback
    2. 仍然關閉 session
    """
    # Act & Assert
    try:
        async with AgentDatabaseService(mock_session):
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Assert
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()
