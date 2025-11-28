from __future__ import annotations

import json
from typing import Any, TYPE_CHECKING

from agents import function_tool, Tool
from agents.mcp import MCPServerStdio, MCPServerSse

from common.logger import logger
from common.enums import TransactionStatus

if TYPE_CHECKING:
    from service.trading_service import TradingService


# ==========================================
# 參數驗證 Helper 函數
# ==========================================


def parse_and_validate_params(
    **kwargs,
) -> dict[str, Any]:
    """
    解析和驗證 AI Agent 傳入的參數。

    處理兩種情況：
    1. 直接的參數：symbol="2330", quantity=1000
    2. JSON 字串參數：args='{"symbol":"2330","quantity":1000}'

    Args:
        **kwargs: 傳入的所有參數

    Returns:
        解析後的參數字典
    """
    # 嘗試從 'args' 參數中解析 JSON（AI Agent 有時會這樣做）
    if "args" in kwargs and isinstance(kwargs["args"], str):
        try:
            parsed = json.loads(kwargs["args"])
            logger.debug(f"成功從 JSON 字串解析參數: {parsed}")
            return parsed
        except json.JSONDecodeError:
            logger.warning(f"無法解析 args 中的 JSON: {kwargs['args']}")

    # 返回原始參數（已去除 'args' 鍵如果存在）
    result = {k: v for k, v in kwargs.items() if k != "args"}
    return result


# ==========================================
# 頂層交易記錄函數
# ==========================================
async def record_trade(
    agent_service,
    agent_id: str,
    ticker: str,
    action: str,
    quantity: int,
    price: float,
    decision_reason: str,
    company_name: str = None,
) -> str:
    """
    記錄交易到資料庫

    Args:
        agent_service: Agent 服務實例
        agent_id: Agent ID
        ticker: 股票代號 (例如: "2330")
        action: 交易動作 ("BUY" 或 "SELL")
        quantity: 交易股數
        price: 交易價格
        decision_reason: 交易決策理由
        company_name: 公司名稱 (可選)

    Returns:
        交易記錄結果訊息
    """
    try:
        # 驗證交易動作
        action_upper = action.upper()
        if action_upper not in ["BUY", "SELL"]:
            raise ValueError(f"無效的交易動作 '{action}'，請使用 'BUY' 或 'SELL'")

        # 計算總金額和手續費
        total_amount = float(quantity * price)
        commission = total_amount * 0.001425  # 假設手續費 0.1425%

        # 創建交易記錄
        await agent_service.create_transaction(
            agent_id=agent_id,
            ticker=ticker,
            company_name=company_name,
            action=action_upper,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            commission=commission,
            decision_reason=decision_reason,
            status=TransactionStatus.EXECUTED,  # 假設交易立即完成
        )

        # 🔄 自動更新持股明細
        try:
            await agent_service.update_agent_holdings(
                agent_id=agent_id,
                ticker=ticker,
                action=action_upper,
                quantity=quantity,
                price=price,
                company_name=company_name,
            )
            logger.info(f"持股更新成功: {action_upper} {quantity} 股 {ticker}")
        except Exception as holding_error:
            logger.error(f"持股更新失敗: {holding_error}")
            # 持股更新失敗不影響交易記錄

        # 📊 自動計算並更新績效指標
        try:
            await agent_service.calculate_and_update_performance(agent_id)
            logger.info(f"績效指標更新成功 for agent {agent_id}")
        except Exception as perf_error:
            logger.error(f"績效指標更新失敗: {perf_error}")
            # 績效更新失敗不影響交易記錄

        # 💰 自動更新資金餘額
        try:
            if action_upper == "BUY":
                # 買入：減少現金
                funds_change = -(total_amount + commission)
            else:
                # 賣出：增加現金
                funds_change = total_amount - commission

            await agent_service.update_agent_funds(
                agent_id=agent_id,
                amount_change=funds_change,
                transaction_type=f"{action_upper} {ticker}",
            )
            logger.info(f"資金更新成功: {funds_change:+.2f} 元")
        except Exception as funds_error:
            logger.error(f"資金更新失敗: {funds_error}")
            # 資金更新失敗不影響交易記錄

        return f"✅ 交易記錄成功：{action_upper} {quantity} 股 {ticker} @ {price} 元，總金額：{total_amount:,.2f} 元，手續費：{commission:.2f} 元\n📊 持股、資金和績效已自動更新"

    except Exception as e:
        logger.error(f"記錄交易失敗: {e}", exc_info=True)
        raise


