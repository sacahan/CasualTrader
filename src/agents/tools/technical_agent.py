"""
技術分析工具
專門化的股票技術分析和圖表分析工具
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel


class TechnicalIndicators(BaseModel):
    """技術指標數據結構"""

    symbol: str
    price_data: dict[str, float]  # open, high, low, close, volume

    # 移動平均線
    ma5: float | None = None
    ma10: float | None = None
    ma20: float | None = None
    ma60: float | None = None

    # 技術指標
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None

    # 布林通道
    bollinger_upper: float | None = None
    bollinger_middle: float | None = None
    bollinger_lower: float | None = None

    # KD 指標
    k_value: float | None = None
    d_value: float | None = None

    # 成交量指標
    volume_ma5: float | None = None
    volume_ratio: float | None = None

    analysis_timestamp: datetime


class TechnicalPattern(BaseModel):
    """技術型態識別結果"""

    pattern_name: str
    pattern_type: str  # "bullish", "bearish", "neutral"
    confidence: float
    description: str
    price_target: float | None = None
    time_horizon: str
    stop_loss_level: float | None = None


class TechnicalAnalysisResult(BaseModel):
    """技術分析結果"""

    symbol: str
    analysis_type: str
    current_trend: str
    trend_strength: float
    support_levels: list[float]
    resistance_levels: list[float]

    entry_signals: list[dict[str, Any]]
    exit_signals: list[dict[str, Any]]

    identified_patterns: list[TechnicalPattern]
    momentum_analysis: dict[str, Any]
    volume_analysis: dict[str, Any]

    overall_signal: str  # "強力買進", "買進", "持有", "賣出", "強力賣出"
    confidence_level: float
    recommended_action: str

    risk_reward_ratio: float | None = None
    suggested_stop_loss: float | None = None
    target_price: float | None = None

    technical_summary: str
    analysis_timestamp: datetime


class TechnicalAgent:
    """
    技術分析工具 - 提供專業的股票技術分析和圖表分析
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("technical_agent")

    async def analyze_technical_indicators(
        self,
        symbol: str,
        timeframe: str = "daily",
        analysis_period: int = 60,
        focus_indicators: list[str] | None = None,
    ) -> TechnicalAnalysisResult:
        """
        技術指標分析

        Args:
            symbol: 股票代碼
            timeframe: 時間週期 ("daily", "weekly", "monthly")
            analysis_period: 分析期間（天數）
            focus_indicators: 重點指標 (可選)

        Returns:
            技術分析結果
        """
        try:
            # 獲取歷史價格數據
            technical_data = await self._fetch_price_data(symbol, analysis_period)

            # 計算技術指標
            indicators = await self._calculate_technical_indicators(technical_data)

            # 識別技術型態
            patterns = await self._identify_chart_patterns(technical_data, indicators)

            # 趨勢分析
            trend_analysis = self._analyze_trend(indicators)

            # 動能分析
            momentum_analysis = self._analyze_momentum(indicators)

            # 成交量分析
            volume_analysis = self._analyze_volume(indicators)

            # 支撐阻力分析
            support_resistance = self._identify_support_resistance(technical_data)

            # 綜合信號分析
            overall_signal = self._generate_trading_signals(
                indicators, patterns, trend_analysis, momentum_analysis
            )

            # 生成技術分析結果
            result = TechnicalAnalysisResult(
                symbol=symbol,
                analysis_type="comprehensive_technical",
                current_trend=trend_analysis["direction"],
                trend_strength=trend_analysis["strength"],
                support_levels=support_resistance["support"],
                resistance_levels=support_resistance["resistance"],
                entry_signals=overall_signal["entry_signals"],
                exit_signals=overall_signal["exit_signals"],
                identified_patterns=patterns,
                momentum_analysis=momentum_analysis,
                volume_analysis=volume_analysis,
                overall_signal=overall_signal["overall"],
                confidence_level=overall_signal["confidence"],
                recommended_action=overall_signal["action"],
                risk_reward_ratio=overall_signal.get("risk_reward"),
                suggested_stop_loss=overall_signal.get("stop_loss"),
                target_price=overall_signal.get("target_price"),
                technical_summary=self._generate_technical_summary(
                    symbol, indicators, patterns, overall_signal
                ),
                analysis_timestamp=datetime.now(),
            )

            self.logger.info(f"Technical analysis completed for {symbol}")
            return result

        except Exception as e:
            self.logger.error(f"Technical analysis failed for {symbol}: {e}")
            raise

    async def _fetch_price_data(self, symbol: str, period: int) -> dict[str, Any]:
        """獲取歷史價格數據"""
        # 這裡將整合 CasualMarket MCP 工具獲取實際歷史數據
        # 目前返回模擬數據結構

        end_date = datetime.now()
        start_date = end_date - timedelta(days=period)

        return {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "current_price": 100.0,
            "daily_data": [
                {
                    "date": end_date - timedelta(days=i),
                    "open": 98.0 + i * 0.5,
                    "high": 102.0 + i * 0.5,
                    "low": 96.0 + i * 0.5,
                    "close": 100.0 + i * 0.3,
                    "volume": 1000000 + i * 10000,
                }
                for i in range(period)
            ],
        }

    async def _calculate_technical_indicators(
        self, price_data: dict[str, Any]
    ) -> TechnicalIndicators:
        """計算技術指標"""
        current_price = price_data["current_price"]
        price_data["daily_data"]

        # 模擬計算結果（實際實作時會進行真實計算）
        return TechnicalIndicators(
            symbol=price_data["symbol"],
            price_data={
                "open": current_price - 1.0,
                "high": current_price + 1.5,
                "low": current_price - 2.0,
                "close": current_price,
                "volume": 1500000,
            },
            ma5=current_price - 0.5,
            ma10=current_price - 1.0,
            ma20=current_price - 2.0,
            ma60=current_price - 5.0,
            rsi=65.5,
            macd=1.2,
            macd_signal=1.0,
            macd_histogram=0.2,
            bollinger_upper=current_price + 3.0,
            bollinger_middle=current_price,
            bollinger_lower=current_price - 3.0,
            k_value=75.0,
            d_value=68.0,
            volume_ma5=1200000,
            volume_ratio=1.25,
            analysis_timestamp=datetime.now(),
        )

    async def _identify_chart_patterns(
        self, price_data: dict[str, Any], indicators: TechnicalIndicators
    ) -> list[TechnicalPattern]:
        """識別圖表型態"""
        patterns = []

        # 模擬型態識別結果
        current_price = indicators.price_data["close"]

        # 上升趨勢型態
        if (
            indicators.ma5
            and indicators.ma10
            and indicators.ma5 > indicators.ma10
            and current_price > indicators.ma5
        ):
            patterns.append(
                TechnicalPattern(
                    pattern_name="上升趨勢",
                    pattern_type="bullish",
                    confidence=0.75,
                    description="價格站上短期均線，呈現上升趨勢",
                    price_target=current_price * 1.08,
                    time_horizon="短期 (1-2週)",
                    stop_loss_level=current_price * 0.95,
                )
            )

        # 突破型態
        if (
            indicators.bollinger_upper
            and current_price > indicators.bollinger_upper
            and indicators.volume_ratio
            and indicators.volume_ratio > 1.5
        ):
            patterns.append(
                TechnicalPattern(
                    pattern_name="布林通道突破",
                    pattern_type="bullish",
                    confidence=0.80,
                    description="價格突破布林通道上軌，伴隨成交量放大",
                    price_target=current_price * 1.12,
                    time_horizon="中期 (2-4週)",
                    stop_loss_level=indicators.bollinger_middle,
                )
            )

        return patterns

    def _analyze_trend(self, indicators: TechnicalIndicators) -> dict[str, Any]:
        """分析趨勢方向和強度"""
        current_price = indicators.price_data["close"]

        # 移動平均線排列
        ma_alignment_score = 0
        if indicators.ma5 and indicators.ma10 and indicators.ma5 > indicators.ma10:
            ma_alignment_score += 1
        if indicators.ma10 and indicators.ma20 and indicators.ma10 > indicators.ma20:
            ma_alignment_score += 1
        if indicators.ma20 and indicators.ma60 and indicators.ma20 > indicators.ma60:
            ma_alignment_score += 1

        # 價格相對位置
        price_position_score = 0
        if indicators.ma5 and current_price > indicators.ma5:
            price_position_score += 1
        if indicators.ma20 and current_price > indicators.ma20:
            price_position_score += 1

        # 綜合趨勢判斷
        total_score = ma_alignment_score + price_position_score

        if total_score >= 4:
            direction = "強勢上升"
            strength = 0.8 + (total_score - 4) * 0.1
        elif total_score >= 3:
            direction = "上升"
            strength = 0.6 + (total_score - 3) * 0.1
        elif total_score >= 2:
            direction = "橫盤整理"
            strength = 0.4 + (total_score - 2) * 0.1
        elif total_score >= 1:
            direction = "下降"
            strength = 0.6
        else:
            direction = "強勢下降"
            strength = 0.8

        return {
            "direction": direction,
            "strength": min(1.0, strength),
            "ma_alignment_score": ma_alignment_score,
            "price_position_score": price_position_score,
            "confidence": 0.7 + (total_score / 10),
        }

    def _analyze_momentum(self, indicators: TechnicalIndicators) -> dict[str, Any]:
        """分析動能指標"""
        momentum_signals = []
        overall_momentum = "中性"
        momentum_score = 0

        # RSI 分析
        if indicators.rsi:
            if indicators.rsi > 70:
                momentum_signals.append("RSI 超買 (>70)")
                momentum_score -= 1
            elif indicators.rsi > 50:
                momentum_signals.append("RSI 偏強 (50-70)")
                momentum_score += 1
            elif indicators.rsi > 30:
                momentum_signals.append("RSI 中性 (30-50)")
            else:
                momentum_signals.append("RSI 超賣 (<30)")
                momentum_score += 2

        # MACD 分析
        if indicators.macd and indicators.macd_signal:
            if indicators.macd > indicators.macd_signal:
                momentum_signals.append("MACD 黃金交叉")
                momentum_score += 1
            else:
                momentum_signals.append("MACD 死亡交叉")
                momentum_score -= 1

            if indicators.macd_histogram and indicators.macd_histogram > 0:
                momentum_signals.append("MACD 柱狀圖轉正")
                momentum_score += 0.5

        # KD 指標分析
        if indicators.k_value and indicators.d_value:
            if indicators.k_value > indicators.d_value and indicators.k_value > 50:
                momentum_signals.append("KD 指標偏多")
                momentum_score += 1
            elif indicators.k_value < indicators.d_value and indicators.k_value < 50:
                momentum_signals.append("KD 指標偏空")
                momentum_score -= 1

        # 綜合動能判斷
        if momentum_score >= 2:
            overall_momentum = "強勁"
        elif momentum_score >= 1:
            overall_momentum = "偏強"
        elif momentum_score <= -2:
            overall_momentum = "疲弱"
        elif momentum_score <= -1:
            overall_momentum = "偏弱"

        return {
            "overall": overall_momentum,
            "score": momentum_score,
            "signals": momentum_signals,
            "rsi_level": indicators.rsi,
            "macd_trend": "上升" if indicators.macd and indicators.macd > 0 else "下降",
            "kd_position": (
                "強勢" if indicators.k_value and indicators.k_value > 50 else "弱勢"
            ),
        }

    def _analyze_volume(self, indicators: TechnicalIndicators) -> dict[str, Any]:
        """分析成交量"""
        volume_signals = []
        volume_trend = "正常"

        current_volume = indicators.price_data["volume"]

        # 成交量比較
        if indicators.volume_ma5:
            volume_ratio = current_volume / indicators.volume_ma5

            if volume_ratio > 2.0:
                volume_signals.append("巨量 (>2倍均量)")
                volume_trend = "巨量"
            elif volume_ratio > 1.5:
                volume_signals.append("大量 (1.5-2倍均量)")
                volume_trend = "放量"
            elif volume_ratio > 1.2:
                volume_signals.append("溫和放量 (1.2-1.5倍均量)")
                volume_trend = "溫和放量"
            elif volume_ratio < 0.7:
                volume_signals.append("縮量 (<0.7倍均量)")
                volume_trend = "縮量"

        # 價量配合分析
        price_change = (
            indicators.price_data["close"] - indicators.price_data["open"]
        ) / indicators.price_data["open"]

        if (
            price_change > 0
            and indicators.volume_ratio
            and indicators.volume_ratio > 1.2
        ):
            volume_signals.append("上漲放量 - 健康")
        elif (
            price_change < 0
            and indicators.volume_ratio
            and indicators.volume_ratio > 1.2
        ):
            volume_signals.append("下跌放量 - 需關注")

        return {
            "trend": volume_trend,
            "current_volume": current_volume,
            "volume_ratio": indicators.volume_ratio,
            "signals": volume_signals,
            "price_volume_relationship": "健康" if price_change > 0 else "需觀察",
        }

    def _identify_support_resistance(
        self, price_data: dict[str, Any]
    ) -> dict[str, Any]:
        """識別支撐阻力位"""
        current_price = price_data["current_price"]
        price_data["daily_data"]

        # 模擬支撐阻力計算（實際實作時會基於歷史高低點）
        support_levels = [
            current_price * 0.95,  # 近期支撐
            current_price * 0.90,  # 重要支撐
            current_price * 0.85,  # 強支撐
        ]

        resistance_levels = [
            current_price * 1.05,  # 近期阻力
            current_price * 1.10,  # 重要阻力
            current_price * 1.15,  # 強阻力
        ]

        return {
            "support": support_levels,
            "resistance": resistance_levels,
            "key_support": support_levels[1],
            "key_resistance": resistance_levels[1],
        }

    def _generate_trading_signals(
        self,
        indicators: TechnicalIndicators,
        patterns: list[TechnicalPattern],
        trend_analysis: dict[str, Any],
        momentum_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """生成交易信號"""

        buy_signals = []
        sell_signals = []
        signal_score = 0

        current_price = indicators.price_data["close"]

        # 趨勢信號
        if trend_analysis["direction"] in ["上升", "強勢上升"]:
            buy_signals.append("趨勢向上")
            signal_score += 2 if "強勢" in trend_analysis["direction"] else 1

        # 動能信號
        if momentum_analysis["overall"] in ["強勁", "偏強"]:
            buy_signals.append("動能偏多")
            signal_score += 2 if momentum_analysis["overall"] == "強勁" else 1
        elif momentum_analysis["overall"] in ["疲弱", "偏弱"]:
            sell_signals.append("動能轉弱")
            signal_score -= 2 if momentum_analysis["overall"] == "疲弱" else 1

        # 型態信號
        bullish_patterns = [p for p in patterns if p.pattern_type == "bullish"]
        bearish_patterns = [p for p in patterns if p.pattern_type == "bearish"]

        if bullish_patterns:
            buy_signals.append(f"看漲型態: {bullish_patterns[0].pattern_name}")
            signal_score += len(bullish_patterns)

        if bearish_patterns:
            sell_signals.append(f"看跌型態: {bearish_patterns[0].pattern_name}")
            signal_score -= len(bearish_patterns)

        # 技術指標信號
        if indicators.rsi and indicators.rsi < 30:
            buy_signals.append("RSI 超賣反彈")
            signal_score += 1
        elif indicators.rsi and indicators.rsi > 70:
            sell_signals.append("RSI 超買回檔")
            signal_score -= 1

        # 綜合信號判斷
        if signal_score >= 4:
            overall_signal = "強力買進"
            action = "建議積極買進"
            confidence = 0.85
        elif signal_score >= 2:
            overall_signal = "買進"
            action = "建議買進"
            confidence = 0.70
        elif signal_score <= -4:
            overall_signal = "強力賣出"
            action = "建議積極賣出"
            confidence = 0.85
        elif signal_score <= -2:
            overall_signal = "賣出"
            action = "建議賣出"
            confidence = 0.70
        else:
            overall_signal = "持有"
            action = "建議持有觀望"
            confidence = 0.60

        # 計算目標價和停損位
        target_price = None
        stop_loss = None
        risk_reward = None

        if signal_score > 0:  # 看多信號
            target_price = current_price * 1.08
            stop_loss = current_price * 0.95
            risk_reward = (target_price - current_price) / (current_price - stop_loss)

        return {
            "overall": overall_signal,
            "action": action,
            "confidence": confidence,
            "signal_score": signal_score,
            "entry_signals": [{"signal": s, "type": "buy"} for s in buy_signals],
            "exit_signals": [{"signal": s, "type": "sell"} for s in sell_signals],
            "target_price": target_price,
            "stop_loss": stop_loss,
            "risk_reward": risk_reward,
        }

    def _generate_technical_summary(
        self,
        symbol: str,
        indicators: TechnicalIndicators,
        patterns: list[TechnicalPattern],
        signals: dict[str, Any],
    ) -> str:
        """生成技術分析摘要"""

        current_price = indicators.price_data["close"]

        pattern_summary = ""
        if patterns:
            main_pattern = patterns[0]
            pattern_summary = f"識別到{main_pattern.pattern_name}型態，"

        return f"""
{symbol} 技術分析摘要：

當前股價：NT${current_price:.2f}
綜合信號：{signals["overall"]} (信心度: {signals["confidence"]:.0%})

關鍵技術指標：
- RSI：{indicators.rsi or "N/A"} (動能{"偏強" if indicators.rsi and indicators.rsi > 50 else "偏弱"})
- MACD：{indicators.macd or "N/A"} (趨勢{"向上" if indicators.macd and indicators.macd > 0 else "向下"})
- 布林通道位置：{"上軌附近" if indicators.bollinger_upper and current_price > indicators.bollinger_upper * 0.98 else "中軌附近"}

{pattern_summary}{signals["action"]}。
{"目標價 NT$" + f"{signals['target_price']:.2f}" if signals.get("target_price") else ""}
{"，停損設於 NT$" + f"{signals['stop_loss']:.2f}" if signals.get("stop_loss") else ""}。
        """.strip()

    def get_technical_watchlist(self, symbols: list[str]) -> dict[str, Any]:
        """技術面觀察清單"""
        return {
            "symbols": symbols,
            "scan_criteria": [
                "突破重要阻力位",
                "RSI 超賣反彈",
                "成交量異常放大",
                "移動平均線多頭排列",
                "MACD 黃金交叉",
            ],
            "alert_conditions": [
                "價格突破布林通道上軌",
                "RSI 跌破 30 或突破 70",
                "成交量超過 20 日均量 2 倍",
                "跌破重要支撐位",
            ],
            "update_frequency": "即時",
        }

    def as_tool(self, tool_name: str, tool_description: str) -> dict[str, Any]:
        """
        將 TechnicalAgent 轉換為可供 OpenAI Agent 使用的工具

        Args:
            tool_name: 工具名稱
            tool_description: 工具描述

        Returns:
            工具配置字典
        """
        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代碼 (例如: 2330)",
                        },
                        "analysis_period": {
                            "type": "string",
                            "enum": ["short", "medium", "long"],
                            "description": "分析週期",
                            "default": "medium",
                        },
                        "include_patterns": {
                            "type": "boolean",
                            "description": "是否包含圖表形態分析",
                            "default": True,
                        },
                        "indicators": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "要分析的技術指標 (可選)",
                        },
                    },
                    "required": ["symbol"],
                },
            },
            "implementation": self.analyze_technical_indicators,
        }
