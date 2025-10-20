"""Sentiment Agent - 市場情緒分析自主型 Agent

這個模組實作具有自主分析能力的市場情緒分析 Agent。
"""

from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from pydantic import BaseModel

from agents import Agent, function_tool, ModelSettings

from common.logger import logger

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gpt-5-mini")
DEFAULT_MAX_TURNS = os.getenv("DEFAULT_MAX_TURNS", 30)


# ===== Pydantic Models for Tool Parameters =====


class MarketData(BaseModel):
    """市場數據模型"""

    price_momentum: float = 50
    market_breadth: float = 50
    volatility: float = 50
    put_call_ratio: float = 50


class TradingData(BaseModel):
    """交易數據模型"""

    large_buy: float = 0
    large_sell: float = 0
    foreign_net: float = 0
    institutional_net: float = 0


class NewsItem(BaseModel):
    """新聞項目模型"""

    title: str
    content: str
    sentiment: float = 0  # -1 到 1
    timestamp: str


class SocialData(BaseModel):
    """社群數據模型"""

    mention_count: int = 0
    positive_mentions: int = 0
    negative_mentions: int = 0
    trending: bool = False


class IndexComponents(BaseModel):
    """恐懼貪婪指數組成分數"""

    price_momentum: float
    market_breadth: float
    volatility: float
    put_call_ratio: float


class FearGreedIndex(BaseModel):
    """恐懼貪婪指數模型"""

    index_value: float
    level: str
    components: IndexComponents
    interpretation: str


class MoneyFlow(BaseModel):
    """資金流向模型"""

    ticker: str
    net_flow: float
    flow_direction: str
    large_order_ratio: float
    foreign_attitude: str
    institutional_attitude: str
    interpretation: str


class NewsSentiment(BaseModel):
    """新聞情緒模型"""

    ticker: str | None
    news_count: int
    positive_ratio: float
    negative_ratio: float
    sentiment_score: float
    key_topics: list[str]
    interpretation: str


class SocialSentiment(BaseModel):
    """社群情緒模型"""

    ticker: str
    mention_count: int
    sentiment_ratio: float
    trending_status: str
    sentiment_score: float
    interpretation: str


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


@function_tool
def calculate_fear_greed_index(
    market_data: MarketData,
) -> str:
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
    logger.info("開始計算恐懼貪婪指數")

    momentum_score = market_data.price_momentum
    breadth_score = market_data.market_breadth
    volatility_score = 100 - market_data.volatility  # 波動率越高越恐慌
    put_call_score = 100 - market_data.put_call_ratio  # 賣權比越高越恐慌

    logger.debug(
        f"組成分數 | 動能: {momentum_score:.1f} | 寬度: {breadth_score:.1f} | "
        f"波動: {volatility_score:.1f} | 賣買權比: {put_call_score:.1f}"
    )

    # 加權平均
    index_value = (
        momentum_score * 0.3 + breadth_score * 0.3 + volatility_score * 0.25 + put_call_score * 0.15
    )

    # 等級判定
    if index_value >= 80:
        level = "極度貪婪"
        interpretation = "市場過熱，考慮獲利了結"
    elif index_value >= 60:
        level = "貪婪"
        interpretation = "市場樂觀，注意風險"
    elif index_value >= 40:
        level = "中性"
        interpretation = "市場平穩，等待機會"
    elif index_value >= 20:
        level = "恐懼"
        interpretation = "市場悲觀，可能接近底部"
    else:
        level = "極度恐慌"
        interpretation = "市場恐慌，考慮逢低買進"

    logger.info(f"恐懼貪婪指數計算完成 | 指數: {index_value:.2f} | 等級: {level}")

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


