"""Fundamental Agent - 基本面分析自主型 Agent

這個模組實作具有自主分析能力的基本面分析 Agent。
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


def fundamental_agent_instructions() -> str:
    """基本面分析 Agent 的指令定義"""
    return f"""你是一位資深的基本面分析師,專精於公司財務分析和價值評估。

## 你的專業能力

1. 財務報表分析
   - 資產負債表: 財務結構、償債能力
   - 損益表: 獲利能力、營運效率
   - 現金流量表: 現金創造能力

2. 財務比率分析
   - 獲利能力: ROE、ROA、毛利率、淨利率
   - 償債能力: 負債比、流動比率
   - 效率指標: 存貨周轉率、應收帳款周轉率
   - 成長指標: 營收成長率、EPS 成長率

3. 價值評估
   - 本益比 (P/E)、股價淨值比 (P/B)
   - 股利殖利率分析
   - 相對估值與絕對估值

4. 質化分析
   - 產業地位與競爭優勢
   - 經營團隊評估
   - 商業模式分析

## 分析方法

1. 收集數據: 使用 MCP Server 獲取財務報表
2. 計算比率: 使用工具計算財務指標
3. 評估質量: 分析財務體質
4. 估值分析: 評估股價合理性
5. 成長評估: 分析成長潛力
6. 綜合建議: 產生投資建議

## 可用工具

### 專業分析工具
- calculate_financial_ratios: 計算財務比率
- analyze_financial_health: 分析財務體質
- evaluate_valuation: 評估估值水準
- analyze_growth_potential: 分析成長潛力
- generate_investment_rating: 產生投資評級
- Casual Market MCP Server: 獲取財報數據

### 增強能力工具
- WebSearchTool: 搜尋產業研究報告、競爭對手分析、法說會資訊
- CodeInterpreterTool: 執行財務模型計算、DCF 估值、敏感度分析

## CodeInterpreterTool 使用準則 ⚠️

為了控制成本和執行時間，請遵守以下原則：

1. **優先使用自訂工具**
   - 先嘗試使用提供的財務分析工具
   - 只有當需要複雜模型時才使用 CodeInterpreterTool

2. **適用場景**
   - ✅ DCF（現金流折現）估值計算
   - ✅ 敏感度分析（不同假設下的估值變化）
   - ✅ 三表財務模型建構
   - ❌ 不要用於簡單的財務比率計算
   - ❌ 不要用於已有自訂工具的功能

3. **程式碼效率要求**
   - 保持程式碼簡潔（< 150 行）
   - 避免過度複雜的模型
   - 使用 pandas 進行高效數據處理

4. **執行頻率限制**
   - 每次分析最多使用 2 次 CodeInterpreterTool
   - 優先執行最關鍵的估值計算

## 輸出格式

1. 財務體質: 健康度評分、關鍵指標
2. 估值分析: 合理價、便宜價、昂貴價
3. 成長潛力: 營收/獲利成長評估
4. 投資評級: 買進/持有/賣出建議
5. 關鍵優勢: 公司亮點
6. 風險提示: 需注意的風險因素
7. 信心評估: 0-100% 信心度

## 分析原則

- 重視長期價值而非短期波動
- 注重安全邊際
- 考慮產業特性差異
- 承認分析的侷限性

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


