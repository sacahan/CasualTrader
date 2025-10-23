"""Risk Agent - 風險評估自主型 Agent

這個模組實作具有自主分析能力的風險評估 Agent。
"""

from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

from agents import Agent, function_tool, ModelSettings

from common.logger import logger

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gpt-5-mini")
DEFAULT_MAX_TURNS = os.getenv("DEFAULT_MAX_TURNS", 30)


# ===== Pydantic Models for Tool Parameters =====


class PositionData(BaseModel):
    """部位數據模型"""

    quantity: int = 0
    avg_cost: float = 0
    current_price: float = 0


class MarketData(BaseModel):
    """市場數據模型"""

    volatility: float = 0.25
    beta: float = 1.0


class Position(BaseModel):
    """投資組合部位模型"""

    ticker: str
    value: float
    sector: str = "其他"


class PositionRisk(BaseModel):
    """部位風險模型"""

    ticker: str
    position_value: float
    unrealized_pnl: float
    pnl_percent: float
    volatility: float
    beta: float
    var_95: float
    max_drawdown: float
    risk_score: float


class StressScenario(BaseModel):
    """壓力測試情境"""

    name: str
    impact: float


# 由於輸出模型不會作為參數傳入，不需要嚴格限制
# 以下模型僅用於類型提示和文檔說明
class Concentration(BaseModel):
    """集中度分析模型(僅用於返回)"""

    model_config = ConfigDict(extra="forbid")

    hhi_index: float
    effective_stocks: float
    top5_concentration: float
    max_position_weight: float
    sector_concentration: dict[str, float]  # 產業名稱到權重的映射
    concentration_level: str
    risk_assessment: str


class PortfolioRisk(BaseModel):
    """投資組合風險模型(僅用於返回)"""

    model_config = ConfigDict(extra="forbid")

    total_value: float
    portfolio_volatility: float
    portfolio_beta: float
    portfolio_var: float
    overall_risk_score: float
    risk_level: str


