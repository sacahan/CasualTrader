"""Risk Agent - 風險評估自主型 Agent

這個模組實作具有自主分析能力的風險評估 Agent。
"""

from __future__ import annotations

import logging
import os
from datetime import datetime

from dotenv import load_dotenv

from agents import Agent, function_tool, ModelSettings

# Logger
logger = logging.getLogger(__name__)

load_dotenv()

DEFAULT_MODEL = os.getenv("DEFAULT_AI_MODEL", "gpt-5-mini")
DEFAULT_MAX_TURNS = os.getenv("DEFAULT_MAX_TURNS", 30)


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


@function_tool
def calculate_position_risk(
    ticker: str,
    position_data: str,
    market_data: str = "",
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

    quantity = position_data.get("quantity", 0)
    avg_cost = position_data.get("avg_cost", 0)
    current_price = position_data.get("current_price", 0)

    position_value = quantity * current_price
    unrealized_pnl = (current_price - avg_cost) * quantity
    pnl_percent = unrealized_pnl / (quantity * avg_cost) if avg_cost > 0 else 0

    logger.debug(
        f"部位基本資訊 | 股票: {ticker} | 數量: {quantity} | "
        f"成本: {avg_cost} | 現價: {current_price} | 未實現損益: {unrealized_pnl:,.0f}"
    )

    volatility = market_data.get("volatility", 0.25) if market_data else 0.25
    beta = market_data.get("beta", 1.0) if market_data else 1.0

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
    positions: str,
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
    sector_weights: str = ""

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
    position_risks: str,
    concentration: str,
    total_value: float,
) -> str:
    """計算整體投資組合風險

    Args:
        position_risks: 個別部位風險列表
        concentration: 集中度分析
        total_value: 投資組合總值

    Returns:
        dict: 投資組合風險指標
    """
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
        weight = risk.get("position_value", 0) / total_value if total_value > 0 else 0
        total_volatility += risk.get("volatility", 0) * weight
        total_beta += risk.get("beta", 0) * weight
        total_var += risk.get("var_95", 0)

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
    positions: str,
    scenarios: str = "",
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
            {"name": "市場崩盤", "impact": -0.20},
            {"name": "急劇修正", "impact": -0.10},
            {"name": "溫和下跌", "impact": -0.05},
        ]

    results = []
    total_value = sum(pos.get("value", 0) for pos in positions)

    logger.debug(f"壓力測試設定 | 總值: {total_value:,.0f} | 情境數: {len(scenarios)}")

    for scenario in scenarios:
        scenario_name = scenario.get("name", "未命名情境")
        impact = scenario.get("impact", 0)

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
    portfolio_risk: str,
    concentration: str,
    position_risks: str,
) -> str:
    """產生風險管理建議

    Args:
        portfolio_risk: 投資組合風險
        concentration: 集中度分析
        position_risks: 部位風險列表

    Returns:
        dict: 風險管理建議
    """
    logger.info("開始產生風險管理建議")

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

    high_risk_positions = [r for r in position_risks if r.get("risk_score", 0) > 70]
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
    model_name: str = DEFAULT_MODEL,
    mcp_servers: str = "",
    openai_tools: str = "",
    max_turns: int = DEFAULT_MAX_TURNS,
) -> Agent:
    """創建風險管理 Agent

    Args:
        model_name: 使用的 AI 模型名稱
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入
        openai_tools: 從 TradingAgent 傳入的共用工具（WebSearchTool, CodeInterpreterTool）
        max_turns: 最大執行回合數

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
        name="Risk Manager",
        instructions=risk_agent_instructions(),
        model=model_name,
        mcp_servers=mcp_servers,
        tools=all_tools,
        model_settings=ModelSettings(
            tool_choice="required",
        ),
    )
    logger.info("Risk Manager Agent created successfully")

    return analyst
