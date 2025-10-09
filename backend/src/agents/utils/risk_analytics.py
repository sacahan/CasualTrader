"""
風險計算模組
提供投資組合風險評估相關計算
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd


class RiskCalculator:
    """風險計算器"""

    def __init__(self):
        self.logger = logging.getLogger("risk_calculator")

    def calculate_volatility(
        self, returns: list[float] | pd.Series, annualize: bool = True
    ) -> float:
        """
        計算波動率 (標準差)

        Args:
            returns: 報酬率序列
            annualize: 是否年化 (預設 True)

        Returns:
            波動率
        """
        if isinstance(returns, list):
            returns = pd.Series(returns)

        volatility = returns.std()

        if annualize:
            # 假設每年 252 個交易日
            volatility = volatility * np.sqrt(252)

        return float(volatility)

    def calculate_returns(self, prices: list[float] | pd.Series) -> pd.Series | list[float]:
        """
        計算報酬率序列

        Args:
            prices: 價格序列

        Returns:
            報酬率序列
        """
        if isinstance(prices, list):
            prices = pd.Series(prices)

        returns = prices.pct_change().dropna()
        return returns

    def calculate_beta(
        self,
        asset_returns: list[float] | pd.Series,
        market_returns: list[float] | pd.Series,
    ) -> float:
        """
        計算 Beta 值

        Args:
            asset_returns: 資產報酬率
            market_returns: 市場報酬率

        Returns:
            Beta 值
        """
        if isinstance(asset_returns, list):
            asset_returns = pd.Series(asset_returns)
        if isinstance(market_returns, list):
            market_returns = pd.Series(market_returns)

        # 計算協方差矩陣
        covariance = asset_returns.cov(market_returns)
        market_variance = market_returns.var()

        beta = covariance / market_variance if market_variance != 0 else 1.0
        return float(beta)

    def calculate_var(
        self, returns: list[float] | pd.Series, confidence_level: float = 0.95
    ) -> float:
        """
        計算風險值 (Value at Risk)

        Args:
            returns: 報酬率序列
            confidence_level: 信賴水準 (預設 0.95)

        Returns:
            VaR 值 (負數表示損失)
        """
        if isinstance(returns, list):
            returns = pd.Series(returns)

        var = returns.quantile(1 - confidence_level)
        return float(var)

    def calculate_max_drawdown(self, prices: list[float] | pd.Series) -> float:
        """
        計算最大回撤

        Args:
            prices: 價格序列

        Returns:
            最大回撤 (負數)
        """
        if isinstance(prices, list):
            prices = pd.Series(prices)

        # 計算累積最高值
        cumulative_max = prices.cummax()

        # 計算回撤
        drawdown = (prices - cumulative_max) / cumulative_max

        # 最大回撤
        max_dd = drawdown.min()
        return float(max_dd)

    def calculate_sharpe_ratio(
        self,
        returns: list[float] | pd.Series,
        risk_free_rate: float = 0.01,
        annualize: bool = True,
    ) -> float:
        """
        計算夏普比率

        Args:
            returns: 報酬率序列
            risk_free_rate: 無風險利率 (年化)
            annualize: 是否年化 (預設 True)

        Returns:
            夏普比率
        """
        if isinstance(returns, list):
            returns = pd.Series(returns)

        # 計算超額報酬
        excess_returns = returns - (risk_free_rate / 252)  # 日化無風險利率

        mean_excess_return = excess_returns.mean()
        std_excess_return = excess_returns.std()

        if std_excess_return == 0:
            return 0.0

        sharpe = mean_excess_return / std_excess_return

        if annualize:
            sharpe = sharpe * np.sqrt(252)

        return float(sharpe)

    def calculate_sortino_ratio(
        self,
        returns: list[float] | pd.Series,
        risk_free_rate: float = 0.01,
        annualize: bool = True,
    ) -> float:
        """
        計算索提諾比率 (只考慮下檔風險)

        Args:
            returns: 報酬率序列
            risk_free_rate: 無風險利率 (年化)
            annualize: 是否年化 (預設 True)

        Returns:
            索提諾比率
        """
        if isinstance(returns, list):
            returns = pd.Series(returns)

        # 計算超額報酬
        excess_returns = returns - (risk_free_rate / 252)

        mean_excess_return = excess_returns.mean()

        # 下檔偏差 (只計算負報酬的標準差)
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = downside_returns.std()

        if downside_std == 0:
            return 0.0

        sortino = mean_excess_return / downside_std

        if annualize:
            sortino = sortino * np.sqrt(252)

        return float(sortino)

    def calculate_correlation_matrix(
        self, returns_dict: dict[str, list[float] | pd.Series]
    ) -> dict[str, dict[str, float]]:
        """
        計算相關性矩陣

        Args:
            returns_dict: 各資產的報酬率字典 {symbol: returns}

        Returns:
            相關性矩陣
        """
        # 轉換為 DataFrame
        df = pd.DataFrame(returns_dict)

        # 計算相關性矩陣
        corr_matrix = df.corr()

        # 轉換為字典格式
        result = {}
        for symbol1 in corr_matrix.index:
            result[symbol1] = {}
            for symbol2 in corr_matrix.columns:
                result[symbol1][symbol2] = float(corr_matrix.loc[symbol1, symbol2])

        return result

    def calculate_portfolio_volatility(
        self,
        weights: list[float],
        returns_dict: dict[str, list[float] | pd.Series],
    ) -> float:
        """
        計算投資組合波動率 (考慮相關性)

        Args:
            weights: 各資產權重
            returns_dict: 各資產的報酬率字典

        Returns:
            投資組合波動率
        """
        # 轉換為 DataFrame
        df = pd.DataFrame(returns_dict)

        # 計算協方差矩陣
        cov_matrix = df.cov()

        # 轉換權重為 numpy 陣列
        weights_array = np.array(weights)

        # 投資組合變異數 = w^T * Cov * w
        portfolio_variance = np.dot(weights_array, np.dot(cov_matrix, weights_array))

        # 投資組合波動率 = sqrt(變異數)
        portfolio_volatility = np.sqrt(portfolio_variance)

        # 年化
        annualized_volatility = portfolio_volatility * np.sqrt(252)

        return float(annualized_volatility)

    def calculate_diversification_ratio(
        self,
        weights: list[float],
        individual_volatilities: list[float],
        portfolio_volatility: float,
    ) -> float:
        """
        計算分散化比率

        Args:
            weights: 各資產權重
            individual_volatilities: 各資產個別波動率
            portfolio_volatility: 投資組合波動率

        Returns:
            分散化比率 (>1 表示良好分散)
        """
        # 加權平均波動率
        weighted_avg_vol = sum(
            w * vol for w, vol in zip(weights, individual_volatilities, strict=False)
        )

        if portfolio_volatility == 0:
            return 1.0

        diversification_ratio = weighted_avg_vol / portfolio_volatility
        return float(diversification_ratio)

    def calculate_concentration_hhi(self, weights: list[float]) -> float:
        """
        計算集中度 (HHI 指數)

        Args:
            weights: 各資產權重

        Returns:
            HHI 指數 (0-1,越高越集中)
        """
        hhi = sum(w**2 for w in weights)
        return float(hhi)


class SentimentAnalyzer:
    """情緒分析器 (基礎版)"""

    def __init__(self):
        self.logger = logging.getLogger("sentiment_analyzer")

    def analyze_price_momentum(
        self, prices: list[float] | pd.Series, period: int = 20
    ) -> dict[str, Any]:
        """
        分析價格動能

        Args:
            prices: 價格序列
            period: 分析週期

        Returns:
            動能分析結果
        """
        if isinstance(prices, list):
            prices = pd.Series(prices)

        if len(prices) < period:
            return {
                "momentum_score": 50.0,
                "trend": "neutral",
                "strength": "weak",
            }

        # 計算報酬率
        period_return = (prices.iloc[-1] - prices.iloc[-period]) / prices.iloc[-period]

        # 計算短期趨勢 (最近5天)
        short_term_return = (prices.iloc[-1] - prices.iloc[-5]) / prices.iloc[-5]

        # 轉換為情緒分數 (0-100)
        momentum_score = 50 + (period_return * 200)  # ±50% 對應 0-100
        momentum_score = max(0, min(100, momentum_score))

        # 判斷趨勢
        if period_return > 0.05:
            trend = "bullish"
        elif period_return < -0.05:
            trend = "bearish"
        else:
            trend = "neutral"

        # 判斷強度
        if abs(period_return) > 0.10:
            strength = "strong"
        elif abs(period_return) > 0.05:
            strength = "moderate"
        else:
            strength = "weak"

        return {
            "momentum_score": float(momentum_score),
            "period_return": float(period_return),
            "short_term_return": float(short_term_return),
            "trend": trend,
            "strength": strength,
        }

    def analyze_volume_sentiment(
        self, volumes: list[float] | pd.Series, prices: list[float] | pd.Series
    ) -> dict[str, Any]:
        """
        分析成交量情緒

        Args:
            volumes: 成交量序列
            prices: 價格序列

        Returns:
            成交量情緒分析
        """
        if isinstance(volumes, list):
            volumes = pd.Series(volumes)
        if isinstance(prices, list):
            prices = pd.Series(prices)

        # 平均成交量
        avg_volume = volumes.mean()
        current_volume = volumes.iloc[-1]

        # 成交量比率
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        # 價格變化
        price_change = prices.pct_change().iloc[-1]

        # 量價配合度分析
        if volume_ratio > 1.5 and price_change > 0:
            sentiment = "bullish_strong"
        elif volume_ratio > 1.5 and price_change < 0:
            sentiment = "bearish_strong"
        elif volume_ratio < 0.7:
            sentiment = "low_interest"
        else:
            sentiment = "neutral"

        return {
            "volume_ratio": float(volume_ratio),
            "average_volume": float(avg_volume),
            "current_volume": float(current_volume),
            "sentiment": sentiment,
        }


# 全域單例
_risk_calculator: RiskCalculator | None = None
_sentiment_analyzer: SentimentAnalyzer | None = None


def get_risk_calculator() -> RiskCalculator:
    """取得風險計算器單例"""
    global _risk_calculator
    if _risk_calculator is None:
        _risk_calculator = RiskCalculator()
    return _risk_calculator


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """取得情緒分析器單例"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer
