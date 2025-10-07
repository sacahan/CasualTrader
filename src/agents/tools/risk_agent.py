"""
風險評估工具
專門化的投資風險分析和風險管理工具
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RiskMetrics(BaseModel):
    """風險度量指標"""

    symbol: str
    portfolio_weight: float
    position_size: float
    current_value: float

    # 波動性風險
    daily_volatility: float | None = None
    annual_volatility: float | None = None
    beta: float | None = None

    # 下檔風險
    var_95: float | None = None  # 95% VaR
    var_99: float | None = None  # 99% VaR
    max_drawdown: float | None = None
    downside_deviation: float | None = None

    # 流動性風險
    avg_daily_volume: float | None = None
    bid_ask_spread: float | None = None
    market_impact_cost: float | None = None

    # 信用風險
    debt_to_equity: float | None = None
    credit_rating: str | None = None
    default_probability: float | None = None

    analysis_timestamp: datetime


class PortfolioRisk(BaseModel):
    """投資組合風險"""

    total_value: float
    cash_position: float
    number_of_positions: int

    # 集中度風險
    concentration_risk: dict[str, Any]
    sector_exposure: dict[str, float]
    single_stock_max_weight: float

    # 整體風險度量
    portfolio_volatility: float | None = None
    portfolio_beta: float | None = None
    portfolio_var: float | None = None
    sharpe_ratio: float | None = None

    # 相關性風險
    correlation_matrix: dict[str, dict[str, float]] | None = None
    diversification_ratio: float | None = None

    analysis_timestamp: datetime


class RiskAssessmentResult(BaseModel):
    """風險評估結果"""

    assessment_type: str
    overall_risk_level: str  # "低", "中低", "中", "中高", "高"
    risk_score: float  # 0-100
    confidence_level: float

    individual_risks: list[RiskMetrics]
    portfolio_risk: PortfolioRisk | None = None

    key_risk_factors: list[str]
    risk_warnings: list[str]
    risk_recommendations: list[str]

    position_sizing_suggestions: dict[str, float]
    hedging_strategies: list[str]
    stop_loss_levels: dict[str, float]

    risk_budget_allocation: dict[str, float]
    stress_test_results: dict[str, Any]

    summary: str
    analysis_timestamp: datetime


class RiskAgent:
    """
    風險評估工具 - 提供全面的投資風險分析和管理建議
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("risk_agent")

    async def assess_investment_risk(
        self,
        positions: list[dict[str, Any]],
        portfolio_value: float,
        risk_tolerance: str = "medium",
        analysis_depth: str = "comprehensive",
    ) -> RiskAssessmentResult:
        """
        投資風險評估

        Args:
            positions: 投資部位列表
            portfolio_value: 投資組合總值
            risk_tolerance: 風險承受度 ("low", "medium", "high")
            analysis_depth: 分析深度

        Returns:
            風險評估結果
        """
        try:
            # 計算個別股票風險
            individual_risks = []
            for position in positions:
                risk_metrics = await self._calculate_individual_risk(position)
                individual_risks.append(risk_metrics)

            # 計算投資組合風險
            portfolio_risk = await self._calculate_portfolio_risk(
                positions, portfolio_value
            )

            # 綜合風險評估
            overall_assessment = self._assess_overall_risk(
                individual_risks, portfolio_risk, risk_tolerance
            )

            # 生成風險管理建議
            recommendations = self._generate_risk_recommendations(
                individual_risks, portfolio_risk, overall_assessment
            )

            # 壓力測試
            stress_results = await self._perform_stress_testing(
                positions, portfolio_value
            )

            result = RiskAssessmentResult(
                assessment_type="comprehensive_risk_analysis",
                overall_risk_level=overall_assessment["level"],
                risk_score=overall_assessment["score"],
                confidence_level=overall_assessment["confidence"],
                individual_risks=individual_risks,
                portfolio_risk=portfolio_risk,
                key_risk_factors=overall_assessment["key_factors"],
                risk_warnings=overall_assessment["warnings"],
                risk_recommendations=recommendations["actions"],
                position_sizing_suggestions=recommendations["position_sizing"],
                hedging_strategies=recommendations["hedging"],
                stop_loss_levels=recommendations["stop_losses"],
                risk_budget_allocation=recommendations["risk_budget"],
                stress_test_results=stress_results,
                summary=self._generate_risk_summary(
                    overall_assessment, portfolio_risk, stress_results
                ),
                analysis_timestamp=datetime.now(),
            )

            self.logger.info(
                f"Risk assessment completed for {len(positions)} positions"
            )
            return result

        except Exception as e:
            self.logger.error(f"Risk assessment failed: {e}")
            raise

    async def _calculate_individual_risk(self, position: dict[str, Any]) -> RiskMetrics:
        """計算個別股票風險指標"""
        symbol = position["symbol"]
        quantity = position.get("quantity", 0)
        current_price = position.get("current_price", 0)
        portfolio_weight = position.get("weight", 0)

        # 獲取歷史數據進行風險計算
        risk_data = await self._fetch_risk_data(symbol)

        return RiskMetrics(
            symbol=symbol,
            portfolio_weight=portfolio_weight,
            position_size=quantity,
            current_value=quantity * current_price,
            daily_volatility=risk_data.get("daily_vol", 0.02),
            annual_volatility=risk_data.get("annual_vol", 0.25),
            beta=risk_data.get("beta", 1.0),
            var_95=risk_data.get("var_95", -0.03),
            var_99=risk_data.get("var_99", -0.05),
            max_drawdown=risk_data.get("max_drawdown", -0.15),
            downside_deviation=risk_data.get("downside_dev", 0.018),
            avg_daily_volume=risk_data.get("avg_volume", 1000000),
            bid_ask_spread=risk_data.get("spread", 0.001),
            market_impact_cost=risk_data.get("impact_cost", 0.002),
            debt_to_equity=risk_data.get("debt_equity", 0.3),
            credit_rating=risk_data.get("rating", "BBB"),
            default_probability=risk_data.get("default_prob", 0.01),
            analysis_timestamp=datetime.now(),
        )

    async def _fetch_risk_data(self, symbol: str) -> dict[str, Any]:
        """獲取風險計算所需數據"""
        # 這裡將整合實際的歷史數據和財務數據
        # 目前返回模擬數據

        return {
            "daily_vol": 0.025,
            "annual_vol": 0.30,
            "beta": 1.2,
            "var_95": -0.035,
            "var_99": -0.055,
            "max_drawdown": -0.18,
            "downside_dev": 0.020,
            "avg_volume": 1500000,
            "spread": 0.0015,
            "impact_cost": 0.0025,
            "debt_equity": 0.35,
            "rating": "BBB+",
            "default_prob": 0.008,
        }

    async def _calculate_portfolio_risk(
        self, positions: list[dict[str, Any]], total_value: float
    ) -> PortfolioRisk:
        """計算投資組合整體風險"""

        # 計算集中度風險
        concentration = self._calculate_concentration_risk(positions)

        # 計算產業曝險
        sector_exposure = self._calculate_sector_exposure(positions)

        # 計算最大單一股票權重
        max_weight = max([pos.get("weight", 0) for pos in positions], default=0)

        # 計算投資組合統計量
        portfolio_stats = self._calculate_portfolio_statistics(positions)

        # 計算相關性矩陣
        correlation_matrix = await self._calculate_correlation_matrix(positions)

        return PortfolioRisk(
            total_value=total_value,
            cash_position=total_value * 0.1,  # 假設 10% 現金
            number_of_positions=len(positions),
            concentration_risk=concentration,
            sector_exposure=sector_exposure,
            single_stock_max_weight=max_weight,
            portfolio_volatility=portfolio_stats.get("volatility", 0.20),
            portfolio_beta=portfolio_stats.get("beta", 1.0),
            portfolio_var=portfolio_stats.get("var", -0.025),
            sharpe_ratio=portfolio_stats.get("sharpe", 0.8),
            correlation_matrix=correlation_matrix,
            diversification_ratio=portfolio_stats.get("diversification", 0.7),
            analysis_timestamp=datetime.now(),
        )

    def _calculate_concentration_risk(
        self, positions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """計算集中度風險"""
        weights = [pos.get("weight", 0) for pos in positions]

        # HHI (Herfindahl-Hirschman Index)
        hhi = sum(w**2 for w in weights)

        # 有效股票數量
        effective_stocks = 1 / hhi if hhi > 0 else 0

        # 前五大持股集中度
        top5_concentration = sum(sorted(weights, reverse=True)[:5])

        if hhi < 0.1:
            concentration_level = "低"
        elif hhi < 0.18:
            concentration_level = "中"
        elif hhi < 0.25:
            concentration_level = "中高"
        else:
            concentration_level = "高"

        return {
            "hhi_index": hhi,
            "effective_number_of_stocks": effective_stocks,
            "top5_concentration": top5_concentration,
            "concentration_level": concentration_level,
            "diversification_score": max(0, 1 - hhi),
        }

    def _calculate_sector_exposure(
        self, positions: list[dict[str, Any]]
    ) -> dict[str, float]:
        """計算產業曝險分布"""
        # 模擬產業分類（實際實作時會基於真實產業數據）
        sector_mapping = {
            "2330": "半導體",
            "2317": "電腦周邊",
            "2454": "光電",
            "1301": "塑化",
            "2882": "金融",
        }

        sector_weights = {}
        for position in positions:
            symbol = position["symbol"]
            weight = position.get("weight", 0)
            sector = sector_mapping.get(symbol, "其他")

            if sector in sector_weights:
                sector_weights[sector] += weight
            else:
                sector_weights[sector] = weight

        return sector_weights

    def _calculate_portfolio_statistics(
        self, positions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """計算投資組合統計量"""
        # 模擬投資組合統計計算
        weights = [pos.get("weight", 0) for pos in positions]

        # 加權平均 Beta
        weighted_beta = sum(
            pos.get("beta", 1.0) * pos.get("weight", 0) for pos in positions
        )

        # 投資組合波動度（簡化計算）
        portfolio_vol = 0.20  # 實際計算需要相關性矩陣

        return {
            "volatility": portfolio_vol,
            "beta": weighted_beta,
            "var": -portfolio_vol * 1.65,  # 95% VaR 近似
            "sharpe": 0.8,  # 假設夏普比率
            "diversification": 0.75,  # 分散化比率
        }

    async def _calculate_correlation_matrix(
        self, positions: list[dict[str, Any]]
    ) -> dict[str, dict[str, float]]:
        """計算相關性矩陣"""
        symbols = [pos["symbol"] for pos in positions]
        correlation_matrix = {}

        # 模擬相關性計算（實際實作時會基於歷史價格數據）
        for i, symbol1 in enumerate(symbols):
            correlation_matrix[symbol1] = {}
            for j, symbol2 in enumerate(symbols):
                if i == j:
                    correlation_matrix[symbol1][symbol2] = 1.0
                else:
                    # 模擬相關系數
                    correlation_matrix[symbol1][symbol2] = 0.3 + (i + j) * 0.1 % 0.7

        return correlation_matrix

    def _assess_overall_risk(
        self,
        individual_risks: list[RiskMetrics],
        portfolio_risk: PortfolioRisk,
        risk_tolerance: str,
    ) -> dict[str, Any]:
        """綜合風險評估"""

        risk_factors = []
        warnings = []
        total_risk_score = 0

        # 個別股票風險評估
        high_risk_stocks = []
        for risk in individual_risks:
            if risk.annual_volatility and risk.annual_volatility > 0.35:
                high_risk_stocks.append(risk.symbol)
                total_risk_score += 20

            if risk.beta and risk.beta > 1.5:
                risk_factors.append(
                    f"{risk.symbol} 系統風險較高 (Beta: {risk.beta:.2f})"
                )
                total_risk_score += 10

            if risk.max_drawdown and risk.max_drawdown < -0.25:
                warnings.append(f"{risk.symbol} 歷史最大回撤超過 25%")
                total_risk_score += 15

        # 投資組合層級風險
        if portfolio_risk.single_stock_max_weight > 0.15:
            risk_factors.append("單一股票集中度過高")
            total_risk_score += 25

        if portfolio_risk.concentration_risk["hhi_index"] > 0.2:
            risk_factors.append("投資組合集中度偏高")
            total_risk_score += 20

        # 產業集中度檢查
        max_sector_weight = max(portfolio_risk.sector_exposure.values(), default=0)
        if max_sector_weight > 0.4:
            risk_factors.append("產業集中度過高")
            total_risk_score += 20

        # 流動性風險
        low_liquidity_stocks = [
            risk.symbol
            for risk in individual_risks
            if risk.avg_daily_volume and risk.avg_daily_volume < 500000
        ]
        if low_liquidity_stocks:
            warnings.append(f"流動性不足標的: {', '.join(low_liquidity_stocks)}")
            total_risk_score += len(low_liquidity_stocks) * 10

        # 根據風險承受度調整評分
        tolerance_multiplier = {"low": 0.7, "medium": 1.0, "high": 1.3}.get(
            risk_tolerance, 1.0
        )
        adjusted_score = total_risk_score * tolerance_multiplier

        # 風險等級判定
        if adjusted_score >= 80:
            risk_level = "高"
            confidence = 0.9
        elif adjusted_score >= 60:
            risk_level = "中高"
            confidence = 0.85
        elif adjusted_score >= 40:
            risk_level = "中"
            confidence = 0.8
        elif adjusted_score >= 20:
            risk_level = "中低"
            confidence = 0.75
        else:
            risk_level = "低"
            confidence = 0.7

        return {
            "level": risk_level,
            "score": min(100, adjusted_score),
            "confidence": confidence,
            "key_factors": risk_factors[:5],  # 最多 5 個主要風險因子
            "warnings": warnings,
            "high_risk_stocks": high_risk_stocks,
        }

    def _generate_risk_recommendations(
        self,
        individual_risks: list[RiskMetrics],
        portfolio_risk: PortfolioRisk,
        assessment: dict[str, Any],
    ) -> dict[str, Any]:
        """生成風險管理建議"""

        recommendations = []
        position_sizing = {}
        stop_losses = {}
        hedging_strategies = []
        risk_budget = {}

        # 部位大小建議
        for risk in individual_risks:
            if risk.annual_volatility and risk.annual_volatility > 0.30:
                suggested_weight = min(0.05, risk.portfolio_weight * 0.7)
                position_sizing[risk.symbol] = suggested_weight
                recommendations.append(
                    f"建議降低 {risk.symbol} 部位至 {suggested_weight:.1%}"
                )

            # 停損水準建議
            if risk.var_95:
                stop_loss = abs(risk.var_95) * 2  # VaR 的 2 倍作為停損
                stop_losses[risk.symbol] = stop_loss
            else:
                stop_losses[risk.symbol] = 0.08  # 預設 8% 停損

        # 投資組合層級建議
        if portfolio_risk.concentration_risk["hhi_index"] > 0.18:
            recommendations.append("建議增加投資標的數量以降低集中度風險")

        if portfolio_risk.single_stock_max_weight > 0.12:
            recommendations.append("建議單一股票權重不超過 12%")

        # 產業分散化建議
        for sector, weight in portfolio_risk.sector_exposure.items():
            if weight > 0.35:
                recommendations.append(f"建議降低{sector}產業曝險 (目前 {weight:.1%})")

        # 避險策略建議
        if assessment["score"] > 60:
            hedging_strategies.extend(
                [
                    "考慮購買台指期貨做空避險",
                    "增加現金部位至 15-20%",
                    "考慮配置防禦性股票",
                ]
            )

        # 風險預算分配
        total_risk_budget = 100
        high_risk_allocation = min(30, max(10, 40 - assessment["score"] * 0.3))
        medium_risk_allocation = 60
        low_risk_allocation = (
            total_risk_budget - high_risk_allocation - medium_risk_allocation
        )

        risk_budget = {
            "高風險標的": high_risk_allocation,
            "中風險標的": medium_risk_allocation,
            "低風險標的": low_risk_allocation,
        }

        return {
            "actions": recommendations,
            "position_sizing": position_sizing,
            "stop_losses": stop_losses,
            "hedging": hedging_strategies,
            "risk_budget": risk_budget,
        }

    async def _perform_stress_testing(
        self, positions: list[dict[str, Any]], portfolio_value: float
    ) -> dict[str, Any]:
        """執行壓力測試"""

        scenarios = {
            "市場崩盤": {"market_drop": -0.20, "volatility_spike": 2.0},
            "金融風暴": {"market_drop": -0.30, "correlation_increase": 0.8},
            "利率急升": {"rate_rise": 0.03, "growth_stocks_impact": -0.25},
            "科技股泡沫": {"tech_drop": -0.40, "other_sectors": -0.10},
            "疫情衝擊": {"travel_drop": -0.50, "tech_gain": 0.15, "overall": -0.15},
        }

        stress_results = {}

        for scenario_name, scenario_params in scenarios.items():
            portfolio_impact = self._calculate_scenario_impact(
                positions, scenario_params
            )

            stress_results[scenario_name] = {
                "portfolio_loss": portfolio_impact["total_loss"],
                "worst_stock": portfolio_impact["worst_performer"],
                "recovery_time_estimate": portfolio_impact["recovery_days"],
                "required_actions": portfolio_impact["recommended_actions"],
            }

        return stress_results

    def _calculate_scenario_impact(
        self, positions: list[dict[str, Any]], scenario: dict[str, Any]
    ) -> dict[str, Any]:
        """計算情境衝擊"""

        total_loss = 0
        worst_loss = 0
        worst_stock = ""

        # 模擬情境計算
        market_impact = scenario.get("market_drop", 0)

        for position in positions:
            symbol = position["symbol"]
            weight = position.get("weight", 0)

            # 基礎市場衝擊
            stock_impact = market_impact

            # 特定產業衝擊
            if "tech_drop" in scenario and symbol in ["2330", "2317", "2454"]:
                stock_impact = scenario["tech_drop"]

            position_loss = weight * stock_impact
            total_loss += position_loss

            if position_loss < worst_loss:
                worst_loss = position_loss
                worst_stock = symbol

        # 恢復時間估算（天數）
        recovery_days = int(abs(total_loss) * 365 * 2)  # 假設需要損失的2倍時間恢復

        # 建議行動
        recommended_actions = []
        if abs(total_loss) > 0.15:
            recommended_actions.append("立即檢討投資組合配置")
            recommended_actions.append("考慮增加避險部位")
        if abs(total_loss) > 0.25:
            recommended_actions.append("緊急風險管理會議")

        return {
            "total_loss": total_loss,
            "worst_performer": worst_stock,
            "recovery_days": recovery_days,
            "recommended_actions": recommended_actions,
        }

    def _generate_risk_summary(
        self,
        assessment: dict[str, Any],
        portfolio_risk: PortfolioRisk,
        stress_results: dict[str, Any],
    ) -> str:
        """生成風險評估摘要"""

        worst_scenario = max(
            stress_results.items(),
            key=lambda x: abs(x[1]["portfolio_loss"]),
            default=("無", {"portfolio_loss": 0}),
        )

        return f"""
投資組合風險評估摘要：

整體風險等級：{assessment['level']} (評分: {assessment['score']:.0f}/100)
信心度：{assessment['confidence']:.0%}

投資組合特徵：
- 持股檔數：{portfolio_risk.number_of_positions}
- 最大單股權重：{portfolio_risk.single_stock_max_weight:.1%}
- 投資組合 Beta：{portfolio_risk.portfolio_beta or 'N/A'}
- 集中度指數：{portfolio_risk.concentration_risk['hhi_index']:.3f}

壓力測試結果：
- 最壞情境：{worst_scenario[0]}
- 預期損失：{worst_scenario[1]['portfolio_loss']:.1%}

主要風險因子：
{chr(10).join(f'• {factor}' for factor in assessment['key_factors'][:3])}

建議採取適當的風險控制措施，定期檢討投資組合配置。
        """.strip()

    def get_risk_monitoring_dashboard(self) -> dict[str, Any]:
        """風險監控儀表板配置"""
        return {
            "key_metrics": [
                "投資組合 VaR",
                "最大回撤",
                "集中度指數",
                "Beta 係數",
                "夏普比率",
            ],
            "alert_thresholds": {
                "單股權重": 0.15,
                "產業集中度": 0.35,
                "日 VaR": 0.03,
                "最大回撤": 0.12,
            },
            "monitoring_frequency": "即時",
            "reporting_schedule": "每日",
        }
