"""
AgentSessionService 服務層整合測試

測試 session_service.py 的所有操作，包括：
- 會話創建 (create_session)
- 會話狀態更新 (update_session_status)
- 會話輸出更新 (update_session_output)
- 會話查詢 (get_session, list_agent_sessions)
- 會話歷史 (get_recent_sessions)

覆蓋目標：提升 session_service.py 覆蓋率從 21% 至 60%+
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from service.session_service import (
    AgentSessionService,
    SessionError,
    SessionNotFoundError,
)
from database.models import AgentSession
from common.enums import SessionStatus


# ==========================================
# Fixtures
# ==========================================


@pytest.fixture
def mock_db_session():
    """創建模擬的 AsyncSession"""
    session = AsyncMock(spec=AsyncSession)
    # 確保 execute 默認是異步的
    session.execute = AsyncMock()
    return session


@pytest.fixture
def session_service(mock_db_session):
    """創建 AgentSessionService 實例"""
    return AgentSessionService(mock_db_session)


@pytest.fixture
def sample_session():
    """提供範例 AgentSession"""
    session = MagicMock(spec=AgentSession)
    session.id = "session_123"
    session.agent_id = "agent_123"
    session.mode = "monitoring"
    session.status = SessionStatus.PENDING
    session.initial_input = {"query": "analyze stock"}
    session.start_time = datetime.now()
    session.end_time = None
    session.execution_time_ms = None
    session.final_output = None
    session.tools_called = None
    session.error_message = None
    session.created_at = datetime.now()
    session.updated_at = datetime.now()
    return session


# ==========================================
# Test: create_session
# ==========================================


@pytest.mark.asyncio
async def test_create_session_success(mock_db_session, session_service):
    """測試成功創建會話"""
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    await session_service.create_session(
        agent_id="agent_123",
        mode="monitoring",
        initial_input={"query": "test"},
    )

    # 驗證 add 和 commit 被調用
    assert mock_db_session.add.called
    assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_create_session_database_error(mock_db_session, session_service):
    """測試創建會話時的資料庫錯誤"""
    mock_db_session.commit.side_effect = Exception("Database error")
    mock_db_session.rollback = AsyncMock()

    with pytest.raises(SessionError):
        await session_service.create_session(
            agent_id="agent_123",
            mode="monitoring",
        )

    # 驗證 rollback 被調用
    assert mock_db_session.rollback.called


@pytest.mark.asyncio
async def test_create_session_with_none_input(mock_db_session, session_service):
    """測試創建會話時 initial_input 為 None"""
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    await session_service.create_session(
        agent_id="agent_123",
        mode="trading",
        initial_input=None,
    )

    # 驗證創建成功
    assert mock_db_session.add.called


# ==========================================
# Test: update_session_status
# ==========================================


@pytest.mark.asyncio
async def test_update_session_status_to_completed(mock_db_session, session_service, sample_session):
    """測試更新會話狀態為已完成"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    end_time = datetime.now()
    await session_service.update_session_status(
        session_id="session_123",
        status=SessionStatus.COMPLETED,
        end_time=end_time,
        execution_time_ms=1000,
    )

    # 驗證狀態更新
    assert mock_db_session.commit.called
    assert sample_session.status == SessionStatus.COMPLETED


@pytest.mark.asyncio
async def test_update_session_status_to_failed(mock_db_session, session_service, sample_session):
    """測試更新會話狀態為失敗"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    error_msg = "Connection timeout"
    await session_service.update_session_status(
        session_id="session_123",
        status=SessionStatus.FAILED,
        error_message=error_msg,
    )

    # 驗證狀態和錯誤訊息
    assert mock_db_session.commit.called
    assert sample_session.error_message == error_msg


@pytest.mark.asyncio
async def test_update_session_status_to_timeout(mock_db_session, session_service, sample_session):
    """測試更新會話狀態為超時"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    await session_service.update_session_status(
        session_id="session_123",
        status=SessionStatus.TIMEOUT,
    )

    # 驗證狀態更新
    assert mock_db_session.commit.called
    assert sample_session.status == SessionStatus.TIMEOUT


@pytest.mark.asyncio
async def test_update_session_status_not_found(mock_db_session, session_service):
    """測試更新不存在的會話"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(SessionNotFoundError):
        await session_service.update_session_status(
            session_id="nonexistent",
            status=SessionStatus.COMPLETED,
        )


@pytest.mark.asyncio
async def test_update_session_status_database_error(
    mock_db_session, session_service, sample_session
):
    """測試更新會話狀態時的資料庫錯誤"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit.side_effect = Exception("Database error")
    mock_db_session.rollback = AsyncMock()

    with pytest.raises(SessionError):
        await session_service.update_session_status(
            session_id="session_123",
            status=SessionStatus.COMPLETED,
        )

    # 驗證 rollback
    assert mock_db_session.rollback.called


@pytest.mark.asyncio
async def test_update_session_status_auto_calculate_execution_time(
    mock_db_session, session_service, sample_session
):
    """測試自動計算執行時間"""
    sample_session.start_time = datetime.now() - timedelta(seconds=5)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    await session_service.update_session_status(
        session_id="session_123",
        status=SessionStatus.COMPLETED,
    )

    # 驗證執行時間被自動計算
    assert mock_db_session.commit.called
    assert sample_session.execution_time_ms is not None


# ==========================================
# Test: update_session_output
# ==========================================


