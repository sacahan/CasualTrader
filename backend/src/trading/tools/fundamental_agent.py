"""Fundamental Agent - 基本面分析自主型 Agent

這個模組實作具有自主分析能力的基本面分析 Agent。
"""

from __future__ import annotations

import os
import json
from typing import Any
from datetime import datetime

from dotenv import load_dotenv

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
    1. 直接的參數：ticker="2330", financial_data={...}
    2. JSON 字串參數：args='{"ticker":"2330","financial_data":{...}}'
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


# 注意：不再使用 Pydantic 模型作為函數參數類型，改用 dict
# 這是因為 agents 庫對 JSON Schema 有嚴格的驗證，
# Pydantic 嵌套模型會導致 additionalProperties 驗證失敗


def fundamental_agent_instructions() -> str:
    """基本面分析 Agent 的指令定義（簡化版，帶記憶追蹤）"""
    return f"""你是基本面分析專家。分析股票的財務體質、估值水準和成長潛力，提供投資評級。
持續追蹤：先查詢 memory_mcp (entity_type = "fundamental_analysis") 歷史研究，對比變化趨勢，識別機會和風險。

## 專業能力

- 財務報表分析與指標計算（ROE、ROA、P/E、P/B、淨利率等）
- 估值評估（相對估值、本益比分析、安全邊際）
- 成長潛力分析（營收成長、EPS 增長、趨勢評估）
- 產業研究與催化劑識別（透過 tavily_mcp 搜尋產業新聞、競爭動態）
- 投資評級生成（綜合評分、買賣建議、信心度）

## 🎯 tavily_mcp 使用限制

⚠️ **重要**：tavily_mcp 使用需要消耗點數，請遵守以下原則：
  - 只在需要時使用（優先檢查 memory_mcp 中的歷史研究）
  - 單次搜尋≤3個關鍵詞，避免重複搜尋相同內容
  - 若找到相關新聞，不必再搜尋同一個主題
  - 不搜尋過於通用的查詢，應基於具體的股票和產業
  - 每次分析最多進行 1-2 次有價值的搜尋

## 執行流程

**步驟 0：檢查記憶庫** → memory_mcp (entity_type="fundamental_analysis")
  - 無研究 → 完整分析
  - 新鮮（≤7 天）→ 增量更新
  - 陳舊（>7 天）→ 完整重新分析 + 對比

**步驟 1-3：數據收集與分析** → casual_market_mcp + tools
  1. 收集財務數據
  2. 分析財務健全性 → analyze_financial_health
  3. 評估成長潛力 → analyze_growth_potential

**步驟 4-6：估值與產業研究** → casual_market_mcp + tavily_mcp + tools
  4. 分析估值水位 → evaluate_valuation
  5. 識別催化劑 → 用 tavily_mcp 搜尋產業新聞、競爭動態、管理層變動
  6. 生成評級 → generate_investment_rating

**步驟 7：對比與保存** → memory_mcp
  - 若有先前研究：對比評級、指標趨勢、變化理由
  - 保存分析結果（含時間戳、快照、對比信息）

## 工具調用

- **calculate_financial_ratios** → 計算所有財務指標
- **analyze_financial_health** → 評估財務體質（0-100分）
- **evaluate_valuation** → 判斷估值水準（便宜/合理/昂貴）
- **analyze_growth_potential** → 評估成長（評分、趨勢）
- **generate_investment_rating** → 生成評級（買進/持有/賣出）

## 輸出結構

- 公司簡介
- 財務評分 (0-10)
- 成長評分 (0-10)
- 估值判斷 + 目標價
- 催化劑與風險
- 交易訊號
- 信心度 (0-100%)
- [若有先前研究] 變化分析

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


@function_tool(strict_mode=False)
def calculate_financial_ratios(
    ticker: str,
    financial_data: dict,
) -> dict:
    """計算財務比率

    **必要參數：**
        ticker: 股票代號 (例如: "2330") [必要]
        financial_data: 財務數據，包含 revenue, net_income, total_assets 等 [必要]

    Returns:
        dict: 財務比率結果 (ROE, ROA, 負債比, 流動比率等)
            {
                "ticker": str,
                "profitability": {"roe": float, "roa": float, "net_margin": float},
                "solvency": {"debt_ratio": float, "current_ratio": float},
                "valuation": {"pe_ratio": float, "pb_ratio": float}
            }

    Raises:
        返回錯誤字典：缺少必要參數或數據不足
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(ticker=ticker, financial_data=financial_data)

        _ticker = params.get("ticker") or ticker
        _financial_data = params.get("financial_data") or financial_data

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {"error": "缺少必要參數: ticker"}

        # 如果 financial_data 為 None，使用預設值
        if not _financial_data:
            logger.warning("缺少 financial_data 參數，使用預設值")
            _financial_data = {
                "revenue": 0,
                "net_income": 0,
                "total_assets": 1,
                "total_equity": 1,
                "total_liabilities": 0,
            }
        elif not isinstance(_financial_data, dict):
            # 如果是其他類型（如 Pydantic 模型），轉換為 dict
            if hasattr(_financial_data, "dict"):
                _financial_data = _financial_data.dict()
            elif hasattr(_financial_data, "model_dump"):
                _financial_data = _financial_data.model_dump()

        logger.info(f"開始計算財務比率 | 股票: {_ticker}")

        result = {
            "ticker": _ticker,
            "profitability": {},
            "solvency": {},
            "valuation": {},
        }

        equity = _financial_data.get("total_equity", 1)
        assets = _financial_data.get("total_assets", 1)
        revenue = _financial_data.get("revenue", 0)
        net_income = _financial_data.get("net_income", 0)

        result["profitability"] = {
            "roe": net_income / equity if equity > 0 else 0,
            "roa": net_income / assets if assets > 0 else 0,
            "net_margin": net_income / revenue if revenue > 0 else 0,
        }

        logger.debug(
            f"獲利能力指標 | ROE: {result['profitability']['roe']:.2%}, "
            f"ROA: {result['profitability']['roa']:.2%}, "
            f"淨利率: {result['profitability']['net_margin']:.2%}"
        )

        total_liabilities = _financial_data.get("total_liabilities", 0)
        current_assets = _financial_data.get("current_assets", 0)
        current_liabilities = _financial_data.get("current_liabilities", 1)

        result["solvency"] = {
            "debt_ratio": total_liabilities / assets if assets > 0 else 0,
            "current_ratio": current_assets / current_liabilities if current_liabilities > 0 else 0,
        }

        logger.debug(
            f"償債能力指標 | 負債比: {result['solvency']['debt_ratio']:.2%}, "
            f"流動比率: {result['solvency']['current_ratio']:.2f}"
        )

        market_cap = _financial_data.get("market_cap", 0)
        result["valuation"] = {
            "pe_ratio": market_cap / net_income if net_income > 0 else 0,
            "pb_ratio": market_cap / equity if equity > 0 else 0,
        }

        logger.info(f"財務比率計算完成 | 股票: {_ticker}")
        return result

    except Exception as e:
        logger.error(f"計算財務比率失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "profitability": {},
            "solvency": {},
            "valuation": {},
        }


