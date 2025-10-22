#!/usr/bin/env python3
"""
測試交易工具功能
"""

import asyncio
import sys
import importlib.util
from pathlib import Path

# 添加 src 目錄到 Python 路徑
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

# 直接導入模組文件，避免循環導入
spec = importlib.util.spec_from_file_location(
    "trading_agent", str(backend_src / "trading" / "trading_agent.py")
)
trading_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trading_agent_module)
TradingAgent = trading_agent_module.TradingAgent


def test_trading_agent_creation():
    """測試 TradingAgent 創建"""
    print("🧪 測試 TradingAgent 創建...")

    try:
        # 創建一個簡單的 TradingAgent 實例
        agent = TradingAgent(agent_id="test_agent_001", agent_config=None, agent_service=None)

        print(f"✅ TradingAgent 創建成功: {agent}")
        return True

    except Exception as e:
        print(f"❌ TradingAgent 創建失敗: {e}")
        return False


def test_trading_tools_setup():
    """測試交易工具設置"""
    print("\n🧪 測試交易工具設置...")

    try:
        # 創建 TradingAgent 實例
        agent = TradingAgent(agent_id="test_agent_002", agent_config=None, agent_service=None)

        # 測試 _setup_trading_tools 方法
        trading_tools = agent._setup_trading_tools()

        print(f"✅ 交易工具設置成功，工具數量: {len(trading_tools)}")

        # 檢查工具名稱
        tool_names = [tool.name if hasattr(tool, "name") else str(tool) for tool in trading_tools]
        print(f"📋 可用工具: {tool_names}")

        return True

    except Exception as e:
        print(f"❌ 交易工具設置失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主測試函數"""
    print("=" * 60)
    print("🚀 交易工具功能測試")
    print("=" * 60)

    results = []

    # 測試 1: TradingAgent 創建
    results.append(test_trading_agent_creation())

    # 測試 2: 交易工具設置
    results.append(test_trading_tools_setup())

    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"✅ 通過: {passed} 個")
    print(f"❌ 失敗: {total - passed} 個")

    if passed == total:
        print("🎉 所有測試通過！")
        return 0
    else:
        print("💥 部分測試失敗！")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
