"""
Trading API Router

Endpoints for querying trading history, portfolio, and strategy changes.
"""

from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger

from ...agents.core.agent_manager import AgentManager

router = APIRouter()

# Global agent manager instance
agent_manager = AgentManager()


@router.get("/agents/{agent_id}/portfolio")
async def get_agent_portfolio(agent_id: str):
    """Get agent's current portfolio."""
    try:
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        portfolio = await agent_manager.get_portfolio(agent_id)
        return {
            "agent_id": agent_id,
            "portfolio": portfolio,
            "timestamp": agent_data.get("updated_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio: {str(e)}",
        ) from e


@router.get("/agents/{agent_id}/trades")
async def get_agent_trades(
    agent_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Get agent's trading history."""
    try:
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        trades = await agent_manager.get_trades(
            agent_id=agent_id, limit=limit, offset=offset
        )

        return {
            "agent_id": agent_id,
            "trades": trades,
            "total": len(trades),
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trades for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trades: {str(e)}",
        ) from e


@router.get("/agents/{agent_id}/strategies")
async def get_strategy_changes(
    agent_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Get agent's strategy change history."""
    try:
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        strategy_changes = await agent_manager.get_strategy_changes(
            agent_id=agent_id, limit=limit, offset=offset
        )

        return {
            "agent_id": agent_id,
            "strategy_changes": strategy_changes,
            "total": len(strategy_changes),
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy changes for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy changes: {str(e)}",
        ) from e


@router.get("/agents/{agent_id}/performance")
async def get_agent_performance(agent_id: str):
    """Get agent's performance metrics."""
    try:
        agent_data = await agent_manager.get_agent(agent_id)
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        performance = await agent_manager.get_performance(agent_id)

        return {
            "agent_id": agent_id,
            "performance": performance,
            "timestamp": agent_data.get("updated_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance: {str(e)}",
        ) from e


@router.get("/market/status")
async def get_market_status():
    """Get current market status."""
    try:
        # This would integrate with the MCP market status tools
        # For now, return a placeholder
        return {
            "is_trading_day": True,
            "is_trading_hours": True,
            "market_open": "09:00",
            "market_close": "13:30",
            "current_time": "10:30",
            "status": "open",
        }

    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market status: {str(e)}",
        ) from e