@function_tool(strict_mode=False)
def analyze_financial_health(
    ticker: str,
    financial_ratios: dict,
) -> dict:
    """分析財務體質

    **必要參數：**
        ticker: 股票代號 (例如: "2330") [必要]
        financial_ratios: 財務比率 (來自 calculate_financial_ratios) [必要]

    Returns:
        dict: 財務體質分析結果
            {
                "ticker": str,
                "health_score": int,        # 0-100
                "health_grade": str,        # A-F
                "strengths": list[str],
                "weaknesses": list[str],
                "assessment": str
            }

    Raises:
        返回錯誤字典：缺少必要參數或數據不足
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(ticker=ticker, financial_ratios=financial_ratios)

        _ticker = params.get("ticker") or ticker
        _financial_ratios = params.get("financial_ratios") or financial_ratios

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {"error": "缺少必要參數: ticker"}

        # 如果 financial_ratios 為 None，使用預設值
        if not _financial_ratios:
            logger.warning("缺少 financial_ratios 參數，使用預設值")
            _financial_ratios = {
                "profitability": {"roe": 0, "roa": 0, "net_margin": 0},
                "solvency": {"debt_ratio": 0, "current_ratio": 2.0},
            }
        elif isinstance(_financial_ratios, dict):
            # 確保字典有必要的鍵
            if "profitability" not in _financial_ratios:
                _financial_ratios["profitability"] = {"roe": 0, "roa": 0, "net_margin": 0}
            if "solvency" not in _financial_ratios:
                _financial_ratios["solvency"] = {"debt_ratio": 0, "current_ratio": 2.0}

        logger.info(f"開始分析財務體質 | 股票: {_ticker}")

        score = 0
        strengths = []
        weaknesses = []

        roe = _financial_ratios["profitability"].get("roe", 0)
        if roe > 0.15:
            score += 25
            strengths.append(f"優異的 ROE ({roe:.1%})")
        elif roe > 0.10:
            score += 15
            strengths.append(f"良好的 ROE ({roe:.1%})")
        elif roe < 0.05:
            weaknesses.append(f"偏低的 ROE ({roe:.1%})")

        debt_ratio = _financial_ratios["solvency"].get("debt_ratio", 0)
        if debt_ratio < 0.3:
            score += 25
            strengths.append(f"低負債比 ({debt_ratio:.1%})")
        elif debt_ratio < 0.5:
            score += 15
        elif debt_ratio > 0.7:
            weaknesses.append(f"高負債比 ({debt_ratio:.1%})")

        current_ratio = _financial_ratios["solvency"].get("current_ratio", 0)
        if current_ratio > 2.0:
            score += 25
            strengths.append(f"優異的流動比率 ({current_ratio:.2f})")
        elif current_ratio > 1.5:
            score += 15
        elif current_ratio < 1.0:
            weaknesses.append(f"流動比率偏低 ({current_ratio:.2f})")

        net_margin = _financial_ratios["profitability"].get("net_margin", 0)
        if net_margin > 0.15:
            score += 25
            strengths.append(f"高淨利率 ({net_margin:.1%})")
        elif net_margin > 0.08:
            score += 15
        elif net_margin < 0.03:
            weaknesses.append(f"淨利率偏低 ({net_margin:.1%})")

        if score >= 80:
            grade, assessment = "A", "財務體質優異"
        elif score >= 60:
            grade, assessment = "B", "財務體質良好"
        elif score >= 40:
            grade, assessment = "C", "財務體質普通"
        elif score >= 20:
            grade, assessment = "D", "財務體質偏弱"
        else:
            grade, assessment = "F", "財務體質堪憂"

        logger.info(
            f"財務體質分析完成 | 股票: {_ticker} | 評級: {grade} | "
            f"得分: {score} | 優勢: {len(strengths)} | 弱點: {len(weaknesses)}"
        )

        return {
            "ticker": _ticker,
            "health_score": score,
            "health_grade": grade,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "assessment": assessment,
        }

    except Exception as e:
        logger.error(f"分析財務體質失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "health_score": 50,
            "health_grade": "C",
            "strengths": [],
            "weaknesses": [],
            "assessment": "分析失敗",
        }


@function_tool(strict_mode=False)
def evaluate_valuation(
    ticker: str,
    current_price: float,
    pe_ratio: float,
    financial_ratios: dict = None,
    industry_avg: dict = None,
) -> dict:
    """評估估值水準

    **必要參數：**
        ticker: 股票代號 (例如: "2330") [必要]
        current_price: 當前股價 [必要]
        pe_ratio: 本益比 [必要]

    **可選參數：**
        financial_ratios: 財務比率 (來自 calculate_financial_ratios)，缺少時使用預設值 [可選]
        industry_avg: 產業平均值，缺少時使用預設值 [可選]

    Returns:
        dict: 估值分析結果
            {
                "ticker": str,
                "current_price": float,
                "valuation_level": str,    # 便宜/合理/昂貴
                "fair_value": float,
                "discount_rate": float,
                "pe_assessment": str,
                "pb_assessment": str
            }

    Raises:
        返回錯誤字典：缺少必要參數
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(
            ticker=ticker,
            current_price=current_price,
            pe_ratio=pe_ratio,
            financial_ratios=financial_ratios,
            industry_avg=industry_avg,
        )

        _ticker = params.get("ticker") or ticker
        _current_price = params.get("current_price") or current_price
        _pe_ratio = params.get("pe_ratio") or pe_ratio
        _financial_ratios = params.get("financial_ratios") or financial_ratios
        _industry_avg = params.get("industry_avg") or industry_avg

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {"error": "缺少必要參數: ticker"}

        if not _current_price:
            logger.warning("缺少必要參數: current_price")
            return {"error": "缺少必要參數: current_price", "ticker": _ticker}

        # 如果 financial_ratios 為 None，使用預設值
        if not _financial_ratios:
            logger.warning("缺少 financial_ratios 參數，使用預設值")
            _financial_ratios = {"valuation": {"pe_ratio": 15, "pb_ratio": 1.8}}
        elif isinstance(_financial_ratios, dict) and "valuation" not in _financial_ratios:
            _financial_ratios["valuation"] = {"pe_ratio": 15, "pb_ratio": 1.8}

        # 如果 industry_avg 為 None，使用預設值
        if not _industry_avg:
            _industry_avg = {"pe": 15.0, "pb": 1.8}

        logger.info(f"開始評估估值 | 股票: {_ticker} | 當前價: {_current_price}")

        pe_ratio = _financial_ratios.get("valuation", {}).get("pe_ratio", 15)
        pb_ratio = _financial_ratios.get("valuation", {}).get("pb_ratio", 1.8)

        industry_pe = _industry_avg.get("pe", 15.0)
        industry_pb = _industry_avg.get("pb", 1.8)

        logger.debug(
            f"估值指標 | P/E: {pe_ratio:.2f} (產業: {industry_pe:.2f}) | "
            f"P/B: {pb_ratio:.2f} (產業: {industry_pb:.2f})"
        )

        pe_assessment = (
            "低估"
            if pe_ratio < industry_pe * 0.8
            else "高估"
            if pe_ratio > industry_pe * 1.2
            else "合理"
        )
        pb_assessment = (
            "低估"
            if pb_ratio < industry_pb * 0.8
            else "高估"
            if pb_ratio > industry_pb * 1.2
            else "合理"
        )

        if pe_assessment == "低估" and pb_assessment == "低估":
            valuation_level, fair_value = "便宜", _current_price * 1.2
        elif pe_assessment == "高估" or pb_assessment == "高估":
            valuation_level, fair_value = "昂貴", _current_price * 0.85
        else:
            valuation_level, fair_value = "合理", _current_price

        discount_rate = (fair_value - _current_price) / _current_price if _current_price > 0 else 0

        logger.info(
            f"估值評估完成 | 股票: {_ticker} | 等級: {valuation_level} | "
            f"合理價: {fair_value:.2f} | 折溢價率: {discount_rate:.1%}"
        )

        return {
            "ticker": _ticker,
            "current_price": _current_price,
            "valuation_level": valuation_level,
            "fair_value": fair_value,
            "discount_rate": discount_rate,
            "pe_assessment": pe_assessment,
            "pb_assessment": pb_assessment,
        }

    except Exception as e:
        logger.error(f"評估估值失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "current_price": current_price or 0,
            "valuation_level": "未知",
            "fair_value": current_price or 0,
            "discount_rate": 0,
            "pe_assessment": "未知",
            "pb_assessment": "未知",
        }


