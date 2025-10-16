#!/usr/bin/env python3
"""
獨立測試交易工具功能 - 不依賴 TradingAgent 類
"""

import asyncio
import sys
import os

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(__file__))

# 測試導入外部 agents SDK
try:
    import agents
    from agents import function_tool

    print("✅ OpenAI Agents SDK 導入成功")
    print(f"📦 agents 版本: {getattr(agents, '__version__', 'unknown')}")
except ImportError as e:
    print(f"❌ OpenAI Agents SDK 導入失敗: {e}")
    sys.exit(1)


def test_function_tool_decorator():
    """測試 function_tool 裝飾器"""
    print("\n🧪 測試 function_tool 裝飾器...")

    try:

        @function_tool
        async def sample_tool(message: str) -> str:
            """測試工具

            Args:
                message: 測試訊息

            Returns:
                回應訊息
            """
            return f"收到訊息: {message}"

        print("✅ function_tool 裝飾器工作正常")
        print(f"📋 工具名稱: {sample_tool.name}")
        return True

    except Exception as e:
        print(f"❌ function_tool 裝飾器失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_trading_tools_concept():
    """測試交易工具概念"""
    print("\n🧪 測試交易工具概念...")

    try:
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
            # 模擬處理
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

        print(f"✅ 交易工具創建成功，工具數量: {len(trading_tools)}")

        # 顯示工具資訊
        for i, tool in enumerate(trading_tools, 1):
            print(f"  {i}. {tool.name} - {tool.description[:50]}...")

        return True

    except Exception as e:
        print(f"❌ 交易工具創建失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_tool_execution():
    """測試工具執行"""
    print("\n🧪 測試工具執行...")

    try:
        # 創建工具
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

        # 測試工具執行
        trade_result = await mock_record_trade("2330", "BUY", 1000, 520.0, "技術突破買進")
        portfolio_result = await mock_get_portfolio()

        print("✅ 交易記錄工具執行結果:")
        print(f"  {trade_result}")

        print("✅ 投資組合查詢工具執行結果:")
        print(f"  {portfolio_result}")

        return True

    except Exception as e:
        print(f"❌ 工具執行失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主測試函數"""
    print("=" * 70)
    print("🚀 交易工具功能獨立測試")
    print("=" * 70)

    results = []

    # 測試 1: function_tool 裝飾器
    results.append(test_function_tool_decorator())

    # 測試 2: 交易工具概念
    results.append(test_trading_tools_concept())

    # 測試 3: 工具執行
    results.append(await test_tool_execution())

    print("\n" + "=" * 70)
    print("📊 測試結果總結")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"✅ 通過: {passed} 個")
    print(f"❌ 失敗: {total - passed} 個")

    if passed == total:
        print("🎉 所有測試通過！交易工具功能設計正確！")
        return 0
    else:
        print("💥 部分測試失敗！")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
