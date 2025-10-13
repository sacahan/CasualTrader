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
    Get current market status using CasualMarket MCP.

    Returns Taiwan stock market status including:
    - Trading day status (with accurate holiday detection via MCP)
    - Current trading hours status
    - Market open/close times
    - Holiday information if applicable

    Uses CasualMarket MCP's check_taiwan_trading_day tool for accurate results.
    """
    try:
        from datetime import datetime, time

        import pytz

        # Get current time in Taipei timezone
        tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(tz)
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")

        # Query CasualMarket MCP for accurate trading day status
        is_trading_day = False
        is_weekend = False
        is_holiday = False
        holiday_name = None

        try:
            import asyncio
            import json

            # Call CasualMarket MCP via CLI
            # Format: uvx casual-market-mcp check-trading-day YYYY-MM-DD
            process = await asyncio.create_subprocess_exec(
                "uvx",
                "casual-market-mcp",
                "check-trading-day",
                current_date,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)

            if process.returncode == 0 and stdout:
                # Parse JSON response
                mcp_response = json.loads(stdout.decode())
                if mcp_response.get("success"):
                    mcp_data = mcp_response.get("data", {})
                    is_trading_day = mcp_data.get("is_trading_day", False)
                    is_weekend = mcp_data.get("is_weekend", False)
                    is_holiday = mcp_data.get("is_holiday", False)
                    holiday_name = mcp_data.get("holiday_name")
                else:
                    logger.warning(
                        f"MCP check_taiwan_trading_day returned error: {mcp_response.get('error')}"
                    )
                    raise ValueError("MCP returned error response")
            else:
                error_msg = stderr.decode() if stderr else "No error output"
                logger.warning(
                    f"MCP subprocess failed (exit code {process.returncode}): {error_msg}"
                )
                raise ValueError(f"MCP subprocess failed with exit code {process.returncode}")

        except (
            asyncio.TimeoutError,
            json.JSONDecodeError,
            ValueError,
            FileNotFoundError,
        ) as mcp_error:
            # Fallback to basic weekday check if MCP unavailable
            logger.warning(f"MCP unavailable, using fallback logic: {mcp_error}")
            is_trading_day = now.weekday() < 5
            is_weekend = now.weekday() >= 5
            is_holiday = False
            holiday_name = None

        # Check if in trading hours (9:00-13:30)
        is_trading_hours = False
        market_status = "closed"

        if is_trading_day:
            if time(9, 0) <= now.time() <= time(13, 30):
                is_trading_hours = True
                market_status = "open"
            elif now.hour < 9:
                market_status = "pre_market"
            else:
                market_status = "after_market"
        elif is_weekend:
            market_status = "weekend"
        elif is_holiday:
            market_status = "holiday"
        else:
            market_status = "closed"

        response = {
            "is_trading_day": is_trading_day,
            "is_trading_hours": is_trading_hours,
            "market_open": "09:00",
            "market_close": "13:30",
            "current_time": current_time,
            "current_date": current_date,
            "status": market_status,
            "is_weekend": is_weekend,
        }

        # Add holiday information if applicable
        if is_holiday and holiday_name:
            response["is_holiday"] = True
            response["holiday_name"] = holiday_name
        else:
            response["is_holiday"] = False

        return response

    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market status: {str(e)}",
        ) from e
