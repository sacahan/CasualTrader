"""Risk Agent - 風險評估自主型 Agent

這個模組實作具有自主分析能力的風險評估 Agent。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# Logger
from ..utils.logger import get_agent_logger

# Agent SDK
try:
    from agents import Agent, CodeInterpreterTool, WebSearchTool, function_tool
except ImportError:
    Agent = Any
    function_tool = Any
    WebSearchTool = Any
    CodeInterpreterTool = Any


def risk_agent_instructions() -> str:
    """風險評估 Agent 的指令定義"""
    return f"""你是一位專業的風險管理專家,專精於投資組合風險分析和風險控制。

## 你的專業能力

1. 風險度量
   - 波動性風險: 標準差、Beta 係數
   - 下檔風險: VaR、最大回撤
   - 流動性風險: 成交量、買賣價差

2. 投資組合風險
   - 集中度風險: HHI 指數
   - 產業曝險分析
   - 相關性分析

3. 風險管理建議
   - 部位大小建議
   - 停損點設置
   - 避險策略
   - 風險預算分配

## 分析方法

1. 收集數據: 使用 MCP Server 獲取價格和部位數據
2. 計算風險: 使用工具計算風險指標
3. 評估集中度: 分析投資組合集中度
4. 壓力測試: 模擬極端情況
5. 給出建議: 產生風險管理建議

## 可用工具

### 專業分析工具
- calculate_position_risk: 計算個別部位風險
- analyze_portfolio_concentration: 分析投資組合集中度
- calculate_portfolio_risk: 計算整體投資組合風險
- perform_stress_test: 執行壓力測試
- generate_risk_recommendations: 產生風險管理建議
- Casual Market MCP Server: 獲取市場數據

### 增強能力工具
- WebSearchTool: 搜尋風險管理最佳實踐、市場風險事件、監管規範
- CodeInterpreterTool: 執行 VaR 計算、蒙地卡羅模擬、相關性矩陣分析

## CodeInterpreterTool 使用準則 ⚠️

為了控制成本和執行時間，請遵守以下原則：

1. **優先使用自訂工具**
   - 先嘗試使用提供的風險分析工具
   - 只有當需要進階風險模型時才使用 CodeInterpreterTool

2. **適用場景**
   - ✅ VaR（風險值）計算（歷史模擬法、蒙地卡羅法）
   - ✅ 投資組合相關性矩陣分析
   - ✅ 壓力測試情境模擬
   - ❌ 不要用於簡單的風險比率計算
   - ❌ 不要用於已有自訂工具的功能

3. **程式碼效率要求**
   - 保持程式碼簡潔（< 150 行）
   - 蒙地卡羅模擬限制在 10,000 次以內
   - 使用 numpy 進行高效數值計算

4. **執行頻率限制**
   - 每次分析最多使用 2 次 CodeInterpreterTool
   - 優先執行最關鍵的風險計算

## 輸出格式

1. 風險評分: 0-100 分,越高越危險
2. 風險等級: 低/中低/中/中高/高
3. 關鍵風險: 需要注意的主要風險
4. 風險警示: 需要立即處理的風險
5. 管理建議: 具體的風險控制措施
6. 信心評估: 0-100% 信心度

## 分析原則

- 保守評估,寧可高估風險
- 重視尾部風險和極端情況
- 考慮流動性風險
- 提供可執行的建議

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


