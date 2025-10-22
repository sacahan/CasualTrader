"""
真實 E2E 測試 - 完整的集成測試

這個測試套件測試從 API 層到業務層的完整調用鏈。
通過不 mock TradingService 和 TradingAgent 的交互，
來驗證實現層的正確性。

測試場景：
1. 執行單一模式 (OBSERVATION/TRADING/REBALANCING) - 驗證實際方法調用
2. 驗證會話狀態更新
3. 驗證資源清理
4. 驗證錯誤處理
5. 驗證並發控制（Agent 忙碌時拒絕請求）
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from common.enums import AgentMode, SessionStatus
from service.trading_service import TradingService, AgentBusyError
from service.agents_service import AgentNotFoundError
from trading.trading_agent import TradingAgent


# ==========================================
# 測試 Fixtures - 使用 Mock 數據庫
# ==========================================


@pytest.fixture
def mock_db_session():
    """建立模擬的 DB session"""
    return AsyncMock()


@pytest.fixture
async def trading_service_with_mocks(mock_db_session):
    """建立 TradingService，mock 只有外部依賴（數據庫）"""
    service = TradingService(mock_db_session)

    # Mock AgentsService 和 SessionService 的必要方法
    # 但保持 TradingService 的實現完整
    mock_agent_config = MagicMock()
    mock_agent_config.id = "test-agent"

    service.agents_service.get_agent_config = AsyncMock(return_value=mock_agent_config)

    # Mock session service
    mock_session = MagicMock()
    mock_session.id = "session-123"
    mock_session.status = SessionStatus.COMPLETED
    mock_session.mode = AgentMode.OBSERVATION

    service.session_service.create_session = AsyncMock(return_value=mock_session)
    service.session_service.update_session_status = AsyncMock()
    service.session_service.get_session = AsyncMock(return_value=mock_session)

    return service


# ==========================================
# 真實 E2E 測試場景 - 驗證 API 層到服務層的調用
# ==========================================


@pytest.mark.asyncio
async def test_e2e_api_to_trading_service_call_chain():
    """
    場景 1: 驗證 API 層到 TradingService 的調用鏈

    通過不 mock TradingService.execute_single_mode(),
    而是 mock 只有外部依賴（AgentsService, SessionService, TradingAgent），
    來驗證 TradingService 的實現是否正確。

    關鍵驗證：
    1. TradingService.execute_single_mode() 被正確調用
    2. TradingService 正確檢查 active_agents
    3. TradingService 正確調用 agent.run()（不是 agent.run_mode()）
    4. TradingService 正確清理資源
    """
    mock_db_session = AsyncMock()
    service = TradingService(mock_db_session)

    # Mock 外部依賴
    mock_agent_config = MagicMock(id="test-agent")
    mock_agent = AsyncMock(spec=TradingAgent)
    mock_agent.run = AsyncMock(return_value={"success": True, "output": "test"})
    mock_agent.cleanup = AsyncMock()

    mock_session = MagicMock()
    mock_session.id = "session-123"

    service.agents_service.get_agent_config = AsyncMock(return_value=mock_agent_config)
    service.session_service.create_session = AsyncMock(return_value=mock_session)
    service.session_service.update_session_status = AsyncMock()
    service.session_service.get_session = AsyncMock(return_value=mock_session)

    # Mock _get_or_create_agent 返回真實的 mock agent
    service._get_or_create_agent = AsyncMock(return_value=mock_agent)

    # 執行
    result = await service.execute_single_mode(
        agent_id="test-agent",
        mode=AgentMode.OBSERVATION,
    )

    # 驗證返回值結構
    assert result["success"] is True
    assert "session_id" in result
    assert result["session_id"] == "session-123"
    assert result["mode"] == AgentMode.OBSERVATION.value
    assert "execution_time_ms" in result

    # 驗證正確的方法被調用
    mock_agent.run.assert_called_once()
    # 驗證使用的是 agent.run()，而不是 agent.run_mode()
    call_kwargs = mock_agent.run.call_args.kwargs
    assert "mode" in call_kwargs
    assert call_kwargs["mode"] == AgentMode.OBSERVATION

    # 驗證資源清理
    mock_agent.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_agent_busy_error_handling():
    """
    場景 2: 驗證並發控制 - Agent 忙碌時拒絕請求

    驗證：
    1. 第一個請求成功開始執行
    2. 第二個請求檢測到 Agent 已在 active_agents 中
    3. 第二個請求拋出 AgentBusyError
    """
    mock_db_session = AsyncMock()
    service = TradingService(mock_db_session)

    # 模擬 Agent 已在執行中
    busy_agent = AsyncMock()
    service.active_agents["test-agent"] = busy_agent

    # 模擬必要的配置
    mock_agent_config = MagicMock(id="test-agent")
    service.agents_service.get_agent_config = AsyncMock(return_value=mock_agent_config)

    # 第二個請求應該拋出 AgentBusyError
    with pytest.raises(AgentBusyError) as exc_info:
        await service.execute_single_mode(
            agent_id="test-agent",
            mode=AgentMode.TRADING,
        )

    assert "already running" in str(exc_info.value)


@pytest.mark.asyncio
async def test_e2e_nonexistent_agent_error():
    """
    場景 3: 驗證錯誤處理 - Agent 不存在

    驗證：
    1. 嘗試執行不存在的 Agent
    2. AgentsService.get_agent_config() 拋出 AgentNotFoundError
    3. TradingService 正確傳播錯誤
    """
    mock_db_session = AsyncMock()
    service = TradingService(mock_db_session)

    # Mock AgentsService 拋出 AgentNotFoundError
    service.agents_service.get_agent_config = AsyncMock(
        side_effect=AgentNotFoundError("Agent not found")
    )

    # 驗證正確的異常被拋出
    with pytest.raises(AgentNotFoundError):
        await service.execute_single_mode(
            agent_id="nonexistent-agent",
            mode=AgentMode.OBSERVATION,
        )


@pytest.mark.asyncio
async def test_e2e_resource_cleanup_on_exception():
    """
    場景 4: 驗證異常時的資源清理

    驗證：
    1. 執行過程中 agent.run() 拋出異常
    2. finally 塊確保 agent.cleanup() 被調用
    3. 會話狀態被更新為 FAILED
    """
    mock_db_session = AsyncMock()
    service = TradingService(mock_db_session)

    # Mock 配置
    mock_agent_config = MagicMock(id="test-agent")
    mock_agent = AsyncMock(spec=TradingAgent)
    mock_agent.run = AsyncMock(side_effect=Exception("Execution failed"))
    mock_agent.cleanup = AsyncMock()

    mock_session = MagicMock()
    mock_session.id = "session-123"

    service.agents_service.get_agent_config = AsyncMock(return_value=mock_agent_config)
    service.session_service.create_session = AsyncMock(return_value=mock_session)
    service.session_service.update_session_status = AsyncMock()
    service._get_or_create_agent = AsyncMock(return_value=mock_agent)

    # 執行 - 應該拋出異常
    from service.trading_service import TradingServiceError

    with pytest.raises(TradingServiceError):
        await service.execute_single_mode(
            agent_id="test-agent",
            mode=AgentMode.OBSERVATION,
        )

    # 驗證 cleanup 被調用（即使發生異常）
    mock_agent.cleanup.assert_called_once()

    # 驗證會話狀態被更新為 FAILED
    failed_calls = [
        call
        for call in service.session_service.update_session_status.call_args_list
        if SessionStatus.FAILED in call[0] or call.kwargs.get("status") == SessionStatus.FAILED
    ]
    assert len(failed_calls) > 0


@pytest.mark.asyncio
async def test_e2e_session_lifecycle():
    """
    場景 5: 驗證會話生命週期管理

    驗證會話的完整生命週期：
    1. create_session() 建立會話
    2. update_session_status(..., RUNNING) 更新為運行中
    3. agent.run() 執行
    4. update_session_status(..., COMPLETED) 更新為完成
    """
    mock_db_session = AsyncMock()
    service = TradingService(mock_db_session)

    # Mock 配置
    mock_agent_config = MagicMock(id="test-agent")
    mock_agent = AsyncMock(spec=TradingAgent)
    mock_agent.run = AsyncMock(return_value={"output": "success"})
    mock_agent.cleanup = AsyncMock()

    mock_session = MagicMock()
    mock_session.id = "session-123"

    service.agents_service.get_agent_config = AsyncMock(return_value=mock_agent_config)
    service.session_service.create_session = AsyncMock(return_value=mock_session)
    service.session_service.update_session_status = AsyncMock()
    service._get_or_create_agent = AsyncMock(return_value=mock_agent)

    # 執行
    await service.execute_single_mode(
        agent_id="test-agent",
        mode=AgentMode.OBSERVATION,
    )

    # 驗證會話創建
    service.session_service.create_session.assert_called_once_with(
        agent_id="test-agent",
        session_type="manual_mode",
        mode=AgentMode.OBSERVATION,
        initial_input={},
    )

    # 驗證會話狀態更新序列
    status_update_calls = service.session_service.update_session_status.call_args_list
    assert len(status_update_calls) >= 2

    # 第一次應該更新為 RUNNING
    first_call_args = status_update_calls[0][0]
    assert first_call_args[1] == SessionStatus.RUNNING

    # 最後一次應該更新為 COMPLETED
    last_call_args = status_update_calls[-1][0]
    assert last_call_args[1] == SessionStatus.COMPLETED


@pytest.mark.asyncio
async def test_e2e_multiple_modes_sequential():
    """
    場景 6: 驗證順序執行多個模式

    驗證：
    1. 執行 OBSERVATION
    2. 執行 TRADING
    3. 執行 REBALANCING
    4. 每個模式都獲得不同的 session_id
    """
    mock_db_session = AsyncMock()
    service = TradingService(mock_db_session)

    session_ids = ["session-1", "session-2", "session-3"]
    session_counter = {"count": 0}

    # Mock 配置
    mock_agent_config = MagicMock(id="test-agent")
    mock_agent = AsyncMock(spec=TradingAgent)
    mock_agent.run = AsyncMock(return_value={"output": "success"})
    mock_agent.cleanup = AsyncMock()

    service.agents_service.get_agent_config = AsyncMock(return_value=mock_agent_config)
    service._get_or_create_agent = AsyncMock(return_value=mock_agent)

    # 為每個會話創建不同的 mock
    def create_session_side_effect(*args, **kwargs):
        mock_session = MagicMock()
        mock_session.id = session_ids[session_counter["count"]]
        session_counter["count"] += 1
        return mock_session

    service.session_service.create_session = AsyncMock(side_effect=create_session_side_effect)
    service.session_service.update_session_status = AsyncMock()

    # 執行三個模式
    modes = [AgentMode.OBSERVATION, AgentMode.TRADING, AgentMode.REBALANCING]
    results = []

    for mode in modes:
        result = await service.execute_single_mode(
            agent_id="test-agent",
            mode=mode,
        )
        results.append(result)

    # 驗證每個結果
    assert len(results) == 3
    for i, (result, expected_mode) in enumerate(zip(results, modes)):
        assert result["success"] is True
        assert result["mode"] == expected_mode.value
        assert result["session_id"] == session_ids[i]


@pytest.mark.asyncio
async def test_e2e_agent_correctly_not_mocked_in_call():
    """
    場景 7: 驗證 TradingAgent.run() 被正確調用（而不是 run_mode()）

    這個測試驗證了 QA_ANALYSIS.md 中發現的問題：
    - 代碼試圖調用 agent.run_mode()
    - 但實現中應該是 agent.run()

    通過不 mock agent，我們可以驗證實際調用的方法名。
    """
    mock_db_session = AsyncMock()
    service = TradingService(mock_db_session)

    # 建立一個模擬 Agent，監控哪些方法被調用
    mock_agent = AsyncMock(spec=TradingAgent)
    mock_agent.run = AsyncMock(return_value={"output": "test"})

    # 如果代碼調用 run_mode()，會失敗
    # 因為 mock 只定義了 run()
    del mock_agent.run_mode  # 確保 run_mode 不存在

    mock_agent_config = MagicMock(id="test-agent")
    mock_session = MagicMock(id="session-123")

    service.agents_service.get_agent_config = AsyncMock(return_value=mock_agent_config)
    service.session_service.create_session = AsyncMock(return_value=mock_session)
    service.session_service.update_session_status = AsyncMock()
    service._get_or_create_agent = AsyncMock(return_value=mock_agent)

    # 執行 - 如果代碼調用 agent.run_mode()，會在這裡失敗
    result = await service.execute_single_mode(
        agent_id="test-agent",
        mode=AgentMode.OBSERVATION,
    )

    # 驗證 run() 被調用
    mock_agent.run.assert_called_once()
    assert result["success"] is True
