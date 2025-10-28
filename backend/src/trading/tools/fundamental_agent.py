"""Fundamental Agent - 基本面分析自主型 Agent

這個模組實作具有自主分析能力的基本面分析 Agent。
"""

from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from pydantic import BaseModel

from agents import Agent, function_tool, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel

from common.logger import logger

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gpt-5-mini")
DEFAULT_MAX_TURNS = os.getenv("DEFAULT_MAX_TURNS", 30)


# ===== Pydantic Models for Tool Parameters =====


class FinancialData(BaseModel):
    """財務數據模型"""

    revenue: float = 0
    net_income: float = 0
    total_assets: float = 1
    total_equity: float = 1
    total_liabilities: float = 0
    current_assets: float = 0
    current_liabilities: float = 1
    market_cap: float = 0


class Profitability(BaseModel):
    """獲利能力指標"""

    roe: float
    roa: float
    net_margin: float


class Solvency(BaseModel):
    """償債能力指標"""

    debt_ratio: float
    current_ratio: float


class Valuation(BaseModel):
    """估值指標"""

    pe_ratio: float
    pb_ratio: float


class FinancialRatios(BaseModel):
    """財務比率模型"""

    ticker: str
    profitability: Profitability
    solvency: Solvency
    valuation: Valuation


class FinancialHealth(BaseModel):
    """財務體質分析"""

    ticker: str
    health_score: float
    health_grade: str
    strengths: list[str]
    weaknesses: list[str]
    assessment: str


class ValuationAnalysis(BaseModel):
    """估值分析"""

    ticker: str
    current_price: float
    valuation_level: str
    fair_value: float
    discount_rate: float
    pe_assessment: str
    pb_assessment: str


class HistoricalData(BaseModel):
    """歷史數據模型"""

    latest_revenue_growth: float = 0
    latest_eps_growth: float = 0


class GrowthAnalysis(BaseModel):
    """成長分析"""

    ticker: str
    growth_score: float
    growth_trend: str
    revenue_growth: float
    eps_growth: float
    assessment: str


class IndustryAverage(BaseModel):
    """產業平均值"""

    pe: float = 15.0
    pb: float = 1.8


