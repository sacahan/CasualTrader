"""
Trading API Router

提供交易、投資組合和績效相關的 API。
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from common.logger import logger
from service.agents_service import (
    AgentNotFoundError,
    AgentsService,
)
from api.config import get_db_session
from api.holiday_client import TaiwanHolidayAPIClient
from api.mcp_client import create_mcp_market_client
from dotenv import load_dotenv

load_dotenv(override=True)

# 掠過市場檢查（用於測試環境）
SKIP_MARKET_CHECK = os.getenv("SKIP_MARKET_CHECK", False) == "true"

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
    description="獲取台灣股市開盤狀態（基於交易日檢查）",
)
async def get_market_status():
    """
    取得市場狀態

    檢查今日是否為股市交易日（非週末且非國定假日）

    Returns:
        市場狀態資訊，包含：
        - is_trading_day: 是否為交易日
        - is_open: 市場是否開盤（簡化版，僅判斷交易日）
        - date: 查詢日期
        - is_weekend: 是否為週末
        - is_holiday: 是否為國定假日
        - holiday_name: 節假日名稱（如果是節假日）

    Note:
        此端點使用台灣節假日API進行交易日判斷
        市場開盤時間為週一至週五 09:00-13:30（不含國定假日）
    """
    try:
        async with TaiwanHolidayAPIClient() as holiday_client:
            # 取得今日日期
            today = datetime.now().date()

            # 檢查是否為週末
            is_weekend = holiday_client.is_weekend(today)

            # 檢查是否為國定假日
            holiday_info = await holiday_client.get_holiday_info(today)
            is_holiday = holiday_info is not None and holiday_info.is_holiday
            holiday_name = holiday_info.name if holiday_info else None

            # 檢查是否為交易日
            is_trading = SKIP_MARKET_CHECK or await holiday_client.is_trading_day(today)

            # 簡化版開盤判斷：交易日即視為開盤
            # 實際應該還要檢查當前時間是否在 09:00-13:30 之間
            current_time = datetime.now().time()
            market_open_time = datetime.strptime("09:00", "%H:%M").time()
            market_close_time = datetime.strptime("13:30", "%H:%M").time()

            is_open = SKIP_MARKET_CHECK or (
                is_trading
                and current_time >= market_open_time
                and current_time <= market_close_time
            )

            return {
                "is_trading_day": is_trading,
                "is_open": is_open,
                "date": today.isoformat(),
                "current_time": current_time.strftime("%H:%M:%S"),
                "market_hours": "09:00-13:30",
                "is_weekend": is_weekend,
                "is_holiday": is_holiday,
                "holiday_name": holiday_name,
            }

    except Exception as e:
        logger.error(f"Failed to get market status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"無法取得市場狀態: {str(e)}",
        ) from e


@router.get(
    "/market/quote/{ticker}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="取得股票報價",
    description="獲取股票即時報價（透過 MCP Server）",
)
async def get_stock_quote(ticker: str):
    """
    取得股票報價

    Args:
        ticker: 股票代碼或公司名稱（如 "2330" 或 "台積電"）

    Returns:
        股票報價資訊，包含：
        - symbol: 股票代碼
        - company_name: 公司名稱
        - current_price: 當前價格
        - change: 漲跌金額
        - change_percent: 漲跌幅百分比
        - volume: 成交量
        - high/low/open: 最高/最低/開盤價
        - previous_close: 昨收價
        - last_update: 最後更新時間

    Note:
        此端點整合 casual-market MCP Server 獲取即時股票報價
    """
    try:
        logger.info(f"Getting stock quote for: {ticker}")

        # 使用上下文管理器確保連接正確關閉
        async with create_mcp_market_client() as mcp_client:
            result = await mcp_client.get_stock_price(ticker)

            # 檢查結果是否成功
            if not result.get("success", False):
                error_msg = result.get("error", "未知錯誤")
                logger.warning(f"MCP 工具返回錯誤: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無法取得股票報價: {error_msg}",
                )

            return result

    except HTTPException:
        # 重新拋出 HTTP 異常
        raise

    except Exception as e:
        logger.error(f"Failed to get stock quote for {ticker}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"無法取得股票報價: {str(e)}",
        ) from e


@router.get(
    "/market/indices",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="取得市場指數",
    description="獲取市場指數資訊（透過 MCP Server）",
)
async def get_market_indices(category: str = "major", count: int = 20, format: str = "detailed"):
    """
    取得市場指數

    Args:
        category: 指數類別
            - "major": 主要指數（加權指數、櫃買指數等）
            - "sector": 類股指數
            - "theme": 主題指數
            - "all": 所有指數
        count: 顯示數量（預設 20）
        format: 顯示格式
            - "detailed": 詳細資訊
            - "simple": 簡易資訊

    Returns:
        市場指數資訊列表，每項包含：
        - index_name: 指數名稱
        - current_value: 當前指數值
        - change: 漲跌點數
        - change_percent: 漲跌幅 (%)
        - volume: 成交量
        - last_update: 最後更新時間

    Note:
        此端點整合 casual-market MCP Server 獲取市場指數
    """
    try:
        logger.info(f"Getting market indices (category={category}, count={count}, format={format})")

        # 使用上下文管理器確保連接正確關閉
        async with create_mcp_market_client() as mcp_client:
            result = await mcp_client.get_market_indices(
                category=category, count=count, format=format
            )

            # 檢查結果是否成功
            if not result.get("success", False):
                error_msg = result.get("error", "未知錯誤")
                logger.warning(f"MCP 工具返回錯誤: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無法取得市場指數: {error_msg}",
                )

            return result

    except HTTPException:
        # 重新拋出 HTTP 異常
        raise

    except Exception as e:
        logger.error(f"Failed to get market indices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"無法取得市場指數: {str(e)}",
        ) from e
