"""簡單測試 - 只測試一個工具"""

import asyncio
from loguru import logger
from src.api.mcp_client import create_mcp_market_client


async def test_simple():
    logger.info("測試: 獲取台積電 (2330) 股票報價")

    async with create_mcp_market_client(timeout=10) as client:
        result = await client.get_stock_price("2330")
        logger.info(f"結果: {result}")

        if result.get("success"):
            logger.success("✅ 測試成功！")
        else:
            logger.error("❌ 測試失敗")


if __name__ == "__main__":
    asyncio.run(test_simple())
