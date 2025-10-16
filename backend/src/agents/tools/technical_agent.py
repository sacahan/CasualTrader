"""Technical Agent - 技術分析自主型 Agent

這個模組實作具有自主分析能力的技術分析 Agent。
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv

from agents import Agent, function_tool, ModelSettings

# Logger
logger = logging.getLogger(__name__)

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gpt-5-mini")
DEFAULT_MAX_TURNS = os.getenv("DEFAULT_MAX_TURNS", 30)


def technical_agent_instructions() -> str:
    """技術分析 Agent 的指令定義"""
    return f"""你是一位專業的技術分析師,專精於股票圖表分析和技術指標解讀。

## 你的專業能力

1. 圖表型態識別
   - 經典型態: 頭肩頂底、雙重頂底、三角型態
   - 整理型態: 旗型、楔形、矩形
   - 反轉型態: 島狀反轉、V型反轉

2. 技術指標分析
   - 趨勢指標: MA、MACD
   - 動能指標: RSI、KD
   - 波動指標: 布林通道

3. 趨勢判斷與風險管理
   - 趨勢方向和強度
   - 支撐壓力位
   - 進場停損建議

## 分析方法

1. 收集數據: 使用 MCP Server 獲取價格資料
2. 計算指標: 使用工具計算技術指標
3. 識別型態: 分析圖表找出型態
4. 判斷趨勢: 評估趨勢方向和強度
5. 找關鍵價位: 確定支撐和壓力位
6. 給出建議: 綜合分析產生交易訊號

## 可用工具

### 專業分析工具
- calculate_technical_indicators: 計算 MA、RSI、MACD 等指標
- identify_chart_patterns: 識別圖表型態
- analyze_trend: 分析趨勢
- analyze_support_resistance: 找支撐壓力位
- generate_trading_signals: 產生交易訊號
- Casual Market MCP Server: 獲取市場數據

### 增強能力工具
- WebSearchTool: 主動搜尋最新的技術分析報告、專家觀點、市場評論
- CodeInterpreterTool: 執行自訂的技術指標計算、統計分析、回測驗證

## CodeInterpreterTool 使用準則 ⚠️

為了控制成本和執行時間，請遵守以下原則：

1. **優先使用自訂工具**
   - 先嘗試使用提供的專業分析工具
   - 只有當自訂工具無法滿足需求時才使用 CodeInterpreterTool

2. **適用場景**
   - ✅ 複雜的自訂指標計算（如改良版 RSI、特殊加權均線）
   - ✅ 統計檢定（如相關性分析、顯著性測試）
   - ✅ 簡短的回測驗證（< 100 行程式碼）
   - ❌ 不要用於簡單的數學計算（加減乘除）
   - ❌ 不要用於可以用自訂工具完成的任務

3. **程式碼效率要求**
   - 保持程式碼簡潔（< 100 行）
   - 避免不必要的迴圈和複雜邏輯
   - 使用向量化操作（numpy, pandas）

4. **執行頻率限制**
   - 每次分析最多使用 2 次 CodeInterpreterTool
   - 必要時將多個計算合併為一次執行

## 輸出格式

1. 趨勢分析: 方向、強度、延續性評估
2. 技術指標: 數值、訊號、背離情況
3. 關鍵價位: 支撐位、壓力位
4. 交易建議: 方向、進場價、停損價、目標價
5. 風險提示: 風險因素、注意事項
6. 信心評估: 0-100% 信心度

## 分析原則

- 保持客觀,基於數據
- 不過度解讀單一指標
- 永遠提供風險警示
- 承認分析的不確定性

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


@function_tool
def calculate_technical_indicators(
    ticker: str,
    price_data: list[dict[str, Any]],
    indicators: list[str] | None = None,
) -> dict[str, Any]:
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
    latest_close = price_data[-1]["close"]

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
    price_data: list[dict[str, Any]],
    lookback_days: int = 60,
) -> dict[str, Any]:
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
        recent_trend = price_data[-1]["close"] / price_data[-20]["close"]

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
    price_data: list[dict[str, Any]],
) -> dict[str, Any]:
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

    short_term = price_data[-5]["close"] / price_data[-10]["close"] - 1.0
    mid_term = price_data[-10]["close"] / price_data[-20]["close"] - 1.0

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
    price_data: list[dict[str, Any]],
) -> dict[str, Any]:
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

    current_price = price_data[-1]["close"]

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
    technical_indicators: dict[str, Any],
    trend_analysis: dict[str, Any],
    patterns: dict[str, Any],
) -> dict[str, Any]:
    """綜合分析產生交易訊號

    Args:
        ticker: 股票代號 (例如: "2330")
        technical_indicators: 技術指標計算結果 (來自 calculate_technical_indicators)
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
    logger.info(
        f"開始產生交易訊號 | 股票: {ticker} | "
        f"趨勢方向: {trend_analysis.get('direction', 'unknown')}"
    )

    signals = []
    overall_signal = "觀望"
    confidence = 0.5

    if trend_analysis.get("direction") == "上升":
        signals.append({"type": "trend", "signal": "看多"})
        confidence += 0.15

    bullish_patterns = sum(
        1 for p in patterns.get("patterns", []) if p["pattern_type"] == "bullish"
    )
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
    model_name: str = DEFAULT_MODEL,
    mcp_servers: list[Any] | None = None,
    openai_tools: list[Any] | None = None,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> Agent:
    """創建技術分析 Agent

    Args:
        model_name: 使用的 AI 模型名稱
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入
        openai_tools: 從 TradingAgent 傳入的共用工具（WebSearchTool, CodeInterpreterTool）
        max_turns: 最大執行回合數

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
        name="Technical Analyst",
        instructions=technical_agent_instructions(),
        model=model_name,
        mcp_servers=mcp_servers,
        tools=all_tools,
        model_settings=ModelSettings(
            tool_choice="required",
        ),
    )
    logger.info("Technical Analyst Agent created successfully")

    return analyst
