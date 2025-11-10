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
# 全局 MCP 伺服器上下文
# ==========================================

# 用於存儲 async 工具可以訪問的 MCP 伺服器實例
_sentiment_agent_context = {
    "tavily_mcp": None,
}


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


# ==========================================
# MCP 工具呼叫輔助函數
# ==========================================


def _parse_detailed_results(text_content: str) -> list[dict[str, Any]]:
    """
    解析 Tavily 返回的 'Detailed Results' 純文本格式。

    格式示例：
    Detailed Results:

    Title: [標的] 2881富邦金說好的教訓呢QQ? - 看板Stock - PTT網頁版
    URL: https://www.pttweb.cc/bbs/Stock/M.1652840005.A.CB4
    Content: 標的：2881.TW 富邦金2. 分類：討論3. 分析/正文： 這幾天大家一直保單問題...

    Args:
        text_content: Tavily 返回的純文本內容

    Returns:
        搜尋結果列表，每筆包含 title, url, content, source, timestamp
    """
    results = []

    try:
        # 移除 "Detailed Results:" 頭部
        content = text_content
        if "Detailed Results:" in content:
            content = content.split("Detailed Results:", 1)[1]

        # 按 "Title:" 分割結果
        result_blocks = content.split("\nTitle:")

        for block in result_blocks:
            title = None
            url = None
            content_text = None

            # 清理 block，移除開始的空白
            block = block.strip()
            if not block:
                continue

            # 解析第一行（可能是 title 或以 Title: 開頭的內容）
            if block.startswith("Title:"):
                block = block[6:]  # 移除 "Title:" 前綴

            lines = block.split("\n")

            # 第一行是 title
            if len(lines) > 0:
                title = lines[0].strip()

            # 查找 URL 和 Content
            for line in lines[1:]:
                line = line.strip()
                if line.startswith("URL:"):
                    url = line[4:].strip()
                elif line.startswith("Content:"):
                    content_text = line[8:].strip()
                elif url is None and line.startswith("http"):
                    # 如果沒有 "URL:" 標籤但看起來是 URL
                    url = line
                elif content_text is None and url is not None:
                    # 如果已有 URL 但沒有 Content，則後續行視為 content
                    content_text = line

            # 只有在有 title 和 url 時才添加結果
            if title and url:
                results.append(
                    {
                        "title": title,
                        "url": url,
                        "content": content_text or "",
                        "source": "tavily-search",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return results

    except Exception as e:
        logger.warning(f"解析 'Detailed Results' 格式時發生錯誤: {e}")
        return []


async def _call_tavily_search(
    mcp_server,
    query: str,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """
    透過 tavily_mcp 搜尋新聞。

    Args:
        mcp_server: tavily_mcp MCPServerStdio 實例
        query: 搜尋查詢
        max_results: 最大結果數

    Returns:
        搜尋結果列表，每筆包含：
        - title: 新聞標題
        - url: 連結
        - content: 新聞內容摘要
        - source: 來源
        - timestamp: 發佈時間
    """
    try:
        if not mcp_server:
            logger.warning("tavily_mcp 不可用，無法執行搜尋")
            return []

        logger.debug(f"開始 tavily 搜尋: {query}")

        result = await mcp_server.session.call_tool(
            "tavily-search",
            {
                "query": query,
                "max_results": max_results,
                "include_images": False,
                "include_answer": True,
            },
        )

        # 解析 MCP 返回值結構: result.content[0].text (JSON string)
        if not result or not hasattr(result, "content") or not result.content:
            logger.warning(
                f"tavily 搜尋返回空結果 | 查詢: {query} | "
                f"result: {result} | result type: {type(result).__name__}"
            )
            return []

        # 添加調試日誌
        logger.debug(
            f"tavily 返回結果 | 查詢: {query} | "
            f"result type: {type(result).__name__} | "
            f"content length: {len(result.content)} | "
            f"content[0] type: {type(result.content[0]).__name__}"
        )

        content_item = result.content[0]

        # 嘗試多種方式提取文本內容
        text_content = None
        if hasattr(content_item, "text"):
            text_content = content_item.text
        elif isinstance(content_item, str):
            text_content = content_item
        elif hasattr(content_item, "text_content"):
            text_content = content_item.text_content
        elif hasattr(content_item, "message"):
            text_content = content_item.message
        else:
            text_content = str(content_item) if content_item else None

        # 檢查返回內容是否為空或非 JSON
        if not text_content or not text_content.strip():
            logger.warning(
                f"tavily 搜尋返回空內容 | 查詢: {query} | "
                f"content_item type: {type(content_item).__name__} | "
                f"content_item dir: {[attr for attr in dir(content_item) if not attr.startswith('_')]} | "
                f"text_content: '{text_content}'"
            )
            return []

        # 嘗試解析 JSON 或 "Detailed Results" 格式
        search_results = []

        # 首先嘗試解析 JSON 格式
        try:
            data = json.loads(text_content)
            search_results = data.get("results", [])
            logger.debug(f"成功解析 JSON 格式，取得 {len(search_results)} 筆結果")
        except json.JSONDecodeError:
            # 嘗試解析 "Detailed Results" 純文本格式
            if "Detailed Results:" in text_content or "Title:" in text_content:
                logger.debug("偵測到 'Detailed Results' 純文本格式，開始解析")
                search_results = _parse_detailed_results(text_content)
                logger.debug(f"成功解析 'Detailed Results' 格式，取得 {len(search_results)} 筆結果")
            else:
                # 既非 JSON 也非 Detailed Results 格式
                logger.warning(
                    f"無法解析 tavily 返回的內容 | 查詢: {query} | "
                    f"返回內容（前200字）: {text_content[:200] if text_content else 'EMPTY'} | "
                    f"返回內容完整長度: {len(text_content)}"
                )
                return []

        logger.debug(f"tavily 搜尋完成，取得 {len(search_results)} 筆結果")

        return search_results

    except Exception as e:
        logger.error(f"tavily 搜尋失敗: {e}", exc_info=True)
        return []


def _extract_sentiment_from_text(text: str) -> float:
    """
    簡單的文本情緒分析。

    使用關鍵詞匹配進行快速情緒評分。

    Args:
        text: 文本內容

    Returns:
        情緒分數 (-1.0 到 1.0)
    """
    if not text:
        return 0.0

    text_lower = text.lower()

    # 正面詞彙
    positive_words = [
        "買超",
        "上升",
        "利好",
        "看好",
        "增長",
        "強勁",
        "上漲",
        "突破",
        "創新高",
        "超預期",
        "成長",
        "樂觀",
        "向上",
        "漲幅",
    ]

    # 負面詞彙
    negative_words = [
        "賣超",
        "下跌",
        "利空",
        "看壞",
        "下降",
        "疲弱",
        "下滑",
        "破位",
        "創新低",
        "不及預期",
        "衰退",
        "悲觀",
        "向下",
        "跌幅",
    ]

    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    total = positive_count + negative_count
    if total == 0:
        return 0.0

    sentiment = (positive_count - negative_count) / total
    return max(-1.0, min(1.0, sentiment))


def _extract_key_topics(articles: list[dict[str, Any]]) -> list[str]:
    """
    從文章列表提取關鍵主題。

    簡單實作：從標題和內容中提取常見詞彙。

    Args:
        articles: 文章列表

    Returns:
        關鍵主題列表
    """
    topics = {}

    keywords_to_watch = [
        "台積電",
        "TSMC",
        "晶片",
        "AI",
        "半導體",
        "電動車",
        "EV",
        "蘋果",
        "鴻海",
        "聯發科",
        "聯電",
        "三星",
        "英特爾",
        "房市",
        "央行",
        "匯率",
        "利率",
        "股市",
    ]

    for article in articles:
        title = article.get("title", "").lower()
        content = article.get("content", "").lower()
        text = f"{title} {content}"

        for keyword in keywords_to_watch:
            if keyword.lower() in text:
                topics[keyword] = topics.get(keyword, 0) + 1

    # 返回出現最頻繁的主題（最多3個）
    sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, _ in sorted_topics[:3]]


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

    **可選參數：**
        market_data: 市場數據，缺少時使用預設值 [可選]
            - price_momentum: 價格動能 (0-100)
            - market_breadth: 市場寬度 (0-100)
            - volatility: 波動率 (0-100)
            - put_call_ratio: 賣權買權比 (0-100)
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 恐懼貪婪指數結果
            {
                "index_value": float,       # 0-100
                "level": str,               # 恐慌/恐懼/中性/貪婪/極度貪婪
                "components": dict,         # 各組成分數
                "interpretation": str       # 解讀說明
            }

    Note:
        此函數具有高度的容錯能力，缺少參數時使用預設中性值。
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
    ticker: str,
    trading_data: TradingData = None,
    **kwargs,
) -> str:
    """分析資金流向

    **必要參數：**
        ticker: 股票代號 (例如: "2330") [必要]

    **可選參數：**
        trading_data: 交易數據，缺少時使用預設值 [可選]
            - large_buy: 大單買進
            - large_sell: 大單賣出
            - foreign_net: 外資淨買賣
            - institutional_net: 法人淨買賣
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 資金流向分析結果
            {
                "ticker": str,
                "net_flow": float,          # 淨流入金額
                "flow_direction": str,      # 流入/流出/平衡
                "large_order_ratio": float, # 大單佔比
                "foreign_attitude": str,    # 外資態度
                "interpretation": str
            }

    Raises:
        返回錯誤字典：缺少必要參數
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
    *,
    auto_fetch: bool = True,
    **kwargs,
) -> dict:
    """分析新聞情緒

    **可選參數：**
        ticker: 股票代號 (例如: "2330")，None 表示整體市場 [可選]
        news_data: 新聞列表，缺少時根據 auto_fetch 決定行為 [可選]
            每筆包含：
            - title: 標題
            - content: 內容
            - sentiment: 情緒分數 (-1 到 1) [可選]
            - timestamp: 時間 [可選]
        auto_fetch: 當 news_data 為空時是否自動透過 tavily_mcp 搜尋 [可選，預設 True]
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 新聞情緒分析結果
            {
                "ticker": str,
                "news_count": int,
                "positive_ratio": float,
                "negative_ratio": float,
                "sentiment_score": float,   # -100 到 100
                "key_topics": [str, ...],
                "interpretation": str,
                "data_source": str          # "provided" | "fetched" | "empty"
            }

    Note:
        此函數具有高度的容錯能力，即使無法蒐集數據也能返回有效結果。
        當 news_data 為空且 auto_fetch=True 時，自動透過 tavily_mcp 搜尋。

        由於 @function_tool 期望同步函數，async 調用已包裝為同步。
    """
    try:
        import asyncio

        # 參數驗證和容錯
        params = parse_tool_params(ticker=ticker, news_data=news_data, **kwargs)

        _ticker = params.get("ticker") or ticker
        _news_data = params.get("news_data") or news_data

        target = _ticker or "市場"
        logger.info(
            f"開始分析新聞情緒 | 標的: {target} | 傳入新聞數: {len(_news_data) if _news_data else 0}"
        )

        # 如果沒有數據且允許自動蒐集，則搜尋新聞
        data_source = "provided"
        if not _news_data and auto_fetch:
            logger.info(f"無新聞數據，自動透過 tavily 搜尋 | 標的: {target}")

            tavily_mcp = _sentiment_agent_context.get("tavily_mcp")
            if tavily_mcp:
                # 構建搜尋查詢
                if _ticker:
                    query = f"{_ticker} news today"
                else:
                    query = "Taiwan stock market news today"

                # 以同步方式運行 async 調用
                try:
                    loop = asyncio.get_running_loop()
                    # 已在 async 上下文中，建立任務
                    search_results = asyncio.run_coroutine_threadsafe(
                        _call_tavily_search(tavily_mcp, query, max_results=5), loop
                    ).result(timeout=10)
                except RuntimeError:
                    # 沒有運行的 loop，建立新的
                    search_results = asyncio.run(
                        _call_tavily_search(tavily_mcp, query, max_results=5)
                    )

                if search_results:
                    data_source = "fetched"
                    logger.info(f"取得 {len(search_results)} 筆新聞")

                    # 轉換為 NewsItem 物件
                    _news_data = []
                    for result in search_results:
                        sentiment = _extract_sentiment_from_text(
                            f"{result.get('title', '')} {result.get('content', '')}"
                        )
                        _news_data.append(
                            NewsItem(
                                title=result.get("title", ""),
                                content=result.get("content", ""),
                                sentiment=sentiment,
                                timestamp=result.get("timestamp", datetime.now().isoformat()),
                            )
                        )
                else:
                    logger.warning(f"tavily 搜尋無結果 | 標的: {target}")
                    _news_data = []
            else:
                logger.warning("tavily_mcp 不可用，無法自動搜尋新聞")
                _news_data = []
        elif not _news_data:
            logger.debug(f"無新聞數據且 auto_fetch=False | 標的: {target}")
            _news_data = []
            data_source = "empty"

        # 轉換字典為 NewsItem 物件
        if _news_data and isinstance(_news_data[0], dict):
            _news_data = [
                NewsItem(**item) if isinstance(item, dict) else item for item in _news_data
            ]

        logger.info(
            f"準備分析新聞 | 標的: {target} | 新聞數: {len(_news_data)} | 來源: {data_source}"
        )

        if not _news_data:
            logger.debug(f"無新聞數據可分析 | 標的: {target}")
            return {
                "ticker": _ticker,
                "news_count": 0,
                "positive_ratio": 0,
                "negative_ratio": 0,
                "sentiment_score": 0,
                "key_topics": [],
                "interpretation": "無可用新聞數據",
                "data_source": data_source,
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

        # 提取關鍵主題
        key_topics = _extract_key_topics(
            [{"title": n.title, "content": n.content} for n in _news_data]
        )

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
            f"正面: {positive_ratio:.1%} | 負面: {negative_ratio:.1%} | 來源: {data_source}"
        )

        return {
            "ticker": _ticker,
            "news_count": news_count,
            "positive_ratio": positive_ratio,
            "negative_ratio": negative_ratio,
            "sentiment_score": sentiment_score,
            "key_topics": key_topics,
            "interpretation": interpretation,
            "data_source": data_source,
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
            "data_source": "error",
        }


@function_tool(strict_mode=False)
def analyze_social_sentiment(
    ticker: str,
    social_data: SocialData = None,
    *,
    auto_fetch: bool = True,
    **kwargs,
) -> dict:
    """分析社群媒體情緒

    **必要參數：**
        ticker: 股票代號 (例如: "2330") [必要]

    **可選參數：**
        social_data: 社群數據，缺少時根據 auto_fetch 決定行為 [可選]
            - mention_count: 提及次數
            - positive_mentions: 正面提及
            - negative_mentions: 負面提及
            - trending: 是否熱門
        auto_fetch: 當 social_data 為空時是否自動透過 tavily_mcp 搜尋 [可選，預設 True]
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 社群情緒分析結果
            {
                "ticker": str,
                "mention_count": int,
                "sentiment_ratio": float,    # 正負面比
                "trending_status": str,      # 熱度狀態
                "sentiment_score": float,    # -100 到 100
                "interpretation": str,
                "data_source": str           # "provided" | "fetched" | "empty"
            }

    Note:
        此函數具有高度的容錯能力，即使無法蒐集數據也能返回有效結果。
        當 social_data 為空且 auto_fetch=True 時，自動透過 tavily_mcp 搜尋社群討論。

        由於 @function_tool 期望同步函數，async 調用已包裝為同步。
    """
    try:
        import asyncio

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
                "data_source": "error",
            }

        logger.info(f"開始分析社群情緒 | 股票: {_ticker} | 傳入社群數據: {bool(_social_data)}")

        # 如果沒有數據且允許自動蒐集，則搜尋社群討論
        data_source = "provided"
        if not _social_data and auto_fetch:
            logger.info(f"無社群數據，自動透過 tavily 搜尋 | 股票: {_ticker}")

            tavily_mcp = _sentiment_agent_context.get("tavily_mcp")
            if tavily_mcp:
                # 構建搜尋查詢（聚焦社群討論和輿情）
                query = f"{_ticker} PTT Dcard 討論 社群輿情"

                # 以同步方式運行 async 調用
                try:
                    loop = asyncio.get_running_loop()
                    search_results = asyncio.run_coroutine_threadsafe(
                        _call_tavily_search(tavily_mcp, query, max_results=5), loop
                    ).result(timeout=10)
                except RuntimeError:
                    search_results = asyncio.run(
                        _call_tavily_search(tavily_mcp, query, max_results=5)
                    )

                if search_results:
                    data_source = "fetched"
                    logger.info(f"取得 {len(search_results)} 筆社群相關結果")

                    # 簡單統計：根據情緒分析結果計算提及和態度
                    mention_count = len(search_results) * 100  # 估計提及次數
                    positive_mentions = 0
                    negative_mentions = 0

                    for result in search_results:
                        sentiment = _extract_sentiment_from_text(
                            f"{result.get('title', '')} {result.get('content', '')}"
                        )
                        if sentiment > 0.2:
                            positive_mentions += 1
                        elif sentiment < -0.2:
                            negative_mentions += 1

                    _social_data = {
                        "mention_count": mention_count,
                        "positive_mentions": positive_mentions,
                        "negative_mentions": negative_mentions,
                        "trending": len(search_results) > 3,
                    }
                    logger.debug(f"社群數據構建完成: {_social_data}")
                else:
                    logger.warning(f"tavily 搜尋無結果 | 股票: {_ticker}")
                    _social_data = None
            else:
                logger.warning("tavily_mcp 不可用，無法自動搜尋社群數據")
                _social_data = None
        elif not _social_data:
            logger.debug(f"無社群數據且 auto_fetch=False | 股票: {_ticker}")
            _social_data = None
            data_source = "empty"

        # 如果轉換後仍為 None，使用預設值
        if not _social_data:
            logger.debug(f"無法取得社群數據，使用預設值 | 股票: {_ticker}")
            _social_data = {
                "mention_count": 0,
                "positive_mentions": 0,
                "negative_mentions": 0,
                "trending": False,
            }

        # 確保字典類型
        if isinstance(_social_data, dict):
            pass
        else:
            # 如果是 Pydantic 模型，轉換為字典
            if hasattr(_social_data, "dict"):
                _social_data = _social_data.dict()
            elif hasattr(_social_data, "model_dump"):
                _social_data = _social_data.model_dump()

        logger.info(f"準備分析社群 | 股票: {_ticker} | 來源: {data_source}")

        mention_count = _social_data.get("mention_count", 0)
        positive = _social_data.get("positive_mentions", 0)
        negative = _social_data.get("negative_mentions", 0)
        trending = _social_data.get("trending", False)

        if mention_count == 0:
            logger.debug(f"無社群數據 | 股票: {_ticker}")
            return {
                "ticker": _ticker,
                "mention_count": 0,
                "sentiment_ratio": 0,
                "trending_status": "低關注",
                "sentiment_score": 0,
                "interpretation": "無社群提及數據",
                "data_source": data_source,
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
            f"熱度: {trending_status} | 提及: {mention_count} | 來源: {data_source}"
        )

        return {
            "ticker": _ticker,
            "mention_count": mention_count,
            "sentiment_ratio": sentiment_ratio,
            "trending_status": trending_status,
            "sentiment_score": sentiment_score,
            "interpretation": interpretation,
            "data_source": data_source,
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
            "data_source": "error",
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

    **可選參數：**
        fear_greed_index: 恐懼貪婪指數 (來自 calculate_fear_greed_index)，缺少時使用預設值 [可選]
        money_flow: 資金流向分析 (來自 analyze_money_flow)，缺少時使用預設值 [可選]
        news_sentiment: 新聞情緒 (來自 analyze_news_sentiment)，缺少時使用預設值 [可選]
        social_sentiment: 社群情緒 (來自 analyze_social_sentiment)，缺少時使用預設值 [可選]
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 情緒交易訊號結果
            {
                "overall_signal": str,      # "買進" | "賣出" | "觀望"
                "confidence": float,        # 信心度 0-1
                "strategy": str,            # "反向" | "順勢" | "觀望"
                "reasoning": [str, ...],    # 分析理由
                "risk_level": str,          # "高" | "中" | "低"
                "timestamp": str
            }

    Note:
        此函數具有高度的容錯能力，即使缺少部分輸入參數也能返回有效訊號。
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
        - 工具會自動透過全局上下文訪問 tavily_mcp 進行數據蒐集
    """
    logger.info(f"get_sentiment_agent() called with model={llm_model}")

    logger.debug("Creating custom tools with function_tool")

    # 確保 mcp_servers 為列表
    if mcp_servers is None:
        mcp_servers = []

    # 提取 tavily_mcp 伺服器並設置到全局上下文（工具可訪問）
    if mcp_servers:
        for server in mcp_servers:
            if hasattr(server, "name") and server.name == "tavily_mcp":
                _sentiment_agent_context["tavily_mcp"] = server
                logger.debug("tavily_mcp 已設置到全局上下文")
                break

    all_tools = [
        calculate_fear_greed_index,
        analyze_money_flow,
        analyze_news_sentiment,
        analyze_social_sentiment,
        generate_sentiment_signals,
    ]

    logger.debug(f"Total tools: {len(all_tools)}")
    tavily_available = _sentiment_agent_context.get("tavily_mcp") is not None
    logger.info(
        f"Creating Agent with model={llm_model}, mcp_servers={len(mcp_servers) if mcp_servers else 0}, "
        f"tools={len(all_tools)}, tavily_mcp={'available' if tavily_available else 'not available'}"
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
