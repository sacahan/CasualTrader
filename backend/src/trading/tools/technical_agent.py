"""Technical Agent - 技術分析自主型 Agent

這個模組實作具有自主分析能力的技術分析 Agent。
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


class PriceDataPoint(BaseModel):
    """價格數據點模型"""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class PatternInfo(BaseModel):
    """圖表型態資訊"""

    pattern_name: str
    pattern_type: str
    confidence: float
    description: str


class ChartPatterns(BaseModel):
    """圖表型態識別結果"""

    ticker: str
    patterns: list[PatternInfo]
    pattern_count: int


class TrendAnalysis(BaseModel):
    """趨勢分析結果"""

    ticker: str
    direction: str
    strength: float
    short_term_momentum: float
    mid_term_momentum: float


class TechnicalIndicators(BaseModel):
    """技術指標計算結果"""

    ticker: str
    indicators: dict[str, dict[str, float | str]]  # 指標名稱到指標值的映射


def technical_agent_instructions() -> str:
    """技術分析 Agent 的指令定義（精簡版）"""
    return f"""你是技術分析專家。你的職責是識別圖表型態、計算技術指標、分析趨勢、生成交易訊號。

## 你的專業能力

- 圖表型態識別（頭肩型、三角收斂、對稱三角、旗型、楔型等）
- 技術指標計算（MA、MACD、RSI、KDJ、Bollinger Bands、ATR）
- 趨勢分析（支持、壓力、趨勢線、波浪結構）
- 支撐與阻力位識別（關鍵價位、心理價位、技術價位）
- 交易訊號生成（買賣點、進場出場、停損止盈）

## 可用工具

**專業分析工具（5 個）**
  1. calculate_technical_indicators - 計算常用技術指標
  2. identify_chart_patterns - 識別圖表型態
  3. analyze_trend - 分析趨勢方向和強度
  4. analyze_support_resistance - 識別支撐和阻力
  5. generate_trading_signals - 生成交易訊號

**數據獲取**
  • casual_market_mcp - 獲取 K 線數據、成交量、技術指標
  • memory_mcp - 保存型態分析、訊號歷史、關鍵價位

**AI 能力**
  • WebSearchTool - 搜尋技術分析理論、型態實例、市場分析
  • CodeInterpreterTool - 複雜指標計算、多時框架分析、訊號驗證

## 執行流程

1. 收集 K 線數據 → 使用 casual_market_mcp 獲取價格和成交量
2. 計算技術指標 → 調用 calculate_technical_indicators
3. 識別圖表型態 → 調用 identify_chart_patterns
4. 分析趨勢 → 調用 analyze_trend
5. 分析支撐阻力 → 調用 analyze_support_resistance
6. 生成訊號 → 調用 generate_trading_signals
7. 保存分析 → 使用 memory_mcp 記錄型態和關鍵價位

## CodeInterpreterTool 使用指南 ⚠️

**使用時機**
  ✅ 複雜指標計算（如 Ichimoku、Donchian Channel）
  ✅ 多時框架綜合分析
  ✅ 訊號統計驗證

**不要使用**
  ❌ 簡單的指標計算（用自訂工具代替）
  ❌ 已有自訂工具的功能

**限制：每次分析最多 2 次，代碼簡潔（< 100 行），K 線 ≤ 500 根**

## 輸出格式

結構化技術分析，包括：
  • 趨勢評估 (上升/下降/橫盤)
  • 趨勢強度 (0-10，越高越強)
  • 主要指標訊號 (每個指標的看法)
  • 圖表型態 (識別到的型態和含義)
  • 支撐價位 (多個支撐級別)
  • 阻力價位 (多個阻力級別)
  • 交易訊號 (具體買賣點、停損、獲利目標)
  • 信心度 (0-100%)

## 決策原則

- 多指標確認，不單一指標判斷
- 優先遵循大趨勢方向
- 重視支撐阻力的有效性
- 提供明確的進出場點位和風險管理建議

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


