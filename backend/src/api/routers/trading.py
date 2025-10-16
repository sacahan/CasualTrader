"""
Trading API Router

提供交易、投資組合和績效相關的 API。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...service.agents_service import (
    AgentNotFoundError,
    AgentsService,
)
from ..config import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trading", tags=["trading"])


# ==========================================
# Dependencies
# ==========================================


def get_agents_service(db_session: AsyncSession = Depends(get_db_session)) -> AgentsService:
    """
    獲取 AgentsService 實例

    Args:
        db_session: SQLAlchemy 異步 session

    Returns:
        AgentsService 實例
    """
    return AgentsService(db_session)


# ==========================================
# Portfolio Endpoints
# ==========================================


@router.get(
    "/agents/{agent_id}/portfolio",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="取得投資組合",
    description="獲取 Agent 的完整投資組合資訊",
)
async def get_portfolio(
    agent_id: str,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    取得投資組合

    Args:
        agent_id: Agent ID
        agents_service: AgentsService 實例

    Returns:
        投資組合資訊

    Raises:
        404: Agent 不存在
        500: 查詢失敗
    """
    try:
        logger.info(f"Getting portfolio for agent: {agent_id}")

        # 獲取 agent 配置
        agent = await agents_service.get_agent_config(agent_id)

        # 獲取持股
        holdings = await agents_service.get_agent_holdings(agent_id)

        # 計算投資組合總值
        cash_balance = float(agent.current_funds or agent.initial_funds)
        total_stock_value = sum(
            holding.quantity * float(holding.average_cost) for holding in holdings
        )
        total_portfolio_value = cash_balance + total_stock_value

        # 組裝回應
        portfolio = {
            "agent_id": agent_id,
            "cash_balance": cash_balance,
            "initial_funds": float(agent.initial_funds),
            "total_stock_value": total_stock_value,
            "total_portfolio_value": total_portfolio_value,
            "total_return": total_portfolio_value - float(agent.initial_funds),
            "total_return_percent": (
                (total_portfolio_value - float(agent.initial_funds))
                / float(agent.initial_funds)
                * 100
                if float(agent.initial_funds) > 0
                else 0
            ),
            "holdings_count": len(holdings),
            "holdings": [
                {
                    "ticker": holding.ticker,
                    "company_name": holding.company_name,
                    "quantity": holding.quantity,
                    "average_cost": float(holding.average_cost),
                    "current_price": float(holding.current_price)
                    if holding.current_price
                    else None,
                    "market_value": holding.quantity * float(holding.average_cost),
                    "unrealized_pnl": (
                        float(holding.unrealized_pnl) if holding.unrealized_pnl else None
                    ),
                    "last_updated": (
                        holding.last_updated.isoformat() if holding.last_updated else None
                    ),
                }
                for holding in holdings
            ],
            "last_updated": agent.updated_at.isoformat() if agent.updated_at else None,
        }

        return portfolio

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except Exception as e:
        logger.error(f"Failed to get portfolio for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get(
    "/agents/{agent_id}/holdings",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="取得持股明細",
    description="獲取 Agent 的所有持股明細",
)
async def get_holdings(
    agent_id: str,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    取得持股明細

    Args:
        agent_id: Agent ID
        agents_service: AgentsService 實例

    Returns:
        持股明細列表

    Raises:
        404: Agent 不存在
        500: 查詢失敗
    """
    try:
        logger.info(f"Getting holdings for agent: {agent_id}")

        # 驗證 agent 存在
        await agents_service.get_agent_config(agent_id)

        # 獲取持股
        holdings = await agents_service.get_agent_holdings(agent_id)

        # 組裝回應
        holdings_list = [
            {
                "ticker": holding.ticker,
                "company_name": holding.company_name,
                "quantity": holding.quantity,
                "average_cost": float(holding.average_cost),
                "current_price": float(holding.current_price) if holding.current_price else None,
                "market_value": holding.quantity * float(holding.average_cost),
                "cost_basis": holding.quantity * float(holding.average_cost),
                "unrealized_pnl": float(holding.unrealized_pnl) if holding.unrealized_pnl else None,
                "unrealized_pnl_percent": (
                    (
                        float(holding.unrealized_pnl)
                        / (holding.quantity * float(holding.average_cost))
                        * 100
                    )
                    if holding.unrealized_pnl and holding.quantity > 0
                    else None
                ),
                "first_purchase_date": (
                    holding.first_purchase_date.isoformat() if holding.first_purchase_date else None
                ),
                "last_updated": (
                    holding.last_updated.isoformat() if holding.last_updated else None
                ),
            }
            for holding in holdings
        ]

        return holdings_list

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except Exception as e:
        logger.error(f"Failed to get holdings for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


# ==========================================
# Transaction History Endpoints
# ==========================================


@router.get(
    "/agents/{agent_id}/transactions",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="取得交易歷史",
    description="獲取 Agent 的交易歷史記錄",
)
async def get_transactions(
    agent_id: str,
    limit: int = 50,
    offset: int = 0,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    取得交易歷史

    Args:
        agent_id: Agent ID
        limit: 返回記錄數量限制
        offset: 偏移量
        agents_service: AgentsService 實例

    Returns:
        交易歷史記錄

    Raises:
        404: Agent 不存在
        500: 查詢失敗
    """
    try:
        logger.info(f"Getting transactions for agent: {agent_id} (limit={limit}, offset={offset})")

        # 驗證 agent 存在
        await agents_service.get_agent_config(agent_id)

        # 獲取交易記錄
        transactions = await agents_service.get_agent_transactions(
            agent_id=agent_id,
            limit=limit,
            offset=offset,
        )

        # 組裝回應
        transactions_list = [
            {
                "id": tx.id,
                "ticker": tx.ticker,
                "company_name": tx.company_name,
                "action": tx.action.value if hasattr(tx.action, "value") else tx.action,
                "quantity": tx.quantity,
                "price": float(tx.price),
                "total_amount": float(tx.total_amount),
                "commission": float(tx.commission) if tx.commission else 0.0,
                "net_amount": float(tx.total_amount)
                + (float(tx.commission) if tx.commission else 0.0),
                "status": tx.status.value if hasattr(tx.status, "value") else tx.status,
                "execution_time": tx.execution_time.isoformat() if tx.execution_time else None,
                "decision_reason": tx.decision_reason,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in transactions
        ]

        return {
            "agent_id": agent_id,
            "total": len(transactions_list),
            "limit": limit,
            "offset": offset,
            "transactions": transactions_list,
        }

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except Exception as e:
        logger.error(f"Failed to get transactions for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get(
    "/agents/{agent_id}/trades",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="取得交易記錄",
    description="獲取 Agent 的交易記錄（別名，同 transactions）",
)
async def get_trades(
    agent_id: str,
    limit: int = 50,
    offset: int = 0,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    取得交易記錄（別名端點）

    這是 get_transactions 的別名，提供相同的功能

    Args:
        agent_id: Agent ID
        limit: 返回記錄數量限制
        offset: 偏移量
        agents_service: AgentsService 實例

    Returns:
        交易記錄

    Raises:
        404: Agent 不存在
        500: 查詢失敗
    """
    return await get_transactions(agent_id, limit, offset, agents_service)


# ==========================================
# Performance Endpoints
# ==========================================


@router.get(
    "/agents/{agent_id}/performance",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="取得績效指標",
    description="獲取 Agent 的績效分析指標",
)
async def get_performance(
    agent_id: str,
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    取得績效指標

    Args:
        agent_id: Agent ID
        agents_service: AgentsService 實例

    Returns:
        績效指標

    Raises:
        404: Agent 不存在
        500: 查詢失敗
    """
    try:
        logger.info(f"Getting performance for agent: {agent_id}")

        # 獲取 agent 配置
        agent = await agents_service.get_agent_config(agent_id)

        # 獲取持股和交易記錄
        holdings = await agents_service.get_agent_holdings(agent_id)
        transactions = await agents_service.get_agent_transactions(agent_id, limit=1000)

        # 計算基本指標
        cash_balance = float(agent.current_funds or agent.initial_funds)
        total_stock_value = sum(
            holding.quantity * float(holding.average_cost) for holding in holdings
        )
        total_portfolio_value = cash_balance + total_stock_value
        total_return = total_portfolio_value - float(agent.initial_funds)
        total_return_percent = (
            (total_return / float(agent.initial_funds)) * 100
            if float(agent.initial_funds) > 0
            else 0
        )

        # 計算交易統計
        total_trades = len(transactions)
        buy_trades = sum(1 for tx in transactions if tx.action.value == "BUY")
        sell_trades = sum(1 for tx in transactions if tx.action.value == "SELL")

        # 計算實現損益（簡化版）
        realized_pnl = sum(
            float(tx.total_amount) if tx.action.value == "SELL" else -float(tx.total_amount)
            for tx in transactions
        )

        # 計算未實現損益
        unrealized_pnl = sum(
            float(holding.unrealized_pnl) if holding.unrealized_pnl else 0 for holding in holdings
        )

        # 組裝回應
        performance = {
            "agent_id": agent_id,
            "period": "all_time",
            "total_return": total_return,
            "total_return_percent": total_return_percent,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": realized_pnl + unrealized_pnl,
            "initial_funds": float(agent.initial_funds),
            "current_value": total_portfolio_value,
            "cash_balance": cash_balance,
            "stock_value": total_stock_value,
            "total_trades": total_trades,
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "holdings_count": len(holdings),
            "win_rate": None,  # 需要更複雜的計算
            "sharpe_ratio": None,  # 需要歷史價格數據
            "max_drawdown": None,  # 需要歷史淨值數據
            "last_updated": agent.updated_at.isoformat() if agent.updated_at else None,
        }

        return performance

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except Exception as e:
        logger.error(f"Failed to get performance for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


# ==========================================
# Market Data Endpoints (Placeholder)
# ==========================================


@router.get(
    "/market/status",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="取得市場狀態",
    description="獲取市場開盤狀態（暫未實現，建議使用 MCP Server）",
)
async def get_market_status():
    """
    取得市場狀態

    Returns:
        市場狀態資訊

    Note:
        建議使用 MCP Server (casual-market) 獲取即時市場資料
    """
    return {
        "is_open": False,
        "next_open_time": None,
        "message": "Market data feature not implemented. Please use MCP Server for real-time market data.",
    }


@router.get(
    "/market/quote/{ticker}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="取得股票報價",
    description="獲取股票即時報價（暫未實現，建議使用 MCP Server）",
)
async def get_stock_quote(ticker: str):
    """
    取得股票報價

    Args:
        ticker: 股票代碼

    Returns:
        股票報價資訊

    Note:
        建議使用 MCP Server (casual-market) 獲取即時股票報價
    """
    return {
        "ticker": ticker,
        "price": None,
        "message": "Stock quote feature not implemented. Please use MCP Server for real-time quotes.",
    }


@router.get(
    "/market/indices",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="取得市場指數",
    description="獲取市場指數資訊（暫未實現，建議使用 MCP Server）",
)
async def get_market_indices():
    """
    取得市場指數

    Returns:
        市場指數資訊

    Note:
        建議使用 MCP Server (casual-market) 獲取即時市場指數
    """
    return {
        "indices": [],
        "message": "Market indices feature not implemented. Please use MCP Server for real-time indices.",
    }