# 頂層投資組合查詢函數
async def get_portfolio_status(agent_service, agent_id: str) -> str:
    """
    取得當前投資組合狀態

    Args:
        agent_service: Agent 服務實例
        agent_id: Agent ID

    Returns:
        投資組合詳細資訊的文字描述

    Raises:
        Exception: 如果無法取得必要的配置或持股資訊
    """
    if not agent_service:
        raise ValueError("agent_service 不能為 None")

    # 取得 Agent 配置（包含資金資訊）
    agent_config = await agent_service.get_agent_config(agent_id)
    if not agent_config:
        raise ValueError(f"Agent {agent_id} 的配置不存在")

    # 取得持股明細
    holdings = await agent_service.get_agent_holdings(agent_id)
    logger.debug(f"Retrieved {len(holdings)} holdings for agent {agent_id}")

    # 計算投資組合資訊
    cash_balance = float(agent_config.current_funds or agent_config.initial_funds)
    total_stock_value = 0.0
    position_details = []

    for holding in holdings:
        if holding is None:
            logger.error("WARNING: get_agent_holdings() 返回了 None 元素！這表示數據庫查詢有問題")
            raise ValueError("持股列表包含 None 元素，這表示數據庫操作有誤")

        market_value = float(holding.quantity * holding.average_cost)
        total_stock_value += market_value

        company_name = holding.company_name or "未知公司"
        position_details.append(
            f"  • {holding.ticker} ({company_name}): "
            f"{holding.quantity} 股，平均成本 {holding.average_cost:.2f} 元，"
            f"市值 {market_value:,.2f} 元"
        )

    total_portfolio_value = cash_balance + total_stock_value

    # 組合回報訊息
    portfolio_summary = f"""
📊 **投資組合狀態摘要** (Agent: {agent_id})

💰 **資金狀況**
• 現金餘額：{cash_balance:,.2f} 元
• 股票市值：{total_stock_value:,.2f} 元
• 投資組合總值：{total_portfolio_value:,.2f} 元
• 初始資金：{float(agent_config.initial_funds):,.2f} 元

📈 **持股明細** ({len(holdings)} 檔股票)
{chr(10).join(position_details) if position_details else "  • 目前無持股"}

📊 **資產配置**
• 現金比例：{(cash_balance / total_portfolio_value * 100):.1f}%
• 股票比例：{(total_stock_value / total_portfolio_value * 100):.1f}%
"""

    return portfolio_summary.strip()


