"""
Agent Execution API Router

提供 Agent 單一模式執行的 RESTful API（手動觸發設計）。
"""

from __future__ import annotations

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
    """單一模式執行響應"""

    success: bool
    session_id: str
    mode: str
    execution_time_ms: int
    output: str | None = None
    error: str | None = None


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


# ==========================================
# API Endpoints
# ==========================================


@router.post(
    "/{agent_id}/start",
    response_model=StartModeResponse,
    status_code=status.HTTP_200_OK,
    summary="執行單一模式",
    description="執行 Agent 指定模式（執行完後立即返回）",
)
async def start_agent_mode(
    agent_id: str,
    request: StartModeRequest,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    執行 Agent 指定模式

    Args:
        agent_id: Agent ID
        request.mode: 執行模式 (OBSERVATION | TRADING | REBALANCING)
        request.max_turns: 最大輪數（可選）

    Returns:
        執行結果

    Raises:
        404: Agent 不存在
        409: Agent 已在執行中
        400: 無效的模式
        500: 執行失敗
    """
    try:
        logger.info(f"Starting {request.mode.value} for agent {agent_id}")

        try:
            mode = AgentMode[request.mode.value]
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mode: {request.mode.value}",
            ) from e

        # 執行單一模式
        result = await trading_service.execute_single_mode(
            agent_id=agent_id,
            mode=mode,
            max_turns=request.max_turns,
        )

        return StartModeResponse(**result)

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
        logger.error(f"Execution failed for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/{agent_id}/stop",
    response_model=StopResponse,
    status_code=status.HTTP_200_OK,
    summary="停止 Agent 執行",
    description="停止 Agent 正在執行的任務",
)
async def stop_agent(
    agent_id: str,
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    停止 Agent 執行

    Args:
        agent_id: Agent ID

    Returns:
        停止結果

    Raises:
        404: Agent 不存在
        500: 停止失敗
    """
    try:
        logger.info(f"Stopping agent {agent_id}")

        # 停止正在執行的任務
        result = await trading_service.stop_agent(agent_id)

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
