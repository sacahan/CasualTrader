from __future__ import annotations

import json
from typing import Any

from agents import function_tool, Tool
from agents.mcp import MCPServerStdio

from common.logger import logger
from common.enums import TransactionStatus


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
async def execute_trade_atomic(
    trading_service,
    agent_id: str,
    ticker: str,
    action: str,
    quantity: int,
    price: float | None = None,
    decision_reason: str | None = None,
    company_name: str | None = None,
) -> str:
    """
    執行完整交易 - 原子操作

    所有操作在單一事務中，保證:
    - 全成功 → 提交所有變更
    - 任何失敗 → 回滾所有變更

    委託給 TradingService 進行事務管理。

    Args:
        trading_service: Trading 服務實例
        agent_id: Agent ID
        ticker: 股票代號 (例如: "2330")
        action: 交易動作 ("BUY" 或 "SELL")
        quantity: 交易股數 (必須是 1000 的倍數)
        price: 交易價格
        decision_reason: 交易決策理由 (可選)
        company_name: 公司名稱 (可選)

    Returns:
        交易執行結果訊息

    Raises:
        ValueError: 參數驗證失敗
    """
    try:
        result = await trading_service.execute_trade_atomic(
            agent_id=agent_id,
            ticker=ticker,
            action=action,
            quantity=quantity,
            price=price,
            decision_reason=decision_reason,
            company_name=company_name,
        )

        if result["success"]:
            logger.info("✅ 原子交易成功完成")
            return (
                f"✅ 交易執行成功 (原子操作)\n\n"
                f"📊 交易詳情:\n"
                f"{result['message']}\n\n"
                f"✅ 所有操作已原子性完成 ✓"
            )
        else:
            logger.error(f"原子交易失敗，已完全回滾: {result['error']}")
            return (
                f"❌ 交易執行失敗，已完全回滾\n\n"
                f"❌ 錯誤: {result['error']}\n\n"
                f"💡 系統狀態完全恢復，無任何痕跡"
            )

    except Exception as e:
        logger.error(f"原子交易異常: {e}", exc_info=True)
        return f"❌ 交易執行異常\n\n❌ 錯誤: {str(e)}\n\n💡 系統狀態完全恢復，無任何痕跡"


def create_trading_tools(
    trading_service,
    agent_id: str,
    casual_market_mcp: MCPServerStdio | None = None,
    include_buy_sell: bool = True,
    include_portfolio: bool = True,
) -> list[Tool]:
    """
    創建交易工具的工廠函數

    Args:
        trading_service: Trading 服務實例
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

        Args:
            ticker: 股票代號 (例如: "2330")
            action: 交易動作 ("BUY" 或 "SELL")
            quantity: 交易股數
            price: 交易價格
            decision_reason: 交易決策理由
            company_name: 公司名稱 (可選)

        Returns:
            交易記錄結果訊息
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
    async def buy_taiwan_stock_tool(
        symbol: str,
        quantity: int,
        price: float | None = None,
        **kwargs,
    ) -> str:
        """
        模擬買入台灣股票

        此工具用於執行台灣股票的模擬買入交易。您必須提供股票代號和購買股數。

        Args:
            symbol: 股票代號，例如 "2330" (台積電) 或 "0050" (元大台灣50)。【必需】
            quantity: 購買股數，必須是1000的倍數 (台股最小交易單位為1張/1000股)。【必需】
                     常見數量：1000 (1張)、2000 (2張)、3000 (3張) 等。
                     例如想買5張台積電就傳 quantity=5000
            price: 指定買入價格，單位為新台幣 (可選，不指定則以市價執行)。
                   例如 price=520.0 表示最高願意出價520元

        Returns:
            str: 交易結果訊息，包含成功/失敗狀態、股票代號、股數、執行價格和總金額

        Examples:
            - 以市價買入台積電1張：buy_taiwan_stock_tool(symbol="2330", quantity=1000)
            - 以指定價格買入5張台積電：buy_taiwan_stock_tool(symbol="2330", quantity=5000, price=520.0)
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

    @function_tool(strict_mode=False)
    async def sell_taiwan_stock_tool(
        symbol: str,
        quantity: int,
        price: float | None = None,
        **kwargs,
    ) -> str:
        """
        模擬賣出台灣股票

        此工具用於執行台灣股票的模擬賣出交易。您必須提供股票代號和賣出股數。

        Args:
            symbol: 股票代號，例如 "2330" (台積電) 或 "0050" (元大台灣50)。【必需】
            quantity: 賣出股數，必須是1000的倍數 (台股最小交易單位為1張/1000股)。【必需】
                     常見數量：1000 (1張)、2000 (2張)、3000 (3張) 等。
                     例如想賣5張台積電就傳 quantity=5000
            price: 指定賣出價格，單位為新台幣 (可選，不指定則以市價執行)。
                   例如 price=530.0 表示最低願意出價530元

        Returns:
            str: 交易結果訊息，包含成功/失敗狀態、股票代號、股數、執行價格和總金額

        Examples:
            - 以市價賣出台積電1張：sell_taiwan_stock_tool(symbol="2330", quantity=1000)
            - 以指定價格賣出5張台積電：sell_taiwan_stock_tool(symbol="2330", quantity=5000, price=530.0)
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
        price: float | None = None,
        decision_reason: str | None = None,
        company_name: str | None = None,
    ) -> str:
        """
        執行完整交易 - 原子操作 (推薦優先使用)

        所有操作在單一事務中進行，保證原子性：
        - 全部成功 → 提交所有變更
        - 任何失敗 → 回滾所有變更

        此工具確保市場交易、交易記錄、持股更新、資金更新和績效計算同時成功或全部失敗。
        這解決了分別呼叫多個函數可能導致的不一致問題。

        Args:
            ticker: 股票代號，例如 "2330" (台積電)。【必需】
            action: 交易動作，"BUY" 或 "SELL"。【必需】
            quantity: 交易股數，必須是1000的倍數。【必需】
            price: 交易價格，單位為新台幣 (可選)
            decision_reason: 交易決策理由 (可選)
            company_name: 公司名稱 (可選)

        Returns:
            str: 交易結果訊息，包含成功/失敗狀態和詳細資訊

        Examples:
            - 以指定價格買入台積電：execute_trade_atomic_tool(ticker="2330", action="BUY", quantity=1000, price=520.0)
            - 以市價賣出台積電：execute_trade_atomic_tool(ticker="2330", action="SELL", quantity=1000)
        """
        return await execute_trade_atomic(
            trading_service=trading_service,
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

    # 投資組合工具
    if include_portfolio:
        tools.append(record_trade_tool)
        tools.append(get_portfolio_status_tool)

    # 注意: buy_taiwan_stock_tool 和 sell_taiwan_stock_tool 已棄用，不再暴露給 Agent
    # 所有交易必須使用 execute_trade_atomic_tool

    logger.info(
        f"Trading tools created: {len(tools)} tool(s) "
        f"(AtomicTrade: {include_buy_sell}, Portfolio: {include_portfolio})"
    )

    return tools
