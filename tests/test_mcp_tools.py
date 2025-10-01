#!/usr/bin/env python3
"""
測試 MCP 工具功能。

這個腳本用於測試新建立的 MCP 工具介面是否正常運作。
"""

import asyncio
from market_mcp.tools.stock_price_tool import StockPriceTool


async def test_stock_price_tool():
    """測試股票價格查詢工具。"""
    print("🔧 初始化股票價格工具...")
    tool = StockPriceTool()

    print("📋 取得工具定義...")
    tool_def = tool.get_tool_definition()
    print(f"✅ 工具名稱: {tool_def['name']}")
    print(f"✅ 工具描述: {tool_def['description']}")

    print("\n📊 執行健康檢查...")
    health = await tool.health_check()
    print(f"✅ 健康狀態: {health}")

    print("\n📈 測試股票查詢 (台積電 2330)...")
    try:
        result = await tool.get_taiwan_stock_price({"symbol": "2330"})
        print("✅ 查詢成功!")
        print("回應內容:")
        print(result[0]["text"])
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")

    print("\n❌ 測試錯誤處理 (無效股票代號)...")
    try:
        result = await tool.get_taiwan_stock_price({"symbol": "invalid"})
        print("⚠️  預期應該失敗，但成功了")
    except Exception as e:
        print(f"✅ 正確捕獲錯誤: {type(e).__name__}")
        # 測試使用錯誤處理器
        from market_mcp.handlers.error_handler import MCPErrorHandler

        error_response = MCPErrorHandler.handle_exception(e, "test_invalid_symbol")
        print("錯誤回應:")
        print(error_response[0]["text"])

    print("\n📜 取得工具說明...")
    help_text = tool.get_help_text()
    print("✅ 說明文字已生成 (長度: {} 字元)".format(len(help_text)))

    print("\n📊 取得支援的股票代號...")
    symbols = await tool.get_supported_symbols()
    print(f"✅ 支援 {len(symbols)} 個範例股票代號")
    for symbol in symbols[:3]:  # 只顯示前3個
        print(f"   - {symbol['symbol']}: {symbol['name']}")


if __name__ == "__main__":
    print("🚀 開始測試 CasualTrader MCP 工具...")
    asyncio.run(test_stock_price_tool())
    print("✅ 測試完成！")
