"""Risk Agent - 風險評估自主型 Agent

這個模組實作具有自主分析能力的風險評估 Agent。
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
    1. 直接的參數：ticker="2330", position_data={...}
    2. JSON 字串參數：args='{"ticker":"2330","position_data":{...}}'
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


def risk_agent_instructions() -> str:
    """風險評估 Agent 的指令定義（簡化版，帶記憶追蹤）"""
    return f"""你是風險管理專家。評估投資組合風險、識別風險因素、提供風險控制建議。
持續追蹤：先查詢 memory_mcp 歷史風險評估，監控風險變化，及時預警。

## 專業能力

- 風險度量（波動性、Beta、VaR、最大回撤）
- 投資組合集中度評估（HHI 指數、產業曝險）
- 部位風險分析（未實現損益、風險分數）
- 市場風險監控（透過 tavily_mcp 搜尋市場風險、公司風險新聞）
- 壓力測試與情景分析
- 風險管理建議（停損、避險、部位調整）

## 🎯 tavily_mcp 使用限制

⚠️ **重要**：tavily_mcp 使用需要消耗點數，請遵守以下原則：
  - 只在檢測到高風險訊號時使用（不進行日常監控搜尋）
  - 優先檢查 memory_mcp 中的歷史風險記錄
  - 搜尋突發事件、市場震盪、公司風險事件
  - 單次搜尋≤2個關鍵詞，聚焦於具體風險因素
  - 若風險新聞已取得充分信息，立即停止搜尋
  - 每次分析最多進行 1 次搜尋

## 執行流程

**步驟 0：檢查記憶庫** → memory_mcp
  - 無評估 → 完整分析
  - 新鮮（≤1 天）→ 增量更新
  - 陳舊（>1 天）→ 完整重新分析 + 對比

**步驟 1-3：風險數據收集** → casual_market_mcp + tavily_mcp + tools
  1. 收集波動率、融資融券等風險數據
  2. 計算單一部位風險 → calculate_position_risk
  3. 分析組合集中度 → analyze_portfolio_concentration

**步驟 4-6：壓力測試與風險評級** → tavily_mcp + tools
  4. 計算整體組合風險 → calculate_portfolio_risk
  5. 透過 tavily_mcp 搜尋市場風險新聞、執行壓力測試 → perform_stress_test
  6. 生成管理建議 → generate_risk_recommendations

**步驟 7：對比與保存** → memory_mcp
  - 若有先前評估：對比風險評級、集中度指標、超限情況
  - 保存結果（含時間戳、風險評分、推薦動作、預警信息）

## 工具調用

- **calculate_position_risk** → 計算單一部位風險 (0-10)
- **analyze_portfolio_concentration** → 計算 HHI 集中度指數
- **calculate_portfolio_risk** → 計算整體組合風險 (0-10)
- **perform_stress_test** → 執行壓力測試（極端情景分析）
- **generate_risk_recommendations** → 生成風險管理和對沖建議

## 輸出結構

- 單一部位風險評分 (0-10)
- 組合風險評分 (0-10)
- 集中度評級 (分散/中等/集中/高度集中)
- 市場風險等級 (低/中/高/極高)
- 超限檢查 (是否超過風險限額)
- 主要風險來源 (波動率/融資/融券/系統風險)
- 壓力測試結果 (極端情景下的潛在損失)
- 管理建議 (停損/部位調整/對沖方案)
- 信心度 (0-100%)
- [若有先前評估] 風險變化 (風險評級升降、新增/消退的威脅)
當前時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


