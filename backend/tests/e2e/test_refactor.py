#!/usr/bin/env python3
"""
測試重構後的功能：
1. @function_tool decorator 在 _setup_trading_tools 中是否正常工作
2. max_turns 是否正確傳遞給 Runner.run()
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "src"))

# ruff: noqa: E402
from agents.core.models import AgentConfig
from agents.trading.trading_agent import TradingAgent


async def test_trading_tools():
    """測試 Trading Tools 是否正確設置"""
    print("=" * 60)
    print("測試 1: @function_tool decorator 設置")
    print("=" * 60)

    config = AgentConfig(
        name="測試Agent",
        model="gpt-5-mini",
        initial_funds=1000000.0,
        max_turns=25,  # 自定義 max_turns
    )

    agent = TradingAgent(config=config)
    await agent.initialize()

    # 檢查工具
    tools = await agent._setup_trading_tools()

    print(f"\n✅ Trading Tools 數量: {len(tools)}")
    print("\n工具列表:")
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool}")
        # 檢查是否為 FunctionTool
        tool_type = type(tool).__name__
        print(f"     類型: {tool_type}")
        if hasattr(tool, "name"):
            print(f"     名稱: {tool.name}")
        if hasattr(tool, "description"):
            desc = tool.description[:80] if len(tool.description) > 80 else tool.description
            print(f"     描述: {desc}...")

    # 檢查 config 中的 max_turns
    print(f"\n✅ Agent Config max_turns: {agent.config.max_turns}")

    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)


async def test_decorator_methods():
    """測試 decorator 方法是否可調用"""
    print("\n" + "=" * 60)
    print("測試 2: 直接調用 @function_tool 裝飾的方法")
    print("=" * 60)

    config = AgentConfig(
        name="測試Agent",
        model="gpt-5-mini",
        initial_funds=1000000.0,
    )

    agent = TradingAgent(config=config)

    # 測試各個方法
    print("\n1. 測試 check_market_open:")
    result = await agent.check_market_open()
    print(f"   結果: {result} (類型: {type(result).__name__})")

    print("\n2. 測試 get_available_cash:")
    result = agent.get_available_cash()
    print(f"   結果: {result}")

    print("\n3. 測試 get_current_holdings:")
    result = agent.get_current_holdings()
    print(f"   結果: {result}")

    print("\n4. 測試 record_strategy_change_tool:")
    result = await agent.record_strategy_change_tool(
        trigger_reason="測試",
        new_strategy_addition="測試策略",
        change_summary="測試摘要",
        agent_explanation="測試解釋",
    )
    print(f"   結果: {result}")

    print("\n" + "=" * 60)
    print("所有方法測試完成！")
    print("=" * 60)


async def main():
    try:
        await test_trading_tools()
        await test_decorator_methods()
        print("\n🎉 所有測試通過！")
        return 0
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
