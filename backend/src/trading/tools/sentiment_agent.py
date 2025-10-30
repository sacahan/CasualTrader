"""Sentiment Agent - 市場情緒分析自主型 Agent

這個模組實作具有自主分析能力的市場情緒分析 Agent。
"""

from __future__ import annotations

import os
import json
from typing import Any
from datetime import datetime

from dotenv import load_dotenv
from pydantic import BaseModel

from agents import Agent, function_tool, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel

from common.logger import logger

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gpt-5-mini")
DEFAULT_MAX_TURNS = os.getenv("DEFAULT_MAX_TURNS", 30)


# ==========================================
# 參數驗證和容錯 Helper 函數
# ==========================================


def parse_tool_params(
    **kwargs,
) -> dict[str, Any]:
    """
    解析和驗證 AI Agent 傳入的參數。

    處理多種情況：
    1. 直接的參數：symbol="2330", quantity=1000
    2. JSON 字串參數：args='{"symbol":"2330","quantity":1000}'
    3. 單個 'input' 參數（某些 sub-agent 呼叫方式）

    Args:
        **kwargs: 傳入的所有參數

    Returns:
        解析後的參數字典
    """
    # 嘗試從 'args' 參數中解析 JSON
    if "args" in kwargs and isinstance(kwargs["args"], str):
        try:
            parsed = json.loads(kwargs["args"])
            logger.debug(f"成功從 JSON 字串解析參數: {parsed}")
            return parsed
        except json.JSONDecodeError:
            logger.debug(f"無法解析 args 中的 JSON: {kwargs['args']}")

    # 移除無效的參數（例如 input_image）
    result = {}
    for k, v in kwargs.items():
        if k not in ["args", "input", "input_image"]:
            result[k] = v

    return result


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
    """情緒分析 Agent 的指令定義（簡化版，帶記憶追蹤）"""
    return f"""你是情緒分析專家。評估市場情緒、分析資金流向、生成情緒驅動的交易訊號。
持續追蹤：先查詢 memory_mcp 歷史情緒，對比情緒轉變，識別極端點。

## 專業能力

- 市場情緒指標（Fear & Greed、隱含波動率、極端情緒）
- 資金流向分析（大宗交易、機構動向、融資融券）
- 新聞與社群情緒（透過 tavily_mcp 搜尋最新新聞、社交熱度、輿情分析）
- 情緒反轉訊號識別（極端情緒警告、機會預警）
- 情緒交易策略（訊號生成、時機把握）

## 🎯 tavily_mcp 使用限制

⚠️ **重要**：tavily_mcp 使用需要消耗點數，請遵守以下原則：
  - 只在需要時使用（優先檢查 memory_mcp 中的歷史情緒）
  - 搜尋當日或近日重大新聞（不搜尋舊聞）
  - 單次搜尋≤3個關鍵詞，避免重複查詢
  - 若新聞充分反映情緒，不必繼續搜尋
  - 專注於對市場情緒有實質影響的新聞
  - 每次分析最多進行 1 次搜尋

## 執行流程

**步驟 0：檢查記憶庫** → memory_mcp
  - 無訊號 → 完整分析
  - 新鮮（≤1 天）→ 增量更新
  - 陳舊（>1 天）→ 完整重新分析 + 對比

**步驟 1-3：情緒數據收集** → casual_market_mcp + tools
  1. 收集市場情緒數據和成交量
  2. 計算恐懼貪婪指數 → calculate_fear_greed_index
  3. 分析資金流向 → analyze_money_flow

**步驟 4-6：新聞與社群** → tavily_mcp + tools
  4. 透過 tavily_mcp 搜尋即時新聞 → analyze_news_sentiment
  5. 分析社群情緒 → analyze_social_sentiment
  6. 生成訊號 → generate_sentiment_signals

**步驟 7：對比與保存** → memory_mcp
  - 若有先前訊號：對比情緒級別、資金流向、新聞風向
  - 保存結果（含時間戳、情緒評分、訊號、轉變理由）

## 工具調用

- **calculate_fear_greed_index** → 計算恐懼貪婪指數 (-100 到 +100)
- **analyze_money_flow** → 分析資金流向和機構動向
- **analyze_news_sentiment** → 評估新聞整體情緒 (負面/中立/正面)
- **analyze_social_sentiment** → 分析社群討論情緒和聲量
- **generate_sentiment_signals** → 生成情緒交易訊號

## 輸出結構

- 市場情緒評分 (-100 到 +100, -100 極恐懼, +100 極貪婪)
- 情緒階段 (恐慌/悲觀/中立/樂觀/狂熱)
- 資金流向 (買盤優勢/賣盤優勢/均衡)
- 新聞情緒 (負面/中立/正面) + 重大新聞摘要
- 社群聲量 (上升/下降/穩定)
- 極端檢測 (是否達到極端恐懼或貪婪)
- 交易訊號 (買賣建議、時機評估)
- 信心度 (0-100%)
- [若有先前訊號] 變化分析 (情緒轉變、資金流向變化)

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


@function_tool(strict_mode=False)
def calculate_fear_greed_index(
    market_data: MarketData = None,
    **kwargs,
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
    try:
        logger.info("開始計算恐懼貪婪指數")

        # 參數驗證和容錯
        params = parse_tool_params(market_data=market_data, **kwargs)

        # 如果 market_data 仍為 None，使用預設值
        if not market_data and not params.get("market_data"):
            logger.warning("缺少 market_data 參數，使用預設值")
            market_data = MarketData()
        elif params.get("market_data"):
            if isinstance(params["market_data"], dict):
                market_data = MarketData(**params["market_data"])
            else:
                market_data = params["market_data"]

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
            momentum_score * 0.3
            + breadth_score * 0.3
            + volatility_score * 0.25
            + put_call_score * 0.15
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

    except Exception as e:
        logger.error(f"計算恐懼貪婪指數失敗: {e}", exc_info=True)
        # 返回中性值而不是拋出異常
        return {
            "index_value": 50,
            "level": "中性（計算失敗）",
            "components": {
                "price_momentum": 50,
                "market_breadth": 50,
                "volatility": 50,
                "put_call_ratio": 50,
            },
            "interpretation": f"指數計算發生錯誤: {str(e)}",
        }


@function_tool(strict_mode=False)
def analyze_money_flow(
    ticker: str = None,
    trading_data: TradingData = None,
    **kwargs,
) -> str:
    """分析資金流向

    Args:
        ticker: 股票代號 (例如: "2330")
        trading_data: 交易數據,包含:
            - large_buy: 大單買進
            - large_sell: 大單賣出
            - foreign_net: 外資淨買賣
            - institutional_net: 法人淨買賣
        **kwargs: 額外參數（用於容錯）

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
    try:
        # 參數驗證和容錯
        params = parse_tool_params(ticker=ticker, trading_data=trading_data, **kwargs)

        _ticker = params.get("ticker") or ticker
        _trading_data = params.get("trading_data") or trading_data

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {
                "error": "缺少必要參數: ticker",
                "net_flow": 0,
                "flow_direction": "平衡",
                "large_order_ratio": 0,
                "foreign_attitude": "未知",
                "interpretation": "無法分析，缺少股票代號",
            }

        # 如果 trading_data 為 None，使用預設值
        if not _trading_data:
            logger.warning("缺少 trading_data 參數，使用預設值")
            _trading_data = {
                "large_buy": 0,
                "large_sell": 0,
                "foreign_net": 0,
                "institutional_net": 0,
            }
        elif isinstance(_trading_data, dict):
            # 確保字典有必要的鍵
            pass
        else:
            # 如果是 Pydantic 模型，轉換為字典
            if hasattr(_trading_data, "dict"):
                _trading_data = _trading_data.dict()
            elif hasattr(_trading_data, "model_dump"):
                _trading_data = _trading_data.model_dump()

        logger.info(f"開始分析資金流向 | 股票: {_ticker}")

        large_buy = _trading_data.get("large_buy", 0)
        large_sell = _trading_data.get("large_sell", 0)
        foreign_net = _trading_data.get("foreign_net", 0)
        institutional_net = _trading_data.get("institutional_net", 0)

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
            f"資金流向分析完成 | 股票: {_ticker} | 淨流: {net_flow:,.0f} | "
            f"方向: {flow_direction} | 外資: {foreign_attitude}"
        )

        return {
            "ticker": _ticker,
            "net_flow": net_flow,
            "flow_direction": flow_direction,
            "large_order_ratio": large_order_ratio,
            "foreign_attitude": foreign_attitude,
            "institutional_attitude": "買超" if institutional_net > 0 else "賣超",
            "interpretation": interpretation,
        }

    except Exception as e:
        logger.error(f"分析資金流向失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "net_flow": 0,
            "flow_direction": "平衡",
            "large_order_ratio": 0,
            "foreign_attitude": "未知",
            "institutional_attitude": "未知",
            "interpretation": f"分析失敗: {str(e)}",
        }


