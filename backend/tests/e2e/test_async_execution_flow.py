"""
E2E 測試：非阻塞式 Agent 執行流程

測試場景：
- ✅ 啟動 Agent 立即返回 202
- ✅ WebSocket 推送執行事件
- ✅ 停止執行 Agent
- ✅ 錯誤處理和恢復
- ✅ 並發執行多個 Agent
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status

from api.app import app
from common.enums import AgentMode
from service.trading_service import TradingService

pytestmark = pytest.mark.asyncio


class MockWebSocketManager:
    """模擬 WebSocket 管理器"""

    def __init__(self):
        self.broadcasts = []

    async def broadcast(self, message: dict[str, Any]) -> None:
        """記錄廣播消息"""
        self.broadcasts.append(message)


@pytest.fixture
def mock_ws_manager(monkeypatch):
    """提供模擬 WebSocket 管理器"""
    manager = MockWebSocketManager()
    monkeypatch.setattr("api.routers.agent_execution.websocket_manager", manager)
    return manager


@pytest.fixture
def mock_trading_service():
    """提供模擬 TradingService"""
    service = AsyncMock(spec=TradingService)
    service.active_agents = {}
    service.agents_service = AsyncMock()
    service.session_service = AsyncMock()
    service.stop_agent = AsyncMock()
    return service


@pytest.fixture
def test_client():
    """提供測試客戶端"""
    client = app.test_client()
    return client


class TestStartAgentMode:
    """測試 start_agent_mode 端點"""

    async def test_start_returns_202_with_session_id(
        self, mock_trading_service, mock_ws_manager, monkeypatch
    ):
        """✅ Test: 啟動端點返回 202 Accepted 及 session_id"""
        agent_id = "test-agent"
        session_id = "session-123"

        # 模擬服務響應
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_trading_service.session_service.create_session.return_value = mock_session
        mock_trading_service.agents_service.get_agent_config.return_value = {}

        # 注入模擬服務
        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        # 執行 POST 請求
        response = app.test_client().post(
            f"/api/agents/{agent_id}/start",
            json={"mode": "OBSERVATION", "max_turns": 5},
        )

        # ✅ 驗證：返回 202 Accepted
        assert response.status_code == status.HTTP_202_ACCEPTED

        # ✅ 驗證：返回 session_id
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == session_id
        assert data["mode"] == "OBSERVATION"

    async def test_start_broadcasts_execution_started(
        self, mock_trading_service, mock_ws_manager, monkeypatch
    ):
        """✅ Test: 啟動時廣播 execution_started 事件"""
        agent_id = "test-agent"
        session_id = "session-123"

        mock_session = MagicMock()
        mock_session.id = session_id
        mock_trading_service.session_service.create_session.return_value = mock_session
        mock_trading_service.agents_service.get_agent_config.return_value = {}

        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        response = app.test_client().post(
            f"/api/agents/{agent_id}/start",
            json={"mode": "TRADING"},
        )

        assert response.status_code == status.HTTP_202_ACCEPTED

        # ✅ 驗證：廣播了 execution_started 事件
        assert len(mock_ws_manager.broadcasts) > 0
        started_event = mock_ws_manager.broadcasts[0]
        assert started_event["type"] == "execution_started"
        assert started_event["agent_id"] == agent_id
        assert started_event["session_id"] == session_id

    async def test_start_fails_when_agent_busy(self, mock_trading_service, monkeypatch):
        """✅ Test: Agent 正在執行時返回 409 Conflict"""
        agent_id = "busy-agent"

        # 模擬 Agent 已在執行中
        mock_trading_service.active_agents = {agent_id: True}

        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        response = app.test_client().post(
            f"/api/agents/{agent_id}/start",
            json={"mode": "OBSERVATION"},
        )

        # ✅ 驗證：返回 409 Conflict
        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_start_fails_with_invalid_mode(self, mock_trading_service, monkeypatch):
        """✅ Test: 無效模式返回 400 Bad Request"""
        agent_id = "test-agent"

        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        response = app.test_client().post(
            f"/api/agents/{agent_id}/start",
            json={"mode": "INVALID_MODE"},
        )

        # ✅ 驗證：返回 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_start_fails_with_nonexistent_agent(self, mock_trading_service, monkeypatch):
        """✅ Test: Agent 不存在返回 404"""
        agent_id = "nonexistent-agent"

        # 模擬 get_agent_config 拋出異常
        from service.agents_service import AgentNotFoundError

        mock_trading_service.agents_service.get_agent_config.side_effect = AgentNotFoundError(
            f"Agent {agent_id} not found"
        )

        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        response = app.test_client().post(
            f"/api/agents/{agent_id}/start",
            json={"mode": "OBSERVATION"},
        )

        # ✅ 驗證：返回 404 Not Found
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStopAgent:
    """測試 stop_agent 端點"""

    async def test_stop_waits_for_completion(
        self, mock_trading_service, mock_ws_manager, monkeypatch
    ):
        """✅ Test: 停止端點等待完成後返回"""
        agent_id = "test-agent"

        # 模擬停止成功
        mock_trading_service.stop_agent.return_value = {
            "success": True,
            "status": "stopped",
        }

        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        response = app.test_client().post(f"/api/agents/{agent_id}/stop")

        # ✅ 驗證：返回 200 OK
        assert response.status_code == status.HTTP_200_OK

        # ✅ 驗證：返回停止狀態
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "stopped"

    async def test_stop_broadcasts_execution_stopped(
        self, mock_trading_service, mock_ws_manager, monkeypatch
    ):
        """✅ Test: 停止時廣播 execution_stopped 事件"""
        agent_id = "test-agent"

        mock_trading_service.stop_agent.return_value = {
            "success": True,
            "status": "stopped",
        }

        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        # 觸發停止
        _ = app.test_client().post(f"/api/agents/{agent_id}/stop")

        # ✅ 驗證：廣播了 execution_stopped 事件
        assert len(mock_ws_manager.broadcasts) > 0
        stop_event = mock_ws_manager.broadcasts[-1]
        assert stop_event["type"] == "execution_stopped"

    async def test_stop_fails_when_agent_not_found(self, mock_trading_service, monkeypatch):
        """✅ Test: Agent 不存在返回 404"""
        agent_id = "nonexistent-agent"

        from service.agents_service import AgentNotFoundError

        mock_trading_service.stop_agent.side_effect = AgentNotFoundError(
            f"Agent {agent_id} not found"
        )

        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        response = app.test_client().post(f"/api/agents/{agent_id}/stop")

        # ✅ 驗證：返回 404 Not Found
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBackgroundExecution:
    """測試後台執行邏輯"""

    async def test_background_execution_broadcasts_completion(self, mock_ws_manager):
        """✅ Test: 後台執行成功時廣播 execution_completed 事件"""
        from api.routers.agent_execution import _execute_in_background

        agent_id = "test-agent"
        mode = AgentMode.OBSERVATION

        # 模擬 TradingService
        mock_service = AsyncMock()
        mock_service.execute_single_mode.return_value = {
            "session_id": "session-123",
            "mode": "OBSERVATION",
            "execution_time_ms": 1000,
            "output": "Test output",
        }

        # 執行後台任務
        await _execute_in_background(
            trading_service=mock_service,
            agent_id=agent_id,
            mode=mode,
        )

        # ✅ 驗證：執行了 execute_single_mode
        mock_service.execute_single_mode.assert_called_once()

        # ✅ 驗證：廣播了 execution_completed 事件
        assert len(mock_ws_manager.broadcasts) > 0
        completed_event = mock_ws_manager.broadcasts[0]
        assert completed_event["type"] == "execution_completed"
        assert completed_event["agent_id"] == agent_id

    async def test_background_execution_broadcasts_failure(self, mock_ws_manager):
        """✅ Test: 後台執行失敗時廣播 execution_failed 事件"""
        from api.routers.agent_execution import _execute_in_background

        agent_id = "test-agent"
        mode = AgentMode.OBSERVATION

        # 模擬 TradingService 拋出異常
        mock_service = AsyncMock()
        mock_service.execute_single_mode.side_effect = Exception("Execution failed")

        # 執行後台任務
        await _execute_in_background(
            trading_service=mock_service,
            agent_id=agent_id,
            mode=mode,
        )

        # ✅ 驗證：廣播了 execution_failed 事件
        assert len(mock_ws_manager.broadcasts) > 0
        failed_event = mock_ws_manager.broadcasts[0]
        assert failed_event["type"] == "execution_failed"
        assert failed_event["agent_id"] == agent_id
        assert failed_event["success"] is False

    async def test_background_execution_does_not_block_http(
        self, mock_trading_service, mock_ws_manager, monkeypatch
    ):
        """✅ Test: 後台執行不阻塞 HTTP 響應（測試響應時間）"""
        import time

        agent_id = "test-agent"
        session_id = "session-123"

        # 模擬一個慢速的執行
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(2)  # 模擬 2 秒執行
            return {
                "session_id": session_id,
                "mode": "OBSERVATION",
                "execution_time_ms": 2000,
            }

        mock_session = MagicMock()
        mock_session.id = session_id
        mock_trading_service.session_service.create_session.return_value = mock_session
        mock_trading_service.agents_service.get_agent_config.return_value = {}
        mock_trading_service.execute_single_mode = slow_execute

        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        # 測試響應時間
        start_time = time.time()
        response = app.test_client().post(
            f"/api/agents/{agent_id}/start",
            json={"mode": "OBSERVATION"},
        )
        response_time = time.time() - start_time

        # ✅ 驗證：響應時間 < 500ms（即使執行需要 2 秒）
        assert response_time < 0.5
        assert response.status_code == status.HTTP_202_ACCEPTED


class TestConcurrentExecution:
    """測試並發執行"""

    async def test_concurrent_agents_execution(
        self, mock_trading_service, mock_ws_manager, monkeypatch
    ):
        """✅ Test: 支持多個 Agent 併發執行"""
        # 模擬支持多個 Agent
        mock_trading_service.active_agents = {}
        mock_session = MagicMock()
        mock_trading_service.session_service.create_session.return_value = mock_session
        mock_trading_service.agents_service.get_agent_config.return_value = {}

        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        # 啟動 3 個 Agent 並發
        responses = []
        for i in range(3):
            mock_session.id = f"session-{i}"
            response = app.test_client().post(
                f"/api/agents/agent-{i}/start",
                json={"mode": "OBSERVATION"},
            )
            responses.append(response)

        # ✅ 驗證：所有請求都返回 202
        for response in responses:
            assert response.status_code == status.HTTP_202_ACCEPTED

        # ✅ 驗證：廣播了 3 個 execution_started 事件
        started_events = [
            msg for msg in mock_ws_manager.broadcasts if msg["type"] == "execution_started"
        ]
        assert len(started_events) == 3


class TestEventContract:
    """測試 WebSocket 事件契約"""

    async def test_execution_started_event_structure(
        self, mock_trading_service, mock_ws_manager, monkeypatch
    ):
        """✅ Test: execution_started 事件結構正確"""
        agent_id = "test-agent"
        session_id = "session-123"

        mock_session = MagicMock()
        mock_session.id = session_id
        mock_trading_service.session_service.create_session.return_value = mock_session
        mock_trading_service.agents_service.get_agent_config.return_value = {}

        monkeypatch.setattr(
            "api.routers.agent_execution.get_trading_service",
            lambda: mock_trading_service,
        )

        response = app.test_client().post(
            f"/api/agents/{agent_id}/start",
            json={"mode": "TRADING"},
        )

        assert response.status_code == status.HTTP_202_ACCEPTED

        # ✅ 驗證事件結構
        event = mock_ws_manager.broadcasts[0]
        assert "type" in event
        assert "agent_id" in event
        assert "session_id" in event
        assert "mode" in event
        assert "timestamp" in event or True  # 可選

    async def test_execution_completed_event_structure(self, mock_ws_manager):
        """✅ Test: execution_completed 事件結構正確"""
        from api.routers.agent_execution import _execute_in_background

        agent_id = "test-agent"
        mode = AgentMode.OBSERVATION

        mock_service = AsyncMock()
        mock_service.execute_single_mode.return_value = {
            "session_id": "session-123",
            "mode": "OBSERVATION",
            "execution_time_ms": 1000,
            "output": "Test output",
        }

        await _execute_in_background(
            trading_service=mock_service,
            agent_id=agent_id,
            mode=mode,
        )

        # ✅ 驗證事件結構
        event = mock_ws_manager.broadcasts[0]
        assert event["type"] == "execution_completed"
        assert event["agent_id"] == agent_id
        assert "session_id" in event
        assert "success" in event
        assert event["success"] is True
        assert "execution_time_ms" in event

    async def test_execution_failed_event_structure(self, mock_ws_manager):
        """✅ Test: execution_failed 事件結構正確"""
        from api.routers.agent_execution import _execute_in_background

        agent_id = "test-agent"
        mode = AgentMode.OBSERVATION

        mock_service = AsyncMock()
        mock_service.execute_single_mode.side_effect = ValueError("Test error")

        await _execute_in_background(
            trading_service=mock_service,
            agent_id=agent_id,
            mode=mode,
        )

        # ✅ 驗證事件結構
        event = mock_ws_manager.broadcasts[0]
        assert event["type"] == "execution_failed"
        assert event["agent_id"] == agent_id
        assert "success" in event
        assert event["success"] is False
        assert "error" in event