def risk_agent_instructions() -> str:
    """風險評估 Agent 的指令定義（精簡版）"""
    return f"""你是風險管理專家。你的職責是評估投資組合風險、識別風險因素、提供風險控制建議。

## 你的專業能力

- 風險度量（波動性、Beta、VaR、最大回撤）
- 投資組合集中度評估（HHI 指數、產業曝險）
- 部位風險分析（未實現損益、風險分數）
- 壓力測試與情景分析
- 風險管理建議（停損、避險、部位調整）

## 可用工具

**專業分析工具（5 個）**
  1. calculate_position_risk - 計算個別部位風險
  2. analyze_portfolio_concentration - 分析集中度（HHI 指數）
  3. calculate_portfolio_risk - 計算整體風險
  4. perform_stress_test - 執行壓力測試
  5. generate_risk_recommendations - 生成風險管理建議

**數據獲取**
  • casual_market_mcp - 獲取市場數據、部位信息、波動率數據
  • memory_mcp - 保存風險分析、監控指標、歷史經驗

**AI 能力**
  • WebSearchTool - 搜尋風險管理實踐、市場風險事件、監管規範
  • CodeInterpreterTool - 執行 VaR 計算、蒙地卡羅模擬、相關性分析

## 執行流程

1. 收集部位數據 → 使用 casual_market_mcp 獲取投資組合信息
2. 計算部位風險 → 調用 calculate_position_risk
3. 分析集中度 → 調用 analyze_portfolio_concentration
4. 計算整體風險 → 調用 calculate_portfolio_risk
5. 執行壓力測試 → 調用 perform_stress_test
6. 生成建議 → 調用 generate_risk_recommendations
7. 保存分析 → 使用 memory_mcp 記錄風險監控數據

## CodeInterpreterTool 使用指南 ⚠️

**使用時機**
  ✅ VaR 計算（歷史模擬、蒙地卡羅法）
  ✅ 相關性矩陣分析
  ✅ 複雜壓力測試情景

**不要使用**
  ❌ 簡單的風險計算（用自訂工具代替）
  ❌ 已有自訂工具的功能

**限制：每次分析最多 2 次，代碼簡潔（< 100 行），蒙地卡羅 ≤ 10000 次**

## 輸出格式

結構化風險評估，包括：
  • 風險評分 (0-100, 越高越危險)
  • 風險等級 (低/中低/中/中高/高)
  • 部位風險 (每個部位的風險貢獻)
  • 集中度風險 (HHI、產業分布)
  • 壓力測試結果 (最大損失、最壞情境)
  • 管理建議 (具體可行動項)
  • 信心度 (0-100%)

## 決策原則

- 保守評估，寧可高估風險
- 重視尾部風險和極端情況
- 提供可執行的風險控制措施
- 優先保護下檔風險

當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


@function_tool
def calculate_position_risk(
    ticker: str,
    position_data: PositionData,
    market_data: MarketData | None = None,
) -> str:
    """計算個別部位風險

    Args:
        ticker: 股票代號 (例如: "2330")
        position_data: 部位數據
        market_data: 市場數據 (可選)

    Returns:
        dict: 部位風險指標
    """
    logger.info(f"開始計算部位風險 | 股票: {ticker}")

    quantity = position_data.quantity
    avg_cost = position_data.avg_cost
    current_price = position_data.current_price

    position_value = quantity * current_price
    unrealized_pnl = (current_price - avg_cost) * quantity
    pnl_percent = unrealized_pnl / (quantity * avg_cost) if avg_cost > 0 else 0

    logger.debug(
        f"部位基本資訊 | 股票: {ticker} | 數量: {quantity} | "
        f"成本: {avg_cost} | 現價: {current_price} | 未實現損益: {unrealized_pnl:,.0f}"
    )

    volatility = market_data.volatility if market_data else 0.25
    beta = market_data.beta if market_data else 1.0

    var_95 = position_value * volatility * 1.65
    max_drawdown = position_value * (volatility * 2)
    risk_score = min(100, (volatility * 100 + abs(beta - 1) * 30))

    logger.info(
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


@function_tool
def analyze_portfolio_concentration(
    positions: list[Position],
    total_value: float,
) -> str:
    """分析投資組合集中度

    Args:
        positions: 部位列表
        total_value: 投資組合總值

    Returns:
        dict: 集中度分析結果
    """
    logger.info(f"開始分析投資組合集中度 | 部位數: {len(positions)} | 總值: {total_value:,.0f}")

    if not positions or total_value <= 0:
        logger.warning("無效的投資組合數據")
        return {"error": "無效的投資組合數據"}

    weights = []
    sector_weights: dict = {}

    for pos in positions:
        value = pos.value
        weight = value / total_value if total_value > 0 else 0
        weights.append(weight)

        sector = pos.sector
        sector_weights[sector] = sector_weights.get(sector, 0) + weight

    hhi = sum(w**2 for w in weights)
    effective_stocks = 1 / hhi if hhi > 0 else 0
    top5_concentration = sum(sorted(weights, reverse=True)[:5])
    max_weight = max(weights) if weights else 0

    logger.debug(
        f"集中度計算 | HHI: {hhi:.4f} | 有效股票數: {effective_stocks:.2f} | "
        f"前5大集中度: {top5_concentration:.2%} | 最大權重: {max_weight:.2%}"
    )

    if hhi < 0.1:
        concentration_level = "非常分散"
        risk_assessment = "集中度風險低"
    elif hhi < 0.18:
        concentration_level = "適度分散"
        risk_assessment = "集中度風險可接受"
    elif hhi < 0.25:
        concentration_level = "略為集中"
        risk_assessment = "建議注意集中度"
    else:
        concentration_level = "高度集中"
        risk_assessment = "集中度風險偏高，建議分散"

    logger.info(
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


@function_tool
def calculate_portfolio_risk(
    position_risks: list[PositionRisk],
    concentration_json: str,
    total_value: float,
) -> str:
    """計算整體投資組合風險

    Args:
        position_risks: 個別部位風險列表
        concentration_json: 集中度分析結果的 JSON 字串
        total_value: 投資組合總值

    Returns:
        dict: 投資組合風險指標
    """
    import json

    logger.info(
        f"開始計算投資組合整體風險 | 部位數: {len(position_risks)} | 總值: {total_value:,.0f}"
    )

    if not position_risks:
        logger.warning("無部位風險數據")
        return {"error": "無部位風險數據"}

    total_volatility = 0.0
    total_beta = 0.0
    total_var = 0.0

    for risk in position_risks:
        weight = risk.position_value / total_value if total_value > 0 else 0
        total_volatility += risk.volatility * weight
        total_beta += risk.beta * weight
        total_var += risk.var_95

    concentration = (
        json.loads(concentration_json)
        if isinstance(concentration_json, str)
        else concentration_json
    )
    hhi = concentration.get("hhi_index", 0)
    concentration_penalty = hhi * 50

    logger.debug(
        f"風險指標計算 | 波動度: {total_volatility:.4f} | Beta: {total_beta:.4f} | "
        f"VaR總和: {total_var:,.0f} | 集中度懲罰: {concentration_penalty:.2f}"
    )

    overall_risk_score = min(
        100,
        (total_volatility * 100 + abs(total_beta - 1) * 20 + concentration_penalty),
    )

    if overall_risk_score >= 80:
        risk_level = "高風險"
    elif overall_risk_score >= 60:
        risk_level = "中高風險"
    elif overall_risk_score >= 40:
        risk_level = "中等風險"
    elif overall_risk_score >= 20:
        risk_level = "中低風險"
    else:
        risk_level = "低風險"

    logger.info(
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


@function_tool
def perform_stress_test(
    positions: list[Position],
    scenarios: list[StressScenario] | None = None,
) -> str:
    """執行壓力測試

    Args:
        positions: 部位列表
        scenarios: 壓力情境列表 (可選)

    Returns:
        dict: 壓力測試結果
    """
    logger.info(
        f"開始壓力測試 | 部位數: {len(positions)} | 情境數: {len(scenarios) if scenarios else 0}"
    )
    if not scenarios:
        scenarios = [
            StressScenario(name="市場崩盤", impact=-0.20),
            StressScenario(name="急劇修正", impact=-0.10),
            StressScenario(name="溫和下跌", impact=-0.05),
        ]

    results = []
    total_value = sum(pos.value for pos in positions)

    logger.debug(f"壓力測試設定 | 總值: {total_value:,.0f} | 情境數: {len(scenarios)}")

    for scenario in scenarios:
        scenario_name = scenario.name
        impact = scenario.impact

        loss_amount = total_value * abs(impact)
        loss_percent = abs(impact) * 100

        if loss_percent >= 20:
            severity = "極端"
        elif loss_percent >= 10:
            severity = "嚴重"
        else:
            severity = "中度"

        results.append(
            {
                "scenario_name": scenario_name,
                "loss_amount": loss_amount,
                "loss_percent": loss_percent,
                "severity": severity,
                "impact": impact,
            }
        )

        logger.debug(
            f"情境: {scenario_name} | 影響: {impact:.1%} | 損失: {loss_amount:,.0f} ({loss_percent:.1f}%)"
        )

    max_loss = max((r["loss_amount"] for r in results), default=0)
    worst_scenario = next((r for r in results if r["loss_amount"] == max_loss), None)

    logger.info(
        f"壓力測試完成 | 最大損失: {max_loss:,.0f} | "
        f"最壞情境: {worst_scenario['scenario_name'] if worst_scenario else 'N/A'}"
    )

    return {
        "total_value": total_value,
        "stress_scenarios": results,
        "max_potential_loss": max_loss,
        "worst_scenario": worst_scenario,
    }


@function_tool
def generate_risk_recommendations(
    portfolio_risk_json: str,
    concentration_json: str,
    position_risks: list[PositionRisk],
) -> str:
    """產生風險管理建議

    Args:
        portfolio_risk_json: 投資組合風險的 JSON 字串
        concentration_json: 集中度分析的 JSON 字串
        position_risks: 部位風險列表

    Returns:
        dict: 風險管理建議
    """
    import json

    logger.info("開始產生風險管理建議")

    portfolio_risk = (
        json.loads(portfolio_risk_json)
        if isinstance(portfolio_risk_json, str)
        else portfolio_risk_json
    )
    concentration = (
        json.loads(concentration_json)
        if isinstance(concentration_json, str)
        else concentration_json
    )

    recommendations = []
    risk_score = portfolio_risk.get("overall_risk_score", 50)

    if risk_score >= 80:
        recommendations.append(
            {"priority": "高", "action": "立即降低部位", "reason": "整體風險過高"}
        )

    hhi = concentration.get("hhi_index", 0)
    if hhi > 0.25:
        recommendations.append(
            {"priority": "中", "action": "增加持股分散度", "reason": "投資組合過於集中"}
        )

    high_risk_positions = [r for r in position_risks if r.risk_score > 70]
    if high_risk_positions:
        recommendations.append(
            {
                "priority": "中",
                "action": f"檢視 {len(high_risk_positions)} 個高風險部位",
                "reason": "個別部位風險偏高",
            }
        )

    logger.info(f"風險管理建議產生完成 | 建議數: {len(recommendations)}")

    return {
        "risk_score": risk_score,
        "risk_level": portfolio_risk.get("risk_level", "未知"),
        "recommendations": recommendations,
        "summary": f"產生 {len(recommendations)} 項風險管理建議",
    }


async def get_risk_agent(
    model_name: str = None,
    mcp_servers: list | None = None,
    openai_tools: list | None = None,
) -> Agent:
    """創建風險管理 Agent

    Args:
        model_name: 使用的 AI 模型名稱
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入
        openai_tools: 從 TradingAgent 傳入的共用工具（WebSearchTool, CodeInterpreterTool）

    Returns:
        Agent: 配置好的風險管理 Agent

    Note:
        Timeout 由主 TradingAgent 的 execution_timeout 統一控制，
        sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制。
    """
    logger.info(f"get_risk_agent() called with model={model_name}")

    logger.debug("Creating custom tools with function_tool")
    custom_tools = [
        calculate_position_risk,
        analyze_portfolio_concentration,
        calculate_portfolio_risk,
        perform_stress_test,
        generate_risk_recommendations,
    ]

    # 合併自訂工具和共用工具
    all_tools = custom_tools + (openai_tools or [])
    logger.debug(f"Total tools (custom + shared): {len(all_tools)}")

    logger.info(
        f"Creating Agent with model={model_name}, mcp_servers={len(mcp_servers) if mcp_servers else 0}, tools={len(all_tools)}"
    )
    analyst = Agent(
        name="risk_analyst",
        instructions=risk_agent_instructions(),
        model=model_name,
        mcp_servers=mcp_servers,
        tools=all_tools,
        model_settings=ModelSettings(
            tool_choice="required",
            max_completion_tokens=500,  # 控制回答長度，避免過度冗長
        ),
    )
    logger.info("Risk Manager Agent created successfully")

    return analyst
