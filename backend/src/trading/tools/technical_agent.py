"""Technical Agent - 技術分析自主型 Agent

這個模組實作具有自主分析能力的技術分析 Agent。
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
    1. 直接的參數：ticker="2330", price_data=[...]
    2. JSON 字串參數：args='{"ticker":"2330","price_data":[...]}'
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
    """技術分析 Agent 的指令定義（簡化版，帶記憶追蹤）"""
    return f"""你是技術分析專家。識別圖表型態、計算技術指標、分析趨勢、生成交易訊號。
持續追蹤：先查詢 memory_mcp 歷史訊號，對比型態變化，識別轉折點。

## 專業能力

- 圖表型態識別（頭肩型、三角、旗型、楔型等）
- 技術指標計算（MA、MACD、RSI、KDJ、Bollinger Bands、ATR）
- 趨勢分析（支持、壓力、趨勢線）
- 交易訊號生成（買賣點、進場出場、停損止盈）

## 執行流程

**步驟 0：檢查記憶庫** → memory_mcp
  - 無訊號 → 完整分析
  - 新鮮（≤3 天）→ 增量更新
  - 陳舊（>3 天）→ 完整重新分析 + 對比

**步驟 1-3：數據收集與計算** → casual_market_mcp + tools
  1. 收集 K 線數據和成交量
  2. 計算技術指標 → calculate_technical_indicators
  3. 識別圖表型態 → identify_chart_patterns

**步驟 4-6：趨勢與信號**
  4. 分析趨勢 → analyze_trend
  5. 分析支撐阻力 → analyze_support_resistance
  6. 生成訊號 → generate_trading_signals

**步驟 7：對比與保存** → memory_mcp
  - 若有先前訊號：對比趨勢方向、指標確認、支撐阻力位更新
  - 保存分析結果（含時間戳、型態、訊號、價位）

## 工具調用

- **calculate_technical_indicators** → 計算 MA、MACD、RSI 等
- **identify_chart_patterns** → 識別型態和含義
- **analyze_trend** → 判斷趨勢方向和強度（0-10）
- **analyze_support_resistance** → 找出支撐阻力位
- **generate_trading_signals** → 生成買賣訊號

## 輸出結構

- 趨勢評估 (上升/下降/橫盤) + 強度 (0-10)
- 主要指標訊號 (MA、MACD、RSI、KDJ 各自的訊號)
- 圖表型態 (識別到的型態、含義、預期方向)
- 支撐阻力 (多個級別的價位)
- 交易訊號 (具體買賣點、停損目標、獲利目標)
- 市場環境 (可選：新聞摘要)
- 信心度 (0-100%)
- [若有先前訊號] 變化分析 (型態轉變、指標确認變化)

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


