"""
技術指標計算模組
提供常用技術指標的計算功能
使用 pandas 和 numpy 進行高效計算
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd


class TechnicalIndicatorCalculator:
    """技術指標計算器"""

    def __init__(self):
        self.logger = logging.getLogger("technical_indicators")

    def calculate_ma(self, prices: list[float] | pd.Series, period: int) -> list[float]:
        """
        計算移動平均線 (Moving Average)

        Args:
            prices: 價格序列
            period: 週期

        Returns:
            移動平均值列表
        """
        if isinstance(prices, list):
            prices = pd.Series(prices)

        ma = prices.rolling(window=period).mean()
        return ma.tolist()

    def calculate_ema(self, prices: list[float] | pd.Series, period: int) -> list[float]:
        """
        計算指數移動平均線 (Exponential Moving Average)

        Args:
            prices: 價格序列
            period: 週期

        Returns:
            指數移動平均值列表
        """
        if isinstance(prices, list):
            prices = pd.Series(prices)

        ema = prices.ewm(span=period, adjust=False).mean()
        return ema.tolist()

    def calculate_rsi(self, prices: list[float] | pd.Series, period: int = 14) -> list[float]:
        """
        計算相對強弱指標 (Relative Strength Index)

        Args:
            prices: 價格序列
            period: 週期 (預設 14)

        Returns:
            RSI 值列表
        """
        if isinstance(prices, list):
            prices = pd.Series(prices)

        # 計算價格變化
        delta = prices.diff()

        # 分離上漲和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 計算平均漲幅和跌幅
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # 計算 RS 和 RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.tolist()

    def calculate_macd(
        self,
        prices: list[float] | pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> dict[str, list[float]]:
        """
        計算 MACD 指標 (Moving Average Convergence Divergence)

        Args:
            prices: 價格序列
            fast_period: 快線週期 (預設 12)
            slow_period: 慢線週期 (預設 26)
            signal_period: 訊號線週期 (預設 9)

        Returns:
            包含 MACD、訊號線、柱狀圖的字典
        """
        if isinstance(prices, list):
            prices = pd.Series(prices)

        # 計算快慢 EMA
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()

        # MACD 線 = 快線 - 慢線
        macd_line = ema_fast - ema_slow

        # 訊號線 = MACD 的 EMA
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # 柱狀圖 = MACD - 訊號線
        histogram = macd_line - signal_line

        return {
            "macd": macd_line.tolist(),
            "signal": signal_line.tolist(),
            "histogram": histogram.tolist(),
        }

    def calculate_bollinger_bands(
        self, prices: list[float] | pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> dict[str, list[float]]:
        """
        計算布林通道 (Bollinger Bands)

        Args:
            prices: 價格序列
            period: 週期 (預設 20)
            std_dev: 標準差倍數 (預設 2.0)

        Returns:
            包含上軌、中軌、下軌的字典
        """
        if isinstance(prices, list):
            prices = pd.Series(prices)

        # 中軌 = 移動平均
        middle_band = prices.rolling(window=period).mean()

        # 標準差
        std = prices.rolling(window=period).std()

        # 上軌 = 中軌 + (標準差 × 倍數)
        upper_band = middle_band + (std * std_dev)

        # 下軌 = 中軌 - (標準差 × 倍數)
        lower_band = middle_band - (std * std_dev)

        return {
            "upper": upper_band.tolist(),
            "middle": middle_band.tolist(),
            "lower": lower_band.tolist(),
        }

    def calculate_stochastic(
        self,
        high: list[float] | pd.Series,
        low: list[float] | pd.Series,
        close: list[float] | pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> dict[str, list[float]]:
        """
        計算 KD 隨機指標 (Stochastic Oscillator)

        Args:
            high: 最高價序列
            low: 最低價序列
            close: 收盤價序列
            k_period: K 值週期 (預設 14)
            d_period: D 值週期 (預設 3)

        Returns:
            包含 K 值、D 值的字典
        """
        if isinstance(high, list):
            high = pd.Series(high)
        if isinstance(low, list):
            low = pd.Series(low)
        if isinstance(close, list):
            close = pd.Series(close)

        # 計算最低價和最高價
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        # K 值 = (收盤價 - 最低價) / (最高價 - 最低價) × 100
        k_value = 100 * (close - lowest_low) / (highest_high - lowest_low)

        # D 值 = K 值的移動平均
        d_value = k_value.rolling(window=d_period).mean()

        return {
            "k": k_value.tolist(),
            "d": d_value.tolist(),
        }

    def calculate_atr(
        self,
        high: list[float] | pd.Series,
        low: list[float] | pd.Series,
        close: list[float] | pd.Series,
        period: int = 14,
    ) -> list[float]:
        """
        計算平均真實波幅 (Average True Range)

        Args:
            high: 最高價序列
            low: 最低價序列
            close: 收盤價序列
            period: 週期 (預設 14)

        Returns:
            ATR 值列表
        """
        if isinstance(high, list):
            high = pd.Series(high)
        if isinstance(low, list):
            low = pd.Series(low)
        if isinstance(close, list):
            close = pd.Series(close)

        # 計算真實波幅
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 計算 ATR (真實波幅的移動平均)
        atr = true_range.rolling(window=period).mean()

        return atr.tolist()

    def calculate_support_resistance(
        self,
        high: list[float] | pd.Series,
        low: list[float] | pd.Series,
        close: list[float] | pd.Series,
        window: int = 20,
    ) -> dict[str, Any]:
        """
        識別支撐和阻力位

        Args:
            high: 最高價序列
            low: 最低價序列
            close: 收盤價序列
            window: 計算視窗 (預設 20)

        Returns:
            包含支撐阻力位的字典
        """
        if isinstance(high, list):
            high = pd.Series(high)
        if isinstance(low, list):
            low = pd.Series(low)
        if isinstance(close, list):
            close = pd.Series(close)

        current_price = close.iloc[-1]

        # 找出區間內的高低點
        recent_high = high.rolling(window=window).max().iloc[-1]
        recent_low = low.rolling(window=window).min().iloc[-1]

        # 計算支撐位 (近期低點)
        support_levels = [
            recent_low,
            current_price * 0.95,
            current_price * 0.90,
        ]

        # 計算阻力位 (近期高點)
        resistance_levels = [
            recent_high,
            current_price * 1.05,
            current_price * 1.10,
        ]

        return {
            "support": sorted(support_levels),
            "resistance": sorted(resistance_levels),
            "key_support": recent_low,
            "key_resistance": recent_high,
        }

    def calculate_volume_indicators(
        self, volume: list[float] | pd.Series, period: int = 20
    ) -> dict[str, Any]:
        """
        計算成交量指標

        Args:
            volume: 成交量序列
            period: 週期 (預設 20)

        Returns:
            成交量指標字典
        """
        if isinstance(volume, list):
            volume = pd.Series(volume)

        # 成交量移動平均
        volume_ma = volume.rolling(window=period).mean()

        # 當前成交量與平均的比率
        current_volume = volume.iloc[-1]
        avg_volume = volume_ma.iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        return {
            "volume_ma": volume_ma.tolist(),
            "current_volume": current_volume,
            "average_volume": avg_volume,
            "volume_ratio": volume_ratio,
        }


# 全域單例
_calculator: TechnicalIndicatorCalculator | None = None


def get_indicator_calculator() -> TechnicalIndicatorCalculator:
    """取得技術指標計算器單例"""
    global _calculator
    if _calculator is None:
        _calculator = TechnicalIndicatorCalculator()
    return _calculator