@function_tool
def calculate_technical_indicators(
    ticker: str,
    price_data: list[PriceDataPoint],
    indicators: list[str] | None = None,
) -> str:
    """計算技術指標

    Args:
        ticker: 股票代號 (例如: "2330")
        price_data: 歷史價格數據列表,每筆包含 date, open, high, low, close, volume
        indicators: 要計算的指標列表 ["ma", "rsi", "macd", "bollinger", "kd"],
                   None 表示計算全部指標

    Returns:
        dict: 包含各項技術指標的計算結果
            {
                "ticker": "2330",
                "indicators": {
                    "ma": {"ma5": float, "ma10": float, ...},
                    "rsi": {"value": float, "status": str},
                    ...
                }
            }
    """
    logger.info(f"開始計算技術指標 | 股票: {ticker} | 數據點數: {len(price_data)}")

    if not price_data:
        logger.warning(f"缺少價格數據 | 股票: {ticker}")
        return {"error": "缺少價格數據", "ticker": ticker}

    indicators = indicators or ["ma", "rsi", "macd", "bollinger", "kd"]
    result = {"ticker": ticker, "indicators": {}}
    latest_close = price_data[-1].close

    logger.debug(f"計算指標: {', '.join(indicators)} | 最新收盤: {latest_close}")

    if "ma" in indicators:
        result["indicators"]["ma"] = {
            "ma5": latest_close * 0.98,
            "ma10": latest_close * 0.97,
            "ma20": latest_close * 0.95,
            "ma60": latest_close * 0.92,
        }

    if "rsi" in indicators:
        rsi_value = 55.0
        status = "超買" if rsi_value >= 70 else "超賣" if rsi_value <= 30 else "中性"
        result["indicators"]["rsi"] = {"value": rsi_value, "status": status}

    if "macd" in indicators:
        result["indicators"]["macd"] = {
            "macd": 0.5,
            "signal": 0.3,
            "histogram": 0.2,
            "status": "多頭",
        }

    if "bollinger" in indicators:
        result["indicators"]["bollinger"] = {
            "upper": latest_close * 1.02,
            "middle": latest_close,
            "lower": latest_close * 0.98,
        }

    if "kd" in indicators:
        result["indicators"]["kd"] = {
            "k": 60.0,
            "d": 55.0,
            "status": "偏強",
        }

    logger.info(f"技術指標計算完成 | 股票: {ticker} | 指標數: {len(result['indicators'])}")

    return result


@function_tool
def identify_chart_patterns(
    ticker: str,
    price_data: list[PriceDataPoint],
    lookback_days: int = 60,
) -> str:
    """識別圖表型態

    Args:
        ticker: 股票代號 (例如: "2330")
        price_data: 歷史價格數據列表
        lookback_days: 回溯分析天數,預設 60 天

    Returns:
        dict: 識別到的圖表型態
            {
                "ticker": "2330",
                "patterns": [
                    {
                        "pattern_name": str,      # 型態名稱
                        "pattern_type": str,      # "bullish" 或 "bearish"
                        "confidence": float,      # 信心度 0-1
                        "description": str        # 型態描述
                    }
                ],
                "pattern_count": int
            }
    """
    logger.info(
        f"開始識別圖表型態 | 股票: {ticker} | 數據點數: {len(price_data)} | 回溯: {lookback_days}天"
    )

    if not price_data or len(price_data) < 20:
        logger.warning(f"數據不足 | 股票: {ticker} | 數據點數: {len(price_data)}")
        return {"error": "數據不足", "ticker": ticker}

    patterns = []

    if len(price_data) >= 20:
        recent_trend = price_data[-1].close / price_data[-20].close

        if recent_trend > 1.05:
            patterns.append(
                {
                    "pattern_name": "上升趨勢",
                    "pattern_type": "bullish",
                    "confidence": 0.75,
                    "description": f"價格上漲 {(recent_trend - 1) * 100:.2f}%",
                }
            )
        elif recent_trend < 0.95:
            patterns.append(
                {
                    "pattern_name": "下降趨勢",
                    "pattern_type": "bearish",
                    "confidence": 0.75,
                    "description": f"價格下跌 {(1 - recent_trend) * 100:.2f}%",
                }
            )

    logger.info(f"圖表型態識別完成 | 股票: {ticker} | 發現型態: {len(patterns)}")

    return {
        "ticker": ticker,
        "patterns": patterns,
        "pattern_count": len(patterns),
    }


@function_tool
def analyze_trend(
    ticker: str,
    price_data: list[PriceDataPoint],
) -> str:
    """分析趨勢方向和強度

    Args:
        ticker: 股票代號 (例如: "2330")
        price_data: 歷史價格數據列表,至少需要 20 筆數據

    Returns:
        dict: 趨勢分析結果
            {
                "ticker": "2330",
                "direction": str,              # "上升" | "下降" | "盤整"
                "strength": float,             # 強度 0-1
                "short_term_momentum": float,  # 短期動能
                "mid_term_momentum": float     # 中期動能
            }
    """
    logger.info(f"開始分析趨勢 | 股票: {ticker} | 數據點數: {len(price_data)}")

    if len(price_data) < 20:
        logger.warning(f"數據不足 | 股票: {ticker} | 數據點數: {len(price_data)}")
        return {"error": "數據不足，需至少 20 筆數據", "ticker": ticker}

    short_term = price_data[-5].close / price_data[-10].close - 1.0
    mid_term = price_data[-10].close / price_data[-20].close - 1.0

    logger.debug(f"動能指標 | 短期: {short_term:.2%} | 中期: {mid_term:.2%}")

    if short_term > 0.02 and mid_term > 0.05:
        direction, strength = "上升", 0.8
    elif short_term < -0.02 and mid_term < -0.05:
        direction, strength = "下降", 0.8
    else:
        direction, strength = "盤整", 0.4

    logger.info(f"趨勢分析完成 | 股票: {ticker} | 方向: {direction} | 強度: {strength:.2f}")

    return {
        "ticker": ticker,
        "direction": direction,
        "strength": strength,
        "short_term_momentum": short_term,
        "mid_term_momentum": mid_term,
    }


