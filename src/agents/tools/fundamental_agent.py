"""
基本面分析工具
專門化的公司基本面和財務分析工具
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CompanyFundamentals(BaseModel):
    """公司基本面數據結構"""

    symbol: str
    company_name: str
    market_cap: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    revenue_growth: float | None = None
    eps_growth: float | None = None
    dividend_yield: float | None = None
    analysis_timestamp: datetime
    quality_score: float | None = None
    valuation_score: float | None = None
    growth_score: float | None = None


class FundamentalAnalysisResult(BaseModel):
    """基本面分析結果"""

    symbol: str
    analysis_type: str
    summary: str
    recommendation: str
    confidence_level: float
    key_strengths: list[str]
    key_concerns: list[str]
    target_price_range: tuple[float, float] | None = None
    risk_level: str
    investment_horizon: str
    detailed_analysis: dict[str, Any]
    data_sources: list[str]
    analysis_timestamp: datetime


class FundamentalAgent:
    """
    基本面分析工具 - 提供深度的公司財務和基本面分析
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("fundamental_agent")

    async def analyze_company_fundamentals(
        self,
        symbol: str,
        analysis_depth: str = "standard",
        focus_areas: list[str] | None = None,
    ) -> FundamentalAnalysisResult:
        """
        分析公司基本面

        Args:
            symbol: 股票代碼
            analysis_depth: 分析深度 ("basic", "standard", "comprehensive")
            focus_areas: 重點分析領域 (可選)

        Returns:
            基本面分析結果
        """
        try:
            # 獲取公司基本面數據
            fundamentals = await self._fetch_company_data(symbol)

            # 執行分析
            analysis_result = await self._perform_fundamental_analysis(
                fundamentals, analysis_depth, focus_areas or []
            )

            self.logger.info(f"Fundamental analysis completed for {symbol}")
            return analysis_result

        except Exception as e:
            self.logger.error(f"Fundamental analysis failed for {symbol}: {e}")
            raise

    async def _fetch_company_data(self, symbol: str) -> CompanyFundamentals:
        """獲取公司基本面數據"""
        # 這裡將整合 CasualMarket MCP 工具獲取實際數據
        # 目前返回模擬數據結構

        return CompanyFundamentals(
            symbol=symbol,
            company_name=f"Company {symbol}",
            analysis_timestamp=datetime.now(),
            # 實際實作時會從 MCP 工具獲取真實數據
            pe_ratio=15.5,
            pb_ratio=1.8,
            roe=0.15,
            debt_to_equity=0.4,
            current_ratio=2.1,
            revenue_growth=0.08,
            eps_growth=0.12,
            dividend_yield=0.025,
        )

    async def _perform_fundamental_analysis(
        self,
        fundamentals: CompanyFundamentals,
        depth: str,
        focus_areas: list[str],
    ) -> FundamentalAnalysisResult:
        """執行基本面分析"""

        # 財務體質分析
        financial_health = self._analyze_financial_health(fundamentals)

        # 估值分析
        valuation_analysis = self._analyze_valuation(fundamentals)

        # 成長性分析
        growth_analysis = self._analyze_growth_potential(fundamentals)

        # 股利政策分析
        dividend_analysis = self._analyze_dividend_policy(fundamentals)

        # 綜合評分
        overall_score = self._calculate_overall_score(
            financial_health, valuation_analysis, growth_analysis, dividend_analysis
        )

        # 投資建議
        recommendation = self._generate_investment_recommendation(
            overall_score, fundamentals
        )

        # 風險評估
        risk_assessment = self._assess_investment_risk(fundamentals)

        return FundamentalAnalysisResult(
            symbol=fundamentals.symbol,
            analysis_type="comprehensive_fundamental",
            summary=self._generate_analysis_summary(
                fundamentals, overall_score, recommendation
            ),
            recommendation=recommendation["action"],
            confidence_level=recommendation["confidence"],
            key_strengths=self._identify_key_strengths(fundamentals),
            key_concerns=self._identify_key_concerns(fundamentals),
            target_price_range=recommendation.get("target_price_range"),
            risk_level=risk_assessment["level"],
            investment_horizon=self._suggest_investment_horizon(fundamentals),
            detailed_analysis={
                "financial_health": financial_health,
                "valuation": valuation_analysis,
                "growth": growth_analysis,
                "dividend": dividend_analysis,
                "risk": risk_assessment,
                "overall_score": overall_score,
            },
            data_sources=["CasualMarket MCP", "Company Filings", "Market Data"],
            analysis_timestamp=datetime.now(),
        )

    def _analyze_financial_health(
        self, fundamentals: CompanyFundamentals
    ) -> dict[str, Any]:
        """分析財務體質"""
        health_score = 0
        analysis = {
            "debt_management": "良好",
            "liquidity": "充足",
            "profitability": "穩定",
            "efficiency": "高效",
            "score": 0,
            "concerns": [],
            "strengths": [],
        }

        # 負債管理評估
        if fundamentals.debt_to_equity and fundamentals.debt_to_equity < 0.3:
            health_score += 25
            analysis["strengths"].append("負債比率低，財務結構穩健")
        elif fundamentals.debt_to_equity and fundamentals.debt_to_equity > 0.6:
            analysis["concerns"].append("負債比率偏高，需關注償債能力")
            analysis["debt_management"] = "需關注"

        # 流動性評估
        if fundamentals.current_ratio and fundamentals.current_ratio > 2.0:
            health_score += 25
            analysis["strengths"].append("流動比率充足，短期償債能力強")
        elif fundamentals.current_ratio and fundamentals.current_ratio < 1.2:
            analysis["concerns"].append("流動比率偏低，短期流動性不足")
            analysis["liquidity"] = "不足"

        # 獲利能力評估
        if fundamentals.roe and fundamentals.roe > 0.15:
            health_score += 25
            analysis["strengths"].append("ROE 表現優異，獲利能力強")
        elif fundamentals.roe and fundamentals.roe < 0.08:
            analysis["concerns"].append("ROE 偏低，獲利能力待改善")
            analysis["profitability"] = "待改善"

        analysis["score"] = health_score
        return analysis

    def _analyze_valuation(self, fundamentals: CompanyFundamentals) -> dict[str, Any]:
        """分析估值水準"""
        valuation_score = 0
        analysis = {
            "pe_assessment": "合理",
            "pb_assessment": "合理",
            "overall_valuation": "合理",
            "score": 0,
            "relative_value": "中性",
        }

        # P/E 比評估
        if fundamentals.pe_ratio:
            if fundamentals.pe_ratio < 12:
                valuation_score += 40
                analysis["pe_assessment"] = "低估"
                analysis["relative_value"] = "便宜"
            elif fundamentals.pe_ratio > 25:
                analysis["pe_assessment"] = "高估"
                analysis["relative_value"] = "昂貴"
            else:
                valuation_score += 20

        # P/B 比評估
        if fundamentals.pb_ratio:
            if fundamentals.pb_ratio < 1.5:
                valuation_score += 30
                analysis["pb_assessment"] = "低估"
            elif fundamentals.pb_ratio > 3.0:
                analysis["pb_assessment"] = "高估"
            else:
                valuation_score += 15

        # 綜合估值判斷
        if valuation_score >= 60:
            analysis["overall_valuation"] = "低估"
        elif valuation_score <= 20:
            analysis["overall_valuation"] = "高估"

        analysis["score"] = valuation_score
        return analysis

    def _analyze_growth_potential(
        self, fundamentals: CompanyFundamentals
    ) -> dict[str, Any]:
        """分析成長潛力"""
        growth_score = 0
        analysis = {
            "revenue_trend": "平穩",
            "earnings_trend": "平穩",
            "growth_quality": "中等",
            "score": 0,
            "growth_drivers": [],
        }

        # 營收成長評估
        if fundamentals.revenue_growth:
            if fundamentals.revenue_growth > 0.15:
                growth_score += 40
                analysis["revenue_trend"] = "強勁"
                analysis["growth_drivers"].append("營收高速成長")
            elif fundamentals.revenue_growth > 0.05:
                growth_score += 20
                analysis["growth_drivers"].append("營收穩定成長")
            elif fundamentals.revenue_growth < 0:
                analysis["revenue_trend"] = "衰退"

        # 獲利成長評估
        if fundamentals.eps_growth:
            if fundamentals.eps_growth > 0.20:
                growth_score += 40
                analysis["earnings_trend"] = "優異"
                analysis["growth_drivers"].append("獲利大幅成長")
            elif fundamentals.eps_growth > 0.08:
                growth_score += 20
                analysis["growth_drivers"].append("獲利穩定成長")
            elif fundamentals.eps_growth < 0:
                analysis["earnings_trend"] = "衰退"

        # 成長品質評估
        if growth_score >= 60:
            analysis["growth_quality"] = "優異"
        elif growth_score >= 30:
            analysis["growth_quality"] = "良好"
        elif growth_score < 15:
            analysis["growth_quality"] = "疲弱"

        analysis["score"] = growth_score
        return analysis

    def _analyze_dividend_policy(
        self, fundamentals: CompanyFundamentals
    ) -> dict[str, Any]:
        """分析股利政策"""
        dividend_score = 0
        analysis = {
            "yield_level": "中等",
            "sustainability": "穩定",
            "policy_assessment": "合理",
            "score": 0,
        }

        if fundamentals.dividend_yield:
            if fundamentals.dividend_yield > 0.04:
                dividend_score += 30
                analysis["yield_level"] = "高"
            elif fundamentals.dividend_yield > 0.02:
                dividend_score += 20
                analysis["yield_level"] = "適中"
            else:
                dividend_score += 10
                analysis["yield_level"] = "低"

            # 股利可持續性評估（基於獲利能力）
            if fundamentals.roe and fundamentals.roe > 0.12:
                dividend_score += 20
                analysis["sustainability"] = "良好"
            elif fundamentals.roe and fundamentals.roe < 0.08:
                analysis["sustainability"] = "需關注"

        analysis["score"] = dividend_score
        return analysis

    def _calculate_overall_score(
        self,
        financial_health: dict[str, Any],
        valuation: dict[str, Any],
        growth: dict[str, Any],
        dividend: dict[str, Any],
    ) -> dict[str, Any]:
        """計算綜合評分"""

        # 加權評分
        weights = {
            "financial_health": 0.3,
            "valuation": 0.3,
            "growth": 0.25,
            "dividend": 0.15,
        }

        overall_score = (
            financial_health["score"] * weights["financial_health"]
            + valuation["score"] * weights["valuation"]
            + growth["score"] * weights["growth"]
            + dividend["score"] * weights["dividend"]
        )

        # 評級判定
        if overall_score >= 75:
            rating = "A"
            description = "優質投資標的"
        elif overall_score >= 60:
            rating = "B"
            description = "良好投資標的"
        elif overall_score >= 45:
            rating = "C"
            description = "中性投資標的"
        elif overall_score >= 30:
            rating = "D"
            description = "較弱投資標的"
        else:
            rating = "E"
            description = "不建議投資"

        return {
            "score": overall_score,
            "rating": rating,
            "description": description,
            "component_scores": {
                "financial_health": financial_health["score"],
                "valuation": valuation["score"],
                "growth": growth["score"],
                "dividend": dividend["score"],
            },
        }

    def _generate_investment_recommendation(
        self, overall_score: dict[str, Any], fundamentals: CompanyFundamentals
    ) -> dict[str, Any]:
        """生成投資建議"""

        score = overall_score["score"]
        rating = overall_score["rating"]

        if score >= 75:
            action = "強力買進"
            confidence = 0.9
        elif score >= 60:
            action = "買進"
            confidence = 0.75
        elif score >= 45:
            action = "持有"
            confidence = 0.6
        elif score >= 30:
            action = "減持"
            confidence = 0.7
        else:
            action = "賣出"
            confidence = 0.8

        return {
            "action": action,
            "confidence": confidence,
            "rating": rating,
            "reasoning": f"基於綜合評分 {score:.1f} 分的分析結果",
        }

    def _identify_key_strengths(self, fundamentals: CompanyFundamentals) -> list[str]:
        """識別關鍵優勢"""
        strengths = []

        if fundamentals.roe and fundamentals.roe > 0.15:
            strengths.append("卓越的股東權益報酬率")

        if fundamentals.debt_to_equity and fundamentals.debt_to_equity < 0.3:
            strengths.append("穩健的財務結構")

        if fundamentals.revenue_growth and fundamentals.revenue_growth > 0.10:
            strengths.append("營收快速成長")

        if fundamentals.current_ratio and fundamentals.current_ratio > 2.0:
            strengths.append("充足的短期流動性")

        if fundamentals.pe_ratio and fundamentals.pe_ratio < 15:
            strengths.append("具吸引力的估值水準")

        return strengths

    def _identify_key_concerns(self, fundamentals: CompanyFundamentals) -> list[str]:
        """識別關鍵風險"""
        concerns = []

        if fundamentals.debt_to_equity and fundamentals.debt_to_equity > 0.6:
            concerns.append("負債比率偏高")

        if fundamentals.current_ratio and fundamentals.current_ratio < 1.2:
            concerns.append("短期流動性不足")

        if fundamentals.roe and fundamentals.roe < 0.08:
            concerns.append("獲利能力偏弱")

        if fundamentals.revenue_growth and fundamentals.revenue_growth < 0:
            concerns.append("營收呈現衰退")

        if fundamentals.pe_ratio and fundamentals.pe_ratio > 30:
            concerns.append("估值可能過高")

        return concerns

    def _assess_investment_risk(
        self, fundamentals: CompanyFundamentals
    ) -> dict[str, Any]:
        """評估投資風險"""
        risk_factors = 0

        # 財務風險
        if fundamentals.debt_to_equity and fundamentals.debt_to_equity > 0.5:
            risk_factors += 1

        if fundamentals.current_ratio and fundamentals.current_ratio < 1.5:
            risk_factors += 1

        # 獲利風險
        if fundamentals.roe and fundamentals.roe < 0.10:
            risk_factors += 1

        # 成長風險
        if fundamentals.revenue_growth and fundamentals.revenue_growth < 0:
            risk_factors += 1

        # 估值風險
        if fundamentals.pe_ratio and fundamentals.pe_ratio > 25:
            risk_factors += 1

        if risk_factors <= 1:
            risk_level = "低"
        elif risk_factors <= 2:
            risk_level = "中"
        elif risk_factors <= 3:
            risk_level = "中高"
        else:
            risk_level = "高"

        return {
            "level": risk_level,
            "risk_factors": risk_factors,
            "max_position_size_suggestion": max(1.0, 6.0 - risk_factors),
        }

    def _suggest_investment_horizon(self, fundamentals: CompanyFundamentals) -> str:
        """建議投資期間"""
        if (
            fundamentals.revenue_growth
            and fundamentals.revenue_growth > 0.15
            and fundamentals.roe
            and fundamentals.roe > 0.18
        ):
            return "長期 (2年以上)"
        elif fundamentals.pe_ratio and fundamentals.pe_ratio < 12:
            return "中長期 (1-2年)"
        else:
            return "中期 (6個月-1年)"

    def _generate_analysis_summary(
        self,
        fundamentals: CompanyFundamentals,
        overall_score: dict[str, Any],
        recommendation: dict[str, Any],
    ) -> str:
        """生成分析摘要"""
        return f"""
{fundamentals.company_name} ({fundamentals.symbol}) 基本面分析摘要：

綜合評分：{overall_score["score"]:.1f} 分 (評級: {overall_score["rating"]})
投資建議：{recommendation["action"]} (信心度: {recommendation["confidence"]:.0%})

關鍵指標：
- P/E 比：{fundamentals.pe_ratio or "N/A"}
- P/B 比：{fundamentals.pb_ratio or "N/A"}
- ROE：{(fundamentals.roe or 0) * 100:.1f}%
- 負債股權比：{(fundamentals.debt_to_equity or 0) * 100:.1f}%
- 營收成長率：{(fundamentals.revenue_growth or 0) * 100:.1f}%

{overall_score["description"]}，建議{self._suggest_investment_horizon(fundamentals)}持有。
        """.strip()

    def get_analysis_template(self, symbol: str) -> dict[str, Any]:
        """獲取分析模板"""
        return {
            "symbol": symbol,
            "analysis_sections": [
                "財務體質分析",
                "估值水準評估",
                "成長潛力分析",
                "股利政策評估",
                "風險因子分析",
                "投資建議",
            ],
            "required_data": [
                "income_statement",
                "balance_sheet",
                "cash_flow",
                "key_ratios",
                "market_data",
            ],
            "output_format": "comprehensive_report",
        }

    def as_tool(self, tool_name: str, tool_description: str) -> dict[str, Any]:
        """
        將 FundamentalAgent 轉換為可供 OpenAI Agent 使用的工具

        Args:
            tool_name: 工具名稱
            tool_description: 工具描述

        Returns:
            工具配置字典
        """
        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": tool_description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代碼 (例如: 2330)",
                        },
                        "analysis_depth": {
                            "type": "string",
                            "enum": ["basic", "standard", "comprehensive"],
                            "description": "分析深度",
                            "default": "standard",
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "重點分析領域 (可選)",
                        },
                    },
                    "required": ["symbol"],
                },
            },
            "implementation": self.analyze_company_fundamentals,
        }