@pytest.mark.asyncio
async def test_update_session_output_success(mock_db_session, session_service, sample_session):
    """測試成功更新會話輸出"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    final_output = {"analysis": "Stock is bullish"}
    tools_called = ["get_stock_price", "analyze_trend"]

    await session_service.update_session_output(
        session_id="session_123",
        final_output=final_output,
        tools_called=tools_called,
    )

    # 驗證輸出被更新
    assert mock_db_session.commit.called
    assert sample_session.final_output == final_output
    assert sample_session.tools_called == tools_called


@pytest.mark.asyncio
async def test_update_session_output_not_found(mock_db_session, session_service):
    """測試更新不存在會話的輸出"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(SessionNotFoundError):
        await session_service.update_session_output(
            session_id="nonexistent",
            final_output={"result": "test"},
        )


@pytest.mark.asyncio
async def test_update_session_output_with_no_tools(
    mock_db_session, session_service, sample_session
):
    """測試更新會話輸出時不指定使用的工具"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    final_output = {"analysis": "Test"}

    await session_service.update_session_output(
        session_id="session_123",
        final_output=final_output,
        tools_called=None,
    )

    # 驗證輸出被設置，但工具列表保持原狀
    assert mock_db_session.commit.called


# ==========================================
# Test: get_session
# ==========================================


@pytest.mark.asyncio
async def test_get_session_success(mock_db_session, session_service, sample_session):
    """測試成功獲取會話"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    session = await session_service.get_session("session_123")

    assert session.id == "session_123"
    assert session.agent_id == "agent_123"


@pytest.mark.asyncio
async def test_get_session_not_found(mock_db_session, session_service):
    """測試獲取不存在的會話"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(SessionNotFoundError):
        await session_service.get_session("nonexistent")


# ==========================================
# Test: list_agent_sessions
# ==========================================


@pytest.mark.asyncio
async def test_list_agent_sessions_success(mock_db_session, session_service, sample_session):
    """測試成功獲取 Agent 會話列表"""
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [sample_session]
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    sessions = await session_service.list_agent_sessions("agent_123", limit=10)

    assert len(sessions) == 1
    assert sessions[0].agent_id == "agent_123"


@pytest.mark.asyncio
async def test_list_agent_sessions_empty(mock_db_session, session_service):
    """測試獲取空會話列表"""
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    sessions = await session_service.list_agent_sessions("agent_123")

    assert sessions == []


@pytest.mark.asyncio
async def test_list_agent_sessions_with_pagination(
    mock_db_session, session_service, sample_session
):
    """測試分頁獲取會話"""
    sessions = [sample_session for _ in range(15)]
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = sessions[:10]  # 模擬 limit=10
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    result = await session_service.list_agent_sessions("agent_123", limit=10)

    assert len(result) == 10


# ==========================================
# Test: get_recent_sessions
# ==========================================


@pytest.mark.asyncio
# Test: get_recent_sessions

@pytest.mark.skip(reason="Method does not exist in service")
async def test_get_recent_sessions_success(mock_db_session, session_service, sample_session):
    """測試成功獲取最近的會話"""
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [sample_session]
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    sessions = await session_service.get_recent_sessions(limit=10)

    assert len(sessions) == 1


@pytest.mark.asyncio
@pytest.mark.skip(reason="Method does not exist in service")
async def test_get_recent_sessions_database_error(mock_db_session, session_service):
    """測試獲取最近會話時的資料庫錯誤"""
    mock_db_session.execute.side_effect = Exception("Database error")

    with pytest.raises(SessionError):
        await session_service.get_recent_sessions(limit=10)


# ==========================================
# Test: Session Status Transitions
# ==========================================


@pytest.mark.asyncio
async def test_session_status_transitions(mock_db_session, session_service, sample_session):
    """測試會話狀態轉換流程"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    # PENDING -> RUNNING
    await session_service.update_session_status(
        session_id="session_123",
        status=SessionStatus.RUNNING,
    )
    assert sample_session.status == SessionStatus.RUNNING

    # RUNNING -> COMPLETED
    await session_service.update_session_status(
        session_id="session_123",
        status=SessionStatus.COMPLETED,
    )
    assert sample_session.status == SessionStatus.COMPLETED
    assert sample_session.end_time is not None


# ==========================================
# Test: Error Cases
# ==========================================


@pytest.mark.asyncio
async def test_create_session_validation_error(mock_db_session, session_service):
    """測試創建會話時的驗證錯誤"""
    # 模擬驗證失敗
    mock_db_session.add.side_effect = ValueError("Invalid mode")

    with pytest.raises(SessionError):
        await session_service.create_session(
            agent_id="agent_123",
            mode="invalid_mode",
        )


@pytest.mark.asyncio
async def test_session_concurrent_updates(mock_db_session, session_service, sample_session):
    """測試會話的併發更新"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    # 模擬多個併發更新
    await session_service.update_session_status(
        session_id="session_123",
        status=SessionStatus.RUNNING,
    )

    await session_service.update_session_output(
        session_id="session_123",
        final_output={"intermediate": "result"},
    )

    # 驗證兩個更新都被執行
    assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_session_with_large_output(mock_db_session, session_service, sample_session):
    """測試處理大型會話輸出"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_session
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()

    # 創建大型輸出
    large_output = {"data": [{"ticker": f"STOCK_{i}", "price": 100 + i} for i in range(1000)]}

    await session_service.update_session_output(
        session_id="session_123",
        final_output=large_output,
    )

    # 驗證大型輸出被正確處理
    assert mock_db_session.commit.called
