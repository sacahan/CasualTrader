"""
投資組合查詢功能
提供投資組合的各種查詢和分析功能
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel


class Position(BaseModel):
    """持倉資訊"""

    symbol: str
    quantity: int
    average_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    weight: float  # 在投資組合中的權重
    sector: str | None = None
    purchase_date: datetime | None = None


class PortfolioSummary(BaseModel):
    """投資組合摘要"""

    total_value: float
    cash_balance: float
    invested_amount: float
    total_unrealized_pnl: float
    total_unrealized_pnl_percent: float
    total_realized_pnl: float
    positions_count: int
    diversification_score: float
    last_updated: datetime


class PerformanceMetrics(BaseModel):
    """績效指標"""

    total_return: float
    annualized_return: float | None = None
    volatility: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    win_rate: float | None = None
    profit_factor: float | None = None


class PortfolioQueries:
    """
    投資組合查詢器
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("portfolio_queries")

    async def get_portfolio_summary(
        self, agent_id: str, include_history: bool = False
    ) -> PortfolioSummary:
        """
        獲取投資組合摘要

        Args:
            agent_id: Agent ID
            include_history: 是否包含歷史數據

        Returns:
            投資組合摘要
        """
        try:
            # 這裡將整合資料庫查詢
            # 目前返回模擬數據

            # 模擬投資組合數據
            positions_data = await self._get_positions_data(agent_id)
            cash_balance = await self._get_cash_balance(agent_id)

            total_market_value = sum(pos["market_value"] for pos in positions_data)
            total_value = total_market_value + cash_balance

            total_unrealized_pnl = sum(pos["unrealized_pnl"] for pos in positions_data)
            total_unrealized_pnl_percent = (
                total_unrealized_pnl / total_market_value
                if total_market_value > 0
                else 0
            )

            # 計算分散化分數
            diversification_score = self._calculate_diversification_score(
                positions_data
            )

            # 獲取已實現損益
            total_realized_pnl = await self._get_realized_pnl(agent_id)

            return PortfolioSummary(
                total_value=total_value,
                cash_balance=cash_balance,
                invested_amount=total_market_value,
                total_unrealized_pnl=total_unrealized_pnl,
                total_unrealized_pnl_percent=total_unrealized_pnl_percent,
                total_realized_pnl=total_realized_pnl,
                positions_count=len(positions_data),
                diversification_score=diversification_score,
                last_updated=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Failed to get portfolio summary: {e}")
            raise

    async def get_current_positions(self, agent_id: str) -> list[Position]:
        """
        獲取當前持倉

        Args:
            agent_id: Agent ID

        Returns:
            持倉列表
        """
        try:
            positions_data = await self._get_positions_data(agent_id)
            portfolio_value = await self._get_total_portfolio_value(agent_id)

            positions = []
            for pos_data in positions_data:
                position = Position(
                    symbol=pos_data["symbol"],
                    quantity=pos_data["quantity"],
                    average_price=pos_data["average_price"],
                    current_price=pos_data["current_price"],
                    market_value=pos_data["market_value"],
                    unrealized_pnl=pos_data["unrealized_pnl"],
                    unrealized_pnl_percent=pos_data["unrealized_pnl_percent"],
                    weight=pos_data["market_value"] / portfolio_value,
                    sector=pos_data.get("sector"),
                    purchase_date=pos_data.get("purchase_date"),
                )
                positions.append(position)

            # 按市值排序
            positions.sort(key=lambda x: x.market_value, reverse=True)

            return positions

        except Exception as e:
            self.logger.error(f"Failed to get current positions: {e}")
            raise

    async def get_position_by_symbol(
        self, agent_id: str, symbol: str
    ) -> Position | None:
        """
        根據股票代碼獲取特定持倉

        Args:
            agent_id: Agent ID
            symbol: 股票代碼

        Returns:
            持倉資訊或 None
        """
        positions = await self.get_current_positions(agent_id)
        return next((pos for pos in positions if pos.symbol == symbol), None)

    async def get_performance_metrics(
        self, agent_id: str, period_days: int = 30
    ) -> PerformanceMetrics:
        """
        獲取績效指標

        Args:
            agent_id: Agent ID
            period_days: 計算期間（天數）

        Returns:
            績效指標
        """
        try:
            # 獲取歷史數據
            historical_data = await self._get_historical_portfolio_data(
                agent_id, period_days
            )

            if not historical_data:
                return PerformanceMetrics(total_return=0.0)

            # 計算總報酬
            initial_value = historical_data[0]["total_value"]
            current_value = historical_data[-1]["total_value"]
            total_return = (current_value - initial_value) / initial_value

            # 計算年化報酬
            annualized_return = None
            if period_days >= 365:
                years = period_days / 365
                annualized_return = (current_value / initial_value) ** (1 / years) - 1

            # 計算波動率
            daily_returns = []
            for i in range(1, len(historical_data)):
                prev_value = historical_data[i - 1]["total_value"]
                curr_value = historical_data[i]["total_value"]
                daily_return = (curr_value - prev_value) / prev_value
                daily_returns.append(daily_return)

            volatility = None
            if len(daily_returns) > 1:
                import statistics

                volatility = statistics.stdev(daily_returns) * (252**0.5)  # 年化波動率

            # 計算最大回撤
            max_drawdown = self._calculate_max_drawdown(historical_data)

            # 計算夏普比率
            sharpe_ratio = None
            if volatility and volatility > 0:
                risk_free_rate = 0.01  # 假設無風險利率 1%
                excess_return = (annualized_return or total_return) - risk_free_rate
                sharpe_ratio = excess_return / volatility

            # 獲取交易統計
            trade_stats = await self._get_trade_statistics(agent_id, period_days)

            return PerformanceMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=trade_stats.get("win_rate"),
                profit_factor=trade_stats.get("profit_factor"),
            )

        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            raise

    async def get_sector_allocation(self, agent_id: str) -> dict[str, Any]:
        """
        獲取產業配置

        Args:
            agent_id: Agent ID

        Returns:
            產業配置資訊
        """
        try:
            positions = await self.get_current_positions(agent_id)

            sector_allocation = {}
            total_value = sum(pos.market_value for pos in positions)

            for position in positions:
                sector = position.sector or "其他"
                if sector not in sector_allocation:
                    sector_allocation[sector] = {
                        "value": 0.0,
                        "weight": 0.0,
                        "positions": [],
                    }

                sector_allocation[sector]["value"] += position.market_value
                sector_allocation[sector]["positions"].append(
                    {
                        "symbol": position.symbol,
                        "weight": position.weight,
                        "value": position.market_value,
                    }
                )

            # 計算權重
            for sector_data in sector_allocation.values():
                sector_data["weight"] = sector_data["value"] / total_value

            # 按權重排序
            sorted_sectors = dict(
                sorted(
                    sector_allocation.items(),
                    key=lambda x: x[1]["weight"],
                    reverse=True,
                )
            )

            return {
                "sector_allocation": sorted_sectors,
                "concentration_metrics": {
                    "max_sector_weight": max(
                        data["weight"] for data in sector_allocation.values()
                    ),
                    "top3_sectors_weight": sum(
                        data["weight"] for data in list(sorted_sectors.values())[:3]
                    ),
                    "herfindahl_index": sum(
                        data["weight"] ** 2 for data in sector_allocation.values()
                    ),
                },
                "diversification_score": 1
                - sum(data["weight"] ** 2 for data in sector_allocation.values()),
            }

        except Exception as e:
            self.logger.error(f"Failed to get sector allocation: {e}")
            raise

    async def get_top_positions(
        self, agent_id: str, limit: int = 10, sort_by: str = "market_value"
    ) -> list[Position]:
        """
        獲取前 N 大持倉

        Args:
            agent_id: Agent ID
            limit: 返回數量限制
            sort_by: 排序方式 ("market_value", "weight", "unrealized_pnl")

        Returns:
            前 N 大持倉
        """
        positions = await self.get_current_positions(agent_id)

        # 根據指定欄位排序
        sort_key = {
            "market_value": lambda x: x.market_value,
            "weight": lambda x: x.weight,
            "unrealized_pnl": lambda x: x.unrealized_pnl,
            "unrealized_pnl_percent": lambda x: x.unrealized_pnl_percent,
        }.get(sort_by, lambda x: x.market_value)

        sorted_positions = sorted(positions, key=sort_key, reverse=True)

        return sorted_positions[:limit]

    async def get_losers_winners(
        self, agent_id: str, limit: int = 5
    ) -> dict[str, list[Position]]:
        """
        獲取投資組合中的贏家和輸家

        Args:
            agent_id: Agent ID
            limit: 每類返回數量

        Returns:
            贏家和輸家列表
        """
        positions = await self.get_current_positions(agent_id)

        # 按未實現損益百分比排序
        sorted_by_pnl = sorted(
            positions, key=lambda x: x.unrealized_pnl_percent, reverse=True
        )

        winners = [pos for pos in sorted_by_pnl if pos.unrealized_pnl_percent > 0][
            :limit
        ]
        losers = [pos for pos in sorted_by_pnl if pos.unrealized_pnl_percent < 0][
            -limit:
        ]

        return {
            "winners": winners,
            "losers": losers,
            "neutral": [pos for pos in positions if pos.unrealized_pnl_percent == 0],
        }

    async def get_portfolio_risk_metrics(self, agent_id: str) -> dict[str, Any]:
        """
        獲取投資組合風險指標

        Args:
            agent_id: Agent ID

        Returns:
            風險指標
        """
        try:
            positions = await self.get_current_positions(agent_id)
            summary = await self.get_portfolio_summary(agent_id)

            # 集中度風險
            weights = [pos.weight for pos in positions]
            hhi = sum(w**2 for w in weights)  # HHI 指數

            # 單一最大持倉
            max_position_weight = max(weights) if weights else 0

            # 前五大持股集中度
            top5_weight = sum(sorted(weights, reverse=True)[:5])

            # 估算投資組合 Beta（簡化計算）
            portfolio_beta = 1.0  # 實際計算需要個股 Beta 數據

            return {
                "concentration_risk": {
                    "hhi_index": hhi,
                    "max_position_weight": max_position_weight,
                    "top5_concentration": top5_weight,
                    "effective_positions": 1 / hhi if hhi > 0 else 0,
                },
                "risk_measures": {
                    "portfolio_beta": portfolio_beta,
                    "cash_ratio": summary.cash_balance / summary.total_value,
                    "portfolio_volatility": 0.20,  # 估算值
                },
                "risk_warnings": self._generate_risk_warnings(
                    positions, summary, max_position_weight, hhi
                ),
            }

        except Exception as e:
            self.logger.error(f"Failed to get portfolio risk metrics: {e}")
            raise

    def _generate_risk_warnings(
        self,
        positions: list[Position],
        summary: PortfolioSummary,
        max_weight: float,
        hhi: float,
    ) -> list[str]:
        """生成風險警告"""
        warnings = []

        if max_weight > 0.15:
            warnings.append(f"單一持倉權重過高 ({max_weight:.1%})")

        if hhi > 0.2:
            warnings.append("投資組合集中度偏高")

        if summary.cash_balance / summary.total_value < 0.05:
            warnings.append("現金比例過低，流動性不足")

        if summary.positions_count < 5:
            warnings.append("持股檔數過少，缺乏分散化")

        negative_positions = [pos for pos in positions if pos.unrealized_pnl < 0]
        if len(negative_positions) / len(positions) > 0.6:
            warnings.append("超過 60% 持股處於虧損狀態")

        return warnings

    # 以下為私有方法，用於數據獲取（實際實作時會連接資料庫）

    async def _get_positions_data(self, agent_id: str) -> list[dict[str, Any]]:
        """獲取持倉數據（模擬）"""
        return [
            {
                "symbol": "2330",
                "quantity": 2000,
                "average_price": 580.0,
                "current_price": 595.0,
                "market_value": 1190000,
                "unrealized_pnl": 30000,
                "unrealized_pnl_percent": 0.0259,
                "sector": "半導體",
                "purchase_date": datetime.now() - timedelta(days=30),
            },
            {
                "symbol": "2317",
                "quantity": 1000,
                "average_price": 120.0,
                "current_price": 115.0,
                "market_value": 115000,
                "unrealized_pnl": -5000,
                "unrealized_pnl_percent": -0.0417,
                "sector": "電腦週邊",
                "purchase_date": datetime.now() - timedelta(days=15),
            },
        ]

    async def _get_cash_balance(self, agent_id: str) -> float:
        """獲取現金餘額（模擬）"""
        return 150000.0

    async def _get_total_portfolio_value(self, agent_id: str) -> float:
        """獲取投資組合總值（模擬）"""
        positions_data = await self._get_positions_data(agent_id)
        cash = await self._get_cash_balance(agent_id)
        return sum(pos["market_value"] for pos in positions_data) + cash

    async def _get_realized_pnl(self, agent_id: str) -> float:
        """獲取已實現損益（模擬）"""
        return 25000.0

    def _calculate_diversification_score(
        self, positions_data: list[dict[str, Any]]
    ) -> float:
        """計算分散化分數"""
        if not positions_data:
            return 0.0

        total_value = sum(pos["market_value"] for pos in positions_data)
        weights = [pos["market_value"] / total_value for pos in positions_data]

        # 使用 1 - HHI 作為分散化分數
        hhi = sum(w**2 for w in weights)
        return 1 - hhi

    async def _get_historical_portfolio_data(
        self, agent_id: str, period_days: int
    ) -> list[dict[str, Any]]:
        """獲取歷史投資組合數據（模擬）"""
        # 模擬歷史數據
        historical_data = []
        base_value = 1000000
        current_date = datetime.now() - timedelta(days=period_days)

        for i in range(period_days):
            # 模擬價格波動
            daily_return = (
                hash(str(current_date + timedelta(days=i))) % 100 - 50
            ) / 10000
            base_value *= 1 + daily_return

            historical_data.append(
                {
                    "date": current_date + timedelta(days=i),
                    "total_value": base_value,
                }
            )

        return historical_data

    def _calculate_max_drawdown(self, historical_data: list[dict[str, Any]]) -> float:
        """計算最大回撤"""
        if len(historical_data) < 2:
            return 0.0

        values = [data["total_value"] for data in historical_data]
        peak = values[0]
        max_drawdown = 0.0

        for value in values[1:]:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    async def _get_trade_statistics(
        self, agent_id: str, period_days: int
    ) -> dict[str, Any]:
        """獲取交易統計（模擬）"""
        return {
            "total_trades": 15,
            "winning_trades": 9,
            "losing_trades": 6,
            "win_rate": 0.6,
            "profit_factor": 1.5,
            "average_win": 8500,
            "average_loss": -3200,
        }