@function_tool
def analyze_money_flow(
    ticker: str,
    trading_data: TradingData,
) -> str:
    """分析資金流向

    Args:
        ticker: 股票代號 (例如: "2330")
        trading_data: 交易數據,包含:
            - large_buy: 大單買進
            - large_sell: 大單賣出
            - foreign_net: 外資淨買賣
            - institutional_net: 法人淨買賣

    Returns:
        dict: 資金流向分析
            {
                "ticker": "2330",
                "net_flow": float,          # 淨流入金額
                "flow_direction": str,      # 流入/流出/平衡
                "large_order_ratio": float, # 大單佔比
                "foreign_attitude": str,    # 外資態度
                "interpretation": str
            }
    """
    logger.info(f"開始分析資金流向 | 股票: {ticker}")

    large_buy = trading_data.large_buy
    large_sell = trading_data.large_sell
    foreign_net = trading_data.foreign_net
    institutional_net = trading_data.institutional_net

    logger.debug(
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
        foreign_attitude = "買超" if foreign_net > 10000000 else "小買"
    elif foreign_net < 0:
        foreign_attitude = "賣超" if abs(foreign_net) > 10000000 else "小賣"
    else:
        foreign_attitude = "觀望"

    interpretation = f"資金呈{flow_strength}{flow_direction}態勢,外資{foreign_attitude}"

    logger.info(
        f"資金流向分析完成 | 股票: {ticker} | 淨流: {net_flow:,.0f} | "
        f"方向: {flow_direction} | 外資: {foreign_attitude}"
    )

    return {
        "ticker": ticker,
        "net_flow": net_flow,
        "flow_direction": flow_direction,
        "large_order_ratio": large_order_ratio,
        "foreign_attitude": foreign_attitude,
        "institutional_attitude": "買超" if institutional_net > 0 else "賣超",
        "interpretation": interpretation,
    }


@function_tool
def analyze_news_sentiment(
    ticker: str | None,
    news_data: list[NewsItem],
) -> str:
    """分析新聞情緒

    Args:
        ticker: 股票代號 (可選,None 表示整體市場)
        news_data: 新聞列表,每筆包含:
            - title: 標題
            - content: 內容
            - sentiment: 情緒分數 (-1 到 1)
            - timestamp: 時間

    Returns:
        dict: 新聞情緒分析
            {
                "ticker": str,
                "news_count": int,
                "positive_ratio": float,
                "negative_ratio": float,
                "sentiment_score": float,   # -100 到 100
                "key_topics": [str, ...],
                "interpretation": str
            }
    """
    target = ticker or "市場"

    logger.info(f"開始分析新聞情緒 | 標的: {target} | 新聞數: {len(news_data)}")

    if not news_data:
        logger.warning(f"無新聞數據 | 標的: {target}")
        return {
            "error": "無新聞數據",
            "ticker": ticker,
            "news_count": 0,
            "sentiment_score": 0,
        }

    news_count = len(news_data)
    sentiments = [news.sentiment for news in news_data]

    positive_count = sum(1 for s in sentiments if s > 0.2)
    negative_count = sum(1 for s in sentiments if s < -0.2)

    logger.debug(
        f"情緒分布 | 正面: {positive_count} | 負面: {negative_count} | "
        f"中性: {news_count - positive_count - negative_count}"
    )

    positive_ratio = positive_count / news_count if news_count > 0 else 0
    negative_ratio = negative_count / news_count if news_count > 0 else 0

    # 計算整體情緒分數 (-100 到 100)
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    sentiment_score = avg_sentiment * 100

    # 解讀
    if sentiment_score > 50:
        interpretation = "新聞情緒極度正面，市場情緒樂觀"
    elif sentiment_score > 20:
        interpretation = "新聞情緒偏正面，市場氛圍良好"
    elif sentiment_score > -20:
        interpretation = "新聞情緒中性，市場觀望"
    elif sentiment_score > -50:
        interpretation = "新聞情緒偏負面，市場擔憂"
    else:
        interpretation = "新聞情緒極度負面，市場悲觀"

    logger.info(
        f"新聞情緒分析完成 | 標的: {target} | 分數: {sentiment_score:.1f} | "
        f"正面: {positive_ratio:.1%} | 負面: {negative_ratio:.1%}"
    )

    return {
        "ticker": ticker,
        "news_count": news_count,
        "positive_ratio": positive_ratio,
        "negative_ratio": negative_ratio,
        "sentiment_score": sentiment_score,
        "key_topics": [],  # 可以擴展實作關鍵詞提取
        "interpretation": interpretation,
    }


@function_tool
def analyze_social_sentiment(
    ticker: str,
    social_data: SocialData,
) -> str:
    """分析社群媒體情緒

    Args:
        ticker: 股票代號 (例如: "2330")
        social_data: 社群數據,包含:
            - mention_count: 提及次數
            - positive_mentions: 正面提及
            - negative_mentions: 負面提及
            - trending: 是否熱門

    Returns:
        dict: 社群情緒分析
            {
                "ticker": "2330",
                "mention_count": int,
                "sentiment_ratio": float,    # 正負面比
                "trending_status": str,      # 熱度狀態
                "sentiment_score": float,    # -100 到 100
                "interpretation": str
            }
    """
    logger.info(f"開始分析社群情緒 | 股票: {ticker}")

    mention_count = social_data.mention_count
    positive = social_data.positive_mentions
    negative = social_data.negative_mentions
    trending = social_data.trending

    if mention_count == 0:
        logger.warning(f"無社群數據 | 股票: {ticker}")
        return {
            "error": "無社群數據",
            "ticker": ticker,
            "mention_count": 0,
            "sentiment_score": 0,
        }

    logger.debug(
        f"社群數據 | 提及: {mention_count} | 正面: {positive} | 負面: {negative} | 熱門: {trending}"
    )

    # 計算情緒比例
    total_sentiment = positive + negative
    if total_sentiment > 0:
        sentiment_ratio = (positive - negative) / total_sentiment
    else:
        sentiment_ratio = 0

    sentiment_score = sentiment_ratio * 100

    # 熱度狀態
    if mention_count > 1000:
        trending_status = "極度熱門"
    elif mention_count > 500:
        trending_status = "熱門"
    elif mention_count > 100:
        trending_status = "中等關注"
    else:
        trending_status = "低關注"

    # 解讀
    if sentiment_score > 50:
        interpretation = f"社群高度看好，{trending_status}"
    elif sentiment_score > 20:
        interpretation = f"社群偏向樂觀，{trending_status}"
    elif sentiment_score > -20:
        interpretation = f"社群態度中性，{trending_status}"
    elif sentiment_score > -50:
        interpretation = f"社群偏向悲觀，{trending_status}"
    else:
        interpretation = f"社群高度看壞，{trending_status}"

    logger.info(
        f"社群情緒分析完成 | 股票: {ticker} | 分數: {sentiment_score:.1f} | "
        f"熱度: {trending_status} | 提及: {mention_count}"
    )

    return {
        "ticker": ticker,
        "mention_count": mention_count,
        "sentiment_ratio": sentiment_ratio,
        "trending_status": trending_status,
        "sentiment_score": sentiment_score,
        "interpretation": interpretation,
    }


@function_tool
def generate_sentiment_signals(
    fear_greed_index: FearGreedIndex,
    money_flow: MoneyFlow,
    news_sentiment: NewsSentiment,
    social_sentiment: SocialSentiment,
) -> str:
    """產生情緒交易訊號

    Args:
        fear_greed_index: 恐懼貪婪指數 (來自 calculate_fear_greed_index)
        money_flow: 資金流向分析 (來自 analyze_money_flow)
        news_sentiment: 新聞情緒 (來自 analyze_news_sentiment)
        social_sentiment: 社群情緒 (來自 analyze_social_sentiment)

    Returns:
        dict: 情緒交易訊號
            {
                "overall_signal": str,      # "買進" | "賣出" | "觀望"
                "confidence": float,        # 信心度 0-1
                "strategy": str,            # "反向" | "順勢" | "觀望"
                "reasoning": [str, ...],    # 分析理由
                "risk_level": str,          # "高" | "中" | "低"
                "timestamp": str
            }
    """
    logger.info("開始產生情緒交易訊號")

    signals = []
    confidence = 0.5
    reasoning = []

    # 分析恐懼貪婪指數
    fg_value = fear_greed_index.index_value
    if fg_value >= 80:
        signals.append("賣出")
        reasoning.append(f"恐懼貪婪指數過高 ({fg_value:.0f})，市場過熱")
        confidence += 0.15
    elif fg_value <= 20:
        signals.append("買進")
        reasoning.append(f"恐懼貪婪指數過低 ({fg_value:.0f})，市場恐慌")
        confidence += 0.15

    # 分析資金流向
    flow_direction = money_flow.flow_direction
    if flow_direction == "流入":
        signals.append("買進")
        reasoning.append("資金持續流入，多方力量強勁")
        confidence += 0.1
    elif flow_direction == "流出":
        signals.append("賣出")
        reasoning.append("資金流出明顯，空方佔優")
        confidence += 0.1

    # 分析新聞情緒
    news_score = news_sentiment.sentiment_score
    if news_score > 50:
        signals.append("買進")
        reasoning.append(f"新聞情緒極度正面 ({news_score:.0f})")
        confidence += 0.05
    elif news_score < -50:
        signals.append("賣出")
        reasoning.append(f"新聞情緒極度負面 ({news_score:.0f})")
        confidence += 0.05

    # 分析社群情緒
    social_score = social_sentiment.sentiment_score
    if social_score > 50:
        signals.append("買進")
        reasoning.append(f"社群高度看好 ({social_score:.0f})")
        confidence += 0.05
    elif social_score < -50:
        signals.append("賣出")
        reasoning.append(f"社群高度看壞 ({social_score:.0f})")
        confidence += 0.05

    logger.debug(f"訊號彙總 | 買進: {signals.count('買進')} | 賣出: {signals.count('賣出')}")

    # 決定整體訊號
    buy_count = signals.count("買進")
    sell_count = signals.count("賣出")

    if buy_count > sell_count and buy_count >= 2:
        overall_signal = "買進"
        strategy = "順勢" if fg_value < 60 else "反向"
    elif sell_count > buy_count and sell_count >= 2:
        overall_signal = "賣出"
        strategy = "順勢" if fg_value > 40 else "反向"
    else:
        overall_signal = "觀望"
        strategy = "觀望"

    # 風險評估
    if confidence > 0.75:
        risk_level = "低"
    elif confidence > 0.60:
        risk_level = "中"
    else:
        risk_level = "高"

    confidence = min(0.95, confidence)

    logger.info(
        f"情緒訊號產生完成 | 訊號: {overall_signal} | 策略: {strategy} | "
        f"信心度: {confidence:.1%} | 風險: {risk_level}"
    )

    return {
        "overall_signal": overall_signal,
        "confidence": confidence,
        "strategy": strategy,
        "reasoning": reasoning,
        "risk_level": risk_level,
        "timestamp": datetime.now().isoformat(),
    }


async def get_sentiment_agent(
    model_name: str = None,
    mcp_servers: list | None = None,
    openai_tools: list | None = None,
) -> Agent:
    """創建市場情緒分析 Agent

    Args:
        model_name: 使用的 AI 模型名稱
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入
        openai_tools: 從 TradingAgent 傳入的共用工具（WebSearchTool, CodeInterpreterTool）

    Returns:
        Agent: 配置好的市場情緒分析 Agent

    Note:
        Timeout 由主 TradingAgent 的 execution_timeout 統一控制，
        sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制。
    """
    logger.info(f"get_sentiment_agent() called with model={model_name}")

    logger.debug("Creating custom tools with function_tool")
    custom_tools = [
        calculate_fear_greed_index,
        analyze_money_flow,
        analyze_news_sentiment,
        analyze_social_sentiment,
        generate_sentiment_signals,
    ]

    # 合併自訂工具和共用工具
    all_tools = custom_tools + (openai_tools or [])
    logger.debug(f"Total tools (custom + shared): {len(all_tools)}")

    logger.info(
        f"Creating Agent with model={model_name}, "
        f"mcp_servers={len(mcp_servers) if mcp_servers else 0}, tools={len(all_tools)}"
    )
    analyst = Agent(
        name="Sentiment Analyst",
        instructions=sentiment_agent_instructions(),
        model=model_name,
        mcp_servers=mcp_servers,
        tools=all_tools,
        model_settings=ModelSettings(
            tool_choice="required",
            max_completion_tokens=500,  # 控制回答長度，避免過度冗長
        ),
    )
    logger.info("Sentiment Analyst Agent created successfully")

    return analyst
