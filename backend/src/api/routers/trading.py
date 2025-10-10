"""
Trading API Router

Endpoints for querying trading history, portfolio, and strategy changes.
"""

from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger

# Import the same agent_manager instance from agents router
from .agents import agent_manager

router = APIRouter()


# Note: This router does NOT directly use MCP tools
# MCP tools are only available within Agent execution context via OpenAI SDK
# For system-level market status checks, we use simplified logic (weekday check)
#
# If accurate holiday detection is needed, Agents use MarketStatusChecker
# with MCP tools configured via their mcp_servers parameter.


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

        trades = await agent_manager.get_trades(agent_id=agent_id, limit=limit, offset=offset)

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
    """
    Get current market status using simplified logic.

    Returns Taiwan stock market status including:
    - Trading day status (weekday check only, NO holiday detection)
    - Current trading hours status
    - Market open/close times

    Note: Does NOT detect Taiwan national holidays.
    For accurate holiday detection, use Agent with MCP tools.
    """
    try:
        from datetime import datetime, time

        import pytz

        # Get current time in Taipei timezone
        tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(tz)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")

        # Basic weekday check (no holiday detection)
        is_weekday = now.weekday() < 5

        # Check if in trading hours (9:00-13:30)
        is_trading_hours = False
        market_status = "closed"

        if is_weekday:
            if time(9, 0) <= now.time() <= time(13, 30):
                is_trading_hours = True
                market_status = "open"
            elif now.hour < 9:
                market_status = "pre_market"
            else:
                market_status = "after_market"
        else:
            market_status = "weekend"

        return {
            "is_trading_day": is_weekday,
            "is_trading_hours": is_trading_hours,
            "market_open": "09:00",
            "market_close": "13:30",
            "current_time": current_time,
            "current_date": current_date,
            "status": market_status,
            "is_weekend": not is_weekday,
        }

    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market status: {str(e)}",
        ) from e
