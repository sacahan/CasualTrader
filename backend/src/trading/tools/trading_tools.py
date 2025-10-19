from __future__ import annotations

from agents import function_tool, Tool

from common.logger import logger


def create_trading_tools(agent_service, agent_id: str) -> list[Tool]:
    """
    創建交易工具的工廠函數

    Args:
        agent_service: Agent 服務實例
        agent_id: Agent ID

    Returns:
        交易工具列表
    """
    tools = []

    # 交易紀錄工具
    @function_tool
    async def record_trade(
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
        try:
            if not agent_service:
                return "錯誤：無法存取資料庫服務"

            # 驗證交易動作
            action_upper = action.upper()
            if action_upper not in ["BUY", "SELL"]:
                return f"錯誤：無效的交易動作 '{action}'，請使用 'BUY' 或 'SELL'"

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
            return f"錯誤：記錄交易失敗 - {str(e)}"

    # 投資組合查詢工具
    @function_tool
    async def get_portfolio_status() -> str:
        """
        取得當前投資組合狀態

        Returns:
            投資組合詳細資訊的文字描述
        """
        try:
            if not agent_service:
                return "錯誤：無法存取資料庫服務"

            # 取得 Agent 配置（包含資金資訊）
            agent_config = await agent_service.get_agent_config(agent_id)

            # 取得持股明細
            holdings = await agent_service.get_agent_holdings(agent_id)

            # 計算投資組合資訊
            cash_balance = float(agent_config.current_funds or agent_config.initial_funds)
            total_stock_value = 0.0
            position_details = []

            for holding in holdings:
                market_value = float(
                    holding.quantity * holding.average_cost
                )  # 簡化：使用平均成本作為當前價值
                total_stock_value += market_value

                position_details.append(
                    f"  • {holding.ticker} ({holding.company_name or '未知公司'}): "
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

        except Exception as e:
            logger.error(f"取得投資組合狀態失敗: {e}", exc_info=True)
            return f"錯誤：無法取得投資組合狀態 - {str(e)}"

    tools.extend([record_trade, get_portfolio_status])
    return tools