@function_tool(strict_mode=False)
def calculate_position_risk(
    ticker: str = None,
    position_data: dict = None,
    market_data: dict = None,
    **kwargs,
) -> str:
    """計算個別部位風險

    Args:
        ticker: 股票代號 (例如: "2330")
        position_data: 部位數據
        market_data: 市場數據 (可選)
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 部位風險指標
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(
            ticker=ticker, position_data=position_data, market_data=market_data, **kwargs
        )

        _ticker = params.get("ticker") or ticker
        _position_data = params.get("position_data") or position_data
        _market_data = params.get("market_data") or market_data

        # 驗證必要參數
        if not _ticker:
            logger.warning("缺少必要參數: ticker")
            return {"error": "缺少必要參數: ticker"}

        # 如果 position_data 為 None，使用預設值
        if not _position_data:
            logger.warning("缺少 position_data 參數，使用預設值")
            _position_data = {
                "quantity": 0,
                "avg_cost": 0,
                "current_price": 0,
            }
        elif not isinstance(_position_data, dict):
            # 如果是其他類型（如 Pydantic 模型），轉換為 dict
            if hasattr(_position_data, "dict"):
                _position_data = _position_data.dict()
            elif hasattr(_position_data, "model_dump"):
                _position_data = _position_data.model_dump()

        # 如果 market_data 為 None，使用預設值
        if not _market_data:
            logger.warning("缺少 market_data 參數，使用預設值")
            _market_data = {
                "volatility": 0.25,
                "beta": 1.0,
            }
        elif not isinstance(_market_data, dict):
            # 如果是其他類型（如 Pydantic 模型），轉換為 dict
            if hasattr(_market_data, "dict"):
                _market_data = _market_data.dict()
            elif hasattr(_market_data, "model_dump"):
                _market_data = _market_data.model_dump()

        logger.info(f"開始計算部位風險 | 股票: {_ticker}")

        quantity = _position_data.get("quantity", 0)
        avg_cost = _position_data.get("avg_cost", 0)
        current_price = _position_data.get("current_price", 0)

        position_value = quantity * current_price
        unrealized_pnl = (current_price - avg_cost) * quantity
        pnl_percent = unrealized_pnl / (quantity * avg_cost) if avg_cost > 0 else 0

        logger.debug(
            f"部位基本資訊 | 股票: {_ticker} | 數量: {quantity} | "
            f"成本: {avg_cost} | 現價: {current_price} | 未實現損益: {unrealized_pnl:,.0f}"
        )

        volatility = _market_data.get("volatility", 0.25)
        beta = _market_data.get("beta", 1.0)

        var_95 = position_value * volatility * 1.65
        max_drawdown = position_value * (volatility * 2)
        risk_score = min(100, (volatility * 100 + abs(beta - 1) * 30))

        logger.info(
            f"部位風險計算完成 | 股票: {_ticker} | 風險評分: {risk_score:.1f} | "
            f"VaR(95%): {var_95:,.0f} | 波動率: {volatility:.2%}"
        )

        return {
            "ticker": _ticker,
            "position_value": position_value,
            "unrealized_pnl": unrealized_pnl,
            "pnl_percent": pnl_percent,
            "volatility": volatility,
            "beta": beta,
            "var_95": var_95,
            "max_drawdown": max_drawdown,
            "risk_score": risk_score,
        }

    except Exception as e:
        logger.error(f"計算部位風險失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "ticker": ticker,
            "position_value": 0,
            "unrealized_pnl": 0,
            "pnl_percent": 0,
            "volatility": 0,
            "beta": 0,
            "var_95": 0,
            "max_drawdown": 0,
            "risk_score": 0,
        }


@function_tool(strict_mode=False)
def analyze_portfolio_concentration(
    positions: list = None,
    total_value: float = None,
    **kwargs,
) -> dict:
    """分析投資組合集中度

    Args:
        positions: 部位列表
        total_value: 投資組合總價值
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 集中度分析結果
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(positions=positions, total_value=total_value, **kwargs)

        _positions = params.get("positions") or positions or []
        _total_value = params.get("total_value") or total_value or 0

        # 驗證參數
        if not _positions:
            logger.warning("缺少 positions 參數")
            return {
                "error": "缺少 positions 參數",
                "hhi": 0,
                "sector_weights": {},
                "top_5_concentration": 0,
            }

        if _total_value <= 0:
            logger.warning("total_value 無效")
            return {
                "error": "total_value 無效",
                "hhi": 0,
                "sector_weights": {},
                "top_5_concentration": 0,
            }

        logger.info(
            f"開始分析投資組合集中度 | 總部位數: {len(_positions)} | 總價值: {_total_value:,.0f}"
        )

        # 轉換 positions 為適當格式
        position_list = []
        for pos in _positions:
            if isinstance(pos, dict):
                position_list.append(pos)
            elif hasattr(pos, "__dict__"):
                position_list.append(pos.__dict__)
            else:
                position_list.append({"ticker": str(pos), "value": 0, "sector": "未分類"})

        # 計算集中度指標
        weights = []
        sector_weights = {}

        for pos in position_list:
            try:
                pos_value = (
                    pos.get("value", 0) if isinstance(pos, dict) else getattr(pos, "value", 0)
                )
                weight = (pos_value / _total_value) if _total_value > 0 else 0
                weights.append(weight)

                sector = (
                    pos.get("sector", "未分類")
                    if isinstance(pos, dict)
                    else getattr(pos, "sector", "未分類")
                )
                if sector not in sector_weights:
                    sector_weights[sector] = 0
                sector_weights[sector] += weight
            except (AttributeError, KeyError, TypeError) as e:
                logger.debug(f"無法解析部位: {e}")
                continue

        # 計算 HHI (Herfindahl-Hirschman Index)
        hhi = sum(w**2 for w in weights) if weights else 0

        # 計算前5大集中度
        sorted_weights = sorted(weights, reverse=True)[:5]
        top_5_concentration = sum(sorted_weights)

        logger.info(
            f"投資組合集中度分析完成 | HHI: {hhi:.4f} | "
            f"前5大集中度: {top_5_concentration:.2%} | 行業數: {len(sector_weights)}"
        )

        return {
            "hhi": hhi,
            "sector_weights": sector_weights,
            "top_5_concentration": top_5_concentration,
            "total_sectors": len(sector_weights),
        }

    except Exception as e:
        logger.error(f"分析投資組合集中度失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "hhi": 0,
            "sector_weights": {},
            "top_5_concentration": 0,
            "total_sectors": 0,
        }


