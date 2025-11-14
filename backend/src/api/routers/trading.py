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
from service.dashboard_service import DashboardService
from schemas.dashboard import DashboardData
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
                    "total_cost": float(holding.total_cost),
                    "market_value": float(holding.total_cost),
                    "unrealized_pnl": 0.0,  # 需要實時價格才能計算
                    "unrealized_pnl_percent": 0.0,  # 需要實時價格才能計算
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
                "total_cost": float(holding.total_cost),
                "market_value": float(holding.total_cost),
                "cost_basis": float(holding.total_cost),
                "unrealized_pnl": 0.0,  # 需要實時價格才能計算
                "unrealized_pnl_percent": 0.0,  # 需要實時價格才能計算
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
                "action": _get_enum_value(tx.action),
                "quantity": tx.quantity,
                "price": float(tx.price),
                "total_amount": float(tx.total_amount),
                "commission": float(tx.commission) if tx.commission else 0.0,
                "net_amount": float(tx.total_amount)
                + (float(tx.commission) if tx.commission else 0.0),
                "status": _get_enum_value(tx.status),
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


# ==========================================
# Performance Endpoints
# ==========================================


def _get_action_value(action: Any) -> str:
    """輔助函數：獲取交易動作值

    處理 action 既可能是 Enum 也可能是字符串的情況

    Args:
        action: 交易動作，可能是 Enum 或字符串

    Returns:
        交易動作的字符串值
    """
    return action.value if hasattr(action, "value") else str(action)


def _get_enum_value(enum_obj: Any) -> str:
    """輔助函數：獲取 Enum 值

    處理物件既可能是 Enum 也可能是字符串的情況

    Args:
        enum_obj: Enum 物件或字符串

    Returns:
        Enum 的字符串值
    """
    return enum_obj.value if hasattr(enum_obj, "value") else str(enum_obj)


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
        buy_trades = sum(1 for tx in transactions if _get_action_value(tx.action) == "BUY")
        sell_trades = sum(1 for tx in transactions if _get_action_value(tx.action) == "SELL")

        # 計算實現損益（根據已完成交易）
        # 買入時為負（支出），賣出時為正（收入）
        realized_pnl = 0.0
        for tx in transactions:
            if _get_action_value(tx.action) == "SELL":
                # 賣出：收入 - 原始成本
                buy_tx = next(
                    (
                        t
                        for t in transactions
                        if _get_enum_value(t.status) == "EXECUTED"
                        and _get_action_value(t.action) == "BUY"
                        and t.ticker == tx.ticker
                    ),
                    None,
                )
                if buy_tx:
                    realized_pnl += float(tx.total_amount) - (float(buy_tx.price) * tx.quantity)

        # 計算未實現損益
        # 未實現損益 = 當前持股總市值 - 持股成本基礎
        # 由於沒有實時價格，設置為 0（應透過 AgentPerformance 表存儲歷史數據）
        unrealized_pnl = 0.0

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


