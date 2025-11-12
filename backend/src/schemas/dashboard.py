"""
Dashboard API Schemas

定義性能儀表板的數據結構和驗證
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


# ==========================================
# KPI Metrics
# ==========================================


class KPIMetrics(BaseModel):
    """KPI 快速指標"""

    net_value_growth: float = Field(..., description="淨值增長率 (%)", example=5.2)
    total_return: float = Field(..., description="總報酬率 (%)", example=12.5)
    win_rate: float = Field(..., description="勝率 (%)", example=70.5)
    max_drawdown: float = Field(..., description="最大回撤 (%)", example=-8.5)

    class Config:
        json_schema_extra = {
            "example": {
                "net_value_growth": 5.2,
                "total_return": 12.5,
                "win_rate": 70.5,
                "max_drawdown": -8.5,
            }
        }


# ==========================================
# Risk Metrics
# ==========================================


class RiskMetrics(BaseModel):
    """風險指標詳情"""

    sharpe_ratio: Optional[float] = Field(
        None, description="Sharpe Ratio (風險調整後的報酬)", example=1.25
    )
    sortino_ratio: Optional[float] = Field(
        None, description="Sortino Ratio (只考慮下行風險)", example=1.50
    )
    calmar_ratio: Optional[float] = Field(
        None, description="Calmar Ratio (年化報酬/最大回撤)", example=0.75
    )
    information_ratio: Optional[float] = Field(
        None, description="Information Ratio (相對於基準的超額報酬)", example=2.30
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sharpe_ratio": 1.25,
                "sortino_ratio": 1.50,
                "calmar_ratio": 0.75,
                "information_ratio": 2.30,
            }
        }


# ==========================================
# Performance Data Points
# ==========================================


class PerformanceDataPoint(BaseModel):
    """績效數據點"""

    date: date = Field(..., description="日期", example="2025-10-12")
    value: float = Field(..., description="投資組合價值", example=1000000.0)
    daily_return: float = Field(..., description="每日報酬率 (%)", example=0.52)

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-10-12",
                "value": 1000000.0,
                "daily_return": 0.52,
            }
        }


# ==========================================
# Trade Statistics
# ==========================================


class TradeStats(BaseModel):
    """交易統計"""

    total_trades: int = Field(..., description="總交易次數", example=42)
    winning_trades: int = Field(..., description="獲利交易次數", example=28)
    losing_trades: int = Field(..., description="虧損交易次數", example=14)
    win_rate: float = Field(..., description="勝率 (%)", example=66.7)
    avg_return: float = Field(..., description="平均單筆收益 (%)", example=2.5)

    class Config:
        json_schema_extra = {
            "example": {
                "total_trades": 42,
                "winning_trades": 28,
                "losing_trades": 14,
                "win_rate": 66.7,
                "avg_return": 2.5,
            }
        }


# ==========================================
# Dashboard Response
# ==========================================


class DashboardData(BaseModel):
    """完整儀表板數據"""

    agent_id: str = Field(
        ..., description="Agent ID", example="550e8400-e29b-41d4-a716-446655440000"
    )
    time_period: str = Field(..., description="時間段 (1D|1W|1M|3M|1Y|all)", example="1M")
    period_start: date = Field(..., description="時間段開始日期", example="2025-10-12")
    period_end: date = Field(..., description="時間段結束日期", example="2025-11-12")

    # 各個指標
    kpi_metrics: KPIMetrics = Field(..., description="KPI 快速指標")
    risk_metrics: RiskMetrics = Field(..., description="風險指標詳情")
    performance_data: list[PerformanceDataPoint] = Field(..., description="績效趨勢數據")
    trade_stats: TradeStats = Field(..., description="交易統計")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "550e8400-e29b-41d4-a716-446655440000",
                "time_period": "1M",
                "period_start": "2025-10-12",
                "period_end": "2025-11-12",
                "kpi_metrics": {
                    "net_value_growth": 5.2,
                    "total_return": 12.5,
                    "win_rate": 70.5,
                    "max_drawdown": -8.5,
                },
                "risk_metrics": {
                    "sharpe_ratio": 1.25,
                    "sortino_ratio": 1.50,
                    "calmar_ratio": 0.75,
                    "information_ratio": 2.30,
                },
                "performance_data": [
                    {"date": "2025-10-12", "value": 1000000.0, "daily_return": 0.0},
                    {"date": "2025-10-13", "value": 1005200.0, "daily_return": 0.52},
                ],
                "trade_stats": {
                    "total_trades": 42,
                    "winning_trades": 28,
                    "losing_trades": 14,
                    "win_rate": 66.7,
                    "avg_return": 2.5,
                },
            }
        }