# ==========================================
# 原子交易執行函數
# ==========================================
async def _execute_market_trade(
    casual_market_mcp,
    ticker: str,
    action: str,
    quantity: int,
    price: float | None,
) -> dict[str, Any]:
    """
    執行市場交易（透過 casual_market_mcp）

    此函數負責呼叫 casual_market_mcp 的 buy_taiwan_stock 或 sell_taiwan_stock 工具，
    驗證交易是否可行並取得實際成交結果。

    Args:
        casual_market_mcp: Casual Market MCP 實例
        ticker: 股票代號
        action: 交易動作 ("BUY" 或 "SELL")
        quantity: 交易股數
        price: 交易價格（可為 None 表示市價）

    Returns:
        交易結果字典:
        {
            "success": bool,
            "executed_price": float (實際成交價格),
            "total_amount": float (總金額),
            "error": str (如果失敗)
        }
    """
    if casual_market_mcp is None:
        return {
            "success": False,
            "error": "casual_market_mcp 未配置，無法執行市場交易",
        }

    try:
        # 決定呼叫哪個工具
        tool_name = "buy_taiwan_stock" if action.upper() == "BUY" else "sell_taiwan_stock"

        # 構建參數
        params = {
            "symbol": ticker,
            "quantity": quantity,
        }
        if price is not None:
            params["price"] = price

        logger.info(f"🔄 呼叫 casual_market_mcp.{tool_name}: {params}")

        # 呼叫 MCP 工具
        result = await casual_market_mcp.session.call_tool(tool_name, params)

        # 解析結果
        if result and hasattr(result, "content") and result.content:
            content_item = result.content[0]
            text_content = content_item.text if hasattr(content_item, "text") else str(content_item)

            try:
                data = json.loads(text_content)
            except json.JSONDecodeError:
                logger.error(f"無法解析 MCP 回傳的 JSON: {text_content}")
                return {
                    "success": False,
                    "error": f"無法解析市場交易回傳結果: {text_content[:100]}",
                }

            if data.get("success"):
                trading_data = data.get("data", {})
                executed_price = trading_data.get("price")
                total_amount = trading_data.get("total_amount")
                net_amount = trading_data.get("net_amount")
                fee = trading_data.get("fee", 0)
                tax = trading_data.get("tax", 0)

                # 如果沒有回傳成交價格，使用傳入的價格
                if executed_price is None:
                    executed_price = price

                # 如果仍然沒有價格，這是個問題
                if executed_price is None:
                    return {
                        "success": False,
                        "error": "市場交易未回傳成交價格，交易無效",
                    }

                logger.info(
                    f"✅ 市場交易成功: {action.upper()} {quantity} 股 {ticker} @ {executed_price}"
                )

                return {
                    "success": True,
                    "executed_price": float(executed_price),
                    "total_amount": float(total_amount)
                    if total_amount
                    else float(quantity * executed_price),
                    "net_amount": float(net_amount) if net_amount else None,
                    "fee": float(fee) if fee else 0,
                    "tax": float(tax) if tax else 0,
                }
            else:
                error = data.get("error", "未知錯誤")
                logger.error(f"❌ 市場交易失敗: {error}")
                return {
                    "success": False,
                    "error": error,
                }

        return {
            "success": False,
            "error": "MCP 回傳結果為空",
        }

    except Exception as e:
        logger.error(f"市場交易異常: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


def _validate_trade_params(
    action: str,
    quantity: int,
    price: float | None,
) -> tuple[str, int, float]:
    """
    驗證交易參數

    Args:
        action: 交易動作
        quantity: 交易股數
        price: 交易價格

    Returns:
        tuple[str, int, float]: (action_upper, validated_quantity, validated_price)

    Raises:
        ValueError: 參數驗證失敗
    """
    # 驗證交易動作
    action_upper = action.upper()
    if action_upper not in ["BUY", "SELL"]:
        raise ValueError(f"無效的交易動作: {action}，必須是 'BUY' 或 'SELL'")

    # 驗證股數
    if not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"股數必須是正整數，收到: {quantity}")

    if quantity % 1000 != 0:
        raise ValueError(
            f"股數必須是 1000 的倍數（台股最小交易單位為 1 張 = 1000 股），收到: {quantity}"
        )

    # 驗證價格
    if price is None:
        raise ValueError("交易價格 (price) 不能為 None，必須提供具體的交易價格")

    validated_price = price
    if not isinstance(price, (int, float)):
        try:
            validated_price = float(price)
        except (TypeError, ValueError) as e:
            raise ValueError(f"交易價格無效: {price}，無法轉換為浮點數") from e

    if validated_price <= 0:
        raise ValueError(f"交易價格必須是正數，收到: {validated_price}")

    return action_upper, quantity, validated_price


async def _validate_trade_feasibility(
    agent_service,
    agent_id: str,
    ticker: str,
    action: str,
    quantity: int,
    price: float,
) -> dict[str, Any]:
    """
    驗證交易可行性（資金充足性 / 持股充足性）

    在執行市場交易前，先驗證：
    - BUY: 是否有足夠資金支付買入費用（含手續費）
    - SELL: 是否有足夠持股可賣出

    Args:
        agent_service: Agent 服務實例
        agent_id: Agent ID
        ticker: 股票代號
        action: 交易動作 ("BUY" 或 "SELL")
        quantity: 交易股數
        price: 交易價格

    Returns:
        dict: {
            "valid": bool,
            "agent_config": AgentConfig (如果成功),
            "current_funds": float (如果成功),
            "holding": AgentHolding | None (如果成功且為 SELL),
            "error": str (如果失敗)
        }
    """
    try:
        # 取得 Agent 配置
        agent_config = await agent_service.get_agent_config(agent_id)
        if not agent_config:
            return {
                "valid": False,
                "error": f"Agent {agent_id} 不存在",
            }

        current_funds = float(agent_config.current_funds or agent_config.initial_funds)

        if action.upper() == "BUY":
            # 計算買入所需資金（含手續費 0.1425%）
            total_amount = quantity * price
            commission = total_amount * 0.001425
            required_funds = total_amount + commission

            if current_funds < required_funds:
                return {
                    "valid": False,
                    "error": f"資金不足: 現有 {current_funds:,.2f} 元，"
                    f"買入 {quantity} 股 {ticker} @ {price} 需要 {required_funds:,.2f} 元"
                    f"（含手續費 {commission:,.2f} 元）",
                }

            return {
                "valid": True,
                "agent_config": agent_config,
                "current_funds": current_funds,
                "required_funds": required_funds,
            }

        elif action.upper() == "SELL":
            # 檢查持股是否足夠
            holdings = await agent_service.get_agent_holdings(agent_id)
            holding = next((h for h in holdings if h.ticker == ticker), None)

            if not holding:
                return {
                    "valid": False,
                    "error": f"無法賣出 {ticker}: 沒有該股票的持股記錄",
                }

            if holding.quantity < quantity:
                return {
                    "valid": False,
                    "error": f"持股不足: 持有 {holding.quantity} 股 {ticker}，"
                    f"無法賣出 {quantity} 股",
                }

            return {
                "valid": True,
                "agent_config": agent_config,
                "current_funds": current_funds,
                "holding": holding,
            }

        else:
            return {
                "valid": False,
                "error": f"未知的交易動作: {action}",
            }

    except Exception as e:
        logger.error(f"驗證交易可行性失敗: {e}", exc_info=True)
        return {
            "valid": False,
            "error": f"驗證交易可行性時發生錯誤: {str(e)}",
        }