@function_tool(strict_mode=False)
def analyze_news_sentiment(
    ticker: str = None,
    news_data: list = None,
    **kwargs,
) -> str:
    """分析新聞情緒

    Args:
        ticker: 股票代號 (可選,None 表示整體市場)
        news_data: 新聞列表,每筆包含:
            - title: 標題
            - content: 內容
            - sentiment: 情緒分數 (-1 到 1)
            - timestamp: 時間
        **kwargs: 額外參數（用於容錯）

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
    try:
        # 參數驗證和容錯
        params = parse_tool_params(ticker=ticker, news_data=news_data, **kwargs)

        _ticker = params.get("ticker") or ticker
        _news_data = params.get("news_data") or news_data

        # 如果 news_data 為 None，使用空列表
        if not _news_data:
            logger.warning("缺少 news_data 參數，使用空列表")
            _news_data = []

        # 轉換字典為 NewsItem 物件
        if _news_data and isinstance(_news_data[0], dict):
            _news_data = [
                NewsItem(**item) if isinstance(item, dict) else item for item in _news_data
            ]

        target = _ticker or "市場"
        logger.info(f"開始分析新聞情緒 | 標的: {target} | 新聞數: {len(_news_data)}")

        if not _news_data:
            logger.warning(f"無新聞數據 | 標的: {target}")
            return {
                "error": "無新聞數據",
                "ticker": _ticker,
                "news_count": 0,
                "positive_ratio": 0,
                "negative_ratio": 0,
                "sentiment_score": 0,
                "key_topics": [],
                "interpretation": "無可用新聞數據",
            }

        news_count = len(_news_data)
        sentiments = [news.sentiment for news in _news_data]

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
            "ticker": _ticker,
            "news_count": news_count,
            "positive_ratio": positive_ratio,
            "negative_ratio": negative_ratio,
            "sentiment_score": sentiment_score,
            "key_topics": [],  # 可以擴展實作關鍵詞提取
            "interpretation": interpretation,
        }

    except Exception as e:
        logger.error(f"分析新聞情緒失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "news_count": 0,
            "positive_ratio": 0,
            "negative_ratio": 0,
            "sentiment_score": 0,
            "key_topics": [],
            "interpretation": f"分析失敗: {str(e)}",
        }


@function_tool(strict_mode=False)
def analyze_social_sentiment(
    ticker: str = None,
    social_data: SocialData = None,
    **kwargs,
) -> str:
    """分析社群媒體情緒

    Args:
        ticker: 股票代號 (例如: "2330")
        social_data: 社群數據,包含:
            - mention_count: 提及次數
            - positive_mentions: 正面提及
            - negative_mentions: 負面提及
            - trending: 是否熱門
        **kwargs: 額外參數（用於容錯）

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
    try:
        # 參數驗證和容錯
        params = parse_tool_params(ticker=ticker, social_data=social_data, **kwargs)

        _ticker = params.get("ticker") or ticker
        _social_data = params.get("social_data") or social_data

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {
                "error": "缺少必要參數: ticker",
                "ticker": _ticker,
                "mention_count": 0,
                "sentiment_ratio": 0,
                "trending_status": "未知",
                "sentiment_score": 0,
                "interpretation": "無法分析，缺少股票代號",
            }

        # 如果 social_data 為 None，使用預設值
        if not _social_data:
            logger.warning("缺少 social_data 參數，使用預設值")
            _social_data = {
                "mention_count": 0,
                "positive_mentions": 0,
                "negative_mentions": 0,
                "trending": False,
            }
        elif isinstance(_social_data, dict):
            # 確保字典有必要的鍵
            pass
        else:
            # 如果是 Pydantic 模型，轉換為字典
            if hasattr(_social_data, "dict"):
                _social_data = _social_data.dict()
            elif hasattr(_social_data, "model_dump"):
                _social_data = _social_data.model_dump()

        logger.info(f"開始分析社群情緒 | 股票: {_ticker}")

        mention_count = _social_data.get("mention_count", 0)
        positive = _social_data.get("positive_mentions", 0)
        negative = _social_data.get("negative_mentions", 0)
        trending = _social_data.get("trending", False)

        if mention_count == 0:
            logger.warning(f"無社群數據 | 股票: {_ticker}")
            return {
                "error": "無社群數據",
                "ticker": _ticker,
                "mention_count": 0,
                "sentiment_ratio": 0,
                "trending_status": "低關注",
                "sentiment_score": 0,
                "interpretation": "無社群提及數據",
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
            f"社群情緒分析完成 | 股票: {_ticker} | 分數: {sentiment_score:.1f} | "
            f"熱度: {trending_status} | 提及: {mention_count}"
        )

        return {
            "ticker": _ticker,
            "mention_count": mention_count,
            "sentiment_ratio": sentiment_ratio,
            "trending_status": trending_status,
            "sentiment_score": sentiment_score,
            "interpretation": interpretation,
        }

    except Exception as e:
        logger.error(f"分析社群情緒失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "mention_count": 0,
            "sentiment_ratio": 0,
            "trending_status": "未知",
            "sentiment_score": 0,
            "interpretation": f"分析失敗: {str(e)}",
        }


