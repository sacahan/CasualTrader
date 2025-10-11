#!/usr/bin/env python
"""
驗證程式碼修改的腳本
檢查：
1. TradingAgent 不再有 auto_mode_selection 和 execute_with_auto_mode
2. AgentManager 現在有 start_agent 方法
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def verify_trading_agent():
    """驗證 TradingAgent 修改"""
    print("🔍 驗證 TradingAgent...")

    from agents.trading.trading_agent import TradingAgent
    from agents.core.models import AgentConfig

    # 檢查方法不存在
    assert not hasattr(TradingAgent, "auto_mode_selection"), "❌ auto_mode_selection 應該已被移除"
    assert not hasattr(
        TradingAgent, "execute_with_auto_mode"
    ), "❌ execute_with_auto_mode 應該已被移除"

    # 檢查正常功能仍存在
    config = AgentConfig(
        name="測試 Agent",
        model="gpt-4o-mini",
        initial_funds=1000000.0,
    )
    agent = TradingAgent(config)

    # 驗證基本屬性
    assert agent.agent_id is not None
    assert agent.config.name == "測試 Agent"
    assert hasattr(agent, "get_strategy_changes")
    assert hasattr(agent, "record_strategy_change")

    print("✅ TradingAgent 驗證通過")


async def verify_agent_manager():
    """驗證 AgentManager 修改"""
    print("🔍 驗證 AgentManager...")

    from agents.core.agent_manager import AgentManager

    manager = AgentManager()

    # 檢查 start_agent 方法存在
    assert hasattr(manager, "start_agent"), "❌ start_agent 方法應該存在"

    # 檢查方法簽名
    import inspect

    sig = inspect.signature(manager.start_agent)
    params = list(sig.parameters.keys())

    assert "agent_id" in params, "❌ start_agent 應該有 agent_id 參數"
    assert "max_cycles" in params, "❌ start_agent 應該有 max_cycles 參數"
    assert "stop_loss_threshold" in params, "❌ start_agent 應該有 stop_loss_threshold 參數"

    print("✅ AgentManager 驗證通過")


async def main():
    """主驗證流程"""
    print("=" * 60)
    print("開始驗證程式碼修改...")
    print("=" * 60)

    try:
        await verify_trading_agent()
        await verify_agent_manager()

        print("\n" + "=" * 60)
        print("🎉 所有驗證通過！")
        print("=" * 60)
        print("\n修改摘要:")
        print("✅ 已移除 TradingAgent.auto_mode_selection()")
        print("✅ 已移除 TradingAgent.execute_with_auto_mode()")
        print("✅ 已新增 AgentManager.start_agent()")
        print("✅ 已更新測試檔案，移除對已刪除方法的呼叫")

        return 0

    except AssertionError as e:
        print(f"\n❌ 驗證失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