async def execute_trade_atomic(
    trading_service: "TradingService",
    casual_market_mcp,
    agent_id: str,
    ticker: str,
    action: str,
    quantity: int,
    price: float,
    decision_reason: str | None = None,
    company_name: str | None = None,
) -> str:
    """
    執行完整交易 - 原子操作

    此函數確保交易的完整性和一致性：
    0. 預先驗證所有參數和交易可行性（資金/持股充足性）
    1. 透過 casual_market_mcp 執行市場交易
    2. 只有在市場交易成功後，才進行資料庫的原子操作

    所有資料庫操作在單一事務中，保證:
    - 全成功 → 提交所有變更
    - 任何失敗 → 回滾所有變更

    Args:
        trading_service: Trading 服務實例
        casual_market_mcp: Casual Market MCP 實例（必要，用於執行市場交易）
        agent_id: Agent ID
        ticker: 股票代號 (例如: "2330")
        action: 交易動作 ("BUY" 或 "SELL")
        quantity: 交易股數 (必須是 1000 的倍數)
        price: 交易價格 (必須提供，不可為 None)
        decision_reason: 交易決策理由 (可選)
        company_name: 公司名稱 (可選)

    Returns:
        交易執行結果訊息

    Raises:
        ValueError: 參數驗證失敗，包括 price 為 None 的情況
    """
    try:
        # ==========================================
        # Step 0: 預先驗證（在市場交易前完成所有驗證）
        # ==========================================

        # 0.1 驗證基本參數
        try:
            action_upper, validated_quantity, validated_price = _validate_trade_params(
                action=action,
                quantity=quantity,
                price=price,
            )
        except ValueError as e:
            logger.warning(f"參數驗證失敗: {e}")
            return f"❌ 交易參數驗證失敗\n\n❌ 錯誤: {str(e)}\n\n💡 請檢查交易參數後重試"

        # 0.2 驗證交易可行性（資金/持股充足性）
        agent_service = trading_service.agents_service
        feasibility = await _validate_trade_feasibility(
            agent_service=agent_service,
            agent_id=agent_id,
            ticker=ticker,
            action=action_upper,
            quantity=validated_quantity,
            price=validated_price,
        )

        if not feasibility["valid"]:
            error_msg = feasibility.get("error", "交易可行性驗證失敗")
            logger.warning(f"交易可行性驗證失敗: {error_msg}")
            return (
                f"❌ 交易可行性驗證失敗\n\n"
                f"❌ 錯誤: {error_msg}\n\n"
                f"💡 未進行任何交易，系統狀態未變更"
            )

        logger.info(
            f"✅ 預先驗證通過: {action_upper} {validated_quantity} 股 {ticker} @ {validated_price}"
        )

        # ==========================================
        # Step 1: 執行市場交易
        # ==========================================
        logger.info(
            f"📤 開始原子交易: {action_upper} {validated_quantity} 股 {ticker} @ {validated_price}"
        )

        market_result = await _execute_market_trade(
            casual_market_mcp=casual_market_mcp,
            ticker=ticker,
            action=action_upper,
            quantity=validated_quantity,
            price=validated_price,
        )

        if not market_result["success"]:
            # 市場交易失敗，不進行任何資料庫操作
            error_msg = market_result.get("error", "市場交易失敗")
            logger.error(f"❌ 市場交易失敗，中止原子操作: {error_msg}")
            return (
                f"❌ 交易執行失敗（市場交易未成功）\n\n"
                f"❌ 錯誤: {error_msg}\n\n"
                f"💡 未進行任何資料庫操作，系統狀態未變更"
            )

        # ==========================================
        # Step 2: 執行資料庫原子操作
        # ==========================================

        # ⭐ 使用市場實際成交價格（而非傳入的價格）
        executed_price = market_result["executed_price"]
        logger.info(f"✅ 市場交易成功，實際成交價: {executed_price}")

        # 執行資料庫原子操作
        result = await trading_service.execute_trade_atomic(
            agent_id=agent_id,
            ticker=ticker,
            action=action_upper,
            quantity=validated_quantity,
            price=executed_price,  # 使用實際成交價格
            decision_reason=decision_reason,
            company_name=company_name,
        )

        if result["success"]:
            logger.info("✅ 原子交易成功完成（市場交易 + 資料庫更新）")
            return (
                f"✅ 交易執行成功 (原子操作)\n\n"
                f"📊 交易詳情:\n"
                f"{result['message']}\n\n"
                f"✅ 市場交易已完成 ✓\n"
                f"✅ 資料庫更新已完成 ✓"
            )
        else:
            # ⚠️ 市場交易成功但資料庫操作失敗
            # 這是一個嚴重的不一致狀態，需要記錄警告
            logger.error(
                f"⚠️ 市場交易成功但資料庫操作失敗！"
                f"需要手動處理: {action} {quantity} 股 {ticker} @ {executed_price}"
            )
            return (
                f"⚠️ 交易執行部分成功\n\n"
                f"✅ 市場交易已完成: {action} {quantity} 股 @ {executed_price}\n"
                f"❌ 資料庫更新失敗: {result['error']}\n\n"
                f"⚠️ 警告：市場交易已執行但系統記錄失敗，請聯繫管理員處理"
            )

    except Exception as e:
        logger.error(f"原子交易異常: {e}", exc_info=True)
        return f"❌ 交易執行異常\n\n❌ 錯誤: {str(e)}\n\n💡 請檢查交易狀態"