class RiskAnalysisTools:
    """風險分析輔助工具集合

    提供各種風險評估和管理功能。
    Agent 根據需求靈活組合使用。
    """

    def __init__(self) -> None:
        self.logger = get_agent_logger("risk_analysis_tools")

    def calculate_position_risk(
        self,
        ticker: str,
        position_data: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """計算個別部位風險

        Args:
            symbol: 股票代號 (例如: "2330")
            position_data: 部位數據
            market_data: 市場數據 (可選)

        Returns:
            dict: 部位風險指標
        """
        self.logger.info(f"開始計算部位風險 | 股票: {ticker}")

        quantity = position_data.get("quantity", 0)
        avg_cost = position_data.get("avg_cost", 0)
        current_price = position_data.get("current_price", 0)

        position_value = quantity * current_price
        unrealized_pnl = (current_price - avg_cost) * quantity
        pnl_percent = unrealized_pnl / (quantity * avg_cost) if avg_cost > 0 else 0

        self.logger.debug(
            f"部位基本資訊 | 股票: {ticker} | 數量: {quantity} | "
            f"成本: {avg_cost} | 現價: {current_price} | 未實現損益: {unrealized_pnl:,.0f}"
        )

        volatility = market_data.get("volatility", 0.25) if market_data else 0.25
        beta = market_data.get("beta", 1.0) if market_data else 1.0

        var_95 = position_value * volatility * 1.65
        max_drawdown = position_value * (volatility * 2)
        risk_score = min(100, (volatility * 100 + abs(beta - 1) * 30))

        self.logger.info(
            f"部位風險計算完成 | 股票: {ticker} | 風險評分: {risk_score:.1f} | "
            f"VaR(95%): {var_95:,.0f} | 波動率: {volatility:.2%}"
        )

        return {
            "ticker": ticker,
            "position_value": position_value,
            "unrealized_pnl": unrealized_pnl,
            "pnl_percent": pnl_percent,
            "volatility": volatility,
            "beta": beta,
            "var_95": var_95,
            "max_drawdown": max_drawdown,
            "risk_score": risk_score,
        }

    def analyze_portfolio_concentration(
        self,
        positions: list[dict[str, Any]],
        total_value: float,
    ) -> dict[str, Any]:
        """分析投資組合集中度

        Args:
            positions: 部位列表
            total_value: 投資組合總值

        Returns:
            dict: 集中度分析結果
        """
        self.logger.info(
            f"開始分析投資組合集中度 | 部位數: {len(positions)} | 總值: {total_value:,.0f}"
        )

        if not positions or total_value <= 0:
            self.logger.warning("無效的投資組合數據")
            return {"error": "無效的投資組合數據"}

        weights = []
        sector_weights: dict[str, float] = {}

        for pos in positions:
            value = pos.get("value", 0)
            weight = value / total_value if total_value > 0 else 0
            weights.append(weight)

            sector = pos.get("sector", "其他")
            sector_weights[sector] = sector_weights.get(sector, 0) + weight

        hhi = sum(w**2 for w in weights)
        effective_stocks = 1 / hhi if hhi > 0 else 0
        top5_concentration = sum(sorted(weights, reverse=True)[:5])
        max_weight = max(weights) if weights else 0

        self.logger.debug(
            f"集中度計算 | HHI: {hhi:.4f} | 有效股票數: {effective_stocks:.2f} | "
            f"前5大集中度: {top5_concentration:.2%} | 最大權重: {max_weight:.2%}"
        )

        if hhi < 0.1:
            concentration_level = "低"
            risk_assessment = "投資組合分散良好"
        elif hhi < 0.18:
            concentration_level = "中低"
            risk_assessment = "投資組合適度分散"
        elif hhi < 0.25:
            concentration_level = "中"
            risk_assessment = "投資組合集中度偏高"
        else:
            concentration_level = "高"
            risk_assessment = "投資組合過度集中,風險較高"

        self.logger.info(
            f"集中度分析完成 | 等級: {concentration_level} | 產業分布: {len(sector_weights)} 個產業"
        )

        return {
            "hhi_index": hhi,
            "effective_stocks": effective_stocks,
            "top5_concentration": top5_concentration,
            "max_position_weight": max_weight,
            "sector_concentration": sector_weights,
            "concentration_level": concentration_level,
            "risk_assessment": risk_assessment,
        }

    def calculate_portfolio_risk(
        self,
        position_risks: list[dict[str, Any]],
        concentration: dict[str, Any],
        total_value: float,
    ) -> dict[str, Any]:
        """計算整體投資組合風險

        Args:
            position_risks: 個別部位風險列表
            concentration: 集中度分析
            total_value: 投資組合總值

        Returns:
            dict: 投資組合風險指標
        """
        self.logger.info(
            f"開始計算投資組合整體風險 | 部位數: {len(position_risks)} | 總值: {total_value:,.0f}"
        )

        if not position_risks:
            self.logger.warning("無部位風險數據")
            return {"error": "無部位風險數據"}

        total_volatility = 0.0
        total_beta = 0.0
        total_var = 0.0

        for risk in position_risks:
            weight = risk.get("position_value", 0) / total_value if total_value > 0 else 0
            total_volatility += risk.get("volatility", 0) * weight
            total_beta += risk.get("beta", 0) * weight
            total_var += risk.get("var_95", 0)

        hhi = concentration.get("hhi_index", 0)
        concentration_penalty = hhi * 50

        self.logger.debug(
            f"風險指標計算 | 波動度: {total_volatility:.4f} | Beta: {total_beta:.4f} | "
            f"VaR總和: {total_var:,.0f} | 集中度懲罰: {concentration_penalty:.2f}"
        )

        overall_risk_score = min(
            100,
            (total_volatility * 100 + abs(total_beta - 1) * 20 + concentration_penalty),
        )

        if overall_risk_score >= 80:
            risk_level = "高"
        elif overall_risk_score >= 60:
            risk_level = "中高"
        elif overall_risk_score >= 40:
            risk_level = "中"
        elif overall_risk_score >= 20:
            risk_level = "中低"
        else:
            risk_level = "低"

        self.logger.info(
            f"投資組合風險計算完成 | 風險等級: {risk_level} | 風險分數: {overall_risk_score:.2f} | "
            f"組合VaR: {total_var:,.0f}"
        )

        return {
            "total_value": total_value,
            "portfolio_volatility": total_volatility,
            "portfolio_beta": total_beta,
            "portfolio_var": total_var,
            "overall_risk_score": overall_risk_score,
            "risk_level": risk_level,
        }

    def perform_stress_test(
        self,
        positions: list[dict[str, Any]],
        scenarios: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """執行壓力測試

        Args:
            positions: 部位列表
            scenarios: 壓力情境列表 (可選)

        Returns:
            dict: 壓力測試結果
        """
        self.logger.info(
            f"開始壓力測試 | 部位數: {len(positions)} | 情境數: {len(scenarios) if scenarios else 0}"
        )
        if not scenarios:
            scenarios = [
                {"name": "市場大跌 10%", "market_change": -0.10},
                {"name": "市場暴跌 20%", "market_change": -0.20},
                {"name": "個股腰斬", "stock_change": -0.50},
            ]

        results = []
        total_value = sum(pos.get("value", 0) for pos in positions)

        self.logger.debug(f"壓力測試設定 | 總值: {total_value:,.0f} | 情境數: {len(scenarios)}")

        for scenario in scenarios:
            if "market_change" in scenario:
                impact_percent = scenario["market_change"]
                loss_amount = total_value * abs(impact_percent)
            elif "stock_change" in scenario:
                max_position = max((pos.get("value", 0) for pos in positions), default=0)
                impact_percent = scenario["stock_change"]
                loss_amount = max_position * abs(impact_percent)
            else:
                impact_percent = 0
                loss_amount = 0

            self.logger.debug(
                f"情境測試: {scenario['name']} | 影響: {impact_percent:.1%} | "
                f"損失: {loss_amount:,.0f}"
            )

            results.append(
                {
                    "name": scenario["name"],
                    "impact": impact_percent,
                    "loss_amount": loss_amount,
                    "remaining_value": total_value - loss_amount,
                }
            )

        max_loss = max((r["loss_amount"] for r in results), default=0)
        self.logger.info(f"壓力測試完成 | 情境數: {len(results)} | 最大損失: {max_loss:,.0f}")

        return {"scenarios": results, "total_value": total_value}

    def generate_risk_recommendations(
        self,
        portfolio_risk: dict[str, Any],
        concentration: dict[str, Any],
        position_risks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """產生風險管理建議

        Args:
            portfolio_risk: 投資組合風險
            concentration: 集中度分析
            position_risks: 個別部位風險列表

        Returns:
            dict: 風險管理建議
        """
        risk_score = portfolio_risk.get("overall_risk_score", 0)
        hhi = concentration.get("hhi_index", 0)
        max_weight = concentration.get("max_position_weight", 0)

        self.logger.info(
            f"開始產生風險管理建議 | 風險分數: {risk_score:.2f} | HHI: {hhi:.4f} | "
            f"最大權重: {max_weight:.2%}"
        )

        key_risks = []
        warnings = []
        recommendations = []
        position_adjustments = {}
        stop_loss_suggestions = {}

        if risk_score > 70:
            key_risks.append(f"投資組合整體風險偏高 (評分: {risk_score:.1f})")
            recommendations.append("建議降低整體部位或增加避險")

        if hhi > 0.20:
            key_risks.append(f"投資組合過度集中 (HHI: {hhi:.3f})")
            recommendations.append("建議增加持股分散度")

        if max_weight > 0.15:
            warnings.append(f"單一持股權重過高 ({max_weight:.1%})")
            recommendations.append("建議降低最大單一持股權重至 15% 以下")

        for risk in position_risks:
            ticker = risk["ticker"]
            risk_score_pos = risk.get("risk_score", 0)

            if risk_score_pos > 70:
                warnings.append(f"{ticker} 風險偏高")
                position_adjustments[ticker] = "建議減碼"

                current_price = (
                    risk.get("position_value", 0) / risk.get("quantity", 1)
                    if "quantity" in risk
                    else 0
                )
                stop_loss = current_price * 0.92
                stop_loss_suggestions[ticker] = stop_loss

        sector_conc = concentration.get("sector_concentration", {})
        for sector, weight in sector_conc.items():
            if weight > 0.40:
                key_risks.append(f"{sector} 產業曝險過高 ({weight:.1%})")
                recommendations.append(f"建議降低 {sector} 產業權重")

        self.logger.info(
            f"風險建議產生完成 | 關鍵風險: {len(key_risks)} 項 | "
            f"警示: {len(warnings)} 項 | 建議: {len(recommendations)} 項 | "
            f"部位調整: {len(position_adjustments)} 個 | 停損建議: {len(stop_loss_suggestions)} 個"
        )

        return {
            "key_risks": key_risks,
            "warnings": warnings,
            "recommendations": recommendations,
            "position_adjustments": position_adjustments,
            "stop_loss_suggestions": stop_loss_suggestions,
        }


async def get_risk_agent(
    mcp_servers: list[Any],
    model_name: str = "gpt-4o-mini",
    shared_tools: list[Any] | None = None,
    max_turns: int = 15,
) -> Agent:
    """創建風險管理 Agent

    Args:
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入
        model_name: 使用的 AI 模型名稱
        shared_tools: 從 TradingAgent 傳入的共用工具（WebSearchTool, CodeInterpreterTool）
        max_turns: 最大執行回合數（預設 15）

    Returns:
        Agent: 配置好的風險管理 Agent

    Note:
        Timeout 由主 TradingAgent 的 execution_timeout 統一控制，
        sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制。
    """
    tools_instance = RiskAnalysisTools()

    custom_tools = [
        function_tool(
            tools_instance.calculate_position_risk,
            name_override="calculate_position_risk",
            description_override="計算個別部位風險 (波動率, Beta, VaR, 最大回撤)",
            strict_mode=False,
        ),
        function_tool(
            tools_instance.analyze_portfolio_concentration,
            name_override="analyze_portfolio_concentration",
            description_override="分析投資組合集中度 (HHI 指數、產業曝險)",
            strict_mode=False,
        ),
        function_tool(
            tools_instance.calculate_portfolio_risk,
            name_override="calculate_portfolio_risk",
            description_override="計算整體投資組合風險評分和等級",
            strict_mode=False,
        ),
        function_tool(
            tools_instance.perform_stress_test,
            name_override="perform_stress_test",
            description_override="執行壓力測試模擬極端情境",
            strict_mode=False,
        ),
        function_tool(
            tools_instance.generate_risk_recommendations,
            name_override="generate_risk_recommendations",
            description_override="產生風險管理建議 (部位調整、停損點)",
            strict_mode=False,
        ),
    ]

    # 合併自訂工具和共用工具
    all_tools = custom_tools + (shared_tools or [])

    analyst = Agent(
        name="Risk Manager",
        instructions=risk_agent_instructions(),
        model=model_name,
        mcp_servers=mcp_servers,
        tools=all_tools,
    )

    return analyst
