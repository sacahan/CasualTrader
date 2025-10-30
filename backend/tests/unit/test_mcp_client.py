"""
測試 MCP Client 功能

測試與 casual-market MCP Server 的集成是否正常運作。
"""

import asyncio

from loguru import logger

from src.api.mcp_client import create_mcp_market_client


async def test_stock_price():
    """測試獲取股票報價"""
    logger.info("=" * 60)
    logger.info("測試 1: 獲取台積電 (2330) 股票報價")
    logger.info("=" * 60)

    try:
        async with create_mcp_market_client() as client:
            result = await client.get_stock_price("2330")

            if result.get("success"):
                data = result.get("data", {})
                logger.success("✅ 股票報價獲取成功！")
                logger.info(f"股票代碼: {data.get('symbol')}")
                logger.info(f"公司名稱: {data.get('company_name')}")
                logger.info(f"當前價格: {data.get('current_price')}")
                logger.info(f"漲跌幅: {data.get('change_percent')}%")
            else:
                logger.error(f"❌ 失敗: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        raise


async def test_market_indices():
    """測試獲取市場指數"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 2: 獲取主要市場指數")
    logger.info("=" * 60)

    try:
        async with create_mcp_market_client() as client:
            result = await client.get_market_indices()

            if result.get("success"):
                logger.success("✅ 市場指數獲取成功！")
                data = result.get("data", [])
                if isinstance(data, list):
                    logger.info(f"獲取到 {len(data)} 個指數")
                    for idx in data[:3]:  # 顯示前 3 個
                        logger.info(
                            f"  - {idx.get('index_name')}: {idx.get('current_value')} ({idx.get('change_percent')}%)"
                        )
                else:
                    logger.info(f"指數數據: {data}")
            else:
                logger.error(f"❌ 失敗: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        raise


async def test_trading_day_check():
    """測試交易日檢查"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 3: 檢查今日是否為交易日")
    logger.info("=" * 60)

    try:
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")

        async with create_mcp_market_client() as client:
            result = await client.check_trading_day(today)

            if result.get("success"):
                data = result.get("data", {})
                logger.success("✅ 交易日檢查成功！")
                logger.info(f"日期: {data.get('date')}")
                logger.info(f"是否為交易日: {data.get('is_trading_day')}")
                logger.info(f"是否為週末: {data.get('is_weekend')}")
                logger.info(f"是否為假日: {data.get('is_holiday')}")

                if data.get("holiday_name"):
                    logger.info(f"節假日名稱: {data.get('holiday_name')}")
            else:
                logger.error(f"❌ 失敗: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        raise


async def test_buy_stock_simulation():
    """測試模擬買入股票"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 4: 模擬買入台積電 (2330) 1 張")
    logger.info("=" * 60)

    try:
        async with create_mcp_market_client() as client:
            result = await client.buy_stock(
                symbol="2330",
                quantity=1000,  # 1 張 = 1000 股
            )

            if result.get("success"):
                data = result.get("data", {})
                logger.success("✅ 模擬交易成功！")
                logger.info(f"股票代碼: {data.get('symbol')}")
                logger.info(f"動作: {data.get('action')}")
                logger.info(f"數量: {data.get('quantity')} 股")
                logger.info(f"成交價格: {data.get('price')}")
                logger.info(f"交易總額: {data.get('total_amount')}")
                logger.info(f"手續費: {data.get('fee')}")
                logger.info(f"實際支付: {data.get('net_amount')}")
            else:
                logger.error(f"❌ 失敗: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        raise


async def test_company_profile():
    """測試獲取公司基本資料"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 5: 獲取台積電 (2330) 公司基本資料")
    logger.info("=" * 60)

    try:
        async with create_mcp_market_client() as client:
            result = await client.get_company_profile("2330")

            if result.get("success"):
                data = result.get("data", {})
                logger.success("✅ 公司資料獲取成功！")
                logger.info(f"公司名稱: {data.get('company_name')}")
                logger.info(f"產業: {data.get('industry')}")
                logger.info(f"董事長: {data.get('chairman')}")
                logger.info(f"成立日期: {data.get('establishment_date')}")
                logger.info(f"資本額: {data.get('capital')}")
                logger.info(f"員工人數: {data.get('employee_count')}")
                logger.info(f"網站: {data.get('website')}")
            else:
                logger.error(f"❌ 失敗: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        raise


async def main():
    """執行所有測試"""
    logger.info("🚀 開始測試 MCP Client")
    logger.info("請確保已安裝 casual-market-mcp: uvx casual-market-mcp")
    logger.info("")

    tests = [
        test_stock_price,
        test_market_indices,
        test_trading_day_check,
        test_buy_stock_simulation,
        test_company_profile,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            logger.error(f"測試 {test_func.__name__} 失敗: {e}")
            failed += 1

    # 總結
    logger.info("\n" + "=" * 60)
    logger.info("測試總結")
    logger.info("=" * 60)
    logger.info(f"✅ 通過: {passed}")
    logger.info(f"❌ 失敗: {failed}")
    logger.info(f"📊 總計: {passed + failed}")

    if failed == 0:
        logger.success("🎉 所有測試通過！")
    else:
        logger.warning(f"⚠️  {failed} 個測試失敗")


if __name__ == "__main__":
    asyncio.run(main())
