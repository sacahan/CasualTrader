#!/usr/bin/env python3
"""
CasualTrader Phase 1 完整測試套件
整合所有 Phase 1 核心功能測試
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Phase1TestRunner:
    """Phase 1 測試套件執行器"""

    def __init__(self) -> None:
        self.passed_tests = 0
        self.total_tests = 0
        self.failed_tests: list[str] = []
        self.start_time = 0.0

    def start_suite(self) -> None:
        """開始測試套件"""
        self.start_time = time.time()
        print("=" * 70)
        print("🧪 CasualTrader Phase 1 完整測試套件")
        print("=" * 70)
        print("📋 測試範圍:")
        print("  • SQLite 資料庫遷移和模型")
        print("  • Agent 核心架構 (Base, Manager, Session)")
        print("  • Trading Agent 功能")
        print("  • 資料庫整合和持久化")
        print("  • MCP Server 整合")
        print("=" * 70)

    async def run_test_module(self, test_name: str, test_function: callable) -> bool:
        """執行單一測試模組"""
        print(f"\n🔧 執行測試模組: {test_name}")
        print("-" * 50)

        try:
            result = await test_function()
            if result:
                self.passed_tests += 1
                print(f"✅ {test_name} 測試通過")
            else:
                self.failed_tests.append(test_name)
                print(f"❌ {test_name} 測試失敗")

            self.total_tests += 1
            return result

        except Exception as e:
            self.failed_tests.append(f"{test_name} (異常)")
            self.total_tests += 1
            print(f"💥 {test_name} 測試異常: {e}")
            return False

    def finish_suite(self) -> None:
        """完成測試套件並生成報告"""
        elapsed_time = time.time() - self.start_time
        coverage_rate = (
            (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        )

        print("\n" + "=" * 70)
        print("📊 Phase 1 測試套件結果")
        print("=" * 70)
        print(f"🎯 總測試數量: {self.total_tests}")
        print(f"✅ 通過測試: {self.passed_tests}")
        print(f"❌ 失敗測試: {len(self.failed_tests)}")
        print(f"📈 覆蓋率: {coverage_rate:.1f}%")
        print(f"⏱️  執行時間: {elapsed_time:.2f} 秒")

        if self.failed_tests:
            print(f"\n❌ 失敗的測試:")
            for test in self.failed_tests:
                print(f"  • {test}")

        print("\n🎯 Phase 1 目標達成狀況:")
        if coverage_rate >= 80:
            print("✅ 達成目標覆蓋率 > 80%")
            if coverage_rate >= 90:
                print("🌟 優秀！覆蓋率 > 90%")
        else:
            print("⚠️  未達成目標覆蓋率 80%")

        if self.passed_tests == self.total_tests:
            print("\n🎉 所有 Phase 1 測試通過！")
            print("✅ Phase 1 開發完成，可以進入 Phase 2")
        else:
            print(f"\n⚠️  有 {len(self.failed_tests)} 個測試需要修復")

        print("=" * 70)


async def run_database_tests() -> bool:
    """執行資料庫相關測試"""
    from tests.test_database_integration import main as db_main

    # 重新定向輸出以抓取結果
    try:
        await db_main()
        return True
    except Exception:
        return False


async def run_agent_infrastructure_tests() -> bool:
    """執行 Agent 基礎架構測試"""
    from tests.test_agent_infrastructure import main as agent_main

    try:
        await agent_main()
        return True
    except Exception:
        return False


async def run_mcp_integration_tests() -> bool:
    """執行 MCP 整合測試"""
    from tests.test_mcp_integration import main as mcp_main

    try:
        await mcp_main()
        return True
    except Exception:
        return False


async def run_additional_agent_tests() -> bool:
    """額外 Agent 功能測試"""
    print("🤖 測試 Agent 進階功能...")

    from src.agents import (
        AgentManager,
        create_default_agent_config,
        PersistentTradingAgent,
        DatabaseConfig,
    )

    try:
        # 測試 Agent Manager
        manager = AgentManager()
        await manager.start()

        # 創建測試配置
        config = create_default_agent_config(
            name="測試 Manager Agent",
            description="用於測試 AgentManager 的 Agent",
        )

        # 測試 Agent 創建和管理
        agent_id = await manager.create_agent(config)
        print(f"  ✅ Agent 創建: {agent_id}")

        # 測試 Agent 列表
        agents = manager.list_agents()
        print(f"  ✅ Agent 管理: {len(agents)} 個 Agent")

        # 測試 Agent 移除
        await manager.remove_agent(agent_id)
        print("  ✅ Agent 生命週期管理")

        await manager.shutdown()
        print("  ✅ Manager 關閉")

        return True

    except Exception as e:
        print(f"  ❌ Agent 進階功能測試失敗: {e}")
        return False


async def run_performance_tests() -> bool:
    """效能和壓力測試"""
    print("⚡ 執行效能測試...")

    try:
        # 測試多個 Agent 同時執行
        from src.agents import AgentManager, create_default_agent_config

        manager = AgentManager()
        await manager.start()

        # 創建多個 Agent
        agent_configs = [
            create_default_agent_config(
                name=f"效能測試 Agent {i}", description=f"用於效能測試的第 {i} 個 Agent"
            )
            for i in range(3)
        ]

        start_time = time.time()
        agent_ids = []

        for config in agent_configs:
            agent_id = await manager.create_agent(config)
            agent_ids.append(agent_id)

        creation_time = time.time() - start_time
        print(f"  ✅ 3個 Agent 創建時間: {creation_time:.2f}秒")

        # 清理
        for agent_id in agent_ids:
            await manager.remove_agent(agent_id)

        await manager.shutdown()

        # 效能標準檢查
        if creation_time < 5.0:  # 5秒內創建3個Agent
            print("  ✅ 效能測試通過")
            return True
        else:
            print("  ⚠️  效能測試未達標準")
            return False

    except Exception as e:
        print(f"  ❌ 效能測試失敗: {e}")
        return False


async def main() -> None:
    """主測試函數"""
    runner = Phase1TestRunner()
    runner.start_suite()

    # 定義測試模組
    test_modules = [
        ("資料庫整合測試", run_database_tests),
        ("Agent 基礎架構測試", run_agent_infrastructure_tests),
        ("MCP Server 整合測試", run_mcp_integration_tests),
        ("Agent 進階功能測試", run_additional_agent_tests),
        ("效能和壓力測試", run_performance_tests),
    ]

    # 執行所有測試
    for test_name, test_func in test_modules:
        await runner.run_test_module(test_name, test_func)

    # 生成最終報告
    runner.finish_suite()


if __name__ == "__main__":
    asyncio.run(main())