@function_tool(strict_mode=False)
def calculate_portfolio_risk(
    position_risks: list = None,
    concentration_json: str = None,
    total_value: float = None,
    **kwargs,
) -> dict:
    """計算投資組合整體風險

    Args:
        position_risks: 部位風險列表
        concentration_json: JSON 格式的集中度數據
        total_value: 投資組合總價值
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 投資組合風險指標
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(
            position_risks=position_risks,
            concentration_json=concentration_json,
            total_value=total_value,
            **kwargs,
        )

        _position_risks = params.get("position_risks") or position_risks or []
        _concentration_json = params.get("concentration_json") or concentration_json
        _total_value = params.get("total_value") or total_value or 0

        # 驗證參數
        if not _position_risks:
            logger.warning("缺少 position_risks 參數")
            return {
                "error": "缺少 position_risks 參數",
                "risk_level": "未知",
                "overall_risk_score": 0,
                "total_var_95": 0,
                "max_portfolio_drawdown": 0,
                "correlation_adjustment": 1.0,
            }

        logger.info(
            f"開始計算投資組合風險 | 部位數: {len(_position_risks)} | 總價值: {_total_value:,.0f}"
        )

        # 解析 concentration 數據
        concentration_data = {}
        if _concentration_json:
            try:
                if isinstance(_concentration_json, str):
                    concentration_data = json.loads(_concentration_json)
                elif isinstance(_concentration_json, dict):
                    concentration_data = _concentration_json
            except (json.JSONDecodeError, TypeError) as e:
                logger.debug(f"無法解析 concentration_json: {e}")
                concentration_data = {}

        # 轉換 position_risks 為列表格式
        risks_list = []
        for risk in _position_risks:
            if isinstance(risk, dict):
                risks_list.append(risk)
            elif hasattr(risk, "__dict__"):
                risks_list.append(risk.__dict__)
            else:
                risks_list.append({"risk_score": 50, "var_95": 0})

        # 計算組合級風險
        total_var_95 = sum(
            r.get("var_95", 0) if isinstance(r, dict) else getattr(r, "var_95", 0)
            for r in risks_list
        )
        avg_risk_score = (
            sum(
                r.get("risk_score", 50) if isinstance(r, dict) else getattr(r, "risk_score", 50)
                for r in risks_list
            )
            / len(risks_list)
            if risks_list
            else 50
        )

        # 集中度調整
        hhi = concentration_data.get("hhi", 0.1)
        correlation_adjustment = 1 + (hhi - 0.1) * 0.5

        portfolio_max_drawdown = total_var_95 * correlation_adjustment
        overall_risk_score = min(100, avg_risk_score * correlation_adjustment)

        # 判斷風險等級
        if overall_risk_score < 30:
            risk_level = "低"
        elif overall_risk_score < 60:
            risk_level = "中"
        elif overall_risk_score < 80:
            risk_level = "中高"
        else:
            risk_level = "高"

        logger.info(
            f"投資組合風險計算完成 | 風險等級: {risk_level} | "
            f"風險評分: {overall_risk_score:.1f} | VaR(95%): {total_var_95:,.0f}"
        )

        return {
            "risk_level": risk_level,
            "overall_risk_score": overall_risk_score,
            "total_var_95": total_var_95,
            "max_portfolio_drawdown": portfolio_max_drawdown,
            "correlation_adjustment": correlation_adjustment,
            "position_count": len(risks_list),
        }

    except Exception as e:
        logger.error(f"計算投資組合風險失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "risk_level": "未知",
            "overall_risk_score": 0,
            "total_var_95": 0,
            "max_portfolio_drawdown": 0,
            "correlation_adjustment": 1.0,
            "position_count": 0,
        }


@function_tool(strict_mode=False)
def perform_stress_test(
    positions: list = None,
    scenarios: list = None,
    **kwargs,
) -> dict:
    """執行投資組合壓力測試

    Args:
        positions: 部位列表
        scenarios: 壓力測試情景列表
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 壓力測試結果
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(positions=positions, scenarios=scenarios, **kwargs)

        _positions = params.get("positions") or positions or []
        _scenarios = params.get("scenarios") or scenarios or []

        # 驗證參數
        if not _positions:
            logger.warning("缺少 positions 參數")
            return {
                "error": "缺少 positions 參數",
                "stress_scenarios": [],
            }

        # 如果未提供 scenarios，生成預設情景
        if not _scenarios:
            logger.info("未提供 scenarios，生成預設壓力測試情景")
            _scenarios = [
                {"name": "市場下跌10%", "price_change": -0.10},
                {"name": "市場下跌20%", "price_change": -0.20},
                {"name": "市場下跌30%", "price_change": -0.30},
                {"name": "波動率上升50%", "volatility_change": 1.5},
                {"name": "行業輪動", "sector_impact": {"科技": -0.15, "金融": 0.10}},
            ]

        logger.info(f"開始執行壓力測試 | 部位數: {len(_positions)} | 情景數: {len(_scenarios)}")

        stress_results = []

        for scenario in _scenarios:
            try:
                if isinstance(scenario, str):
                    scenario = (
                        json.loads(scenario) if scenario.startswith("{") else {"name": scenario}
                    )
                elif not isinstance(scenario, dict):
                    scenario = {"name": "未知情景"}

                scenario_name = scenario.get("name", "未知情景")
                portfolio_loss = 0
                affected_positions = []

                for pos in _positions:
                    try:
                        pos_dict = pos if isinstance(pos, dict) else pos.__dict__
                        pos_value = pos_dict.get("value", 0)
                        price_change = scenario.get("price_change", 0)

                        if price_change != 0:
                            loss = pos_value * price_change
                            portfolio_loss += loss
                            affected_positions.append(
                                {
                                    "ticker": pos_dict.get("ticker", "未知"),
                                    "loss": loss,
                                }
                            )
                    except (AttributeError, KeyError, TypeError) as e:
                        logger.debug(f"無法計算部位損失: {e}")
                        continue

                stress_results.append(
                    {
                        "scenario": scenario_name,
                        "portfolio_loss": portfolio_loss,
                        "affected_positions": affected_positions,
                    }
                )

            except Exception as e:
                logger.warning(f"處理情景失敗: {e}")
                continue

        logger.info(f"壓力測試完成 | 評估情景數: {len(stress_results)}")

        return {
            "stress_scenarios": stress_results,
            "scenario_count": len(stress_results),
        }

    except Exception as e:
        logger.error(f"執行壓力測試失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "stress_scenarios": [],
            "scenario_count": 0,
        }


