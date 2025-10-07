"""
市場情緒分析工具
專門化的市場情緒和資金流向分析工具
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel


class MarketSentiment(BaseModel):
    """市場情緒指標"""

    sentiment_score: float  # -100 to 100
    sentiment_level: str  # "極度悲觀", "悲觀", "中性", "樂觀", "極度樂觀"
    confidence: float
    data_sources: list[str]
    analysis_timestamp: datetime


class NewsAnalysis(BaseModel):
    """新聞情緒分析"""

    symbol: str | None = None
    news_count: int
    positive_news: int
    negative_news: int
    neutral_news: int
    overall_sentiment: float
    key_topics: list[str]
    impact_assessment: str


class SocialSentiment(BaseModel):
    """社群媒體情緒"""

    platform: str
    mention_count: int
    sentiment_distribution: dict[str, float]
    trending_topics: list[str]
    influence_score: float


class MoneyFlowAnalysis(BaseModel):
    """資金流向分析"""

    symbol: str
    net_inflow: float
    large_order_ratio: float
    institutional_activity: str
    retail_activity: str
    foreign_activity: str
    flow_trend: str  # "流入", "流出", "平衡"
    analysis_period: str


class SentimentAnalysisResult(BaseModel):
    """情緒分析結果"""

    analysis_type: str
    overall_market_sentiment: MarketSentiment
    individual_sentiments: list[dict[str, Any]]

    news_analysis: list[NewsAnalysis]
    social_sentiment: list[SocialSentiment]
    money_flow: list[MoneyFlowAnalysis]

    fear_greed_index: float  # 0-100
    volatility_index: float
    put_call_ratio: float | None = None

    sentiment_indicators: dict[str, Any]
    contrarian_signals: list[str]
    momentum_signals: list[str]

    market_psychology: str
    recommended_strategy: str
    timing_assessment: str

    summary: str
    analysis_timestamp: datetime


class SentimentAgent:
    """
    市場情緒分析工具 - 提供全面的市場心理和資金流向分析
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("sentiment_agent")

    async def analyze_market_sentiment(
        self,
        symbols: list[str] | None = None,
        analysis_period: str = "7d",
        include_social: bool = True,
        include_news: bool = True,
    ) -> SentimentAnalysisResult:
        """
        市場情緒分析

        Args:
            symbols: 特定股票代碼列表 (None 表示整體市場)
            analysis_period: 分析期間 ("1d", "7d", "30d")
            include_social: 是否包含社群媒體分析
            include_news: 是否包含新聞分析

        Returns:
            情緒分析結果
        """
        try:
            # 整體市場情緒分析
            market_sentiment = await self._analyze_overall_market_sentiment()

            # 個股情緒分析
            individual_sentiments = []
            if symbols:
                for symbol in symbols:
                    sentiment = await self._analyze_individual_sentiment(symbol)
                    individual_sentiments.append(sentiment)

            # 新聞情緒分析
            news_analysis = []
            if include_news:
                if symbols:
                    for symbol in symbols:
                        news = await self._analyze_news_sentiment(symbol)
                        news_analysis.append(news)
                else:
                    # 整體市場新聞
                    market_news = await self._analyze_news_sentiment(None)
                    news_analysis.append(market_news)

            # 社群媒體情緒
            social_sentiment = []
            if include_social:
                social_data = await self._analyze_social_sentiment(symbols or [])
                social_sentiment.extend(social_data)

            # 資金流向分析
            money_flow = []
            if symbols:
                for symbol in symbols:
                    flow = await self._analyze_money_flow(symbol)
                    money_flow.append(flow)

            # 恐懼貪婪指數
            fear_greed = await self._calculate_fear_greed_index()

            # 波動率指數
            volatility_index = await self._calculate_volatility_index()

            # 情緒指標
            sentiment_indicators = await self._calculate_sentiment_indicators()

            # 反向指標信號
            contrarian_signals = self._identify_contrarian_signals(
                market_sentiment, sentiment_indicators
            )

            # 動能信號
            momentum_signals = self._identify_momentum_signals(
                individual_sentiments, social_sentiment
            )

            # 市場心理評估
            market_psychology = self._assess_market_psychology(
                market_sentiment, fear_greed, volatility_index
            )

            # 策略建議
            strategy_recommendation = self._generate_strategy_recommendation(
                market_sentiment, contrarian_signals, momentum_signals
            )

            # 時機評估
            timing_assessment = self._assess_market_timing(
                market_sentiment, sentiment_indicators
            )

            result = SentimentAnalysisResult(
                analysis_type="comprehensive_sentiment_analysis",
                overall_market_sentiment=market_sentiment,
                individual_sentiments=individual_sentiments,
                news_analysis=news_analysis,
                social_sentiment=social_sentiment,
                money_flow=money_flow,
                fear_greed_index=fear_greed,
                volatility_index=volatility_index,
                sentiment_indicators=sentiment_indicators,
                contrarian_signals=contrarian_signals,
                momentum_signals=momentum_signals,
                market_psychology=market_psychology,
                recommended_strategy=strategy_recommendation,
                timing_assessment=timing_assessment,
                summary=self._generate_sentiment_summary(
                    market_sentiment, fear_greed, strategy_recommendation
                ),
                analysis_timestamp=datetime.now(),
            )

            self.logger.info(
                f"Sentiment analysis completed for {len(symbols or [])} symbols"
            )
            return result

        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {e}")
            raise

    async def _analyze_overall_market_sentiment(self) -> MarketSentiment:
        """分析整體市場情緒"""
        # 模擬市場情緒計算（實際實作時會整合多個數據源）

        # 綜合多個指標計算情緒分數
        technical_sentiment = 65.0  # 技術面情緒
        fundamental_sentiment = 55.0  # 基本面情緒
        news_sentiment = 45.0  # 新聞情緒
        social_sentiment = 70.0  # 社群情緒

        # 加權平均
        overall_score = (
            technical_sentiment * 0.3
            + fundamental_sentiment * 0.25
            + news_sentiment * 0.25
            + social_sentiment * 0.20
        )

        # 轉換為 -100 到 100 的範圍
        sentiment_score = (overall_score - 50) * 2

        # 情緒等級判定
        if sentiment_score >= 60:
            sentiment_level = "極度樂觀"
        elif sentiment_score >= 20:
            sentiment_level = "樂觀"
        elif sentiment_score >= -20:
            sentiment_level = "中性"
        elif sentiment_score >= -60:
            sentiment_level = "悲觀"
        else:
            sentiment_level = "極度悲觀"

        return MarketSentiment(
            sentiment_score=sentiment_score,
            sentiment_level=sentiment_level,
            confidence=0.75,
            data_sources=["技術指標", "新聞分析", "社群媒體", "資金流向"],
            analysis_timestamp=datetime.now(),
        )

    async def _analyze_individual_sentiment(self, symbol: str) -> dict[str, Any]:
        """分析個股情緒"""
        # 模擬個股情緒分析
        sentiment_score = 45.0 + hash(symbol) % 50  # 基於符號的模擬分數

        return {
            "symbol": symbol,
            "sentiment_score": sentiment_score,
            "sentiment_level": (
                "樂觀"
                if sentiment_score > 60
                else "中性" if sentiment_score > 40 else "悲觀"
            ),
            "price_momentum": "正向" if sentiment_score > 55 else "負向",
            "volume_sentiment": "活躍" if sentiment_score > 65 else "普通",
            "analyst_sentiment": "看多" if sentiment_score > 60 else "中性",
            "retail_sentiment": "積極" if sentiment_score > 50 else "保守",
        }

    def get_sentiment_monitoring_setup(self) -> dict[str, Any]:
        """情緒監控設置"""
        return {
            "監控指標": [
                "恐懼貪婪指數",
                "波動率指數",
                "新聞情緒分數",
                "社群討論熱度",
                "資金流向指標",
            ],
            "預警條件": {
                "極度貪婪": "恐懼貪婪指數 > 80",
                "極度恐懼": "恐懼貪婪指數 < 20",
                "情緒急轉": "單日情緒變化 > 30%",
                "異常熱度": "討論量暴增 > 3倍",
            },
            "更新頻率": "每小時",
        }
