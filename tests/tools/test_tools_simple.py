#!/usr/bin/env python3
"""
簡單的工具測試腳本。
"""

import asyncio

from market_mcp.tools.stock_price_tool import (
    get_tool_definitions as get_stock_tool_defs,
)
from market_mcp.tools.trading_tool import get_trading_tool_definitions


async def test_tools():
    """測試工具定義。"""
    print("🔧 測試工具定義...")

    # 測試股票價格工具
    stock_tools = get_stock_tool_defs()
    print(f"📊 股票價格工具: {len(stock_tools)} 個")
    for tool in stock_tools:
        print(f"  - {tool['name']}: {tool['description']}")

    # 測試交易工具
    trading_tools = get_trading_tool_definitions()
    print(f"📊 交易工具: {len(trading_tools)} 個")
    for tool in trading_tools:
        print(f"  - {tool['name']}: {tool['description']}")

    # 總計
    total_tools = len(stock_tools) + len(trading_tools)
    print(f"\n✅ 總計: {total_tools} 個工具")

    print("\n🔍 所有工具名稱:")
    all_tools = stock_tools + trading_tools
    for i, tool in enumerate(all_tools, 1):
        print(f"  {i}. {tool['name']}")


if __name__ == "__main__":
    asyncio.run(test_tools())
