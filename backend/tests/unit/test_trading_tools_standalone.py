#!/usr/bin/env python3
"""
獨立測試交易工具功能 - 不依賴 TradingAgent 類
"""

import sys
import os
import pytest

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(__file__))

# 測試導入外部 agents SDK
try:
    from agents import function_tool

except ImportError as e:
    pytest.skip(f"OpenAI Agents SDK 不可用: {e}", allow_module_level=True)


def test_function_tool_decorator():
    """測試 function_tool 裝飾器"""

    @function_tool
    async def sample_tool(message: str) -> str:
        """測試工具

        Args:
            message: 測試訊息

        Returns:
            回應訊息
        """
        return f"收到訊息: {message}"

    assert sample_tool is not None
    assert hasattr(sample_tool, "name")


def test_trading_tools_concept():
    """測試交易工具概念"""

    # 模擬交易記錄工具
    @function_tool
    async def record_trade(
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        decision_reason: str,
    ) -> str:
        """
        記錄交易到資料庫

        Args:
            symbol: 股票代號 (例如: "2330")
            action: 交易動作 ("BUY" 或 "SELL")
            quantity: 交易股數
            price: 交易價格
            decision_reason: 交易決策理由

        Returns:
            交易記錄結果訊息
        """
        total_amount = quantity * price
        return f"✅ 模擬交易記錄：{action} {quantity} 股 {symbol} @ {price} 元，總金額：{total_amount:,.2f} 元"

    # 模擬投資組合查詢工具
    @function_tool
    async def get_portfolio_status() -> str:
        """
        取得當前投資組合狀態

        Returns:
            投資組合詳細資訊的文字描述
        """
        return """
📊 **模擬投資組合狀態摘要**

💰 **資金狀況**
  • 現金餘額：500,000.00 元
  • 股票市值：500,000.00 元
  • 投資組合總值：1,000,000.00 元

📈 **持股明細** (2 檔股票)
  • 2330 (台積電): 1000 股，平均成本 500.00 元，市值 500,000.00 元
  • 2454 (聯發科): 500 股，平均成本 1000.00 元，市值 500,000.00 元

📊 **資產配置**
  • 現金比例：50.0%
  • 股票比例：50.0%
"""

    trading_tools = [record_trade, get_portfolio_status]

    assert len(trading_tools) > 0
    assert all(hasattr(tool, "name") for tool in trading_tools)


@pytest.mark.asyncio
async def test_tool_execution():
    """測試工具定義（不實際調用，因為 FunctionTool 對象不可直接調用）"""

    @function_tool
    async def mock_record_trade(
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        decision_reason: str,
    ) -> str:
        """模擬記錄交易"""
        total_amount = quantity * price
        return f"✅ 模擬交易記錄：{action} {quantity} 股 {symbol} @ {price} 元，總金額：{total_amount:,.2f} 元，理由：{decision_reason}"

    @function_tool
    async def mock_get_portfolio() -> str:
        """模擬取得投資組合"""
        return "📊 模擬投資組合：現金 50 萬，股票 50 萬，總計 100 萬"

    # 驗證工具對象被正確創建
    assert mock_record_trade is not None
    assert hasattr(mock_record_trade, "name")
    assert mock_get_portfolio is not None
    assert hasattr(mock_get_portfolio, "name")