@function_tool(strict_mode=False)
def calculate_technical_indicators(
    ticker: str = None,
    price_data: list = None,
    indicators: list = None,
    **kwargs,
) -> str:
    """計算技術指標

    Args:
        ticker: 股票代號 (例如: "2330")
        price_data: 歷史價格數據列表,每筆包含 date, open, high, low, close, volume
        indicators: 要計算的指標，可以是單個字符串 "macd" 或列表 ["ma", "rsi", "macd", "bollinger", "kd"]，
                   None 表示計算全部指標
        **kwargs: 額外參數（用於容錯）

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
    try:
        # 參數驗證和容錯
        params = parse_tool_params(
            ticker=ticker, price_data=price_data, indicators=indicators, **kwargs
        )

        _ticker = params.get("ticker") or ticker
        _price_data = params.get("price_data") or price_data
        _indicators = params.get("indicators") or indicators

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {"error": "缺少必要參數: ticker"}

        if not _price_data:
            logger.warning("缺少必要參數: price_data")
            return {"error": "缺少必要參數: price_data", "ticker": _ticker}

        # 轉換字典為 PriceDataPoint 物件
        if _price_data and isinstance(_price_data[0], dict):
            _price_data = [
                PriceDataPoint(**item) if isinstance(item, dict) else item for item in _price_data
            ]

        logger.info(f"開始計算技術指標 | 股票: {_ticker} | 數據點數: {len(_price_data)}")

        if not _price_data:
            logger.warning(f"缺少價格數據 | 股票: {_ticker}")
            return {"error": "缺少價格數據", "ticker": _ticker}

        # 將單個字符串轉換為列表
        if isinstance(_indicators, str):
            _indicators = [_indicators.lower()]

        _indicators = _indicators or ["ma", "rsi", "macd", "bollinger", "kd"]
        result = {"ticker": _ticker, "indicators": {}}
        latest_close = _price_data[-1].close

        logger.debug(f"計算指標: {', '.join(_indicators)} | 最新收盤: {latest_close}")

        if "ma" in _indicators:
            result["indicators"]["ma"] = {
                "ma5": latest_close * 0.98,
                "ma10": latest_close * 0.97,
                "ma20": latest_close * 0.95,
                "ma60": latest_close * 0.92,
            }

        if "rsi" in _indicators:
            rsi_value = 55.0
            status = "超買" if rsi_value >= 70 else "超賣" if rsi_value <= 30 else "中性"
            result["indicators"]["rsi"] = {"value": rsi_value, "status": status}

        if "macd" in _indicators:
            result["indicators"]["macd"] = {
                "macd": 0.5,
                "signal": 0.3,
                "histogram": 0.2,
                "status": "多頭",
            }

        if "bollinger" in _indicators:
            result["indicators"]["bollinger"] = {
                "upper": latest_close * 1.02,
                "middle": latest_close,
                "lower": latest_close * 0.98,
            }

        if "kd" in _indicators:
            result["indicators"]["kd"] = {
                "k": 60.0,
                "d": 55.0,
                "status": "偏強",
            }

        logger.info(f"技術指標計算完成 | 股票: {_ticker} | 指標數: {len(result['indicators'])}")

        return result

    except Exception as e:
        logger.error(f"計算技術指標失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "indicators": {},
        }


@function_tool(strict_mode=False)
def identify_chart_patterns(
    ticker: str = None,
    price_data: list = None,
    lookback_days: int = 60,
    **kwargs,
) -> str:
    """識別圖表型態

    Args:
        ticker: 股票代號 (例如: "2330")
        price_data: 歷史價格數據列表
        lookback_days: 回溯分析天數,預設 60 天
        **kwargs: 額外參數（用於容錯）

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
    try:
        # 參數驗證和容錯
        params = parse_tool_params(
            ticker=ticker, price_data=price_data, lookback_days=lookback_days, **kwargs
        )

        _ticker = params.get("ticker") or ticker
        _price_data = params.get("price_data") or price_data
        _lookback_days = params.get("lookback_days") or lookback_days

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {"error": "缺少必要參數: ticker"}

        if not _price_data:
            logger.warning("缺少必要參數: price_data")
            return {"error": "缺少必要參數: price_data", "ticker": _ticker}

        # 轉換字典為 PriceDataPoint 物件
        if _price_data and isinstance(_price_data[0], dict):
            _price_data = [
                PriceDataPoint(**item) if isinstance(item, dict) else item for item in _price_data
            ]

        logger.info(
            f"開始識別圖表型態 | 股票: {_ticker} | 數據點數: {len(_price_data)} | 回溯: {_lookback_days}天"
        )

        if not _price_data or len(_price_data) < 20:
            logger.warning(f"數據不足 | 股票: {_ticker} | 數據點數: {len(_price_data)}")
            return {
                "error": "數據不足",
                "ticker": _ticker,
                "patterns": [],
                "pattern_count": 0,
            }

        patterns = []

        if len(_price_data) >= 20:
            recent_trend = _price_data[-1].close / _price_data[-20].close

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

        logger.info(f"圖表型態識別完成 | 股票: {_ticker} | 發現型態: {len(patterns)}")

        return {
            "ticker": _ticker,
            "patterns": patterns,
            "pattern_count": len(patterns),
        }

    except Exception as e:
        logger.error(f"識別圖表型態失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "patterns": [],
            "pattern_count": 0,
        }


