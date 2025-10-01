#!/usr/bin/env python3

import asyncio
import json
from market_mcp.tools.stock_price_tool import handle_get_taiwan_stock_price

async def test_stock_price():
    """測試本地股票價格工具"""
    try:
        # 測試台泥1101
        result = await handle_get_taiwan_stock_price({"symbol": "1101"})
        print("本地 MCP 工具回應:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 解析結果
        if result and len(result) > 0:
            text_content = result[0].get("text", "")
            print(f"\n格式化結果:\n{text_content}")
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stock_price())