@function_tool(strict_mode=False)
def analyze_growth_potential(
    ticker: str,
    historical_data: dict,
    **kwargs,
) -> str:
    """分析成長潛力

    **必要參數：**
        ticker: 股票代號 (例如: "2330") [必要]
        historical_data: 歷史財務數據，包含營收成長率、EPS 成長率 [必要]

    **可選參數：**
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 成長潛力分析結果
            {
                "ticker": str,
                "growth_score": int,       # 0-100
                "growth_trend": str,       # 加速/穩定/趨緩
                "revenue_growth": float,
                "eps_growth": float,
                "assessment": str
            }

    Raises:
        返回錯誤字典：缺少必要參數或數據不足
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(ticker=ticker, historical_data=historical_data, **kwargs)

        _ticker = params.get("ticker") or ticker
        _historical_data = params.get("historical_data") or historical_data

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {"error": "缺少必要參數: ticker"}

        # 如果 historical_data 為 None，使用預設值
        if not _historical_data:
            logger.warning("缺少 historical_data 參數，使用預設值")
            _historical_data = {
                "latest_revenue_growth": 0.0,
                "latest_eps_growth": 0.0,
            }
        elif not isinstance(_historical_data, dict):
            # 如果是其他類型（如 Pydantic 模型），轉換為 dict
            if hasattr(_historical_data, "dict"):
                _historical_data = _historical_data.dict()
            elif hasattr(_historical_data, "model_dump"):
                _historical_data = _historical_data.model_dump()

        logger.info(f"開始分析成長潛力 | 股票: {_ticker}")

        score = 0
        revenue_growth = _historical_data.get("latest_revenue_growth", 0.0)
        eps_growth = _historical_data.get("latest_eps_growth", 0.0)

        logger.debug(f"成長數據 | 營收成長: {revenue_growth:.1%} | EPS成長: {eps_growth:.1%}")

        if revenue_growth > 0.15:
            score += 40
            growth_assessment = "高成長"
        elif revenue_growth > 0.08:
            score += 25
            growth_assessment = "穩健成長"
        elif revenue_growth > 0:
            score += 10
            growth_assessment = "低速成長"
        else:
            growth_assessment = "負成長"

        if eps_growth > 0.20:
            score += 40
        elif eps_growth > 0.10:
            score += 25
        elif eps_growth > 0:
            score += 10

        if revenue_growth > 0.10 and eps_growth > 0.15:
            growth_trend = "加速"
        elif revenue_growth > 0.05 and eps_growth > 0.05:
            growth_trend = "穩定"
        else:
            growth_trend = "趨緩"

        logger.info(
            f"成長潛力分析完成 | 股票: {_ticker} | 評估: {growth_assessment} | "
            f"趨勢: {growth_trend} | 分數: {min(score, 100)}"
        )

        return {
            "ticker": _ticker,
            "growth_score": min(score, 100),
            "growth_trend": growth_trend,
            "revenue_growth": revenue_growth,
            "eps_growth": eps_growth,
            "assessment": growth_assessment,
        }

    except Exception as e:
        logger.error(f"分析成長潛力失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "growth_score": 50,
            "growth_trend": "未知",
            "revenue_growth": 0,
            "eps_growth": 0,
            "assessment": "分析失敗",
        }


@function_tool(strict_mode=False)
def generate_investment_rating(
    ticker: str = None,
    financial_health: dict = None,
    valuation: dict = None,
    growth: dict = None,
    **kwargs,
) -> str:
    """產生投資評級

    **可選參數：**
        ticker: 股票代號 (例如: "2330")，缺少時預設為 "未知" [可選]
        financial_health: 財務體質分析，缺少時使用預設值 [可選]
        valuation: 估值分析，缺少時使用預設值 [可選]
        growth: 成長分析，缺少時使用預設值 [可選]
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 投資評級結果
            {
                "ticker": str,
                "rating": str,             # 強力買進/買進/持有/賣出
                "target_price": float,
                "confidence": float,       # 0-1
                "recommendation": str,
                "key_reasons": list[str],
                "timestamp": str
            }

    Note:
        此函數具有高度的容錯能力，即使缺少部分輸入參數也能返回有效結果。
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(
            ticker=ticker,
            financial_health=financial_health,
            valuation=valuation,
            growth=growth,
            **kwargs,
        )

        _ticker = params.get("ticker") or ticker
        _financial_health = params.get("financial_health") or financial_health
        _valuation = params.get("valuation") or valuation
        _growth = params.get("growth") or growth

        # 使用預設值以防參數缺失
        if not _ticker:
            logger.warning("缺少 ticker 參數")
            _ticker = "未知"

        if not _financial_health:
            logger.warning("缺少 financial_health 參數，使用預設值")
            _financial_health = {"health_score": 50, "strengths": [], "weaknesses": []}

        if not _valuation:
            logger.warning("缺少 valuation 參數，使用預設值")
            _valuation = {"valuation_level": "合理", "fair_value": 0}

        if not _growth:
            logger.warning("缺少 growth 參數，使用預設值")
            _growth = {"growth_score": 50}

        health_score = _financial_health.get("health_score", 50)
        valuation_level = _valuation.get("valuation_level", "合理")
        growth_score = _growth.get("growth_score", 50)

        logger.info(
            f"開始產生投資評級 | 股票: {_ticker} | 體質分數: {health_score} | "
            f"估值: {valuation_level} | 成長分數: {growth_score}"
        )

        overall_score = (health_score * 0.4 + growth_score * 0.35) * (
            1.2 if valuation_level == "便宜" else 0.9 if valuation_level == "昂貴" else 1.0
        )

        key_reasons = []

        if overall_score >= 75 and valuation_level == "便宜":
            rating, confidence = "強力買進", 0.85
            recommendation = "優質公司且估值便宜,建議積極買進"
            key_reasons.extend(_financial_health.get("strengths", [])[:2])
        elif overall_score >= 60:
            rating, confidence = "買進", 0.70
            recommendation = "基本面穩健,建議逢低買進"
            key_reasons.extend(_financial_health.get("strengths", [])[:2])
        elif overall_score >= 40:
            rating, confidence = "持有", 0.60
            recommendation = "基本面普通,建議持有觀望"
        else:
            rating, confidence = "賣出", 0.75
            recommendation = "基本面轉弱,建議減碼"
            key_reasons.extend(_financial_health.get("weaknesses", []))

        target_price = _valuation.get("fair_value", 0)

        logger.info(
            f"投資評級產生完成 | 股票: {_ticker} | 評級: {rating} | "
            f"目標價: {target_price:.2f} | 信心度: {confidence:.1%}"
        )

        return {
            "ticker": _ticker,
            "rating": rating,
            "target_price": target_price,
            "confidence": confidence,
            "recommendation": recommendation,
            "key_reasons": key_reasons,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"產生投資評級失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "rating": "觀望",
            "target_price": 0,
            "confidence": 0.3,
            "recommendation": f"評級生成失敗: {str(e)}",
            "key_reasons": [],
            "timestamp": datetime.now().isoformat(),
        }