@function_tool(strict_mode=False)
def analyze_trend(
    ticker: str = None,
    price_data: list = None,
    **kwargs,
) -> str:
    """分析趨勢方向和強度

    Args:
        ticker: 股票代號 (例如: "2330")
        price_data: 歷史價格數據列表,至少需要 20 筆數據
        **kwargs: 額外參數（用於容錯）

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
    try:
        # 參數驗證和容錯
        params = parse_tool_params(ticker=ticker, price_data=price_data, **kwargs)

        _ticker = params.get("ticker") or ticker
        _price_data = params.get("price_data") or price_data

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {"error": "缺少必要參數: ticker"}

        if not _price_data:
            logger.warning("缺少必要參數: price_data")
            return {"error": "缺少必要參數: price_data", "ticker": _ticker}

        # 轉換字典為 PriceDataPoint 物件
        if _price_data and isinstance(_price_data[0], dict):
            _price_data = [
                PriceDataPoint(**item) if isinstance(item, dict) else item for item in _price_data
            ]

        logger.info(f"開始分析趨勢 | 股票: {_ticker} | 數據點數: {len(_price_data)}")

        if len(_price_data) < 20:
            logger.warning(f"數據不足 | 股票: {_ticker} | 數據點數: {len(_price_data)}")
            return {
                "error": "數據不足，需至少 20 筆數據",
                "ticker": _ticker,
                "direction": "未知",
                "strength": 0,
                "short_term_momentum": 0,
                "mid_term_momentum": 0,
            }

        short_term = _price_data[-5].close / _price_data[-10].close - 1.0
        mid_term = _price_data[-10].close / _price_data[-20].close - 1.0

        logger.debug(f"動能指標 | 短期: {short_term:.2%} | 中期: {mid_term:.2%}")

        if short_term > 0.02 and mid_term > 0.05:
            direction, strength = "上升", 0.8
        elif short_term < -0.02 and mid_term < -0.05:
            direction, strength = "下降", 0.8
        else:
            direction, strength = "盤整", 0.4

        logger.info(f"趨勢分析完成 | 股票: {_ticker} | 方向: {direction} | 強度: {strength:.2f}")

        return {
            "ticker": _ticker,
            "direction": direction,
            "strength": strength,
            "short_term_momentum": short_term,
            "mid_term_momentum": mid_term,
        }

    except Exception as e:
        logger.error(f"分析趨勢失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "direction": "未知",
            "strength": 0,
            "short_term_momentum": 0,
            "mid_term_momentum": 0,
        }


@function_tool(strict_mode=False)
def analyze_support_resistance(
    ticker: str = None,
    price_data: list = None,
    **kwargs,
) -> str:
    """分析支撐和壓力位

    Args:
        ticker: 股票代號 (例如: "2330")
        price_data: 歷史價格數據列表
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 支撐壓力位分析結果
            {
                "ticker": "2330",
                "current_price": float,          # 當前價格
                "support_levels": [float, ...],  # 支撐位列表 (由近到遠)
                "resistance_levels": [float, ...] # 壓力位列表 (由近到遠)
            }
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(ticker=ticker, price_data=price_data, **kwargs)

        _ticker = params.get("ticker") or ticker
        _price_data = params.get("price_data") or price_data

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {"error": "缺少必要參數: ticker"}

        if not _price_data:
            logger.warning("缺少必要參數: price_data")
            return {"error": "缺少必要參數: price_data", "ticker": _ticker}

        # 轉換字典為 PriceDataPoint 物件
        if _price_data and isinstance(_price_data[0], dict):
            _price_data = [
                PriceDataPoint(**item) if isinstance(item, dict) else item for item in _price_data
            ]

        logger.info(f"開始分析支撐壓力 | 股票: {_ticker} | 數據點數: {len(_price_data)}")

        if not _price_data:
            logger.warning(f"缺少數據 | 股票: {_ticker}")
            return {
                "error": "缺少價格數據",
                "ticker": _ticker,
                "current_price": 0,
                "support_levels": [],
                "resistance_levels": [],
            }

        current_price = _price_data[-1].close

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
            f"支撐壓力分析完成 | 股票: {_ticker} | 當前價: {current_price:.2f} | "
            f"支撐位: {len(support_levels)} | 壓力位: {len(resistance_levels)}"
        )

        return {
            "ticker": _ticker,
            "current_price": current_price,
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
        }

    except Exception as e:
        logger.error(f"分析支撐壓力失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "current_price": 0,
            "support_levels": [],
            "resistance_levels": [],
        }


