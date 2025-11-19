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
from service.session_service import AgentSessionService
from api.config import get_db_session
from api.websocket import websocket_manager

router = APIRouter()


# ==========================================
# Request Models
# ==========================================


class AgentModeEnum(str, Enum):
    """執行模式枚舉"""

    TRADING = "TRADING"
    REBALANCING = "REBALANCING"


class StartModeRequest(BaseModel):
    """啟動單一模式執行請求"""

    mode: AgentModeEnum = Field(
        default=AgentModeEnum.TRADING,
        description="執行模式: TRADING | REBALANCING",
    )


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
    sessions_aborted: int = 0  # 中斷的會話數量


# ==========================================
# Helper Functions
# ==========================================


async def get_trading_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> TradingService:
    """獲取 TradingService 實例

    NOTE: 此依賴返回的 session 僅用於 API 端點內的同步操作。
    後台任務必須創建自己的 session，以避免在 API 端點返回時
    關閉 session 而後台任務仍在使用的問題。
    """
    return TradingService(db_session)


async def _execute_in_background(
    trading_service: TradingService,
    agent_id: str,
    mode: AgentMode,
    session_id: str,
) -> None:
    """
    後台執行 Agent 並推送狀態更新

    此函數在後台運行，不阻塞 HTTP 回應。
    所有狀態變化透過 WebSocket 廣播。

    ⚠️ 重要：此函數創建自己的 TradingService 和 session，以避免使用
    已在 API 端點返回時被關閉的 session。

    Args:
        trading_service: 已棄用（保留參數以與呼叫者兼容），不使用此實例
        agent_id: Agent ID
        mode: 執行模式
        session_id: 既存的 session ID（由 API 層創建）
    """
    # 為後台執行創建新的 session（獨立於 API 端點的 session）
    from api.config import get_session_maker

    session_maker = get_session_maker()
    bg_session = session_maker()

    try:
        logger.info(f"[Background] Starting execution for agent {agent_id} ({mode.value})")

        # 創建新的 TradingService 實例，使用獨立的 session
        bg_trading_service = TradingService(bg_session)

        # 使用既存的 session_id，避免重複創建
        result = await bg_trading_service.execute_single_mode(
            agent_id=agent_id,
            mode=mode,
            session_id=session_id,
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

    except asyncio.CancelledError:
        logger.warning(f"[Background] Execution cancelled for agent {agent_id}")

        # 推送停止事件
        await websocket_manager.broadcast(
            {
                "type": "execution_stopped",
                "agent_id": agent_id,
                "mode": mode.value,
                "success": True,
                "reason": "User stopped the execution",
            }
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

    finally:
        # 🔒 關鍵：確保後台 session 被正確關閉
        try:
            await bg_session.close()
            logger.debug(f"[Background] Session closed for agent {agent_id}")
        except Exception as cleanup_error:
            logger.error(
                f"[Background] Failed to close session for agent {agent_id}: {cleanup_error}"
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
        request.mode: 執行模式 (TRADING | REBALANCING)

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
            mode=mode,
            initial_input={},
        )
        session_id = session.id

        logger.info(f"API: Created session {session_id}, starting background execution")

        # ⚡ 關鍵：立即標記 agent 為活躍，防止競態條件
        # 使用特殊字串作為佔位符，表示執行即將開始
        trading_service.active_agents[agent_id] = "STARTING"  # type: ignore
        logger.debug(f"Marked agent {agent_id} as active (placeholder)")

        # 💡 核心改變：在後台啟動執行，立即返回 session_id
        # 使用 asyncio.create_task 在後台執行，不阻塞 HTTP 回應
        # 傳遞 session_id 給後台任務，避免重複創建
        task = asyncio.create_task(
            _execute_in_background(
                trading_service=trading_service,
                agent_id=agent_id,
                mode=mode,
                session_id=session_id,
            )
        )
        # ⭐ 保存任務以便後續停止
        trading_service.execution_tasks[agent_id] = task

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

    此端點會：
    1. 取消 Agent 正在執行的任務
    2. 清理所有關聯的資源
    3. 中斷所有 RUNNING 狀態的會話，確保下一輪執行不受阻

    Args:
        agent_id: Agent ID

    Returns:
        停止結果，包含中斷的會話數量

    Raises:
        404: Agent 不存在
        500: 停止失敗
    """
    try:
        logger.info(f"API: Stopping agent {agent_id}")

        # 停止正在執行的任務，並等待完成
        result = await trading_service.stop_agent(agent_id)

        # 推送停止事件和狀態更新事件
        # 1. 執行停止事件（包含會話信息）
        await websocket_manager.broadcast(
            {
                "type": "execution_stopped",
                "agent_id": agent_id,
                "status": result["status"],
                "sessions_aborted": result.get("sessions_aborted", 0),
            }
        )

        # 2. Agent 狀態更新事件（讓前端知道 Agent 已停止）
        # 將後端的 "stopped"/"not_running" 狀態對應到前端的 "stopped"/"idle"
        frontend_status = "idle" if result["status"] == "not_running" else "stopped"
        await websocket_manager.broadcast(
            {
                "type": "agent_status",
                "agent_id": agent_id,
                "status": frontend_status,
            }
        )

        logger.info(
            f"API: Agent {agent_id} stopped with status: {result['status']}, "
            f"sessions aborted: {result.get('sessions_aborted', 0)}"
        )

        return StopResponse(
            success=result["success"],
            agent_id=agent_id,
            status=result["status"],
            sessions_aborted=result.get("sessions_aborted", 0),
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


@router.get(
    "/{agent_id}/history",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
    summary="取得 Agent 執行歷史",
    description="取得 Agent 的執行歷史記錄列表，按時間倒序排列",
)
async def get_execution_history(
    agent_id: str,
    limit: int = 20,
    status_filter: str | None = None,
    session_service: AgentSessionService = Depends(
        lambda db_session=Depends(get_db_session): AgentSessionService(db_session)
    ),
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    取得 Agent 執行歷史

    Args:
        agent_id: Agent ID
        limit: 返回的最大記錄數（預設 20）
        status_filter: 狀態過濾器（可選）：pending, running, completed, failed, stopped

    Returns:
        執行歷史記錄列表（按時間倒序）

    Raises:
        500: 查詢失敗
    """
    try:
        # 轉換 status_filter 字串為 SessionStatus enum（如果提供）
        status_enum = None
        if status_filter:
            try:
                from common.enums import SessionStatus

                status_enum = SessionStatus[status_filter.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}",
                )

        sessions = await session_service.list_agent_sessions(
            agent_id=agent_id,
            limit=limit,
            status=status_enum,
        )

        # 為歷史列表構建回應（包含基本交易統計和詳細交易記錄）
        result = []
        for session in sessions:
            # 獲取該 session 的所有交易記錄
            transactions = await trading_service.get_transactions_by_session(session.id)

            # 構建交易記錄列表（與 get_session_detail 相同格式）
            trades = [
                {
                    "id": tx.id,
                    "ticker": tx.ticker,
                    "symbol": tx.ticker,  # 別名，前端可能使用
                    "company_name": tx.company_name,
                    "action": tx.action.value if hasattr(tx.action, "value") else tx.action,
                    "type": tx.action.value if hasattr(tx.action, "value") else tx.action,  # 別名
                    "quantity": tx.quantity,
                    "shares": tx.quantity,  # 別名
                    "price": float(tx.price),
                    "amount": float(tx.total_amount),
                    "total_amount": float(tx.total_amount),  # 別名
                    "commission": float(tx.commission),
                    "status": tx.status.value if hasattr(tx.status, "value") else tx.status,
                    "execution_time": tx.execution_time.isoformat() if tx.execution_time else None,
                    "decision_reason": tx.decision_reason,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                }
                for tx in transactions
            ]

            # 安全地獲取狀態值（處理 Enum 或字符串）
            filled_count = len(
                [
                    tx
                    for tx in transactions
                    if (tx.status.value if hasattr(tx.status, "value") else tx.status) == "executed"
                ]
            )
            total_notional = sum(float(tx.total_amount) for tx in transactions)

            result.append(
                {
                    "id": session.id,
                    "agent_id": session.agent_id,
                    "mode": session.mode,
                    "status": session.status,
                    "start_time": session.start_time,
                    "end_time": session.end_time,
                    "execution_time_ms": session.execution_time_ms,
                    "final_output": session.final_output,
                    "completed_at": session.end_time,  # 別名，前端可能使用
                    "error_message": session.error_message,
                    "created_at": session.created_at,
                    # 新增：統計資料
                    "trade_count": len(transactions),
                    "filled_count": filled_count,
                    "total_notional": total_notional,
                    # 新增：詳細交易記錄列表
                    "trades": trades,
                }
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution history for agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get(
    "/{agent_id}/sessions/{session_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="取得會話詳細資訊",
    description="取得單個會話的執行結果，包含呼叫的工具列表和交易記錄",
)
async def get_session_detail(
    agent_id: str,
    session_id: str,
    session_service: AgentSessionService = Depends(
        lambda db_session=Depends(get_db_session): AgentSessionService(db_session)
    ),
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    取得會話詳細資訊

    Args:
        agent_id: Agent ID（用於驗證）
        session_id: Session ID

    Returns:
        會話詳細資訊，包含執行結果、呼叫的工具列表、交易記錄等

    Raises:
        404: Session 不存在
        500: 查詢失敗
    """
    try:
        session = await session_service.get_session(session_id)

        if session.agent_id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found for agent {agent_id}",
            )

        # 獲取該 session 的所有交易記錄
        transactions = await trading_service.get_transactions_by_session(session_id)

        # 構建交易記錄列表
        trades = [
            {
                "id": tx.id,
                "ticker": tx.ticker,
                "symbol": tx.ticker,  # 別名，前端可能使用
                "company_name": tx.company_name,
                "action": tx.action.value if hasattr(tx.action, "value") else tx.action,
                "type": tx.action.value if hasattr(tx.action, "value") else tx.action,  # 別名
                "quantity": tx.quantity,
                "shares": tx.quantity,  # 別名
                "price": float(tx.price),
                "amount": float(tx.total_amount),
                "total_amount": float(tx.total_amount),  # 別名
                "commission": float(tx.commission),
                "status": tx.status.value if hasattr(tx.status, "value") else tx.status,
                "execution_time": tx.execution_time.isoformat() if tx.execution_time else None,
                "decision_reason": tx.decision_reason,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in transactions
        ]

        # 計算統計資料
        # 安全地獲取狀態值（處理 Enum 或字符串）
        filled_count = len(
            [
                tx
                for tx in transactions
                if (tx.status.value if hasattr(tx.status, "value") else tx.status) == "executed"
            ]
        )
        total_notional = sum(float(tx.total_amount) for tx in transactions)

        return {
            "id": session.id,
            "agent_id": session.agent_id,
            "mode": session.mode,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "execution_time_ms": session.execution_time_ms,
            "initial_input": session.initial_input,
            "final_output": session.final_output,
            "tools_called": session.tools_called,
            "error_message": session.error_message,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            # 新增：交易記錄列表
            "trades": trades,
            # 新增：統計資料
            "stats": {
                "filled": filled_count,
                "notional": total_notional,
                "total_trades": len(transactions),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
