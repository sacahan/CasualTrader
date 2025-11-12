"""
Dashboard Service

提供儀表板數據聚合和計算功能
"""

from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AgentPerformance, Transaction
from service.dashboard_utils import get_date_range
from schemas.dashboard import (
    DashboardData,
    KPIMetrics,
    RiskMetrics,
    PerformanceDataPoint,
    TradeStats,
)
from common.logger import logger


# ==========================================
# Dashboard Service
# ==========================================


class DashboardService:
    """
    儀表板服務

    提供性能儀表板的數據聚合和計算
    """

    def __init__(self, session: AsyncSession):
        """
        初始化儀表板服務

        Args:
            session: SQLAlchemy 異步 Session
        """
        self.session = session

    async def get_dashboard_data(
        self,
        agent_id: str,
        time_period: str = "1M",
    ) -> DashboardData:
        """
        獲取完整儀表板數據

        Args:
            agent_id: Agent ID
            time_period: 時間段 ('1D', '1W', '1M', '3M', '1Y', 'all')

        Returns:
            完整的儀表板數據

        Raises:
            ValueError: 無效的時間段或數據不足
        """
        # 驗證時間段
        try:
            start_date, end_date = get_date_range(time_period)
        except ValueError as e:
            logger.error(f"無效的時間段: {time_period}, 錯誤: {e}")
            raise

        logger.info(
            f"獲取 Agent {agent_id} 的儀表板數據, 時間段: {time_period} "
            f"({start_date} 到 {end_date})"
        )

        try:
            # 1. 獲取性能歷史數據
            performance_records = await self._get_performance_records(
                agent_id, start_date, end_date
            )

            if not performance_records:
                logger.warning(f"Agent {agent_id} 沒有性能數據")
                raise ValueError("沒有足夠的性能數據")

            # 2. 計算 KPI 指標
            kpi_metrics = self._calculate_kpi_metrics(performance_records)

            # 3. 提取風險指標
            risk_metrics = self._extract_risk_metrics(performance_records)

            # 4. 準備性能數據點
            performance_data = self._prepare_performance_data(performance_records)

            # 5. 計算交易統計
            trade_stats = await self._calculate_trade_stats(agent_id, start_date, end_date)

            # 組合完整數據
            dashboard_data = DashboardData(
                agent_id=agent_id,
                time_period=time_period,
                period_start=start_date,
                period_end=end_date,
                kpi_metrics=kpi_metrics,
                risk_metrics=risk_metrics,
                performance_data=performance_data,
                trade_stats=trade_stats,
            )

            logger.info(f"成功獲取 Agent {agent_id} 的儀表板數據")
            return dashboard_data

        except Exception as e:
            logger.error(f"獲取儀表板數據失敗: {e}", exc_info=True)
            raise

    async def _get_performance_records(
        self,
        agent_id: str,
        start_date: date,
        end_date: date,
    ) -> list[AgentPerformance]:
        """
        獲取指定時間段的性能記錄

        Args:
            agent_id: Agent ID
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            性能記錄列表
        """
        stmt = (
            select(AgentPerformance)
            .where(
                and_(
                    AgentPerformance.agent_id == agent_id,
                    AgentPerformance.date >= start_date,
                    AgentPerformance.date <= end_date,
                )
            )
            .order_by(AgentPerformance.date)
        )

        result = await self.session.execute(stmt)
        records = list(result.scalars().all())

        logger.debug(f"獲取 {len(records)} 條性能記錄")
        return records

    def _calculate_kpi_metrics(
        self,
        performance_records: list[AgentPerformance],
    ) -> KPIMetrics:
        """
        計算 KPI 指標

        Args:
            performance_records: 性能記錄列表

        Returns:
            KPI 指標
        """
        if not performance_records:
            return KPIMetrics(
                net_value_growth=0.0,
                total_return=0.0,
                win_rate=0.0,
                max_drawdown=0.0,
            )

        first_record = performance_records[0]
        last_record = performance_records[-1]

        # 1. 淨值增長率
        initial_value = float(first_record.total_value)
        final_value = float(last_record.total_value)
        net_value_growth = (
            ((final_value - initial_value) / initial_value * 100) if initial_value > 0 else 0.0
        )

        # 2. 總報酬率 (如果有記錄的話，使用最後一筆的 total_return)
        total_return = float(last_record.total_return or 0.0)

        # 3. 勝率 (從最後一筆記錄的 win_rate)
        win_rate = float(last_record.win_rate or 0.0)

        # 4. 最大回撤 (從最後一筆記錄的 max_drawdown)
        max_drawdown = float(last_record.max_drawdown or 0.0)

        kpi_metrics = KPIMetrics(
            net_value_growth=round(net_value_growth, 2),
            total_return=round(total_return, 2),
            win_rate=round(win_rate, 2),
            max_drawdown=round(max_drawdown, 2),
        )

        logger.debug(f"計算的 KPI 指標: {kpi_metrics}")
        return kpi_metrics

    def _extract_risk_metrics(
        self,
        performance_records: list[AgentPerformance],
    ) -> RiskMetrics:
        """
        從性能記錄中提取風險指標

        Args:
            performance_records: 性能記錄列表

        Returns:
            風險指標
        """
        if not performance_records:
            return RiskMetrics()

        # 取最後一筆記錄的風險指標
        last_record = performance_records[-1]

        risk_metrics = RiskMetrics(
            sharpe_ratio=round(float(last_record.sharpe_ratio), 2)
            if last_record.sharpe_ratio
            else None,
            sortino_ratio=round(float(last_record.sortino_ratio), 2)
            if last_record.sortino_ratio
            else None,
            calmar_ratio=round(float(last_record.calmar_ratio), 2)
            if last_record.calmar_ratio
            else None,
            information_ratio=None,  # 未來可添加
        )

        logger.debug(f"提取的風險指標: {risk_metrics}")
        return risk_metrics

    def _prepare_performance_data(
        self,
        performance_records: list[AgentPerformance],
    ) -> list[PerformanceDataPoint]:
        """
        準備性能數據點 (用於圖表)

        Args:
            performance_records: 性能記錄列表

        Returns:
            性能數據點列表
        """
        data_points = []

        for record in performance_records:
            data_point = PerformanceDataPoint(
                date=record.date,
                value=float(record.total_value),
                daily_return=float(record.daily_return or 0.0),
            )
            data_points.append(data_point)

        logger.debug(f"準備 {len(data_points)} 個性能數據點")
        return data_points

    async def _calculate_trade_stats(
        self,
        agent_id: str,
        start_date: date,
        end_date: date,
    ) -> TradeStats:
        """
        計算交易統計

        Args:
            agent_id: Agent ID
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            交易統計
        """
        # 查詢時間段內的交易
        stmt = select(Transaction).where(
            and_(
                Transaction.agent_id == agent_id,
                Transaction.created_at >= datetime.combine(start_date, datetime.min.time()),
                Transaction.created_at <= datetime.combine(end_date, datetime.max.time()),
            )
        )

        result = await self.session.execute(stmt)
        transactions = result.scalars().all()

        total_trades = len(transactions)

        if total_trades == 0:
            return TradeStats(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                avg_return=0.0,
            )

        # 計算獲利和虧損交易
        winning_trades = sum(1 for t in transactions if t.pnl is not None and float(t.pnl) > 0)
        losing_trades = total_trades - winning_trades

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

        # 計算平均收益
        total_pnl = sum(float(t.pnl) if t.pnl is not None else 0.0 for t in transactions)
        avg_return = (total_pnl / total_trades) if total_trades > 0 else 0.0

        trade_stats = TradeStats(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            avg_return=round(avg_return, 2),
        )

        logger.debug(f"計算的交易統計: {trade_stats}")
        return trade_stats
