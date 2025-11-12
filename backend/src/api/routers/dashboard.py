"""
Dashboard API Router

提供儀表板相關的 API 端點
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_db_session
from schemas.dashboard import DashboardData
from service.dashboard_service import DashboardService
from common.logger import logger

router = APIRouter(prefix="/api/trading", tags=["dashboard"])


# ==========================================
# Dependencies
# ==========================================


def get_dashboard_service(db_session: AsyncSession = Depends(get_db_session)) -> DashboardService:
    """
    獲取 DashboardService 實例

    Args:
        db_session: SQLAlchemy 異步 session

    Returns:
        DashboardService 實例
    """
    return DashboardService(db_session)


# ==========================================
# Dashboard Endpoints
# ==========================================


@router.get(
    "/agents/{agent_id}/dashboard",
    response_model=DashboardData,
    status_code=status.HTTP_200_OK,
    summary="取得儀表板數據",
    description="獲取 Agent 的性能儀表板數據，支援不同時間段篩選",
)
async def get_dashboard(
    agent_id: str,
    time_period: str = "1M",
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    """
    取得儀表板數據

    Args:
        agent_id: Agent ID
        time_period: 時間段 (1D, 1W, 1M, 3M, 1Y, all), 預設為 1M
        dashboard_service: DashboardService 實例

    Returns:
        完整的儀表板數據

    Raises:
        400: 無效的時間段
        404: Agent 不存在或沒有數據
        500: 伺服器錯誤

    Examples:
        GET /api/trading/agents/550e8400-e29b-41d4-a716-446655440000/dashboard?time_period=1M
    """
    logger.info(f"獲取 Agent {agent_id} 的儀表板數據, 時間段: {time_period}")

    # 驗證時間段
    valid_periods = ["1D", "1W", "1M", "3M", "1Y", "all"]
    if time_period not in valid_periods:
        logger.warning(f"無效的時間段: {time_period}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無效的時間段: {time_period}. 有效值: {valid_periods}",
        )

    try:
        dashboard_data = await dashboard_service.get_dashboard_data(
            agent_id=agent_id,
            time_period=time_period,
        )
        logger.info(f"成功獲取 Agent {agent_id} 的儀表板數據")
        return dashboard_data

    except ValueError as e:
        logger.warning(f"驗證錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"獲取儀表板數據失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取儀表板數據失敗",
        )