@function_tool(strict_mode=False)
def generate_risk_recommendations(
    portfolio_risk_json: str = None,
    concentration_json: str = None,
    position_risks: list = None,
    **kwargs,
) -> dict:
    """產生風險管理建議

    Args:
        portfolio_risk_json: 投資組合風險的 JSON 字串
        concentration_json: 集中度分析的 JSON 字串
        position_risks: 部位風險列表
        **kwargs: 額外參數（用於容錯）

    Returns:
        dict: 風險管理建議
    """
    try:
        # 參數驗證和容錯
        params = parse_tool_params(
            portfolio_risk_json=portfolio_risk_json,
            concentration_json=concentration_json,
            position_risks=position_risks,
            **kwargs,
        )

        _portfolio_risk_json = params.get("portfolio_risk_json") or portfolio_risk_json
        _concentration_json = params.get("concentration_json") or concentration_json
        _position_risks = params.get("position_risks") or position_risks or []

        logger.info("開始產生風險管理建議")

        # 解析投資組合風險
        portfolio_risk = {}
        if _portfolio_risk_json:
            try:
                if isinstance(_portfolio_risk_json, str):
                    portfolio_risk = json.loads(_portfolio_risk_json)
                elif isinstance(_portfolio_risk_json, dict):
                    portfolio_risk = _portfolio_risk_json
            except (json.JSONDecodeError, TypeError) as e:
                logger.debug(f"無法解析 portfolio_risk_json: {e}")
                portfolio_risk = {"overall_risk_score": 50, "risk_level": "未知"}
        else:
            portfolio_risk = {"overall_risk_score": 50, "risk_level": "未知"}

        # 解析集中度數據
        concentration = {}
        if _concentration_json:
            try:
                if isinstance(_concentration_json, str):
                    concentration = json.loads(_concentration_json)
                elif isinstance(_concentration_json, dict):
                    concentration = _concentration_json
            except (json.JSONDecodeError, TypeError) as e:
                logger.debug(f"無法解析 concentration_json: {e}")
                concentration = {"hhi": 0.1}
        else:
            concentration = {"hhi": 0.1}

        recommendations = []
        risk_score = portfolio_risk.get("overall_risk_score", 50)

        # 基於風險評分生成建議
        if risk_score >= 80:
            recommendations.append(
                {
                    "priority": "高",
                    "action": "立即降低部位",
                    "reason": "整體風險過高",
                }
            )
        elif risk_score >= 60:
            recommendations.append(
                {
                    "priority": "中",
                    "action": "監控風險指標",
                    "reason": "風險評分偏高",
                }
            )

        # 基於集中度生成建議
        hhi = concentration.get("hhi", 0.1)
        if hhi > 0.25:
            recommendations.append(
                {
                    "priority": "中",
                    "action": "增加持股分散度",
                    "reason": "投資組合過於集中",
                }
            )

        # 基於個別部位風險生成建議
        try:
            high_risk_positions = []
            for risk in _position_risks:
                try:
                    risk_score_val = (
                        risk.get("risk_score", 50)
                        if isinstance(risk, dict)
                        else getattr(risk, "risk_score", 50)
                    )
                    if risk_score_val > 70:
                        high_risk_positions.append(risk)
                except (AttributeError, KeyError, TypeError):
                    continue

            if high_risk_positions:
                recommendations.append(
                    {
                        "priority": "中",
                        "action": f"檢視 {len(high_risk_positions)} 個高風險部位",
                        "reason": "個別部位風險偏高",
                    }
                )
        except Exception as e:
            logger.debug(f"無法分析個別部位風險: {e}")

        logger.info(f"風險管理建議產生完成 | 建議數: {len(recommendations)}")

        return {
            "risk_score": risk_score,
            "risk_level": portfolio_risk.get("risk_level", "未知"),
            "recommendations": recommendations,
            "summary": f"產生 {len(recommendations)} 項風險管理建議",
        }

    except Exception as e:
        logger.error(f"產生風險管理建議失敗: {e}", exc_info=True)
        return {
            "error": str(e),
            "risk_score": 0,
            "risk_level": "未知",
            "recommendations": [],
            "summary": "無法產生風險管理建議",
        }