@function_tool(strict_mode=False)
def generate_sentiment_signals(
    fear_greed_index: dict = None,
    money_flow: dict = None,
    news_sentiment: dict = None,
    social_sentiment: dict = None,
    **kwargs,
) -> str:
    """產生情緒交易訊號

    Args:
        fear_greed_index: 恐懼貪婪指數 (來自 calculate_fear_greed_index)
        money_flow: 資金流向分析 (來自 analyze_money_flow)
        news_sentiment: 新聞情緒 (來自 analyze_news_sentiment)
        social_sentiment: 社群情緒 (來自 analyze_social_sentiment)
        **kwargs: 額外參數（用於容錯）

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
    try:
        # 參數驗證和容錯
        params = parse_tool_params(
            fear_greed_index=fear_greed_index,
            money_flow=money_flow,
            news_sentiment=news_sentiment,
            social_sentiment=social_sentiment,
            **kwargs,
        )

        _fear_greed_index = params.get("fear_greed_index") or fear_greed_index
        _money_flow = params.get("money_flow") or money_flow
        _news_sentiment = params.get("news_sentiment") or news_sentiment
        _social_sentiment = params.get("social_sentiment") or social_sentiment

        # 使用預設值以防參數缺失
        if not _fear_greed_index:
            logger.warning("缺少 fear_greed_index 參數，使用預設值")
            _fear_greed_index = {"index_value": 50}

        if not _money_flow:
            logger.warning("缺少 money_flow 參數，使用預設值")
            _money_flow = {"flow_direction": "平衡"}

        if not _news_sentiment:
            logger.warning("缺少 news_sentiment 參數，使用預設值")
            _news_sentiment = {"sentiment_score": 0}

        if not _social_sentiment:
            logger.warning("缺少 social_sentiment 參數，使用預設值")
            _social_sentiment = {"sentiment_score": 0}

        logger.info("開始產生情緒交易訊號")

        signals = []
        confidence = 0.5
        reasoning = []

        # 分析恐懼貪婪指數
        fg_value = _fear_greed_index.get("index_value", 50)
        if fg_value >= 80:
            signals.append("賣出")
            reasoning.append(f"恐懼貪婪指數過高 ({fg_value:.0f})，市場過熱")
            confidence += 0.15
        elif fg_value <= 20:
            signals.append("買進")
            reasoning.append(f"恐懼貪婪指數過低 ({fg_value:.0f})，市場恐慌")
            confidence += 0.15

        # 分析資金流向
        flow_direction = _money_flow.get("flow_direction", "平衡")
        if flow_direction == "流入":
            signals.append("買進")
            reasoning.append("資金持續流入，多方力量強勁")
            confidence += 0.1
        elif flow_direction == "流出":
            signals.append("賣出")
            reasoning.append("資金流出明顯，空方佔優")
            confidence += 0.1

        # 分析新聞情緒
        news_score = _news_sentiment.get("sentiment_score", 0)
        if news_score > 50:
            signals.append("買進")
            reasoning.append(f"新聞情緒極度正面 ({news_score:.0f})")
            confidence += 0.05
        elif news_score < -50:
            signals.append("賣出")
            reasoning.append(f"新聞情緒極度負面 ({news_score:.0f})")
            confidence += 0.05

        # 分析社群情緒
        social_score = _social_sentiment.get("sentiment_score", 0)
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

    except Exception as e:
        logger.error(f"產生情緒訊號失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "overall_signal": "觀望",
            "confidence": 0.3,
            "strategy": "觀望",
            "reasoning": [f"訊號生成失敗: {str(e)}"],
            "risk_level": "高",
            "timestamp": datetime.now().isoformat(),
        }


async def get_sentiment_agent(
    llm_model: LitellmModel = None,
    extra_headers: dict[str, str] = None,
    mcp_servers: list | None = None,
) -> Agent:
    """創建市場情緒分析 Agent

    Args:
        llm_model: 使用的語言模型實例 (LitellmModel)，如果為 None，則使用預設模型
        extra_headers: 額外的 HTTP 標頭，用於模型 API 請求
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入

    Returns:
        Agent: 配置好的市場情緒分析 Agent

    Note:
        - 不使用 WebSearchTool 和 CodeInterpreterTool（託管工具不支援 ChatCompletions API）
        - 只使用自訂工具進行情緒分析
        - Timeout 由主 TradingAgent 的 execution_timeout 統一控制
        - Sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制
    """
    logger.info(f"get_sentiment_agent() called with model={llm_model}")

    logger.debug("Creating custom tools with function_tool")
    all_tools = [
        calculate_fear_greed_index,
        analyze_money_flow,
        analyze_news_sentiment,
        analyze_social_sentiment,
        generate_sentiment_signals,
    ]
    logger.debug(f"Total tools: {len(all_tools)}")

    logger.info(
        f"Creating Agent with model={llm_model}, mcp_servers={len(mcp_servers)}, tools={len(all_tools)}"
    )

    # GitHub Copilot 不支援 tool_choice 參數
    model_settings_dict = {
        "max_completion_tokens": 500,  # 控制回答長度，避免過度冗長
    }

    # 只有非 GitHub Copilot 模型才支援 tool_choice
    model_name = llm_model.model if llm_model else ""
    if "github_copilot" not in model_name.lower():
        model_settings_dict["tool_choice"] = "required"

    if extra_headers:
        model_settings_dict["extra_headers"] = extra_headers

    analyst = Agent(
        name="sentiment_analyst",
        instructions=sentiment_agent_instructions(),
        model=llm_model,
        mcp_servers=mcp_servers,
        tools=all_tools,
        model_settings=ModelSettings(**model_settings_dict),
    )
    logger.info("Sentiment Analyst Agent created successfully")

    return analyst