async def get_fundamental_agent(
    llm_model: LitellmModel = None,
    extra_headers: dict[str, str] = None,
    mcp_servers: list | None = None,
) -> Agent:
    """創建基本面分析 Agent

    Args:
        llm_model: 使用的語言模型實例 (LitellmModel)，如果為 None，則使用預設模型
        extra_headers: 額外的 HTTP 標頭，用於模型 API 請求
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入

    Returns:
        Agent: 配置好的基本面分析 Agent

    Note:
        - 只使用自訂工具進行財務分析
        - Timeout 由主 TradingAgent 的 execution_timeout 統一控制
        - Sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制
    """
    logger.info(f"get_fundamental_agent() called with model={llm_model}")

    logger.debug("Creating custom tools with function_tool")
    all_tools = [
        calculate_financial_ratios,
        analyze_financial_health,
        evaluate_valuation,
        analyze_growth_potential,
        generate_investment_rating,
    ]
    logger.debug(f"Total tools: {len(all_tools)}")

    logger.info(
        f"Creating Agent with model={llm_model}, mcp_servers={len(mcp_servers) if mcp_servers else 0}, tools={len(all_tools)}"
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

    # 確保 mcp_servers 是列表
    if mcp_servers is None:
        mcp_servers = []

    analyst = Agent(
        name="fundamental_analyst",
        instructions=fundamental_agent_instructions(),
        model=llm_model,
        mcp_servers=mcp_servers,
        tools=all_tools,
        model_settings=ModelSettings(**model_settings_dict),
    )
    logger.info("Fundamental Analyst Agent created successfully")

    return analyst
