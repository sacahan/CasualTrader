#!/usr/bin/env python3
"""
測試 MCP 工具註冊腳本。

這個腳本會啟動 MCP 服務器並列出所有可用的工具。
"""

import asyncio
import sys
from io import StringIO

from market_mcp.server import MCPServer


async def test_mcp_tools():
    """測試 MCP 工具註冊。"""
    print("🔧 測試 MCP 工具註冊...")

    try:
        # 創建 MCP 服務器實例
        server = MCPServer()
        print("✅ MCP 服務器創建成功")

        # 獲取工具列表處理器
        handlers = server.server._handlers
        list_tools_handler = None

        for handler_type, handler_func in handlers.items():
            if "list_tools" in str(handler_type):
                list_tools_handler = handler_func
                break

        if list_tools_handler:
            print("✅ 找到 list_tools 處理器")

            # 調用 list_tools
            tools = await list_tools_handler()
            print(f"📊 總共找到 {len(tools)} 個工具:")

            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool.name} - {tool.description}")

            # 檢查是否有交易工具
            tool_names = [tool.name for tool in tools]
            expected_tools = [
                "get_taiwan_stock_price",
                "buy_taiwan_stock",
                "sell_taiwan_stock",
            ]

            print("\n🔍 檢查預期工具:")
            for tool_name in expected_tools:
                if tool_name in tool_names:
                    print(f"  ✅ {tool_name}")
                else:
                    print(f"  ❌ {tool_name} - 未找到")

        else:
            print("❌ 未找到 list_tools 處理器")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