def fundamental_agent_instructions() -> str:
    """基本面分析 Agent 的指令定義（精簡版）"""
    return f"""你是基本面分析專家。你的職責是分析股票的財務體質、估值水準和成長潛力，提供結構化的投資評級。

## 你的專業能力

- 財務報表分析（資產負債表、損益表、現金流量表）
- 財務指標計算（ROE、ROA、P/E、P/B、利潤率等）
- 估值評估（相對估值、本益比分析、安全邊際評估）
- 成長潛力分析（營收成長率、EPS 成長率、趨勢評估）
- 投資評級生成（綜合評分、建議、信心度）

## 可用工具

**專業分析工具（5 個）**
  1. calculate_financial_ratios - 計算財務指標
  2. analyze_financial_health - 評估財務體質（0-100 分評級）
  3. evaluate_valuation - 分析估值水準（便宜/合理/昂貴）
  4. analyze_growth_potential - 評估成長潛力
  5. generate_investment_rating - 生成投資評級和建議

**數據獲取**
  • casual_market_mcp - 獲取股票財報、基本面數據、市場信息
  • memory_mcp - 保存分析過程、重要結論、決策邏輯

**AI 能力**
  • WebSearchTool - 搜尋產業報告、競爭對手分析、法說會信息
  • CodeInterpreterTool - 執行複雜模型（DCF 估值、敏感度分析等）

## 執行流程

1. 收集財務數據 → 使用 casual_market_mcp 獲取財務資料
2. 計算指標 → 調用 calculate_financial_ratios
3. 評估體質 → 調用 analyze_financial_health
4. 分析估值 → 調用 evaluate_valuation
5. 評估成長 → 調用 analyze_growth_potential
6. 生成評級 → 調用 generate_investment_rating
7. 保存知識 → 使用 memory_mcp 記錄分析邏輯和決策依據

## CodeInterpreterTool 使用指南 ⚠️

**使用時機**
  ✅ DCF 現金流折現估值
  ✅ 敏感度分析（多情景模型）
  ✅ 複雜財務模型

**不要使用**
  ❌ 簡單計算（用自訂工具代替）
  ❌ 已有自訂工具的功能

**限制：每次分析最多 2 次，代碼簡潔（< 100 行）**

## 輸出格式

結構化投資評級，包括：
  • 財務評分 (0-100)
  • 估值等級（便宜/合理/昂貴）
  • 成長評估（評分 + 趨勢）
  • 投資建議（買進/持有/賣出）
  • 目標價位
  • 關鍵理由（優勢、弱點、風險）
  • 信心度 (0-100%)

## 決策原則

- 重視長期價值，淡化短期波動
- 注重安全邊際，避免高估股票
- 承認分析侷限，不過度武斷
- 決策理由充分，邏輯自洽

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


@function_tool
def calculate_financial_ratios(
    ticker: str,
    financial_data: FinancialData,
) -> str:
    """計算財務比率

    Args:
        ticker: 股票代號 (例如: "2330")
        financial_data: 財務數據,包含 revenue, net_income, total_assets 等

    Returns:
        str: 財務比率結果的JSON字符串 (ROE, ROA, 負債比, 流動比率等)
    """
    logger.info(f"開始計算財務比率 | 股票: {ticker}")

    result = {
        "ticker": ticker,
        "profitability": {},
        "solvency": {},
        "valuation": {},
    }

    equity = financial_data.total_equity
    assets = financial_data.total_assets
    revenue = financial_data.revenue
    net_income = financial_data.net_income

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

    total_liabilities = financial_data.total_liabilities
    current_assets = financial_data.current_assets
    current_liabilities = financial_data.current_liabilities

    result["solvency"] = {
        "debt_ratio": total_liabilities / assets if assets > 0 else 0,
        "current_ratio": current_assets / current_liabilities if current_liabilities > 0 else 0,
    }

    logger.debug(
        f"償債能力指標 | 負債比: {result['solvency']['debt_ratio']:.2%}, "
        f"流動比率: {result['solvency']['current_ratio']:.2f}"
    )

    market_cap = financial_data.market_cap
    result["valuation"] = {
        "pe_ratio": market_cap / net_income if net_income > 0 else 0,
        "pb_ratio": market_cap / equity if equity > 0 else 0,
    }

    logger.info(f"財務比率計算完成 | 股票: {ticker}")
    return result


@function_tool
def analyze_financial_health(
    ticker: str,
    financial_ratios: FinancialRatios,
) -> str:
    """分析財務體質

    Args:
        ticker: 股票代號 (例如: "2330")
        financial_ratios: 財務比率 (來自 calculate_financial_ratios)

    Returns:
        dict: 財務體質分析 (健康度評分、評級、優勢、弱點)
    """
    logger.info(f"開始分析財務體質 | 股票: {ticker}")

    score = 0
    strengths = []
    weaknesses = []

    roe = financial_ratios.profitability.roe
    if roe > 0.15:
        score += 25
        strengths.append(f"優異的 ROE ({roe:.1%})")
    elif roe > 0.10:
        score += 15
        strengths.append(f"良好的 ROE ({roe:.1%})")
    elif roe < 0.05:
        weaknesses.append(f"偏低的 ROE ({roe:.1%})")

    debt_ratio = financial_ratios.solvency.debt_ratio
    if debt_ratio < 0.3:
        score += 25
        strengths.append(f"低負債比 ({debt_ratio:.1%})")
    elif debt_ratio < 0.5:
        score += 15
    elif debt_ratio > 0.7:
        weaknesses.append(f"高負債比 ({debt_ratio:.1%})")

    current_ratio = financial_ratios.solvency.current_ratio
    if current_ratio > 2.0:
        score += 25
        strengths.append(f"優異的流動比率 ({current_ratio:.2f})")
    elif current_ratio > 1.5:
        score += 15
    elif current_ratio < 1.0:
        weaknesses.append(f"流動比率偏低 ({current_ratio:.2f})")

    net_margin = financial_ratios.profitability.net_margin
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
        f"財務體質分析完成 | 股票: {ticker} | 評級: {grade} | "
        f"得分: {score} | 優勢: {len(strengths)} | 弱點: {len(weaknesses)}"
    )

    return {
        "ticker": ticker,
        "health_score": score,
        "health_grade": grade,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "assessment": assessment,
    }


@function_tool
def evaluate_valuation(
    ticker: str,
    current_price: float,
    financial_ratios: FinancialRatios,
    industry_avg: IndustryAverage | None = None,
) -> str:
    """評估估值水準

    Args:
        ticker: 股票代號 (例如: "2330")
        current_price: 當前股價
        financial_ratios: 財務比率 (來自 calculate_financial_ratios)
        industry_avg: 產業平均值 (可選)

    Returns:
        dict: 估值分析 (估值水準、合理價、折溢價率)
    """
    logger.info(f"開始評估估值 | 股票: {ticker} | 當前價: {current_price}")

    pe_ratio = financial_ratios.valuation.pe_ratio
    pb_ratio = financial_ratios.valuation.pb_ratio

    industry_pe = industry_avg.pe if industry_avg else 15.0
    industry_pb = industry_avg.pb if industry_avg else 1.8

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
        valuation_level, fair_value = "便宜", current_price * 1.2
    elif pe_assessment == "高估" or pb_assessment == "高估":
        valuation_level, fair_value = "昂貴", current_price * 0.85
    else:
        valuation_level, fair_value = "合理", current_price

    discount_rate = (fair_value - current_price) / current_price if current_price > 0 else 0

    logger.info(
        f"估值評估完成 | 股票: {ticker} | 等級: {valuation_level} | "
        f"合理價: {fair_value:.2f} | 折溢價率: {discount_rate:.1%}"
    )

    return {
        "ticker": ticker,
        "current_price": current_price,
        "valuation_level": valuation_level,
        "fair_value": fair_value,
        "discount_rate": discount_rate,
        "pe_assessment": pe_assessment,
        "pb_assessment": pb_assessment,
    }


@function_tool
def analyze_growth_potential(
    ticker: str,
    historical_data: HistoricalData,
) -> str:
    """分析成長潛力

    Args:
        ticker: 股票代號 (例如: "2330")
        historical_data: 歷史財務數據 (營收成長率、EPS 成長率)

    Returns:
        dict: 成長潛力分析 (成長評分、成長趨勢)
    """
    logger.info(f"開始分析成長潛力 | 股票: {ticker}")

    score = 0
    revenue_growth = historical_data.latest_revenue_growth
    eps_growth = historical_data.latest_eps_growth

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
        f"成長潛力分析完成 | 股票: {ticker} | 評估: {growth_assessment} | "
        f"趨勢: {growth_trend} | 分數: {min(score, 100)}"
    )

    return {
        "ticker": ticker,
        "growth_score": min(score, 100),
        "growth_trend": growth_trend,
        "revenue_growth": revenue_growth,
        "eps_growth": eps_growth,
        "assessment": growth_assessment,
    }


@function_tool
def generate_investment_rating(
    ticker: str,
    financial_health: FinancialHealth,
    valuation: ValuationAnalysis,
    growth: GrowthAnalysis,
) -> str:
    """產生投資評級

    Args:
        ticker: 股票代號 (例如: "2330")
        financial_health: 財務體質分析
        valuation: 估值分析
        growth: 成長分析

    Returns:
        dict: 投資評級 (買進/持有/賣出建議)
    """
    health_score = financial_health.health_score
    valuation_level = valuation.valuation_level
    growth_score = growth.growth_score

    logger.info(
        f"開始產生投資評級 | 股票: {ticker} | 體質分數: {health_score} | "
        f"估值: {valuation_level} | 成長分數: {growth_score}"
    )

    overall_score = (health_score * 0.4 + growth_score * 0.35) * (
        1.2 if valuation_level == "便宜" else 0.9 if valuation_level == "昂貴" else 1.0
    )

    key_reasons = []

    if overall_score >= 75 and valuation_level == "便宜":
        rating, confidence = "強力買進", 0.85
        recommendation = "優質公司且估值便宜,建議積極買進"
        key_reasons.extend(financial_health.strengths)
    elif overall_score >= 60:
        rating, confidence = "買進", 0.70
        recommendation = "基本面穩健,建議逢低買進"
        key_reasons.extend(financial_health.strengths[:2])
    elif overall_score >= 40:
        rating, confidence = "持有", 0.60
        recommendation = "基本面普通,建議持有觀望"
    else:
        rating, confidence = "賣出", 0.75
        recommendation = "基本面轉弱,建議減碼"
        key_reasons.extend(financial_health.weaknesses)

    target_price = valuation.fair_value

    logger.info(
        f"投資評級產生完成 | 股票: {ticker} | 評級: {rating} | "
        f"目標價: {target_price:.2f} | 信心度: {confidence:.1%}"
    )

    return {
        "ticker": ticker,
        "rating": rating,
        "target_price": target_price,
        "confidence": confidence,
        "recommendation": recommendation,
        "key_reasons": key_reasons,
        "timestamp": datetime.now().isoformat(),
    }


async def get_fundamental_agent(
    llm_model: LitellmModel = None,
    extra_headers: dict[str, str] = None,
    mcp_servers: list | None = None,
    openai_tools: list | None = None,
) -> Agent:
    """創建基本面分析 Agent

    Args:
        llm_model: 使用的語言模型實例 (LitellmModel)，如果為 None，則使用預設模型
        extra_headers: 額外的 HTTP 標頭，用於模型 API 請求
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入
        openai_tools: 從 TradingAgent 傳入的共用工具（WebSearchTool, CodeInterpreterTool）

    Returns:
        Agent: 配置好的基本面分析 Agent

    Note:
        Timeout 由主 TradingAgent 的 execution_timeout 統一控制，
        sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制。
    """
    logger.info(f"get_fundamental_agent() called with model={llm_model}")

    logger.debug("Creating custom tools with function_tool")
    custom_tools = [
        calculate_financial_ratios,
        analyze_financial_health,
        evaluate_valuation,
        analyze_growth_potential,
        generate_investment_rating,
    ]

    # 合併自訂工具和共用工具
    all_tools = custom_tools + (openai_tools or [])
    logger.debug(f"Total tools (custom + shared): {len(all_tools)}")

    logger.info(
        f"Creating Agent with model={llm_model}, mcp_servers={len(mcp_servers)}, tools={len(all_tools)}"
    )
    analyst = Agent(
        name="fundamental_analyst",
        instructions=fundamental_agent_instructions(),
        model=llm_model,
        mcp_servers=mcp_servers,
        tools=all_tools,
        model_settings=ModelSettings(
            tool_choice="required",  # 強制使用工具
            max_completion_tokens=500,  # 控制回答長度，避免過度冗長
            extra_headers=extra_headers if extra_headers else None,  # 傳遞額外標頭
        ),
    )
    logger.info("Fundamental Analyst Agent created successfully")

    return analyst