@router.get(
    "/agents/{agent_id}/performance-history",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="取得績效歷史",
    description="獲取 Agent 的歷史性能數據用於圖表展示",
)
async def get_performance_history(
    agent_id: str,
    limit: int = 30,
    order: str = "desc",
    agents_service: AgentsService = Depends(get_agents_service),
):
    """
    取得績效歷史 - 圖表展示用（已轉換格式）

    用於前端圖表展示 Agent 的資產淨值變化趨勢。
    ⚠️ 重要: 所有數據已在後端完成格式轉換，前端可直接使用。

    Args:
        agent_id: Agent ID
        limit: 返回的記錄數量，最多 365（預設 30）
        order: 排序順序，'asc'（舊到新）或 'desc'（新到舊，預設）
        agents_service: AgentsService 實例

    Returns:
        性能歷史記錄列表（已格式化），每條包含：
        - date: 記錄日期 (ISO 8601)
        - portfolio_value: 投資組合總資產 (TWD) [欄位已重命名]
        - total_return: 累計回報率 (%) [已轉為百分比]
        - win_rate: 勝率 (%) [已轉為百分比]
        - daily_return: 日回報率 (%) [已轉為百分比]
        - max_drawdown: 最大回撤 (%) [已轉為百分比]
        - sharpe_ratio: 風險調整後的報酬 [進階指標]
        - sortino_ratio: 下行風險調整比率 [進階指標]
        - calmar_ratio: 報酬/最大回撤比值 [進階指標]
        - cash_balance: 現金餘額 (TWD)
        - realized_pnl: 已實現損益 (TWD)
        - unrealized_pnl: 未實現損益 (TWD)
        - total_trades: 總交易數
        - winning_trades: 真實獲利交易數 [使用 FIFO 配對邏輯]

    Raises:
        404: Agent 不存在
        400: 參數無效
        500: 查詢失敗
    """
    try:
        # 驗證參數
        if limit < 1 or limit > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit must be between 1 and 365",
            )

        if order not in ("asc", "desc"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="order must be 'asc' or 'desc'",
            )

        logger.info(
            f"Getting performance history for agent: {agent_id}, limit={limit}, order={order}"
        )

        # 獲取性能歷史
        history = await agents_service.get_performance_history(agent_id, limit=limit, order=order)

        logger.debug(f"Retrieved {len(history)} performance records for agent {agent_id}")

        # 轉換為圖表格式（後端集中處理原則）
        # 1. 欄位重新命名: total_value -> portfolio_value
        # 2. 數值轉換: 小數 -> 百分比 (0.05 -> 5.0)
        # 3. 進階風險指標包含
        formatted_history = []
        for record in history:
            formatted_record = {
                "date": record["date"],
                "portfolio_value": float(record["total_value"]),  # 欄位重新命名
                "total_return": (
                    float(record["total_return"]) * 100  # 轉為百分比
                    if record["total_return"] is not None
                    else None
                ),
                "win_rate": (
                    float(record["win_rate"])  # 已經是百分比格式
                    if record["win_rate"] is not None
                    else None
                ),
                "daily_return": (
                    float(record["daily_return"]) * 100  # 轉為百分比
                    if record["daily_return"] is not None
                    else None
                ),
                "max_drawdown": (
                    float(record["max_drawdown"]) * 100  # 轉為百分比
                    if record["max_drawdown"] is not None
                    else None
                ),
                # 進階風險指標
                "sharpe_ratio": (
                    float(record["sharpe_ratio"])  # 已是小數格式
                    if record.get("sharpe_ratio") is not None
                    else None
                ),
                "sortino_ratio": (
                    float(record["sortino_ratio"])  # 已是小數格式
                    if record.get("sortino_ratio") is not None
                    else None
                ),
                "calmar_ratio": (
                    float(record["calmar_ratio"])  # 已是小數格式
                    if record.get("calmar_ratio") is not None
                    else None
                ),
                # 保留原始欄位用於其他用途
                "cash_balance": float(record["cash_balance"]),
                "realized_pnl": float(record["realized_pnl"]),
                "unrealized_pnl": float(record["unrealized_pnl"]),
                "total_trades": record["total_trades"],
                "winning_trades": record["winning_trades_correct"],  # 使用真實獲利交易數
            }
            formatted_history.append(formatted_record)

        return formatted_history

    except HTTPException:
        raise

    except AgentNotFoundError as e:
        logger.warning(f"Agent not found: {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        ) from e

    except Exception as e:
        logger.error(f"Failed to get performance history for agent {agent_id}: {e}")
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
async def get_market_indices():
    """
    取得市場指數

    Returns:
        市場指數資訊，包含：
        - 日期: 資料日期
        - 指數: 指數名稱
        - 收盤指數: 當前指數值
        - 漲跌: 漲跌符號
        - 漲跌點數: 漲跌點數
        - 漲跌百分比: 漲跌幅 (%)
        - 特殊處理註記: 特殊情況說明

    Note:
        此端點整合 casual-market MCP Server 獲取市場指數
    """
    try:
        logger.info("Getting market indices")

        # 使用上下文管理器確保連接正確關閉
        async with create_mcp_market_client() as mcp_client:
            result = await mcp_client.get_market_indices()

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
