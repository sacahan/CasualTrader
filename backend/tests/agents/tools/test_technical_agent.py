"""技術分析工具測試

測試 TechnicalAgent 的功能，包括：
- 技術指標計算
- 圖表型態識別
- 趨勢分析
- 支撐壓力位分析
- 交易訊號產生
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.agents.tools.technical_agent import TechnicalAnalysisTools  # noqa: E402

# === Fixtures ===


@pytest.fixture
def sample_price_data() -> list[dict[str, Any]]:
    """提供測試用價格數據"""
    return [
        {
            "date": "2025-10-01",
            "open": 500,
            "high": 510,
            "low": 495,
            "close": 505,
            "volume": 1000,
        },
        {
            "date": "2025-10-02",
            "open": 505,
            "high": 515,
            "low": 500,
            "close": 512,
            "volume": 1200,
        },
        {
            "date": "2025-10-03",
            "open": 512,
            "high": 520,
            "low": 510,
            "close": 518,
            "volume": 1100,
        },
        {
            "date": "2025-10-04",
            "open": 518,
            "high": 525,
            "low": 515,
            "close": 522,
            "volume": 1300,
        },
        {
            "date": "2025-10-05",
            "open": 522,
            "high": 530,
            "low": 520,
            "close": 528,
            "volume": 1400,
        },
        {
            "date": "2025-10-06",
            "open": 528,
            "high": 535,
            "low": 525,
            "close": 532,
            "volume": 1500,
        },
        {
            "date": "2025-10-07",
            "open": 532,
            "high": 540,
            "low": 530,
            "close": 538,
            "volume": 1600,
        },
        {
            "date": "2025-10-08",
            "open": 538,
            "high": 545,
            "low": 535,
            "close": 542,
            "volume": 1700,
        },
    ]


@pytest.fixture
def tools() -> TechnicalAnalysisTools:
    """建立 TechnicalAnalysisTools 實例"""
    return TechnicalAnalysisTools()


# === 技術指標計算測試 ===


class TestCalculateTechnicalIndicators:
    """測試技術指標計算功能"""

    def test_calculate_all_indicators(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試計算所有技術指標"""
        result = tools.calculate_technical_indicators("2330", sample_price_data)

        assert "ticker" in result
        assert result["ticker"] == "2330"
        assert "indicators" in result

        indicators = result["indicators"]
        assert "ma" in indicators
        assert "rsi" in indicators
        assert "macd" in indicators
        assert "bollinger" in indicators
        assert "kd" in indicators

    def test_calculate_specific_indicators(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試計算特定技術指標"""
        result = tools.calculate_technical_indicators(
            "2330", sample_price_data, indicators=["ma", "rsi"]
        )

        indicators = result["indicators"]
        assert "ma" in indicators
        assert "rsi" in indicators
        assert "macd" not in indicators

    def test_ma_indicator_structure(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試移動平均線指標結構"""
        result = tools.calculate_technical_indicators("2330", sample_price_data, indicators=["ma"])

        ma = result["indicators"]["ma"]
        assert "ma5" in ma
        assert "ma10" in ma
        assert "ma20" in ma
        assert "ma60" in ma
        assert all(isinstance(v, int | float) for v in ma.values())

    def test_rsi_indicator_structure(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試 RSI 指標結構"""
        result = tools.calculate_technical_indicators("2330", sample_price_data, indicators=["rsi"])

        rsi = result["indicators"]["rsi"]
        assert "value" in rsi
        assert "status" in rsi
        assert 0 <= rsi["value"] <= 100
        assert rsi["status"] in ["超買", "超賣", "中性"]

    def test_macd_indicator_structure(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試 MACD 指標結構"""
        result = tools.calculate_technical_indicators(
            "2330", sample_price_data, indicators=["macd"]
        )

        macd = result["indicators"]["macd"]
        assert "macd" in macd
        assert "signal" in macd
        assert "histogram" in macd
        assert "status" in macd

    def test_bollinger_bands_structure(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試布林通道指標結構"""
        result = tools.calculate_technical_indicators(
            "2330", sample_price_data, indicators=["bollinger"]
        )

        bollinger = result["indicators"]["bollinger"]
        assert "upper" in bollinger
        assert "middle" in bollinger
        assert "lower" in bollinger
        assert bollinger["upper"] > bollinger["middle"] > bollinger["lower"]

    def test_kd_indicator_structure(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試 KD 指標結構"""
        result = tools.calculate_technical_indicators("2330", sample_price_data, indicators=["kd"])

        kd = result["indicators"]["kd"]
        assert "k" in kd
        assert "d" in kd
        assert "status" in kd
        assert 0 <= kd["k"] <= 100
        assert 0 <= kd["d"] <= 100

    def test_empty_price_data(self, tools: TechnicalAnalysisTools):
        """測試空價格數據處理"""
        result = tools.calculate_technical_indicators("2330", [])

        assert "error" in result
        assert result["ticker"] == "2330"


# === 圖表型態識別測試 ===


class TestIdentifyChartPatterns:
    """測試圖表型態識別功能"""

    def test_identify_patterns_basic(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試基本型態識別"""
        # 擴展數據以滿足最小要求（需要至少 10 個數據點）
        extended_data = sample_price_data + [
            {
                "date": f"2025-10-{9 + i:02d}",
                "close": 542 + i * 2,
                "open": 540 + i * 2,
                "high": 545 + i * 2,
                "low": 538 + i * 2,
                "volume": 1000,
            }
            for i in range(15)
        ]

        result = tools.identify_chart_patterns("2330", extended_data)

        assert "ticker" in result
        assert result["ticker"] == "2330"
        assert "patterns" in result
        assert "pattern_count" in result
        assert isinstance(result["patterns"], list)

    def test_pattern_structure(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試型態結構"""
        # 建立上升趨勢數據
        uptrend_data = sample_price_data + [
            {
                "date": f"2025-10-{9 + i:02d}",
                "close": 542 + i * 5,
                "open": 540 + i * 5,
                "high": 545 + i * 5,
                "low": 540 + i * 5,
                "volume": 1000,
            }
            for i in range(20)
        ]

        result = tools.identify_chart_patterns("2330", uptrend_data)

        if result["pattern_count"] > 0:
            pattern = result["patterns"][0]
            assert "pattern_name" in pattern
            assert "pattern_type" in pattern
            assert "confidence" in pattern
            assert "description" in pattern
            assert pattern["pattern_type"] in ["bullish", "bearish"]
            assert 0 <= pattern["confidence"] <= 1

    def test_insufficient_data(self, tools: TechnicalAnalysisTools):
        """測試數據不足情況"""
        short_data = [
            {
                "date": "2025-10-01",
                "close": 500,
                "open": 495,
                "high": 505,
                "low": 490,
                "volume": 1000,
            }
        ]

        result = tools.identify_chart_patterns("2330", short_data)

        assert "error" in result


# === 趨勢分析測試 ===


class TestAnalyzeTrend:
    """測試趨勢分析功能"""

    def test_analyze_uptrend(self, tools: TechnicalAnalysisTools):
        """測試上升趨勢分析"""
        # 建立明顯上升趨勢
        uptrend_data = [
            {
                "date": f"2025-10-{i + 1:02d}",
                "close": 500 + i * 5,
                "open": 498 + i * 5,
                "high": 505 + i * 5,
                "low": 495 + i * 5,
                "volume": 1000,
            }
            for i in range(25)
        ]

        result = tools.analyze_trend("2330", uptrend_data)

        assert "ticker" in result
        assert "direction" in result
        assert "strength" in result
        assert result["direction"] in ["上升", "下降", "盤整"]

    def test_trend_structure(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試趨勢結構"""
        # 延長數據到足夠長度
        extended_data = sample_price_data + [
            {
                "date": f"2025-10-{9 + i:02d}",
                "close": 542 + i * 2,
                "open": 540 + i * 2,
                "high": 545 + i * 2,
                "low": 538 + i * 2,
                "volume": 1000,
            }
            for i in range(20)
        ]

        result = tools.analyze_trend("2330", extended_data)

        assert "direction" in result
        assert "strength" in result
        assert "short_term_momentum" in result
        assert "mid_term_momentum" in result
        assert 0 <= result["strength"] <= 1

    def test_insufficient_data_for_trend(self, tools: TechnicalAnalysisTools):
        """測試數據不足的趨勢分析"""
        short_data = [
            {
                "date": "2025-10-01",
                "close": 500,
                "open": 495,
                "high": 505,
                "low": 490,
                "volume": 1000,
            }
        ]

        result = tools.analyze_trend("2330", short_data)

        assert "error" in result


# === 支撐壓力位分析測試 ===


class TestAnalyzeSupportResistance:
    """測試支撐壓力位分析功能"""

    def test_find_support_resistance(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試尋找支撐壓力位"""
        result = tools.analyze_support_resistance("2330", sample_price_data)

        assert "ticker" in result
        assert "support_levels" in result
        assert "resistance_levels" in result
        assert isinstance(result["support_levels"], list)
        assert isinstance(result["resistance_levels"], list)

    def test_support_resistance_ordering(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試支撐壓力位排序"""
        result = tools.analyze_support_resistance("2330", sample_price_data)

        # 支撐位應該遞減
        if len(result["support_levels"]) > 1:
            for i in range(len(result["support_levels"]) - 1):
                assert result["support_levels"][i] >= result["support_levels"][i + 1]

        # 壓力位應該遞增
        if len(result["resistance_levels"]) > 1:
            for i in range(len(result["resistance_levels"]) - 1):
                assert result["resistance_levels"][i] <= result["resistance_levels"][i + 1]


# === 交易訊號產生測試 ===


class TestGenerateTradingSignals:
    """測試交易訊號產生功能"""

    def test_generate_signals_structure(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試訊號結構"""
        extended_data = sample_price_data + [
            {
                "date": f"2025-10-{9 + i:02d}",
                "close": 542 + i,
                "open": 540 + i,
                "high": 545 + i,
                "low": 538 + i,
                "volume": 1000,
            }
            for i in range(20)
        ]

        indicators = tools.calculate_technical_indicators("2330", extended_data)
        trend = tools.analyze_trend("2330", extended_data)
        patterns = tools.identify_chart_patterns("2330", extended_data)

        result = tools.generate_trading_signals("2330", indicators, trend, patterns)

        assert "ticker" in result
        assert "overall_signal" in result
        assert "confidence" in result
        assert result["overall_signal"] in ["買進", "賣出", "觀望"]
        assert 0 <= result["confidence"] <= 1

    def test_buy_signal(self, tools: TechnicalAnalysisTools):
        """測試買進訊號"""
        # 建立買進情境
        indicators = {
            "ticker": "2330",
            "indicators": {
                "rsi": {"value": 35, "status": "超賣"},
                "macd": {"status": "多頭"},
            },
        }
        trend = {"direction": "上升", "strength": 0.7}
        patterns = {
            "patterns": [{"pattern_type": "bullish", "confidence": 0.8}],
            "pattern_count": 1,
        }

        result = tools.generate_trading_signals("2330", indicators, trend, patterns)

        # 在這個情境下，應該傾向買進
        assert result["overall_signal"] in ["買進", "觀望"]

    def test_sell_signal(self, tools: TechnicalAnalysisTools):
        """測試賣出訊號"""
        # 建立賣出情境
        indicators = {
            "ticker": "2330",
            "indicators": {
                "rsi": {"value": 75, "status": "超買"},
                "macd": {"status": "空頭"},
            },
        }
        trend = {"direction": "下降", "strength": 0.6}
        patterns = {
            "patterns": [{"pattern_type": "bearish", "confidence": 0.7}],
            "pattern_count": 1,
        }

        result = tools.generate_trading_signals("2330", indicators, trend, patterns)

        # 在這個情境下，應該傾向賣出
        assert result["overall_signal"] in ["賣出", "觀望"]


# === 整合測試 ===


class TestTechnicalAgentIntegration:
    """整合測試"""

    def test_complete_analysis_workflow(
        self, tools: TechnicalAnalysisTools, sample_price_data: list[dict[str, Any]]
    ):
        """測試完整分析流程"""
        # 延長數據
        extended_data = sample_price_data + [
            {
                "date": f"2025-10-{9 + i:02d}",
                "close": 542 + i * 2,
                "open": 540 + i * 2,
                "high": 545 + i * 2,
                "low": 538 + i * 2,
                "volume": 1000,
            }
            for i in range(20)
        ]

        # 1. 計算技術指標
        indicators = tools.calculate_technical_indicators("2330", extended_data)
        assert "indicators" in indicators

        # 2. 識別圖表型態
        patterns = tools.identify_chart_patterns("2330", extended_data)
        assert "patterns" in patterns

        # 3. 分析趨勢
        trend = tools.analyze_trend("2330", extended_data)
        assert "direction" in trend

        # 4. 找支撐壓力位
        levels = tools.analyze_support_resistance("2330", extended_data)
        assert "support_levels" in levels

        # 5. 產生交易訊號
        signals = tools.generate_trading_signals("2330", indicators, trend, patterns)
        assert "overall_signal" in signals or "signal" in signals


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
