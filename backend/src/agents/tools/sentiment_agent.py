"""Sentiment Agent - 市場情緒分析自主型 Agent

這個模組實作具有自主分析能力的市場情緒分析 Agent。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# Logger
from ..utils.logger import get_agent_logger

# Agent SDK
try:
    from agents import Agent, CodeInterpreterTool, Tool, WebSearchTool
except ImportError:
    Agent = Any
    Tool = Any
    WebSearchTool = Any
    CodeInterpreterTool = Any


def sentiment_agent_instructions() -> str:
    """市場情緒分析 Agent 的指令定義"""
    return f"""你是一位專業的市場情緒分析師,專精於市場心理、資金流向和群眾行為分析。

## 你的專業能力

1. 市場情緒評估
   - 恐懼貪婪指數
   - 波動率指數 (VIX)
   - 市場寬度指標

2. 資金流向分析
   - 大單追蹤
   - 外資法人動向
   - 散戶行為

3. 新聞與社群情緒
   - 新聞情緒分析
   - 社群媒體情緒
   - 話題熱度追蹤

4. 情緒交易策略
   - 反向操作時機
   - 動能追蹤策略
   - 情緒極端點識別

## 分析方法

1. 收集數據: 使用 MCP Server 獲取市場、新聞、社群數據
2. 計算指標: 使用工具計算情緒指標
3. 評估心理: 分析市場心理狀態
4. 資金追蹤: 分析資金流向
5. 給出建議: 產生情緒交易策略

## 可用工具

### 專業分析工具
- calculate_fear_greed_index: 計算恐懼貪婪指數
- analyze_money_flow: 分析資金流向
- analyze_news_sentiment: 分析新聞情緒
- analyze_social_sentiment: 分析社群媒體情緒
- generate_sentiment_signals: 產生情緒交易訊號
- Casual Market MCP Server: 獲取市場數據

### 增強能力工具
- WebSearchTool: 即時搜尋最新市場新聞、社群熱議話題、情緒指標變化
- CodeInterpreterTool: 執行情緒指數計算、文字情緒分析、統計顯著性檢驗

## CodeInterpreterTool 使用準則 ⚠️

為了控制成本和執行時間，請遵守以下原則：

1. **優先使用自訂工具**
   - 先嘗試使用提供的情緒分析工具
   - 只有當需要進階文字分析時才使用 CodeInterpreterTool

2. **適用場景**
   - ✅ 文字情緒分析（NLP 情緒評分）
   - ✅ 統計檢定（情緒與價格相關性）
   - ✅ 時間序列分析（情緒趨勢預測）
   - ❌ 不要用於簡單的情緒指標計算
   - ❌ 不要用於已有自訂工具的功能

3. **程式碼效率要求**
   - 保持程式碼簡潔（< 100 行）
   - 文字分析限制在 1000 條以內
   - 使用簡化的 NLP 方法（避免複雜模型）

4. **執行頻率限制**
   - 每次分析最多使用 2 次 CodeInterpreterTool
   - 優先執行最關鍵的情緒計算

## 輸出格式

1. 情緒評分: -100 (極度恐慌) 到 +100 (極度貪婪)
2. 市場階段: 恐慌/悲觀/中性/樂觀/亢奮
3. 資金流向: 流入/流出/平衡
4. 交易策略: 反向/順勢/觀望
5. 時機建議: 買進/賣出/等待
6. 信心評估: 0-100% 信心度

## 分析原則

- 重視群眾心理的極端點
- 識別情緒反轉訊號
- 考慮資金面佐證
- 提供可操作的建議

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