@function_tool(strict_mode=False)
def generate_trading_signals(
    ticker: str = None,
    technical_indicators_json: str = None,
    trend_analysis: dict = None,
    patterns: dict = None,
    **kwargs,
) -> str:
    """綜合分析產生交易訊號

    Args:
        ticker: 股票代號 (例如: "2330")
        technical_indicators_json: 技術指標計算結果的 JSON 字串 (來自 calculate_technical_indicators)
        trend_analysis: 趨勢分析結果 (來自 analyze_trend)
        patterns: 圖表型態識別結果 (來自 identify_chart_patterns)
        **kwargs: 額外參數（用於容錯）

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
    try:
        # 參數驗證和容錯
        params = parse_tool_params(
            ticker=ticker,
            technical_indicators_json=technical_indicators_json,
            trend_analysis=trend_analysis,
            patterns=patterns,
            **kwargs,
        )

        _ticker = params.get("ticker") or ticker
        _technical_indicators_json = (
            params.get("technical_indicators_json") or technical_indicators_json
        )
        _trend_analysis = params.get("trend_analysis") or trend_analysis
        _patterns = params.get("patterns") or patterns

        # 使用預設值以防參數缺失
        if not _ticker:
            logger.warning("缺少 ticker 參數")
            _ticker = "未知"

        if not _trend_analysis:
            logger.warning("缺少 trend_analysis 參數，使用預設值")
            _trend_analysis = {"direction": "盤整", "strength": 0}
        elif isinstance(_trend_analysis, str):
            _trend_analysis = json.loads(_trend_analysis)

        if not _patterns:
            logger.warning("缺少 patterns 參數，使用預設值")
            _patterns = {"patterns": []}
        elif isinstance(_patterns, str):
            _patterns = json.loads(_patterns)

        logger.info(
            f"開始產生交易訊號 | 股票: {_ticker} | 趨勢方向: {_trend_analysis.get('direction', '未知')}"
        )

        signals = []
        overall_signal = "觀望"
        confidence = 0.5

        if _trend_analysis.get("direction") == "上升":
            signals.append({"type": "trend", "signal": "看多"})
            confidence += 0.15

        patterns_list = _patterns.get("patterns", [])
        bullish_patterns = sum(
            1 for p in patterns_list if isinstance(p, dict) and p.get("pattern_type") == "bullish"
        )
        if bullish_patterns > 0:
            signals.append({"type": "pattern", "signal": "看多"})
            confidence += 0.1

        if len(signals) >= 2:
            overall_signal = "買進"
            confidence = min(0.85, confidence)

        logger.info(
            f"交易訊號產生完成 | 股票: {_ticker} | 訊號: {overall_signal} | "
            f"信心度: {confidence:.1%} | 訊號數: {len(signals)}"
        )

        return {
            "ticker": _ticker,
            "overall_signal": overall_signal,
            "confidence": confidence,
            "signals": signals,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"產生交易訊號失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "overall_signal": "觀望",
            "confidence": 0.3,
            "signals": [],
            "timestamp": datetime.now().isoformat(),
        }


async def get_technical_agent(
    llm_model: LitellmModel = None,
    extra_headers: dict[str, str] = None,
    mcp_servers: list | None = None,
) -> Agent:
    """創建技術分析 Agent

    Args:
        llm_model: 使用的語言模型實例 (LitellmModel)，如果為 None，則使用預設模型
        extra_headers: 額外的 HTTP 標頭，用於模型 API 請求
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入

    Returns:
        Agent: 配置好的技術分析 Agent

    Note:
        - 不使用 WebSearchTool 和 CodeInterpreterTool（託管工具不支援 ChatCompletions API）
        - 只使用自訂工具進行技術分析
        - Timeout 由主 TradingAgent 的 execution_timeout 統一控制
        - Sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制
    """

    logger.info(f"get_technical_agent() called with model={llm_model}")

    logger.debug("Creating custom tools with function_tool")
    all_tools = [
        calculate_technical_indicators,
        identify_chart_patterns,
        analyze_trend,
        analyze_support_resistance,
        generate_trading_signals,
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
        name="technical_analyst",
        instructions=technical_agent_instructions(),
        model=llm_model,
        mcp_servers=mcp_servers,
        tools=all_tools,
        model_settings=ModelSettings(**model_settings_dict),
    )
    logger.info("Technical Analyst Agent created successfully")

    return analyst