def create_trading_tools(
    trading_service,
    agent_id: str,
    casual_market_mcp: MCPServerStdio | MCPServerSse | None = None,
    include_buy_sell: bool = True,
    include_portfolio: bool = True,
) -> list[Tool]:
    """
    創建交易工具的工廠函數

    Args:
        trading_service: Trading 服務實例 (TradingService)
        agent_id: Agent ID
        casual_market_mcp: Casual Market MCP 實例（可選，用於模擬交易）
        include_buy_sell: 是否包含買賣交易工具 (默認: True)
        include_portfolio: 是否包含投資組合工具 (默認: True)

    Returns:
        交易工具列表
    """
    # 提取 agent_service 用於非原子操作
    agent_service = trading_service.agents_service

    # 用裝飾器包裝頂層函數以用作工具
    @function_tool(strict_mode=False)
    async def record_trade_tool(
        ticker: str,
        action: str,
        quantity: int,
        price: float,
        decision_reason: str,
        company_name: str = None,
    ) -> str:
        """
        記錄交易到資料庫

        **必要參數：**
            ticker: 股票代號 (例如: "2330") [必要]
            action: 交易動作 ("BUY" 或 "SELL") [必要]
            quantity: 交易股數 [必要]
            price: 交易價格 [必要]
            decision_reason: 交易決策理由 [必要]

        **可選參數：**
            company_name: 公司名稱 [可選]

        Returns:
            交易記錄結果訊息

        Raises:
            返回錯誤訊息：缺少必要參數或交易動作無效
        """
        return await record_trade(
            agent_service=agent_service,
            agent_id=agent_id,
            ticker=ticker,
            action=action,
            quantity=quantity,
            price=price,
            decision_reason=decision_reason,
            company_name=company_name,
        )

    @function_tool(strict_mode=False)
    async def get_portfolio_status_tool() -> str:
        """
        取得當前投資組合狀態

        Returns:
            投資組合詳細資訊的文字描述
        """
        return await get_portfolio_status(agent_service=agent_service, agent_id=agent_id)

    @function_tool(strict_mode=False)
    async def get_stock_price_tool(symbol: str, **kwargs) -> str:
        """
        查詢指定股票的即時價格

        此工具用於取得台灣股票的即時價格資訊。

        **必要參數：**
            symbol: 股票代號，例如 "2330" (台積電) 或 "0050" (元大台灣50) [必要]
                   也可使用公司名稱，例如 "台積電"

        **可選參數：**
            **kwargs: 額外參數（用於容錯）

        Returns:
            str: 股票價格詳細資訊，包含目前價格、漲跌、成交量等

        Examples:
            - 查詢台積電價格：get_stock_price_tool(symbol="2330")
            - 查詢元大台灣50價格：get_stock_price_tool(symbol="0050")
            - 使用公司名稱查詢：get_stock_price_tool(symbol="台積電")

        Raises:
            返回錯誤訊息：股票代號不存在或系統異常
        """
        try:
            # 驗證並轉換參數
            _symbol = str(symbol).strip()

            if not _symbol:
                return "❌ 股票代號不能為空"

            # 調用 casual_market_mcp 的 get_taiwan_stock_price 工具
            result = await casual_market_mcp.session.call_tool(
                "get_taiwan_stock_price",
                {
                    "symbol": _symbol,
                },
            )

            # 解析結果並格式化回傳
            if result and hasattr(result, "content") and result.content:
                # 提取 TextContent 物件的文本內容
                content_item = result.content[0]
                text_content = (
                    content_item.text if hasattr(content_item, "text") else str(content_item)
                )

                # 解析 JSON
                try:
                    data = json.loads(text_content)
                except json.JSONDecodeError:
                    # 如果解析失敗，嘗試直接使用內容
                    return f"✅ 查詢指令已送出：{_symbol}"

                if data.get("success"):
                    stock_data = data.get("data", {})
                    symbol_code = stock_data.get("symbol", _symbol)
                    company_name = stock_data.get("company_name", "未知")
                    current_price = stock_data.get("current_price")
                    change = stock_data.get("change")
                    change_percent = stock_data.get("change_percent")
                    volume = stock_data.get("volume")
                    high = stock_data.get("high")
                    low = stock_data.get("low")
                    open_price = stock_data.get("open")
                    previous_close = stock_data.get("previous_close")

                    # 組合詳細資訊
                    price_info = f"""
📊 **股票即時價格查詢結果**

🏢 **基本資訊**
• 股票代號：{symbol_code}
• 公司名稱：{company_name}

💹 **價格資訊**
• 目前價格：{current_price} 元
• 開盤價：{open_price} 元
• 最高價：{high} 元
• 最低價：{low} 元
• 昨收價：{previous_close} 元
• 漲跌：{change:+.2f} 元 ({change_percent:+.2f}%)

📈 **成交資訊**
• 成交量：{volume} 股
"""
                    return price_info.strip()
                else:
                    error = data.get("error", "未知錯誤")
                    return f"❌ 查詢失敗：{error}"

            return f"✅ 查詢指令已送出：{_symbol}"

        except Exception as e:
            logger.error(f"查詢股票價格失敗: {e}", exc_info=True)
            return f"❌ 查詢失敗：{str(e)}"

    # @function_tool(strict_mode=False)
    async def buy_taiwan_stock_tool(
        symbol: str,
        quantity: int,
        price: float | None = None,
        **kwargs,
    ) -> str:
        """
        模擬買入台灣股票

        此工具用於執行台灣股票的模擬買入交易。

        **必要參數：**
            symbol: 股票代號，例如 "2330" (台積電) 或 "0050" (元大台灣50) [必要]
            quantity: 購買股數，必須是1000的倍數 (台股最小交易單位為1張/1000股) [必要]
                     常見數量：1000 (1張)、2000 (2張)、3000 (3張) 等。
                     例如想買5張台積電就傳 quantity=5000

        **可選參數：**
            price: 指定買入價格，單位為新台幣，缺少時以市價執行 [可選]
                   例如 price=520.0 表示最高願意出價520元
            **kwargs: 額外參數（用於容錯）

        Returns:
            str: 交易結果訊息，包含成功/失敗狀態、股票代號、股數、執行價格和總金額

        Examples:
            - 以市價買入台積電1張：buy_taiwan_stock_tool(symbol="2330", quantity=1000)
            - 以指定價格買入5張台積電：buy_taiwan_stock_tool(symbol="2330", quantity=5000, price=520.0)

        Raises:
            返回錯誤訊息：股票代號不存在、股數不符規定、價格無效或系統異常
        """
        try:
            # 由於 symbol 和 quantity 已經是必需參數（在函數簽名中沒有默認值），
            # 我們可以直接使用它們
            _symbol = symbol
            _quantity = quantity
            _price = price

            # 轉換資料型別
            try:
                _quantity = int(_quantity)
                _price = float(_price) if _price else None
            except (ValueError, TypeError) as e:
                return f"❌ 參數型別錯誤：{e}"

            # 調用 casual_market_mcp 的 buy_taiwan_stock 工具
            result = await casual_market_mcp.session.call_tool(
                "buy_taiwan_stock",
                {
                    "symbol": _symbol,
                    "quantity": _quantity,
                    "price": _price,
                },
            )

            # 解析結果並格式化回傳
            if result and hasattr(result, "content") and result.content:
                # 提取 TextContent 物件的文本內容
                content_item = result.content[0]
                text_content = (
                    content_item.text if hasattr(content_item, "text") else str(content_item)
                )

                # 解析 JSON
                try:
                    data = json.loads(text_content)
                except json.JSONDecodeError:
                    # 如果解析失敗，嘗試直接使用內容
                    return f"✅ 模擬買入指令已送出：{_symbol} {_quantity} 股"

                if data.get("success"):
                    trading_data = data.get("data", {})
                    executed_price = trading_data.get("price")

                    # 如果沒有執行價格，使用函數參數的 price（或標記為市價）
                    if executed_price is None:
                        executed_price = _price if _price else "市價"

                    # 計算總金額
                    if executed_price != "市價" and isinstance(executed_price, (int, float)):
                        calculated_total = _quantity * executed_price
                    else:
                        # 如果無法計算，使用 trading_data 中的值或提取的值
                        calculated_total = trading_data.get("total_amount")

                    total_amount_str = (
                        f"{calculated_total:,.2f}" if calculated_total is not None else "未知"
                    )

                    return f"✅ 模擬買入成功：{_symbol} {_quantity} 股 @ {executed_price} 元，總金額：{total_amount_str} 元"
                else:
                    error = data.get("error", "未知錯誤")
                    return f"❌ 模擬買入失敗：{error}"

            return f"✅ 模擬買入指令已送出：{_symbol} {_quantity} 股"

        except Exception as e:
            logger.error(f"模擬買入失敗: {e}", exc_info=True)
            raise

    # @function_tool(strict_mode=False)
    async def sell_taiwan_stock_tool(
        symbol: str,
        quantity: int,
        price: float | None = None,
        **kwargs,
    ) -> str:
        """
        模擬賣出台灣股票

        此工具用於執行台灣股票的模擬賣出交易。

        **必要參數：**
            symbol: 股票代號，例如 "2330" (台積電) 或 "0050" (元大台灣50) [必要]
            quantity: 賣出股數，必須是1000的倍數 (台股最小交易單位為1張/1000股) [必要]
                     常見數量：1000 (1張)、2000 (2張)、3000 (3張) 等。
                     例如想賣5張台積電就傳 quantity=5000

        **可選參數：**
            price: 指定賣出價格，單位為新台幣，缺少時以市價執行 [可選]
                   例如 price=530.0 表示最低願意出價530元
            **kwargs: 額外參數（用於容錯）

        Returns:
            str: 交易結果訊息，包含成功/失敗狀態、股票代號、股數、執行價格和總金額

        Examples:
            - 以市價賣出台積電1張：sell_taiwan_stock_tool(symbol="2330", quantity=1000)
            - 以指定價格賣出5張台積電：sell_taiwan_stock_tool(symbol="2330", quantity=5000, price=530.0)

        Raises:
            返回錯誤訊息：股票代號不存在、股數不符規定、價格無效或系統異常
        """
        try:
            # 由於 symbol 和 quantity 已經是必需參數（在函數簽名中沒有默認值），
            # 我們可以直接使用它們
            _symbol = symbol
            _quantity = quantity
            _price = price

            # 轉換資料型別
            try:
                _quantity = int(_quantity)
                _price = float(_price) if _price else None
            except (ValueError, TypeError) as e:
                return f"❌ 參數型別錯誤：{e}"

            # 調用 casual_market_mcp 的 sell_taiwan_stock 工具
            result = await casual_market_mcp.session.call_tool(
                "sell_taiwan_stock",
                {
                    "symbol": _symbol,
                    "quantity": _quantity,
                    "price": _price,
                },
            )

            # 解析結果並格式化回傳
            if result and hasattr(result, "content") and result.content:
                # 提取 TextContent 物件的文本內容
                content_item = result.content[0]
                text_content = (
                    content_item.text if hasattr(content_item, "text") else str(content_item)
                )

                # 解析 JSON
                try:
                    data = json.loads(text_content)
                except json.JSONDecodeError:
                    # 如果解析失敗，嘗試直接使用內容
                    return f"✅ 模擬賣出指令已送出：{_symbol} {_quantity} 股"

                if data.get("success"):
                    trading_data = data.get("data", {})
                    executed_price = trading_data.get("price")

                    # 如果沒有執行價格，使用函數參數的 price（或標記為市價）
                    if executed_price is None:
                        executed_price = _price if _price else "市價"

                    # 計算總金額
                    if executed_price != "市價" and isinstance(executed_price, (int, float)):
                        calculated_total = _quantity * executed_price
                    else:
                        # 如果無法計算，使用 trading_data 中的值或提取的值
                        calculated_total = trading_data.get("total_amount")

                    total_amount_str = (
                        f"{calculated_total:,.2f}" if calculated_total is not None else "未知"
                    )

                    return f"✅ 模擬賣出成功：{_symbol} {_quantity} 股 @ {executed_price} 元，總金額：{total_amount_str} 元"
                else:
                    error = data.get("error", "未知錯誤")
                    return f"❌ 模擬賣出失敗：{error}"

            return f"✅ 模擬賣出指令已送出：{_symbol} {_quantity} 股"

        except Exception as e:
            logger.error(f"模擬賣出失敗: {e}", exc_info=True)
            raise

    @function_tool(strict_mode=False)
    async def execute_trade_atomic_tool(
        ticker: str,
        action: str,
        quantity: int,
        price: float,
        decision_reason: str | None = None,
        company_name: str | None = None,
        **kwargs,
    ) -> str:
        """
        執行完整交易 - 原子操作 (推薦優先使用)

        此工具會先透過市場交易系統驗證交易可行性，成功後才記錄到資料庫。
        所有操作在單一事務中進行，保證原子性：
        - 全部成功 → 提交所有變更
        - 任何失敗 → 回滾所有變更

        此工具確保市場交易、交易記錄、持股更新、資金更新和績效計算同時成功或全部失敗。
        這解決了分別呼叫多個函數可能導致的不一致問題。

        **必要參數：**
            ticker: 股票代號，例如 "2330" (台積電) [必要]
            action: 交易動作，"BUY" (買入) 或 "SELL" (賣出) [必要]
            quantity: 交易股數，必須是1000的倍數 [必要]
            price: 交易價格，單位為新台幣 [必要]

        **可選參數：**
            decision_reason: 交易決策理由，用於交易記錄和追蹤 [可選]
            company_name: 公司名稱，用於詳細交易資訊記錄 [可選]
            **kwargs: 額外參數（用於容錯）

        Returns:
            str: 交易結果訊息，包含成功/失敗狀態和詳細資訊

        Examples:
            - 買入台積電：execute_trade_atomic_tool(ticker="2330", action="BUY", quantity=1000, price=520.0)
            - 賣出台積電：execute_trade_atomic_tool(ticker="2330", action="SELL", quantity=1000, price=520.0)

        Raises:
            返回錯誤訊息：股票代號不存在、action無效、股數不符規定、price 為空或系統異常
        """
        # ⭐ 檢查 casual_market_mcp 是否可用
        if casual_market_mcp is None:
            return (
                "❌ 交易執行失敗\n\n"
                "❌ 錯誤: 市場交易系統 (casual_market_mcp) 未配置\n\n"
                "💡 無法執行交易，請確認系統配置正確"
            )

        return await execute_trade_atomic(
            trading_service=trading_service,
            casual_market_mcp=casual_market_mcp,
            agent_id=agent_id,
            ticker=ticker,
            action=action,
            quantity=quantity,
            price=price,
            decision_reason=decision_reason,
            company_name=company_name,
        )

    # 根據配置動態構建工具列表
    tools = []

    # 添加原子交易工具（唯一的交易執行方式）
    if include_buy_sell:
        tools.append(execute_trade_atomic_tool)

    # 投資組合和查詢工具
    if include_portfolio:
        # 注意: record_trade_tool 已棄用，不再暴露給 Agent
        # record_trade_tool 不使用原子交易，也不傳遞 session_id，會導致數據不一致
        # 所有交易記錄必須使用 execute_trade_atomic_tool
        tools.append(get_portfolio_status_tool)
        tools.append(get_stock_price_tool)

    # 注意: buy_taiwan_stock_tool 和 sell_taiwan_stock_tool 已棄用，不再暴露給 Agent
    # 所有交易必須使用 execute_trade_atomic_tool

    logger.info(
        f"Trading tools created: {len(tools)} tool(s) "
        f"(AtomicTrade: {include_buy_sell}, Portfolio: {include_portfolio})"
    )

    return tools