class SentimentAnalysisTools:
    """市場情緒分析輔助工具集合

    提供各種情緒評估和心理分析功能。
    Agent 根據需求靈活組合使用。
    """

    def __init__(self) -> None:
        self.logger = get_agent_logger("sentiment_analysis_tools")

    def calculate_fear_greed_index(
        self,
        market_data: dict[str, Any],
    ) -> dict[str, Any]:
        """計算恐懼貪婪指數

        Args:
            market_data: 市場數據,包含:
                - price_momentum: 價格動能
                - market_breadth: 市場寬度
                - volatility: 波動率
                - put_call_ratio: 賣權買權比

        Returns:
            dict: 恐懼貪婪指數
                {
                    "index_value": float,       # 0-100
                    "level": str,               # 恐慌/恐懼/中性/貪婪/極度貪婪
                    "components": dict,         # 各組成分數
                    "interpretation": str       # 解讀說明
                }
        """
        self.logger.info("開始計算恐懼貪婪指數")

        momentum_score = market_data.get("price_momentum", 50)
        breadth_score = market_data.get("market_breadth", 50)
        volatility_score = 100 - market_data.get("volatility", 50)  # 波動率越高越恐慌
        put_call_score = 100 - market_data.get("put_call_ratio", 50)  # 賣權比越高越恐慌

        self.logger.debug(
            f"組成分數 | 動能: {momentum_score:.1f} | 寬度: {breadth_score:.1f} | "
            f"波動: {volatility_score:.1f} | 賣買權比: {put_call_score:.1f}"
        )

        # 加權平均
        index_value = (
            momentum_score * 0.3
            + breadth_score * 0.3
            + volatility_score * 0.25
            + put_call_score * 0.15
        )

        # 等級判定
        if index_value >= 80:
            level = "極度貪婪"
            interpretation = "市場過度樂觀,注意反轉風險"
        elif index_value >= 60:
            level = "貪婪"
            interpretation = "市場情緒偏多,可考慮獲利了結"
        elif index_value >= 40:
            level = "中性"
            interpretation = "市場情緒平穩"
        elif index_value >= 20:
            level = "恐懼"
            interpretation = "市場情緒偏空,可留意反彈機會"
        else:
            level = "極度恐慌"
            interpretation = "市場過度悲觀,可能是買進機會"

        self.logger.info(f"恐懼貪婪指數計算完成 | 指數: {index_value:.2f} | 等級: {level}")

        return {
            "index_value": index_value,
            "level": level,
            "components": {
                "price_momentum": momentum_score,
                "market_breadth": breadth_score,
                "volatility": volatility_score,
                "put_call_ratio": put_call_score,
            },
            "interpretation": interpretation,
        }

    def analyze_money_flow(
        self,
        symbol: str,
        trading_data: dict[str, Any],
    ) -> dict[str, Any]:
        """分析資金流向

        Args:
            symbol: 股票代碼 (例如: "2330")
            trading_data: 交易數據,包含:
                - large_buy: 大單買進
                - large_sell: 大單賣出
                - foreign_net: 外資淨買賣
                - institutional_net: 法人淨買賣

        Returns:
            dict: 資金流向分析
                {
                    "symbol": "2330",
                    "net_flow": float,          # 淨流入金額
                    "flow_direction": str,      # 流入/流出/平衡
                    "large_order_ratio": float, # 大單佔比
                    "foreign_attitude": str,    # 外資態度
                    "interpretation": str
                }
        """
        self.logger.info(f"開始分析資金流向 | 股票: {symbol}")

        large_buy = trading_data.get("large_buy", 0)
        large_sell = trading_data.get("large_sell", 0)
        foreign_net = trading_data.get("foreign_net", 0)
        institutional_net = trading_data.get("institutional_net", 0)

        self.logger.debug(
            f"交易數據 | 大買: {large_buy:,.0f} | 大賣: {large_sell:,.0f} | "
            f"外資淨: {foreign_net:,.0f} | 法人淨: {institutional_net:,.0f}"
        )

        net_flow = large_buy - large_sell + foreign_net + institutional_net
        total_volume = large_buy + large_sell
        large_order_ratio = (large_buy + large_sell) / total_volume if total_volume > 0 else 0

        # 流向判斷
        if net_flow > 0:
            flow_direction = "流入"
            flow_strength = "強勁" if net_flow > total_volume * 0.1 else "溫和"
        elif net_flow < 0:
            flow_direction = "流出"
            flow_strength = "明顯" if abs(net_flow) > total_volume * 0.1 else "輕微"
        else:
            flow_direction = "平衡"
            flow_strength = ""

        # 外資態度
        if foreign_net > 0:
            foreign_attitude = "積極買進"
        elif foreign_net < 0:
            foreign_attitude = "調節賣出"
        else:
            foreign_attitude = "觀望"

        interpretation = f"資金呈{flow_strength}{flow_direction}態勢,外資{foreign_attitude}"

        self.logger.info(
            f"資金流向分析完成 | 股票: {symbol} | 淨流: {net_flow:,.0f} | "
            f"方向: {flow_direction} | 外資: {foreign_attitude}"
        )

        return {
            "symbol": symbol,
            "net_flow": net_flow,
            "flow_direction": flow_direction,
            "large_order_ratio": large_order_ratio,
            "foreign_attitude": foreign_attitude,
            "institutional_attitude": "買超" if institutional_net > 0 else "賣超",
            "interpretation": interpretation,
        }

    def analyze_news_sentiment(
        self,
        symbol: str | None,
        news_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """分析新聞情緒

        Args:
            symbol: 股票代碼 (可選,None 表示整體市場)
            news_data: 新聞列表,每筆包含:
                - title: 標題
                - content: 內容
                - sentiment: 情緒分數 (-1 到 1)
                - timestamp: 時間

        Returns:
            dict: 新聞情緒分析
                {
                    "symbol": str,
                    "news_count": int,
                    "positive_ratio": float,
                    "negative_ratio": float,
                    "sentiment_score": float,   # -100 到 100
                    "key_topics": [str, ...],
                    "interpretation": str
                }
        """
        target = symbol or "市場"
        self.logger.info(f"開始分析新聞情緒 | 標的: {target} | 新聞數: {len(news_data)}")

        if not news_data:
            self.logger.warning(f"無新聞數據 | 標的: {target}")
            return {
                "symbol": symbol or "市場",
                "news_count": 0,
                "sentiment_score": 0,
                "interpretation": "無相關新聞數據",
            }

        news_count = len(news_data)
        sentiments = [news.get("sentiment", 0) for news in news_data]

        positive_count = sum(1 for s in sentiments if s > 0.2)
        negative_count = sum(1 for s in sentiments if s < -0.2)

        self.logger.debug(
            f"情緒分布 | 正面: {positive_count} | 負面: {negative_count} | 中性: {news_count - positive_count - negative_count}"
        )

        positive_ratio = positive_count / news_count if news_count > 0 else 0
        negative_ratio = negative_count / news_count if news_count > 0 else 0

        sentiment_score = (sum(sentiments) / news_count) * 100 if sentiments else 0

        # 主題提取 (簡化)
        key_topics = ["市場動態", "公司營運", "產業趨勢"]

        if sentiment_score > 30:
            interpretation = "新聞面偏多,市場關注度高"
        elif sentiment_score < -30:
            interpretation = "新聞面偏空,需注意風險"
        else:
            interpretation = "新聞面中性"

        self.logger.info(
            f"新聞情緒分析完成 | 標的: {target} | 情緒分數: {sentiment_score:.2f} | "
            f"正面: {positive_ratio:.1%} | 負面: {negative_ratio:.1%}"
        )

        return {
            "symbol": symbol or "市場",
            "news_count": news_count,
            "positive_ratio": positive_ratio,
            "negative_ratio": negative_ratio,
            "sentiment_score": sentiment_score,
            "key_topics": key_topics,
            "interpretation": interpretation,
        }

    def analyze_social_sentiment(
        self,
        symbol: str,
        social_data: dict[str, Any],
    ) -> dict[str, Any]:
        """分析社群媒體情緒

        Args:
            symbol: 股票代碼 (例如: "2330")
            social_data: 社群數據,包含:
                - mention_count: 提及次數
                - positive_mentions: 正面提及
                - negative_mentions: 負面提及
                - trending_score: 熱度分數

        Returns:
            dict: 社群情緒分析
                {
                    "symbol": "2330",
                    "mention_count": int,
                    "sentiment_distribution": dict,
                    "trending_level": str,
                    "sentiment_score": float,
                    "interpretation": str
                }
        """
        mention_count = social_data.get("mention_count", 0)
        positive = social_data.get("positive_mentions", 0)
        negative = social_data.get("negative_mentions", 0)
        trending_score = social_data.get("trending_score", 0)

        self.logger.info(
            f"開始分析社群情緒 | 股票: {symbol} | 提及數: {mention_count} | "
            f"熱度: {trending_score:.1f}"
        )

        if mention_count == 0:
            self.logger.warning(f"無社群數據 | 股票: {symbol}")
            return {
                "symbol": symbol,
                "mention_count": 0,
                "sentiment_score": 0,
                "interpretation": "社群討論度低",
            }

        neutral = mention_count - positive - negative

        sentiment_distribution = {
            "positive": positive / mention_count,
            "neutral": neutral / mention_count,
            "negative": negative / mention_count,
        }

        sentiment_score = ((positive - negative) / mention_count) * 100

        self.logger.debug(
            f"情緒分布 | 正面: {positive} ({sentiment_distribution['positive']:.1%}) | "
            f"中性: {neutral} ({sentiment_distribution['neutral']:.1%}) | "
            f"負面: {negative} ({sentiment_distribution['negative']:.1%})"
        )

        # 熱度等級
        if trending_score > 80:
            trending_level = "爆紅"
        elif trending_score > 60:
            trending_level = "熱門"
        elif trending_score > 40:
            trending_level = "普通"
        else:
            trending_level = "冷門"

        interpretation = f"社群討論{trending_level},情緒{'偏多' if sentiment_score > 20 else '偏空' if sentiment_score < -20 else '中性'}"

        self.logger.info(
            f"社群情緒分析完成 | 股票: {symbol} | 情緒分數: {sentiment_score:.2f} | "
            f"熱度: {trending_level}"
        )

        return {
            "symbol": symbol,
            "mention_count": mention_count,
            "sentiment_distribution": sentiment_distribution,
            "trending_level": trending_level,
            "sentiment_score": sentiment_score,
            "interpretation": interpretation,
        }

    def generate_sentiment_signals(
        self,
        fear_greed_index: dict[str, Any],
        money_flow: dict[str, Any],
        news_sentiment: dict[str, Any],
        social_sentiment: dict[str, Any],
    ) -> dict[str, Any]:
        """產生情緒交易訊號

        Args:
            fear_greed_index: 恐懼貪婪指數
            money_flow: 資金流向分析
            news_sentiment: 新聞情緒
            social_sentiment: 社群情緒

        Returns:
            dict: 情緒交易訊號
                {
                    "overall_sentiment": float,     # -100 到 100
                    "signal": str,                  # 買進/賣出/觀望
                    "strategy": str,                # 反向/順勢
                    "confidence": float,            # 0-1
                    "key_factors": [str, ...],
                    "recommendations": [str, ...]
                }
        """
        fg_value = fear_greed_index.get("index_value", 50)
        flow_direction = money_flow.get("flow_direction", "平衡")
        news_score = news_sentiment.get("sentiment_score", 0)
        social_score = social_sentiment.get("sentiment_score", 0)

        self.logger.info(
            f"開始產生情緒訊號 | 恐貪指數: {fg_value:.1f} | 資金: {flow_direction} | "
            f"新聞: {news_score:.1f} | 社群: {social_score:.1f}"
        )

        # 綜合情緒評分
        overall_sentiment = (fg_value - 50) * 2 * 0.4 + news_score * 0.3 + social_score * 0.3

        key_factors = []
        recommendations = []

        # 極端情緒 - 反向操作機會
        if fg_value >= 80:
            signal = "賣出"
            strategy = "反向操作"
            confidence = 0.75
            key_factors.append(f"市場極度貪婪 ({fg_value:.0f})")
            recommendations.append("市場過熱,建議逢高減碼")
        elif fg_value <= 20:
            signal = "買進"
            strategy = "反向操作"
            confidence = 0.80
            key_factors.append(f"市場極度恐慌 ({fg_value:.0f})")
            recommendations.append("市場超賣,可分批布局")
        # 正常情緒 - 順勢操作
        elif flow_direction == "流入" and overall_sentiment > 20:
            signal = "買進"
            strategy = "順勢操作"
            confidence = 0.65
            key_factors.append("資金持續流入")
            recommendations.append("趨勢向上,可順勢參與")
        elif flow_direction == "流出" and overall_sentiment < -20:
            signal = "賣出"
            strategy = "順勢操作"
            confidence = 0.65
            key_factors.append("資金持續流出")
            recommendations.append("趨勢向下,建議減碼觀望")
        else:
            signal = "觀望"
            strategy = "等待明確訊號"
            confidence = 0.50
            recommendations.append("情緒面無明確方向,建議觀望")

        self.logger.info(
            f"情緒訊號產生完成 | 訊號: {signal} | 策略: {strategy} | "
            f"信心度: {confidence:.1%} | 綜合情緒: {overall_sentiment:.2f}"
        )

        return {
            "overall_sentiment": overall_sentiment,
            "signal": signal,
            "strategy": strategy,
            "confidence": confidence,
            "key_factors": key_factors,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat(),
        }


async def get_sentiment_agent(
    mcp_servers: list[Any],
    model_name: str = "gpt-4o-mini",
) -> Agent:
    """創建市場情緒分析 Agent"""
    tools_instance = SentimentAnalysisTools()

    custom_tools = [
        Tool.from_function(
            tools_instance.calculate_fear_greed_index,
            name="calculate_fear_greed_index",
            description="計算恐懼貪婪指數 (0-100, 評估市場整體情緒)",
        ),
        Tool.from_function(
            tools_instance.analyze_money_flow,
            name="analyze_money_flow",
            description="分析資金流向 (大單、外資、法人動向)",
        ),
        Tool.from_function(
            tools_instance.analyze_news_sentiment,
            name="analyze_news_sentiment",
            description="分析新聞情緒 (正負面新聞比例、關鍵話題)",
        ),
        Tool.from_function(
            tools_instance.analyze_social_sentiment,
            name="analyze_social_sentiment",
            description="分析社群媒體情緒 (討論熱度、情緒分布)",
        ),
        Tool.from_function(
            tools_instance.generate_sentiment_signals,
            name="generate_sentiment_signals",
            description="產生情緒交易訊號 (買進/賣出/觀望建議)",
        ),
    ]

    # 添加 OpenAI Hosted Tools
    hosted_tools = [
        WebSearchTool(),  # 網路搜尋能力
        CodeInterpreterTool(),  # Python 程式碼執行能力
    ]

    analyst = Agent(
        name="Sentiment Analyst",
        instructions=sentiment_agent_instructions(),
        model=model_name,
        mcp_servers=mcp_servers,
        tools=custom_tools + hosted_tools,  # 合併自訂工具和 hosted tools
    )

    return analyst


async def get_sentiment_agent_tool(
    mcp_servers: list[Any],
    model_name: str = "gpt-4o-mini",
) -> Tool:
    """將市場情緒分析 Agent 包裝成工具"""
    analyst = await get_sentiment_agent(mcp_servers, model_name)
    return analyst.as_tool(
        tool_name="SentimentAnalyst",
        tool_description="""專業市場情緒分析 Agent,提供全面的心理面和資金面分析。

功能: 恐懼貪婪指數、資金流向追蹤、新聞情緒分析、社群情緒分析、情緒交易訊號

適用場景: 市場時機判斷、反向操作策略、短線交易、情緒面研究""",
    )
