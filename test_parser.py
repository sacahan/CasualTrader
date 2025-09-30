"""
測試修正後的解析器。
"""

import asyncio
from market_mcp.api.twse_client import create_client


async def test_fixed_parser():
    """測試修正後的解析器。"""
    try:
        client = create_client()
        result = await client.get_stock_quote("2330")

        print("✅ 成功取得股票資料:")
        print(f"   股票代號: {result.symbol}")
        print(f"   公司名稱: {result.company_name}")
        print(f"   當前價格: ${result.current_price}")
        print(f"   漲跌: {result.change:+.2f}")
        print(f"   漲跌幅: {result.change_percent:+.2%}")
        print(f"   成交量: {result.volume:,}")
        print(f"   開盤價: ${result.open_price}")
        print(f"   最高價: ${result.high_price}")
        print(f"   最低價: ${result.low_price}")
        print(f"   昨收價: ${result.previous_close}")
        print(f"   更新時間: {result.update_time}")

        if result.bid_prices:
            print(f"   買一: ${result.bid_prices[0]}")
        if result.ask_prices:
            print(f"   賣一: ${result.ask_prices[0]}")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_fixed_parser())
