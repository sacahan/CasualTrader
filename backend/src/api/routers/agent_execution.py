"""
Agent Execution API Router

使用 TradingService 提供 Agent 執行和管理的 RESTful API。
這是基於新架構的 API 端點，使用 OpenAI Agents SDK。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..service.agents_service import AgentNotFoundError
from ..common.enums import AgentMode, SessionStatus
from ..service.session_service import SessionError
from ..service.trading_service import (
    AgentBusyError,
    TradingService,
    TradingServiceError,
)
from ..api.config import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


# ==========================================
# Request Models
# ==========================================


class ExecuteTaskRequest(BaseModel):
    """執行任務請求"""

    task: str = Field(..., min_length=1, max_length=2000, description="任務描述")
    mode: str | None = Field(None, description="執行模式 (TRADING/OBSERVATION/REBALANCING)")
    context: dict[str, Any] | None = Field(None, description="額外上下文")
    max_turns: int | None = Field(None, ge=1, le=50, description="最大輪數")


class StartAgentRequest(BaseModel):
    """啟動 Agent 請求"""

    mode: str | None = Field(None, description="執行模式")


# ==========================================
# Response Models
# ==========================================


class ExecuteTaskResponse(BaseModel):
    """執行任務響應"""

    success: bool
    session_id: str
    output: str
    trace_id: str
    execution_time_ms: int
    error: str | None = None


class AgentStatusResponse(BaseModel):
    """Agent 狀態響應"""

    agent_id: str
    name: str
    status: str
    mode: str
    is_initialized: bool
    is_running: bool
    current_session_id: str | None
    last_active_at: str | None


class StartStopResponse(BaseModel):
    """啟動/停止響應"""

    success: bool
    agent_id: str
    status: str
    mode: str | None = None


class SessionInfo(BaseModel):
    """會話資訊"""

    session_id: str
    session_type: str
    mode: str
    status: str
    start_time: str
    end_time: str | None
    execution_time_ms: int | None
    error_message: str | None


class ExecutionHistoryResponse(BaseModel):
    """執行歷史響應"""

    agent_id: str
    total_sessions: int
    returned_sessions: int
    sessions: list[SessionInfo]


class SessionDetailsResponse(BaseModel):
    """會話詳情響應"""

    session_id: str
    agent_id: str
    session_type: str
    mode: str
    status: str
    start_time: str
    end_time: str | None
    execution_time_ms: int | None
    initial_input: dict[str, Any]
    final_output: dict[str, Any] | None
    tools_called: str | None
    error_message: str | None
    trace_data: dict[str, Any] | None


class SessionStatistics(BaseModel):
    """會話統計資訊"""

    total_sessions: int
    completed_sessions: int
    failed_sessions: int
    running_sessions: int
    avg_execution_time_ms: float | None
    success_rate: float


class AgentStatisticsResponse(BaseModel):
    """Agent 統計響應"""

    agent_id: str
    statistics: SessionStatistics


# ==========================================
# Helper Functions
# ==========================================


def get_trading_service(db_session: AsyncSession = Depends(get_db_session)) -> TradingService:
    """
    獲取 TradingService 實例

    Args:
        db_session: SQLAlchemy 異步 session

    Returns:
        TradingService 實例
    """
    return TradingService(db_session)


def parse_agent_mode(mode_str: str | None) -> AgentMode | None:
    """
    解析模式字串為 AgentMode enum

    Args:
        mode_str: 模式字串

    Returns:
        AgentMode 或 None

    Raises:
        HTTPException: 無效的模式
    """
    if not mode_str:
        return None

    try:
        return AgentMode[mode_str.upper()]
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode: {mode_str}. Valid modes: {[m.name for m in AgentMode]}",
        ) from e


# ==========================================
# API Endpoints
# ==========================================


@router.post(
    "/{agent_id}/execute",
    response_model=ExecuteTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="執行 Agent 任務",
    description="""
    執行 Agent 任務並返回結果。

    - 創建新的執行會話
    - 追蹤執行狀態
    - 返回執行結果和追蹤資訊
    """,
)
async def execute_agent_task(
    agent_id: str,
    request: ExecuteTaskRequest,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    執行 Agent 任務

    Args:
        agent_id: Agent ID
        request: 執行請求
        trading_service: TradingService 實例

    Returns:
        執行結果

    Raises:
        404: Agent 不存在
        409: Agent 正在執行中
        500: 執行失敗
    """
    try:
        logger.info(f"Executing task for agent {agent_id}: {request.task[:50]}...")

        # 解析模式
        mode = parse_agent_mode(request.mode)

        # 執行任務
        result = await trading_service.execute_agent_task(
            agent_id=agent_id,
            task=request.task,
            mode=mode,
            context=request.context,
            max_turns=request.max_turns,
        )

        return ExecuteTaskResponse(**result)

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except AgentBusyError as e:
        logger.warning(f"Agent busy: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    except TradingServiceError as e:
        logger.error(f"Task execution failed for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/{agent_id}/start",
    response_model=StartStopResponse,
    status_code=status.HTTP_200_OK,
    summary="啟動 Agent",
    description="啟動 Agent，更新狀態為 ACTIVE",
)
async def start_agent(
    agent_id: str,
    request: StartAgentRequest | None = None,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    啟動 Agent

    Args:
        agent_id: Agent ID
        request: 啟動請求（可選）
        trading_service: TradingService 實例

    Returns:
        啟動結果

    Raises:
        404: Agent 不存在
        500: 啟動失敗
    """
    try:
        logger.info(f"Starting agent {agent_id}")

        # 解析模式
        mode = None
        if request and request.mode:
            mode = parse_agent_mode(request.mode)

        # 啟動 Agent
        result = await trading_service.start_agent(agent_id, mode)

        return StartStopResponse(**result)

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except TradingServiceError as e:
        logger.error(f"Failed to start agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/{agent_id}/stop",
    response_model=StartStopResponse,
    status_code=status.HTTP_200_OK,
    summary="停止 Agent",
    description="停止 Agent，更新狀態為 INACTIVE",
)
async def stop_agent(
    agent_id: str,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    停止 Agent

    Args:
        agent_id: Agent ID
        trading_service: TradingService 實例

    Returns:
        停止結果

    Raises:
        404: Agent 不存在
        500: 停止失敗
    """
    try:
        logger.info(f"Stopping agent {agent_id}")

        # 停止 Agent
        result = await trading_service.stop_agent(agent_id)

        return StartStopResponse(**result)

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except TradingServiceError as e:
        logger.error(f"Failed to stop agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get(
    "/{agent_id}/status",
    response_model=AgentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="取得 Agent 狀態",
    description="取得 Agent 當前狀態，包括是否運行中",
)
async def get_agent_status(
    agent_id: str,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    取得 Agent 狀態

    Args:
        agent_id: Agent ID
        trading_service: TradingService 實例

    Returns:
        Agent 狀態

    Raises:
        404: Agent 不存在
        500: 查詢失敗
    """
    try:
        logger.debug(f"Getting status for agent {agent_id}")

        # 取得狀態
        status_data = await trading_service.get_agent_status(agent_id)

        return AgentStatusResponse(**status_data)

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except TradingServiceError as e:
        logger.error(f"Failed to get status for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get(
    "/{agent_id}/history",
    response_model=ExecutionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="取得執行歷史",
    description="取得 Agent 的執行歷史記錄",
)
async def get_execution_history(
    agent_id: str,
    limit: int = 20,
    status_filter: str | None = None,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    取得執行歷史

    Args:
        agent_id: Agent ID
        limit: 最大返回數量
        status_filter: 過濾狀態（可選）
        trading_service: TradingService 實例

    Returns:
        執行歷史

    Raises:
        404: Agent 不存在
        400: 無效的狀態過濾
        500: 查詢失敗
    """
    try:
        logger.debug(f"Getting execution history for agent {agent_id}")

        # 解析狀態過濾
        session_status = None
        if status_filter:
            try:
                session_status = SessionStatus[status_filter.upper()]
            except KeyError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}",
                ) from e

        # 取得歷史
        history = await trading_service.get_execution_history(
            agent_id, limit=limit, status=session_status
        )

        return ExecutionHistoryResponse(**history)

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except TradingServiceError as e:
        logger.error(f"Failed to get history for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get(
    "/{agent_id}/sessions/{session_id}",
    response_model=SessionDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="取得會話詳情",
    description="取得特定會話的詳細資訊",
)
async def get_session_details(
    agent_id: str,
    session_id: str,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    取得會話詳情

    Args:
        agent_id: Agent ID（用於驗證）
        session_id: Session ID
        trading_service: TradingService 實例

    Returns:
        會話詳情

    Raises:
        404: 會話不存在
        500: 查詢失敗
    """
    try:
        logger.debug(f"Getting session details: {session_id}")

        # 取得會話詳情
        details = await trading_service.get_session_details(session_id)

        # 驗證 agent_id 匹配
        if details["agent_id"] != agent_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found for agent {agent_id}",
            )

        return SessionDetailsResponse(**details)

    except SessionError as e:
        logger.warning(f"Session not found: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        ) from e

    except Exception as e:
        logger.error(f"Failed to get session details {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get(
    "/{agent_id}/statistics",
    response_model=AgentStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="取得 Agent 統計",
    description="取得 Agent 的執行統計資訊",
)
async def get_agent_statistics(
    agent_id: str,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    取得 Agent 統計

    Args:
        agent_id: Agent ID
        trading_service: TradingService 實例

    Returns:
        統計資訊

    Raises:
        404: Agent 不存在
        500: 查詢失敗
    """
    try:
        logger.debug(f"Getting statistics for agent {agent_id}")

        # 取得統計
        stats = await trading_service.get_agent_statistics(agent_id)

        return AgentStatisticsResponse(**stats)

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except TradingServiceError as e:
        logger.error(f"Failed to get statistics for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