async def get_risk_agent(
    llm_model: LitellmModel = None,
    extra_headers: dict[str, str] = None,
    mcp_servers: list | None = None,
) -> Agent:
    """創建風險管理 Agent

    Args:
        llm_model: 使用的語言模型實例 (LitellmModel)，如果為 None，則使用預設模型
        extra_headers: 額外的 HTTP 標頭，用於模型 API 請求
        mcp_servers: MCP servers 實例列表（MCPServerStdio 對象），從 TradingAgent 傳入

    Returns:
        Agent: 配置好的風險管理 Agent

    Note:
        - 不使用 WebSearchTool 和 CodeInterpreterTool（託管工具不支援 ChatCompletions API）
        - 只使用自訂工具進行風險分析
        - Timeout 由主 TradingAgent 的 execution_timeout 統一控制
        - Sub-agent 作為 Tool 執行時會受到主 Agent 的 timeout 限制
    """
    logger.info(f"get_risk_agent() called with model={llm_model}")

    logger.debug("Creating custom tools with function_tool")
    all_tools = [
        calculate_position_risk,
        analyze_portfolio_concentration,
        calculate_portfolio_risk,
        perform_stress_test,
        generate_risk_recommendations,
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
        name="risk_analyst",
        instructions=risk_agent_instructions(),
        model=llm_model,
        mcp_servers=mcp_servers,
        tools=all_tools,
        model_settings=ModelSettings(**model_settings_dict),
    )
    logger.info("Risk Manager Agent created successfully")

    return analyst
