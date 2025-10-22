"""
Agent Execution API Router

提供 Agent 單一模式執行的 RESTful API（手動觸發設計）。

設計特性：
- start 端點：立即返回 session_id，在後台異步執行
- stop 端點：等待 Agent 停止完成後返回
- 狀態更新透過 WebSocket 推送
"""

from __future__ import annotations

import asyncio
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from service.agents_service import AgentNotFoundError
from common.enums import AgentMode
from common.logger import logger
from service.trading_service import (
    AgentBusyError,
    TradingService,
    TradingServiceError,
)
from api.config import get_db_session
from api.websocket import websocket_manager

router = APIRouter()


# ==========================================
# Request Models
# ==========================================


class AgentModeEnum(str, Enum):
    """執行模式枚舉"""

    OBSERVATION = "OBSERVATION"
    TRADING = "TRADING"
    REBALANCING = "REBALANCING"


class StartModeRequest(BaseModel):
    """啟動單一模式執行請求"""

    mode: AgentModeEnum = Field(
        default=AgentModeEnum.OBSERVATION,
        description="執行模式: OBSERVATION | TRADING | REBALANCING",
    )
    max_turns: int | None = Field(None, ge=1, le=50, description="最大輪數")


# ==========================================
# Response Models
# ==========================================


class StartModeResponse(BaseModel):
    """單一模式執行響應

    立即返回 session_id，Agent 在後台執行。
    狀態變化透過 WebSocket 推送。
    """

    success: bool
    session_id: str
    mode: str
    message: str = (
        "Agent execution started in background. Status updates will be pushed via WebSocket."
    )


class StopResponse(BaseModel):
    """停止執行響應"""

    success: bool
    agent_id: str
    status: str  # "stopped" or "not_running"


# ==========================================
# Helper Functions
# ==========================================


def get_trading_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> TradingService:
    """獲取 TradingService 實例"""
    return TradingService(db_session)


async def _execute_in_background(
    trading_service: TradingService,
    agent_id: str,
    mode: AgentMode,
    max_turns: int | None = None,
) -> None:
    """
    後台執行 Agent 並推送狀態更新

    此函數在後台運行，不阻塞 HTTP 回應。
    所有狀態變化透過 WebSocket 廣播。

    Args:
        trading_service: TradingService 實例
        agent_id: Agent ID
        mode: 執行模式
        max_turns: 最大輪數
    """
    try:
        logger.info(f"[Background] Starting execution for agent {agent_id} ({mode.value})")

        result = await trading_service.execute_single_mode(
            agent_id=agent_id,
            mode=mode,
            max_turns=max_turns,
        )

        # ✅ 執行成功 - 推送完成事件
        await websocket_manager.broadcast(
            {
                "type": "execution_completed",
                "agent_id": agent_id,
                "session_id": result["session_id"],
                "mode": result["mode"],
                "success": True,
                "execution_time_ms": result["execution_time_ms"],
                "output": result.get("output"),
            }
        )
        logger.info(
            f"[Background] Execution completed for agent {agent_id} "
            f"in {result['execution_time_ms']}ms"
        )

    except Exception as e:
        logger.error(f"[Background] Execution failed for agent {agent_id}: {e}", exc_info=True)

        # ❌ 執行失敗 - 推送錯誤事件
        await websocket_manager.broadcast(
            {
                "type": "execution_failed",
                "agent_id": agent_id,
                "mode": mode.value,
                "success": False,
                "error": str(e),
            }
        )


# ==========================================
# API Endpoints
# ==========================================


@router.post(
    "/{agent_id}/start",
    response_model=StartModeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="執行單一模式（非阻塞）",
    description="立即返回 session_id，在後台執行 Agent。狀態更新透過 WebSocket 推送。",
)
async def start_agent_mode(
    agent_id: str,
    request: StartModeRequest,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    執行 Agent 指定模式（非阻塞設計）

    此端點會立即返回 session_id，Agent 在後台執行。
    所有狀態變化（進行中、完成、錯誤）透過 WebSocket 推送到前端。

    Args:
        agent_id: Agent ID
        request.mode: 執行模式 (OBSERVATION | TRADING | REBALANCING)
        request.max_turns: 最大輪數（可選）

    Returns:
        成功時返回 202 Accepted 及 session_id

    Raises:
        404: Agent 不存在
        409: Agent 已在執行中
        400: 無效的模式
        500: 啟動失敗
    """
    try:
        logger.info(f"API: Starting {request.mode.value} for agent {agent_id}")

        try:
            mode = AgentMode[request.mode.value]
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mode: {request.mode.value}",
            ) from e

        # ⚡ 檢查 Agent 是否已在執行中（快速檢查）
        if agent_id in trading_service.active_agents:
            raise AgentBusyError(f"Agent {agent_id} is already running")

        # 驗證 Agent 存在並創建會話
        await trading_service.agents_service.get_agent_config(agent_id)
        session = await trading_service.session_service.create_session(
            agent_id=agent_id,
            session_type="manual_mode",
            mode=mode,
            initial_input={},
        )
        session_id = session.id

        logger.info(f"API: Created session {session_id}, starting background execution")

        # 💡 核心改變：在後台啟動執行，立即返回 session_id
        # 使用 asyncio.create_task 在後台執行，不阻塞 HTTP 回應
        asyncio.create_task(
            _execute_in_background(
                trading_service=trading_service,
                agent_id=agent_id,
                mode=mode,
                max_turns=request.max_turns,
            )
        )

        # 🚀 立即返回 202 Accepted，包含 session_id
        await websocket_manager.broadcast(
            {
                "type": "execution_started",
                "agent_id": agent_id,
                "session_id": session_id,
                "mode": mode.value,
            }
        )

        return StartModeResponse(
            success=True,
            session_id=session_id,
            mode=mode.value,
        )

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
        logger.error(f"Failed to start execution for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/{agent_id}/stop",
    response_model=StopResponse,
    status_code=status.HTTP_200_OK,
    summary="停止 Agent 執行（阻塞式）",
    description="停止 Agent 正在執行的任務，等待完成後返回。",
)
async def stop_agent(
    agent_id: str,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    停止 Agent 執行（阻塞式）

    與 start 端點不同，此端點會等待 Agent 實際停止完成後才返回。
    這簡化了前端的操作流程。

    Args:
        agent_id: Agent ID

    Returns:
        停止結果

    Raises:
        404: Agent 不存在
        500: 停止失敗
    """
    try:
        logger.info(f"API: Stopping agent {agent_id}")

        # 停止正在執行的任務，並等待完成
        result = await trading_service.stop_agent(agent_id)

        # 推送停止事件
        await websocket_manager.broadcast(
            {
                "type": "execution_stopped",
                "agent_id": agent_id,
                "status": result["status"],
            }
        )

        logger.info(f"API: Agent {agent_id} stopped with status: {result['status']}")

        return StopResponse(
            success=result["success"],
            agent_id=agent_id,
            status=result["status"],
        )

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
