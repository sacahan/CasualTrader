#!/usr/bin/env python3
"""
測試 TradingAgent 導入
"""

import sys
import os

# 添加 backend 目錄到 sys.path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

# 現在可以使用絕對導入
try:
    from src.trading.trading_agent import TradingAgent

    print("✅ TradingAgent 導入成功")
    print(f"TradingAgent 類別: {TradingAgent}")
except Exception as e:
    print(f"❌ TradingAgent 導入失敗: {e}")
    import traceback

    traceback.print_exc()
