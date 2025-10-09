"""
Trading API Router

Endpoints for querying trading history, portfolio, and strategy changes.
"""

from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger

# Import the same agent_manager instance from agents router
from .agents import agent_manager

router = APIRouter()


@router.get("/agents/{agent_id}/portfolio")
async def get_agent_portfolio(agent_id: str):
    """Get agent's current portfolio."""
    try:
        # Check if agent exists using list_agent_ids (which is synchronous)
        if agent_id not in agent_manager.list_agent_ids():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        portfolio = await agent_manager.get_portfolio(agent_id)

        # Get agent data for timestamp
        agent_data = await agent_manager.get_agent(agent_id)

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
        # Check if agent exists
        if agent_id not in agent_manager.list_agent_ids():
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
        # Check if agent exists
        if agent_id not in agent_manager.list_agent_ids():
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
        # Check if agent exists
        if agent_id not in agent_manager.list_agent_ids():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found",
            )

        performance = await agent_manager.get_performance(agent_id)

        # Get agent data for timestamp
        agent_data = await agent_manager.get_agent(agent_id)

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
    """Get current market status using MCP tools."""
    try:
        from datetime import datetime

        import pytz

        from ...agents.integrations.mcp_client import get_mcp_client

        # Initialize MCP client
        mcp_client = get_mcp_client()
        await mcp_client.initialize()

        # Get current time in Taipei timezone
        tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(tz)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")

        # Check if today is a trading day using MCP tool
        trading_day_info = await mcp_client.check_trading_day(current_date)

        # Determine if currently in trading hours (9:00-13:30)
        is_trading_hours = False
        market_status = "closed"

        if trading_day_info.get("is_trading_day", False):
            hour = now.hour
            minute = now.minute

            # Check if in trading hours (9:00-13:30)
            if (hour == 9 and minute >= 0) or (hour > 9 and hour < 13):
                is_trading_hours = True
                market_status = "open"
            elif hour == 13 and minute < 30:
                is_trading_hours = True
                market_status = "open"
            elif hour < 9:
                market_status = "pre_market"
            else:
                market_status = "after_market"
        else:
            # Not a trading day
            if trading_day_info.get("is_weekend"):
                market_status = "weekend"
            elif trading_day_info.get("is_holiday"):
                market_status = "holiday"

        return {
            "is_trading_day": trading_day_info.get("is_trading_day", False),
            "is_trading_hours": is_trading_hours,
            "market_open": "09:00",
            "market_close": "13:30",
            "current_time": current_time,
            "current_date": current_date,
            "status": market_status,
            "is_weekend": trading_day_info.get("is_weekend", False),
            "is_holiday": trading_day_info.get("is_holiday", False),
            "holiday_name": trading_day_info.get("holiday_name"),
        }

    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market status: {str(e)}",
        ) from e