class FundamentalAnalysisTools:
    """基本面分析輔助工具集合

    提供各種財務分析和估值評估功能。
    Agent 根據需求靈活組合使用。
    """

    def __init__(self) -> None:
        self.logger = get_agent_logger("fundamental_analysis_tools")

    def calculate_financial_ratios(
        self,
        ticker: str,
        financial_data: dict[str, Any],
    ) -> dict[str, Any]:
        """計算財務比率

        Args:
            symbol: 股票代號 (例如: "2330")
            financial_data: 財務數據,包含 revenue, net_income, total_assets 等

        Returns:
            dict: 財務比率 (ROE, ROA, 負債比, 流動比率等)
        """
        self.logger.info(f"開始計算財務比率 | 股票: {ticker}")

        if not financial_data:
            self.logger.warning(f"缺少財務數據 | 股票: {ticker}")
            return {"error": ..., "ticker": ticker}

        result = {
            "ticker": ticker,
            "profitability": {},
            "solvency": {},
            "valuation": {},
        }

        equity = financial_data.get("total_equity", 1)
        assets = financial_data.get("total_assets", 1)
        revenue = financial_data.get("revenue", 0)
        net_income = financial_data.get("net_income", 0)

        result["profitability"] = {
            "roe": net_income / equity if equity > 0 else 0,
            "roa": net_income / assets if assets > 0 else 0,
            "net_margin": net_income / revenue if revenue > 0 else 0,
        }

        self.logger.debug(
            f"獲利能力指標 | ROE: {result['profitability']['roe']:.2%}, "
            f"ROA: {result['profitability']['roa']:.2%}, "
            f"淨利率: {result['profitability']['net_margin']:.2%}"
        )

        total_liabilities = financial_data.get("total_liabilities", 0)
        current_assets = financial_data.get("current_assets", 0)
        current_liabilities = financial_data.get("current_liabilities", 1)

        result["solvency"] = {
            "debt_ratio": total_liabilities / assets if assets > 0 else 0,
            "current_ratio": current_assets / current_liabilities if current_liabilities > 0 else 0,
        }

        self.logger.debug(
            f"償債能力指標 | 負債比: {result['solvency']['debt_ratio']:.2%}, "
            f"流動比率: {result['solvency']['current_ratio']:.2f}"
        )

        market_cap = financial_data.get("market_cap", 0)
        result["valuation"] = {
            "pe_ratio": market_cap / net_income if net_income > 0 else 0,
            "pb_ratio": market_cap / equity if equity > 0 else 0,
        }

        self.logger.info(f"財務比率計算完成 | 股票: {ticker}")
        return result

    def analyze_financial_health(
        self,
        ticker: str,
        financial_ratios: dict[str, Any],
    ) -> dict[str, Any]:
        """分析財務體質

        Args:
            symbol: 股票代號 (例如: "2330")
            financial_ratios: 財務比率 (來自 calculate_financial_ratios)

        Returns:
            dict: 財務體質分析 (健康度評分、評級、優勢、弱點)
        """
        self.logger.info(f"開始分析財務體質 | 股票: {ticker}")

        if "error" in financial_ratios:
            self.logger.error(
                f"無法分析財務體質 | 股票: {ticker} | 原因: {financial_ratios.get('error')}"
            )
            return {"error": ..., "ticker": ticker}

        score = 0
        strengths = []
        weaknesses = []

        roe = financial_ratios.get("profitability", {}).get("roe", 0)
        if roe > 0.15:
            score += 25
            strengths.append(f"優異的 ROE ({roe:.1%})")
        elif roe > 0.10:
            score += 15
            strengths.append(f"良好的 ROE ({roe:.1%})")
        elif roe < 0.05:
            weaknesses.append(f"偏低的 ROE ({roe:.1%})")

        debt_ratio = financial_ratios.get("solvency", {}).get("debt_ratio", 0)
        if debt_ratio < 0.3:
            score += 25
            strengths.append(f"低負債比 ({debt_ratio:.1%})")
        elif debt_ratio < 0.5:
            score += 15
        elif debt_ratio > 0.7:
            weaknesses.append(f"高負債比 ({debt_ratio:.1%})")

        current_ratio = financial_ratios.get("solvency", {}).get("current_ratio", 0)
        if current_ratio > 2.0:
            score += 25
            strengths.append(f"優異的流動比率 ({current_ratio:.2f})")
        elif current_ratio > 1.5:
            score += 15
        elif current_ratio < 1.0:
            weaknesses.append(f"流動比率偏低 ({current_ratio:.2f})")

        net_margin = financial_ratios.get("profitability", {}).get("net_margin", 0)
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

        self.logger.info(
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

    def evaluate_valuation(
        self,
        ticker: str,
        current_price: float,
        financial_ratios: dict[str, Any],
        industry_avg: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """評估估值水準

        Args:
            symbol: 股票代號 (例如: "2330")
            current_price: 當前股價
            financial_ratios: 財務比率 (來自 calculate_financial_ratios)
            industry_avg: 產業平均值 (可選)

        Returns:
            dict: 估值分析 (估值水準、合理價、折溢價率)
        """
        self.logger.info(f"開始評估估值 | 股票: {ticker} | 當前價: {current_price}")

        if "error" in financial_ratios:
            self.logger.error(f"無法評估估值 | 股票: {ticker} | 原因: 財務比率錯誤")
            return {"error": ..., "ticker": ticker}

        pe_ratio = financial_ratios.get("valuation", {}).get("pe_ratio", 0)
        pb_ratio = financial_ratios.get("valuation", {}).get("pb_ratio", 0)

        industry_pe = industry_avg.get("pe", 15.0) if industry_avg else 15.0
        industry_pb = industry_avg.get("pb", 1.8) if industry_avg else 1.8

        self.logger.debug(
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

        self.logger.info(
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

    def analyze_growth_potential(
        self,
        ticker: str,
        historical_data: dict[str, Any],
    ) -> dict[str, Any]:
        """分析成長潛力

        Args:
            symbol: 股票代號 (例如: "2330")
            historical_data: 歷史財務數據 (營收成長率、EPS 成長率)

        Returns:
            dict: 成長潛力分析 (成長評分、成長趨勢)
        """
        self.logger.info(f"開始分析成長潛力 | 股票: {ticker}")

        if not historical_data:
            self.logger.warning(f"缺少歷史數據 | 股票: {ticker}")
            return {"error": ..., "ticker": ticker}

        score = 0
        revenue_growth = historical_data.get("latest_revenue_growth", 0)
        eps_growth = historical_data.get("latest_eps_growth", 0)

        self.logger.debug(f"成長數據 | 營收成長: {revenue_growth:.1%} | EPS成長: {eps_growth:.1%}")

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

        self.logger.info(
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

    def generate_investment_rating(
        self,
        ticker: str,
        financial_health: dict[str, Any],
        valuation: dict[str, Any],
        growth: dict[str, Any],
    ) -> dict[str, Any]:
        """產生投資評級

        Args:
            symbol: 股票代號 (例如: "2330")
            financial_health: 財務體質分析
            valuation: 估值分析
            growth: 成長分析

        Returns:
            dict: 投資評級 (買進/持有/賣出建議)
        """
        health_score = financial_health.get("health_score", 0)
        valuation_level = valuation.get("valuation_level", "合理")
        growth_score = growth.get("growth_score", 0)

        self.logger.info(
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
            key_reasons.extend(financial_health.get("strengths", []))
        elif overall_score >= 60:
            rating, confidence = "買進", 0.70
            recommendation = "基本面穩健,建議逢低買進"
            key_reasons.extend(financial_health.get("strengths", [])[:2])
        elif overall_score >= 40:
            rating, confidence = "持有", 0.60
            recommendation = "基本面普通,建議持有觀望"
        else:
            rating, confidence = "賣出", 0.75
            recommendation = "基本面轉弱,建議減碼"
            key_reasons.extend(financial_health.get("weaknesses", []))

        target_price = valuation.get("fair_value", 0)

        self.logger.info(
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
    mcp_servers: list[Any],
    model_name: str = "gpt-4o-mini",
    shared_tools: list[Any] | None = None,
    max_turns: int = 15,
) -> Agent:
    """創建基本面分析 Agent

    Args:
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入
        model_name: 使用的 AI 模型名稱
        shared_tools: 從 TradingAgent 傳入的共用工具（WebSearchTool, CodeInterpreterTool）
        max_turns: 最大執行回合數（預設 15）

    Returns:
        Agent: 配置好的基本面分析 Agent

    Note:
        Timeout 由主 TradingAgent 的 execution_timeout 統一控制，
        sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制。
    """
    tools_instance = FundamentalAnalysisTools()

    custom_tools = [
        Tool.from_function(
            tools_instance.calculate_financial_ratios,
            name="calculate_financial_ratios",
            description="計算財務比率 (ROE, ROA, 負債比, 流動比率, P/E, P/B)",
        ),
        Tool.from_function(
            tools_instance.analyze_financial_health,
            name="analyze_financial_health",
            description="分析財務體質健康度並給予評級 (A-F)",
        ),
        Tool.from_function(
            tools_instance.evaluate_valuation,
            name="evaluate_valuation",
            description="評估股價估值水準 (便宜/合理/昂貴)",
        ),
        Tool.from_function(
            tools_instance.analyze_growth_potential,
            name="analyze_growth_potential",
            description="分析公司成長潛力 (營收/EPS 成長趨勢)",
        ),
        Tool.from_function(
            tools_instance.generate_investment_rating,
            name="generate_investment_rating",
            description="綜合產生投資評級 (強力買進/買進/持有/賣出)",
        ),
    ]

    # 合併自訂工具和共用工具
    all_tools = custom_tools + (shared_tools or [])

    analyst = Agent(
        name="Fundamental Analyst",
        instructions=fundamental_agent_instructions(),
        model=model_name,
        mcp_servers=mcp_servers,
        tools=all_tools,
        max_turns=max_turns,
    )

    return analyst