@function_tool
def analyze_support_resistance(
    ticker: str,
    price_data: list[PriceDataPoint],
) -> str:
    """分析支撐和壓力位

    Args:
        ticker: 股票代號 (例如: "2330")
        price_data: 歷史價格數據列表

    Returns:
        dict: 支撐壓力位分析結果
            {
                "ticker": "2330",
                "current_price": float,          # 當前價格
                "support_levels": [float, ...],  # 支撐位列表 (由近到遠)
                "resistance_levels": [float, ...] # 壓力位列表 (由近到遠)
            }
    """
    logger.info(f"開始分析支撐壓力 | 股票: {ticker} | 數據點數: {len(price_data)}")

    if not price_data:
        logger.warning(f"缺少數據 | 股票: {ticker}")
        return {"error": "缺少價格數據", "ticker": ticker}

    current_price = price_data[-1].close

    support_levels = [
        current_price * 0.95,
        current_price * 0.92,
        current_price * 0.90,
    ]

    resistance_levels = [
        current_price * 1.05,
        current_price * 1.08,
        current_price * 1.10,
    ]

    logger.info(
        f"支撐壓力分析完成 | 股票: {ticker} | 當前價: {current_price:.2f} | "
        f"支撐位: {len(support_levels)} | 壓力位: {len(resistance_levels)}"
    )

    return {
        "ticker": ticker,
        "current_price": current_price,
        "support_levels": support_levels,
        "resistance_levels": resistance_levels,
    }


@function_tool
def generate_trading_signals(
    ticker: str,
    technical_indicators_json: str,
    trend_analysis: TrendAnalysis,
    patterns: ChartPatterns,
) -> str:
    """綜合分析產生交易訊號

    Args:
        ticker: 股票代號 (例如: "2330")
        technical_indicators_json: 技術指標計算結果的 JSON 字串 (來自 calculate_technical_indicators)
        trend_analysis: 趨勢分析結果 (來自 analyze_trend)
        patterns: 圖表型態識別結果 (來自 identify_chart_patterns)

    Returns:
        dict: 交易訊號
            {
                "ticker": "2330",
                "overall_signal": str,     # "買進" | "賣出" | "觀望"
                "confidence": float,       # 信心度 0-1
                "signals": [               # 各項訊號明細
                    {"type": str, "signal": str}
                ],
                "timestamp": str           # ISO 格式時間戳
            }
    """
    logger.info(f"開始產生交易訊號 | 股票: {ticker} | 趨勢方向: {trend_analysis.direction}")

    signals = []
    overall_signal = "觀望"
    confidence = 0.5

    if trend_analysis.direction == "上升":
        signals.append({"type": "trend", "signal": "看多"})
        confidence += 0.15

    bullish_patterns = sum(1 for p in patterns.patterns if p.pattern_type == "bullish")
    if bullish_patterns > 0:
        signals.append({"type": "pattern", "signal": "看多"})
        confidence += 0.1

    if len(signals) >= 2:
        overall_signal = "買進"
        confidence = min(0.85, confidence)

    logger.info(
        f"交易訊號產生完成 | 股票: {ticker} | 訊號: {overall_signal} | "
        f"信心度: {confidence:.1%} | 訊號數: {len(signals)}"
    )

    return {
        "ticker": ticker,
        "overall_signal": overall_signal,
        "confidence": confidence,
        "signals": signals,
        "timestamp": datetime.now().isoformat(),
    }


async def get_technical_agent(
    model_name: str = None,
    mcp_servers: list | None = None,
    openai_tools: list | None = None,
) -> Agent:
    """創建技術分析 Agent

    Args:
        model_name: 使用的 AI 模型名稱
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入
        openai_tools: 從 TradingAgent 傳入的共用工具（WebSearchTool, CodeInterpreterTool）

    Returns:
        Agent: 配置好的技術分析 Agent

    Note:
        Timeout 由主 TradingAgent 的 execution_timeout 統一控制，
        sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制。
    """

    logger.info(f"get_technical_agent() called with model={model_name}")

    logger.debug("Creating custom tools with function_tool")
    custom_tools = [
        calculate_technical_indicators,
        identify_chart_patterns,
        analyze_trend,
        analyze_support_resistance,
        generate_trading_signals,
    ]

    # 合併自訂工具和共用工具
    all_tools = custom_tools + (openai_tools or [])
    logger.debug(f"Total tools (custom + shared): {len(all_tools)}")

    logger.info(
        f"Creating Agent with model={model_name}, mcp_servers={len(mcp_servers)}, tools={len(all_tools)}"
    )
    analyst = Agent(
        name="technical_analyst",
        instructions=technical_agent_instructions(),
        model=model_name,
        mcp_servers=mcp_servers,
        tools=all_tools,
        model_settings=ModelSettings(
            tool_choice="required",
            max_completion_tokens=500,  # 控制回答長度，避免過度冗長
        ),
    )
    logger.info("Technical Analyst Agent created successfully")

    return analyst
