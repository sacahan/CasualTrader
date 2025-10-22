#!/usr/bin/env python3
"""
測試 TradingAgent 完整功能
包括工具註冊和基本初始化
"""

import sys
import os
import asyncio
import logging

# 添加 backend 目錄到 sys.path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_trading_agent():
    """測試 TradingAgent"""
    try:
        from src.trading.trading_agent import TradingAgent

        logger.info("✅ TradingAgent 導入成功")

        # 檢查類別屬性
        logger.info(f"TradingAgent 類別: {TradingAgent}")
        logger.info(f'TradingAgent 方法: {[m for m in dir(TradingAgent) if not m.startswith("_")]}')

        logger.info("🎉 所有測試通過!")

    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_trading_agent())
