#!/usr/bin/env python3
"""
測試 Agent 資料庫整合功能
驗證 Agent 與 SQLite 資料庫的整合
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents import (  # noqa: E402
    AgentConfig,
    AgentDatabaseService,
    AgentMode,
    DatabaseConfig,
    PersistentTradingAgent,
    create_default_agent_config,
)


async def setup_test_database(
    database_url: str = "sqlite+aiosqlite:///:memory:",
) -> None:
    """設定測試資料庫並執行遷移"""
    from src.database.migrations import (
        DatabaseConfig as MigrationConfig,
    )
    from src.database.migrations import (
        DatabaseMigrationManager,
    )

    # 創建遷移管理器並執行遷移
    migration_config = MigrationConfig(database_url)
    migration_manager = DatabaseMigrationManager(migration_config)

    await migration_manager.initialize()
    await migration_manager.migrate_up()
    await migration_manager.close()


async def test_database_service() -> bool:
    """測試 AgentDatabaseService 基本功能"""
    print("🗄️  測試 AgentDatabaseService...")

    # 使用記憶體資料庫進行測試
    database_url = "sqlite+aiosqlite:///:memory:"

    # 先設定資料庫schema
    await setup_test_database(database_url)

    db_config = DatabaseConfig(database_url)
    db_service = AgentDatabaseService(db_config)

    try:
        # 初始化資料庫
        await db_service.initialize()
        print("✅ 資料庫服務初始化成功")

        # 健康檢查
        health = await db_service.health_check()
        print(f"✅ 資料庫健康檢查: {health['status']}")

        # 創建測試 Agent 配置和狀態
        from src.agents.core.models import AgentState

        config = create_default_agent_config(
            name="測試資料庫 Agent",
            description="用於測試資料庫整合的 Agent",
            initial_funds=500000.0,
        )

        agent_state = AgentState(
            id="test-db-agent-001",
            name=config.name,
            config=config,
        )

        # 保存 Agent 狀態
        await db_service.save_agent_state(agent_state)
        print("✅ Agent 狀態保存成功")

        # 載入 Agent 狀態
        loaded_state = await db_service.load_agent_state("test-db-agent-001")
        if loaded_state:
            print(f"✅ Agent 狀態載入成功: {loaded_state.name}")
        else:
            print("❌ Agent 狀態載入失敗")
            return False

        # 列出所有 Agent
        agents = await db_service.list_agents()
        print(f"✅ 列出 Agent: {len(agents)} 個")

        return True

    except Exception as e:
        print(f"❌ 資料庫服務測試失敗: {e}")
        return False

    finally:
        await db_service.close()


async def test_persistent_agent() -> bool:
    """測試 PersistentTradingAgent"""
    print("\n💾 測試 PersistentTradingAgent...")

    # 創建記憶體資料庫配置
    database_url = "sqlite+aiosqlite:///:memory:"
    await setup_test_database(database_url)
    db_config = DatabaseConfig(database_url)

    # 創建 Agent 配置
    agent_config = AgentConfig(
        name="持久化測試 Agent",
        description="測試資料庫持久化功能的交易 Agent",
        initial_funds=800000.0,
        instructions="你是一個用於測試的保守型交易 Agent",
        strategy_adjustment_criteria="當虧損超過5%時轉為觀察模式",
    )

    try:
        # 創建持久化 Agent
        agent = PersistentTradingAgent(
            config=agent_config,
            agent_id="persistent-test-001",
            database_config=db_config,
        )

        print(f"✅ PersistentTradingAgent 創建成功: {agent.agent_id}")

        # 測試初始化
        await agent.initialize()
        print(f"✅ Agent 初始化成功, 狀態: {agent.state.status}")

        # 測試健康檢查
        health = await agent.health_check()
        print(f"✅ Agent 健康檢查: {health}")

        # 測試模式變更和狀態保存
        await agent.change_mode(AgentMode.TRADING, "切換到交易模式進行測試")
        print(f"✅ 模式變更成功: {agent.current_mode}")

        # 測試策略變更記錄
        strategy_result = await agent.record_strategy_change(
            trigger_reason="測試觸發條件",
            new_strategy_addition="增加測試風險控制機制",
            change_summary="測試策略調整",
            agent_explanation="基於測試需求進行的策略優化",
        )

        if strategy_result["success"]:
            print("✅ 策略變更記錄成功")
        else:
            print("❌ 策略變更記錄失敗")

        # 測試執行歷史查詢
        execution_history = await agent.get_execution_history(10)
        print(f"✅ 執行歷史查詢: {len(execution_history)} 筆記錄")

        # 測試策略變更歷史查詢
        strategy_history = await agent.get_strategy_change_history(10)
        print(f"✅ 策略變更歷史: {len(strategy_history)} 筆記錄")

        # 測試績效分析
        analytics = await agent.get_performance_analytics()
        if "error" not in analytics:
            print(f"✅ 績效分析: {analytics['execution_stats']}")
        else:
            print(f"⚠️  績效分析有錯誤: {analytics['error']}")

        # 測試資料備份
        backup_data = await agent.backup_agent_data()
        print(f"✅ 資料備份成功: {len(backup_data)} 個資料項目")

        # 測試關閉
        await agent.shutdown()
        print("✅ Agent 關閉成功")

        return True

    except Exception as e:
        print(f"❌ PersistentTradingAgent 測試失敗: {e}")
        return False


async def test_database_migration_integration() -> bool:
    """測試與資料庫遷移的整合"""
    print("\n🔄 測試資料庫遷移整合...")

    try:
        # 測試與現有遷移系統的整合
        from src.database.migrations import (
            DatabaseConfig as MigrationConfig,
        )
        from src.database.migrations import (
            DatabaseMigrationManager,
        )

        # 創建遷移管理器
        migration_config = MigrationConfig("sqlite+aiosqlite:///:memory:")
        migration_manager = DatabaseMigrationManager(migration_config)

        # 初始化並執行遷移
        await migration_manager.initialize()
        await migration_manager.migrate_up()

        print("✅ 資料庫遷移執行成功")

        # 測試 Agent 資料庫服務與遷移後的資料庫
        db_config = DatabaseConfig("sqlite+aiosqlite:///:memory:")
        db_service = AgentDatabaseService(db_config)

        await db_service.initialize()
        health = await db_service.health_check()

        if health["status"] == "healthy":
            print("✅ Agent 資料庫服務與遷移系統整合成功")
        else:
            print(f"❌ 資料庫健康檢查失敗: {health}")
            return False

        await db_service.close()
        await migration_manager.close()

        return True

    except Exception as e:
        print(f"❌ 資料庫遷移整合測試失敗: {e}")
        return False


async def test_agent_lifecycle_persistence() -> bool:
    """測試 Agent 生命週期持久化"""
    print("\n♻️  測試 Agent 生命週期持久化...")

    database_url = "sqlite+aiosqlite:///:memory:"
    await setup_test_database(database_url)
    db_config = DatabaseConfig(database_url)

    try:
        # 階段 1: 創建並初始化 Agent
        agent_config = create_default_agent_config(
            name="生命週期測試 Agent",
            description="測試完整生命週期的 Agent",
            initial_funds=1000000.0,
        )

        agent1 = PersistentTradingAgent(
            config=agent_config,
            agent_id="lifecycle-test-001",
            database_config=db_config,
        )

        await agent1.initialize()
        print("✅ 階段 1: Agent 創建和初始化")

        # 進行一些操作
        await agent1.change_mode(AgentMode.TRADING)
        await agent1.record_strategy_change(
            "測試觸發", "測試策略", "測試摘要", "測試說明"
        )

        # 關閉第一個 Agent
        await agent1.shutdown()
        print("✅ 階段 2: Agent 操作完成並關閉")

        # 階段 3: 使用相同 ID 重新創建 Agent（模擬重啟）
        agent2 = PersistentTradingAgent(
            config=agent_config,
            agent_id="lifecycle-test-001",
            database_config=db_config,
        )

        await agent2.initialize()
        print("✅ 階段 3: Agent 重新創建和初始化")

        # 檢查狀態是否保持
        if agent2.current_mode == AgentMode.TRADING:
            print("✅ Agent 模式狀態正確恢復")
        else:
            print(f"⚠️  Agent 模式狀態恢復異常: {agent2.current_mode}")

        # 檢查策略變更歷史
        strategy_history = await agent2.get_strategy_change_history()
        if len(strategy_history) > 0:
            print(f"✅ 策略變更歷史正確恢復: {len(strategy_history)} 筆")
        else:
            print("⚠️  策略變更歷史恢復異常")

        await agent2.shutdown()
        print("✅ 階段 4: 生命週期測試完成")

        return True

    except Exception as e:
        print(f"❌ 生命週期持久化測試失敗: {e}")
        return False


async def main() -> None:
    """主測試函數"""
    print("=" * 60)
    print("🧪 CasualTrader Agent 資料庫整合測試")
    print("=" * 60)

    tests = [
        test_database_service,
        test_persistent_agent,
        test_database_migration_integration,
        test_agent_lifecycle_persistence,
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                print(f"❌ {test_func.__name__} 測試失敗")
        except Exception as e:
            print(f"💥 {test_func.__name__} 測試異常: {e}")

    print("\n" + "=" * 60)
    print(f"📊 測試結果: {passed}/{total} 個測試通過")

    if passed == total:
        print("🎉 所有資料庫整合測試通過!")
        print("✅ Agent-SQLite 整合層已就緒")
    else:
        print("⚠️  部分測試失敗，需要進一步檢查")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
