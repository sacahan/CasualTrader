from __future__ import annotations

from agents import function_tool, Tool
from agents.mcp import MCPServerStdio

from common.logger import logger


# 頂層交易記錄函數
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
            status="COMPLETED",  # 假設交易立即完成
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


def create_trading_tools(
    agent_service, agent_id: str, casual_market_mcp: MCPServerStdio
) -> list[Tool]:
    """
    創建交易工具的工廠函數

    Args:
        agent_service: Agent 服務實例
        agent_id: Agent ID
        casual_market_mcp: Casual Market MCP 實例（可選，用於模擬交易）

    Returns:
        交易工具列表
    """

    # 用裝飾器包裝頂層函數以用作工具
    @function_tool
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

    @function_tool
    async def get_portfolio_status_tool() -> str:
        """
        取得當前投資組合狀態

        Returns:
            投資組合詳細資訊的文字描述
        """
        return await get_portfolio_status(agent_service=agent_service, agent_id=agent_id)

    @function_tool
    async def buy_taiwan_stock_tool(
        symbol: str,
        quantity: int,
        price: float = None,
    ) -> str:
        """
        模擬買入台灣股票

        Args:
            symbol: 股票代號 (例如: "2330")
            quantity: 購買股數，必須是1000的倍數 (台股最小單位為1000股)
            price: 指定價格 (可選，不指定則為市價)

        Returns:
            交易結果訊息
        """
        try:
            # 調用 casual_market_mcp 的 buy_taiwan_stock 工具
            result = await casual_market_mcp.session.call_tool(
                "buy_taiwan_stock",
                {
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                },
            )

            # 解析結果並格式化回傳
            if result and hasattr(result, "content"):
                content = result.content[0] if result.content else {}
                if isinstance(content, dict) and content.get("success"):
                    data = content.get("data", {})
                    return f"✅ 模擬買入成功：{data.get('symbol')} {data.get('quantity')} 股 @ {data.get('price')} 元，總金額：{data.get('total_amount'):,.2f} 元"
                else:
                    error = content.get("error", "未知錯誤")
                    return f"❌ 模擬買入失敗：{error}"

            return f"✅ 模擬買入指令已送出：{symbol} {quantity} 股"

        except Exception as e:
            logger.error(f"模擬買入失敗: {e}", exc_info=True)
            raise

    @function_tool
    async def sell_taiwan_stock_tool(
        symbol: str,
        quantity: int,
        price: float = None,
    ) -> str:
        """
        模擬賣出台灣股票

        Args:
            symbol: 股票代號 (例如: "2330")
            quantity: 賣出股數，必須是1000的倍數 (台股最小單位為1000股)
            price: 指定價格 (可選，不指定則為市價)

        Returns:
            交易結果訊息
        """
        try:
            # 調用 casual_market_mcp 的 sell_taiwan_stock 工具
            result = await casual_market_mcp.session.call_tool(
                "sell_taiwan_stock",
                {
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                },
            )

            # 解析結果並格式化回傳
            if result and hasattr(result, "content"):
                content = result.content[0] if result.content else {}
                if isinstance(content, dict) and content.get("success"):
                    data = content.get("data", {})
                    return f"✅ 模擬賣出成功：{data.get('symbol')} {data.get('quantity')} 股 @ {data.get('price')} 元，總金額：{data.get('total_amount'):,.2f} 元"
                else:
                    error = content.get("error", "未知錯誤")
                    return f"❌ 模擬賣出失敗：{error}"

            return f"✅ 模擬賣出指令已送出：{symbol} {quantity} 股"

        except Exception as e:
            logger.error(f"模擬賣出失敗: {e}", exc_info=True)
            raise

    # 將模擬交易工具加入列表
    return [
        record_trade_tool,
        get_portfolio_status_tool,
        buy_taiwan_stock_tool,
        sell_taiwan_stock_tool,
    ]
