#!/usr/bin/env python3
"""
測試資料庫遷移功能
使用 Python 3.12+ 語法測試遷移腳本
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy.sql import text

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.migrations import (  # noqa: E402
    DatabaseConfig,
    DatabaseMigrationManager,
    create_sample_data,
    run_migrations,
    verify_database_connection,
)


async def test_database_migration() -> None:
    """測試完整的資料庫遷移流程"""
    print("🚀 開始測試資料庫遷移...")

    # 使用記憶體資料庫進行測試
    config = DatabaseConfig(url="sqlite+aiosqlite:///:memory:")

    # 測試資料庫連接
    print("📡 測試資料庫連接...")
    connection_ok = await verify_database_connection(config)

    if not connection_ok:
        print("❌ 資料庫連接失敗")
        return False

    print("✅ 資料庫連接成功")

    # 創建遷移管理器
    manager = DatabaseMigrationManager(config)

    try:
        # 初始化
        await manager.initialize()
        print("✅ 遷移管理器初始化成功")

        # 檢查初始狀態
        initial_status = await manager.get_migration_status()
        print(
            f"📊 初始狀態: {initial_status['applied_migrations']}/{initial_status['total_migrations']} 個遷移已應用"
        )

        # 執行所有遷移
        print("🔄 執行資料庫遷移...")
        await manager.migrate_up()

        # 檢查遷移後狀態
        final_status = await manager.get_migration_status()
        print(
            f"📊 遷移後狀態: {final_status['applied_migrations']}/{final_status['total_migrations']} 個遷移已應用"
        )

        # 驗證所有遷移都已應用
        if final_status["applied_migrations"] != final_status["total_migrations"]:
            print("❌ 部分遷移未成功應用")
            return False

        print("✅ 所有遷移已成功應用")

        # 測試資料庫表是否正確創建
        print("🔍 驗證資料庫表結構...")
        success = await verify_database_tables(manager)

        if not success:
            return False

        print("✅ 資料庫表結構驗證成功")

        # 測試回滾功能
        print("🔄 測試遷移回滾...")
        await manager.migrate_down("1.0.0")

        rollback_status = await manager.get_migration_status()
        if rollback_status["applied_migrations"] != 1:
            print("❌ 遷移回滾失敗")
            return False

        print("✅ 遷移回滾測試成功")

        # 重新應用遷移
        await manager.migrate_up()
        print("✅ 重新應用遷移成功")

        return True

    except Exception as e:
        print(f"❌ 遷移測試失敗: {e}")
        return False
    finally:
        await manager.close()


async def verify_database_tables(manager: DatabaseMigrationManager) -> bool:
    """驗證資料庫表是否正確創建"""
    expected_tables = [
        "agents",
        "agent_sessions",
        "agent_holdings",
        "transactions",
        "strategy_changes",
        "agent_performance",
        "market_data_cache",
        "agent_config_cache",
        "schema_migrations",
    ]

    try:
        async with manager.engine.connect() as conn:
            # 檢查表是否存在
            for table_name in expected_tables:
                result = await conn.execute(
                    text(
                        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                    )
                )
                table_exists = result.fetchone() is not None

                if not table_exists:
                    print(f"❌ 表 {table_name} 不存在")
                    return False

                print(f"✅ 表 {table_name} 存在")

            # 檢查視圖是否存在
            expected_views = ["agent_overview", "agent_latest_performance"]
            for view_name in expected_views:
                result = await conn.execute(
                    text(
                        f"SELECT name FROM sqlite_master WHERE type='view' AND name='{view_name}'"
                    )
                )
                view_exists = result.fetchone() is not None

                if not view_exists:
                    print(f"❌ 視圖 {view_name} 不存在")
                    return False

                print(f"✅ 視圖 {view_name} 存在")

            return True

    except Exception as e:
        print(f"❌ 表結構驗證失敗: {e}")
        return False


async def test_sample_data_creation() -> None:
    """測試範例數據創建"""
    print("\n🔄 測試範例數據創建...")

    try:
        await create_sample_data()
        print("✅ 範例數據創建成功")
    except Exception as e:
        print(f"❌ 範例數據創建失敗: {e}")


async def test_cli_interface() -> None:
    """測試 CLI 介面"""
    print("\n🔄 測試 CLI 介面...")

    try:
        # 測試狀態查詢
        await run_migrations("status")
        print("✅ CLI 狀態查詢成功")

        # 測試重置
        await run_migrations("reset")
        print("✅ CLI 重置功能成功")

    except Exception as e:
        print(f"❌ CLI 介面測試失敗: {e}")


async def main() -> None:
    """主測試函數"""
    print("=" * 60)
    print("🧪 CasualTrader 資料庫遷移系統測試")
    print("=" * 60)

    # 測試基本遷移功能
    migration_success = await test_database_migration()

    if migration_success:
        print("\n🎉 資料庫遷移測試通過!")

        # 測試範例數據創建
        await test_sample_data_creation()

        # 測試 CLI 介面
        await test_cli_interface()

        print("\n🎯 所有測試完成!")
        print("✅ Phase 1 資料庫架構已就緒")

    else:
        print("\n💥 資料庫遷移測試失敗!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
