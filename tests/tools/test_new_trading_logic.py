#!/usr/bin/env python3
"""
測試新的交易邏輯 - 即時成交判斷
"""

import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到 Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from market_mcp import server


async def test_trading_logic():
    """測試交易邏輯"""
    print("=== 測試交易邏輯 ===\n")

    # 測試1: 限價買入 - 出價低於市價（應該失敗）
    print("測試1: 限價買入 - 出價100元 vs 中華電信市價134.5元")
    result1 = await server.buy_taiwan_stock.func("2412", 10000, 100.0)
    print(f"結果: {result1}\n")

    # 測試2: 限價買入 - 出價高於市價（應該成功）
    print("測試2: 限價買入 - 出價140元 vs 中華電信市價134.5元")
    result2 = await server.buy_taiwan_stock.func("2412", 10000, 140.0)
    print(f"結果: {result2}\n")

    # 測試3: 市價買入（應該成功）
    print("測試3: 市價買入 - 不指定價格")
    result3 = await server.buy_taiwan_stock.func("2412", 10000)
    print(f"結果: {result3}\n")

    # 測試4: 限價賣出 - 售價高於市價（應該失敗）
    print("測試4: 限價賣出 - 售價150元 vs 中華電信市價134.5元")
    result4 = await server.sell_taiwan_stock.func("2412", 10000, 150.0)
    print(f"結果: {result4}\n")

    # 測試5: 限價賣出 - 售價低於市價（應該成功）
    print("測試5: 限價賣出 - 售價130元 vs 中華電信市價134.5元")
    result5 = await server.sell_taiwan_stock.func("2412", 10000, 130.0)
    print(f"結果: {result5}\n")

    # 測試6: 市價賣出（應該成功）
    print("測試6: 市價賣出 - 不指定價格")
    result6 = await server.sell_taiwan_stock.func("2412", 10000)
    print(f"結果: {result6}\n")


if __name__ == "__main__":
    asyncio.run(test_trading_logic())
