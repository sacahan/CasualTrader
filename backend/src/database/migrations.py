"""
CasualTrader Database Migration System
使用 Python 3.12+ 語法特性和異步 SQLite 支援
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.sql import text

from .models import Base

# ==========================================
# Migration Protocol (Python 3.12+ Protocol)
# ==========================================


class MigrationStep(Protocol):
    """遷移步驟協議定義"""

    async def up(self, engine: AsyncEngine) -> None:
        """執行遷移"""
        ...

    async def down(self, engine: AsyncEngine) -> None:
        """回滾遷移"""
        ...


# ==========================================
# Migration Data Classes (Python 3.12+ dataclass)
# ==========================================


@dataclass
class MigrationInfo:
    """遷移資訊資料結構"""

    version: str
    name: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False
    checksum: str | None = None


@dataclass
class DatabaseConfig:
    """資料庫配置資料結構"""

    url: str = "sqlite+aiosqlite:///casualtrader.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30


# ==========================================
# Migration Steps Implementation
# ==========================================


class InitialSchemaMigration:
    """初始 Schema 遷移 (v1.0.0)"""

    version = "1.0.0"
    name = "initial_schema"
    description = "Create initial database schema for Agent system"

    async def up(self, engine: AsyncEngine) -> None:
        """創建初始 schema"""
        logging.info("Creating initial database schema...")

        # 使用 SQLAlchemy 2.0+ 異步語法
        async with engine.begin() as conn:
            # 創建所有表
            await conn.run_sync(Base.metadata.create_all)

            # 創建額外的索引和視圖
            await self._create_views(conn)
            await self._create_triggers(conn)

        logging.info("Initial schema created successfully")

    async def down(self, engine: AsyncEngine) -> None:
        """刪除 schema"""
        logging.info("Dropping database schema...")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logging.info("Schema dropped successfully")

    async def _create_views(self, conn) -> None:
        """創建資料庫視圖"""

        # Agent 總覽視圖
        agent_overview_sql = text(
            """
        CREATE VIEW IF NOT EXISTS agent_overview AS
        SELECT
            a.id,
            a.name,
            a.status,
            a.current_mode,
            a.initial_funds,
            COUNT(DISTINCT h.ticker) as holdings_count,
            COALESCE(SUM(h.quantity * h.average_cost), 0) as total_invested,
            a.created_at,
            a.last_active_at
        FROM agents a
        LEFT JOIN agent_holdings h ON a.id = h.agent_id
        GROUP BY a.id
        """
        )

        # Agent 最新績效視圖
        latest_performance_sql = text(
            """
        CREATE VIEW IF NOT EXISTS agent_latest_performance AS
        SELECT
            ap.*,
            a.name as agent_name
        FROM agent_performance ap
        INNER JOIN (
            SELECT agent_id, MAX(date) as latest_date
            FROM agent_performance
            GROUP BY agent_id
        ) latest ON ap.agent_id = latest.agent_id AND ap.date = latest.latest_date
        INNER JOIN agents a ON ap.agent_id = a.id
        """
        )

        await conn.execute(agent_overview_sql)
        await conn.execute(latest_performance_sql)

    async def _create_triggers(self, conn) -> None:
        """創建觸發器"""

        # Agent 更新時間觸發器
        agent_trigger_sql = text(
            """
        CREATE TRIGGER IF NOT EXISTS agents_updated_at
            AFTER UPDATE ON agents
        BEGIN
            UPDATE agents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """
        )

        # Holdings 更新時間觸發器
        holdings_trigger_sql = text(
            """
        CREATE TRIGGER IF NOT EXISTS holdings_updated_at
            AFTER UPDATE ON agent_holdings
        BEGIN
            UPDATE agent_holdings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        """
        )

        await conn.execute(agent_trigger_sql)
        await conn.execute(holdings_trigger_sql)


class AddPerformanceIndexesMigration:
    """新增績效相關索引 (v1.1.0)"""

    version = "1.1.0"
    name = "add_performance_indexes"
    description = "Add performance-related indexes for query optimization"

    async def up(self, engine: AsyncEngine) -> None:
        """新增索引"""
        logging.info("Adding performance indexes...")

        async with engine.begin() as conn:
            # 複合索引用於績效查詢優化
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_transactions_agent_ticker ON transactions(agent_id, ticker)",
                "CREATE INDEX IF NOT EXISTS idx_performance_agent_date ON agent_performance(agent_id, date DESC)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_agent_mode_time ON agent_sessions(agent_id, mode, start_time DESC)",
                "CREATE INDEX IF NOT EXISTS idx_strategy_changes_agent_timestamp ON strategy_changes(agent_id, timestamp DESC)",
            ]

            for index_sql in indexes:
                await conn.execute(text(index_sql))

        logging.info("Performance indexes added successfully")

    async def down(self, engine: AsyncEngine) -> None:
        """移除索引"""
        logging.info("Removing performance indexes...")

        async with engine.begin() as conn:
            indexes = [
                "DROP INDEX IF EXISTS idx_transactions_agent_ticker",
                "DROP INDEX IF EXISTS idx_performance_agent_date",
                "DROP INDEX IF EXISTS idx_sessions_agent_mode_time",
                "DROP INDEX IF EXISTS idx_strategy_changes_agent_timestamp",
            ]

            for index_sql in indexes:
                await conn.execute(text(index_sql))

        logging.info("Performance indexes removed successfully")


class AddAIModelConfigMigration:
    """新增 AI 模型配置表和種子資料 (v1.2.0)"""

    version = "1.2.0"
    name = "add_ai_model_config"
    description = "Add AI model configuration table and seed data for unified model management"

    async def up(self, engine: AsyncEngine) -> None:
        """創建 AI 模型配置表並插入種子資料"""
        logging.info("Creating AI model configuration table...")

        # 表已經通過 Base.metadata.create_all 創建
        # 現在插入種子資料
        from .seed_ai_models import seed_ai_models

        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(engine) as session:
            await seed_ai_models(session)

        logging.info("AI model configuration table created and seeded successfully")

    async def down(self, engine: AsyncEngine) -> None:
        """移除 AI 模型配置表"""
        logging.info("Dropping AI model configuration table...")

        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS ai_model_configs"))

        logging.info("AI model configuration table dropped successfully")


# ==========================================
# Migration Manager (Python 3.12+ class with type annotations)
# ==========================================


class DatabaseMigrationManager:
    """資料庫遷移管理器 - 使用 Python 3.12+ 語法"""

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.engine: AsyncEngine | None = None
        self.migrations: list[MigrationStep] = [
            InitialSchemaMigration(),
            AddPerformanceIndexesMigration(),
            AddAIModelConfigMigration(),
        ]

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """初始化資料庫連接"""
        # SQLite 的配置參數不同
        if "sqlite" in self.config.url:
            self.engine = create_async_engine(
                self.config.url,
                echo=self.config.echo,
            )
        else:
            self.engine = create_async_engine(
                self.config.url,
                echo=self.config.echo,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
            )

        # 創建遷移歷史表
        await self._create_migration_table()

    async def _create_migration_table(self) -> None:
        """創建遷移歷史表"""
        sql = text(
            """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            checksum TEXT
        )
        """
        )

        async with self.engine.begin() as conn:
            await conn.execute(sql)

    async def get_applied_migrations(self) -> list[str]:
        """獲取已應用的遷移版本"""
        sql = text("SELECT version FROM schema_migrations ORDER BY applied_at")

        async with self.engine.connect() as conn:
            result = await conn.execute(sql)
            return [row[0] for row in result.fetchall()]

    async def apply_migration(self, migration: MigrationStep) -> None:
        """應用單個遷移"""
        try:
            # 執行遷移
            await migration.up(self.engine)

            # 記錄到遷移歷史
            sql = text(
                """
            INSERT INTO schema_migrations (version, name, description)
            VALUES (:version, :name, :description)
            """
            )

            async with self.engine.begin() as conn:
                await conn.execute(
                    sql,
                    {
                        "version": migration.version,
                        "name": migration.name,
                        "description": migration.description,
                    },
                )

            self.logger.info(f"Applied migration {migration.version}: {migration.name}")

        except Exception as e:
            self.logger.error(f"Failed to apply migration {migration.version}: {e}")
            raise

    async def rollback_migration(self, migration: MigrationStep) -> None:
        """回滾單個遷移"""
        try:
            # 執行回滾
            await migration.down(self.engine)

            # 從遷移歷史中移除
            sql = text("DELETE FROM schema_migrations WHERE version = :version")

            async with self.engine.begin() as conn:
                await conn.execute(sql, {"version": migration.version})

            self.logger.info(f"Rolled back migration {migration.version}: {migration.name}")

        except Exception as e:
            self.logger.error(f"Failed to rollback migration {migration.version}: {e}")
            raise

    async def migrate_up(self, target_version: str | None = None) -> None:
        """執行向上遷移"""
        applied = await self.get_applied_migrations()

        for migration in self.migrations:
            # 使用 match-case 語法 (Python 3.12+)
            match (migration.version in applied, target_version):
                case (True, _):
                    # 已應用，跳過
                    continue
                case (False, None):
                    # 未應用且無目標版本，應用所有
                    await self.apply_migration(migration)
                case (False, target) if migration.version <= target:
                    # 未應用且版本小於等於目標版本
                    await self.apply_migration(migration)
                case _:
                    # 其他情況跳過
                    break

    async def migrate_down(self, target_version: str) -> None:
        """執行向下遷移（回滾）"""
        applied = await self.get_applied_migrations()

        # 按版本倒序回滾
        for migration in reversed(self.migrations):
            if migration.version in applied and migration.version > target_version:
                await self.rollback_migration(migration)

    async def reset_database(self) -> None:
        """重設資料庫（清空所有數據）"""
        self.logger.warning("Resetting database - all data will be lost!")

        # 回滾所有遷移
        applied = await self.get_applied_migrations()
        for migration in reversed(self.migrations):
            if migration.version in applied:
                await self.rollback_migration(migration)

        # 重新應用所有遷移
        await self.migrate_up()

        self.logger.info("Database reset completed")

    async def get_migration_status(self) -> dict[str, Any]:
        """獲取遷移狀態"""
        applied = await self.get_applied_migrations()

        status = {
            "total_migrations": len(self.migrations),
            "applied_migrations": len(applied),
            "pending_migrations": len(self.migrations) - len(applied),
            "details": [],
        }

        for migration in self.migrations:
            is_applied = migration.version in applied
            status["details"].append(
                {
                    "version": migration.version,
                    "name": migration.name,
                    "description": migration.description,
                    "applied": is_applied,
                }
            )

        return status

    async def close(self) -> None:
        """關閉資料庫連接"""
        if self.engine:
            await self.engine.dispose()


# ==========================================
# CLI Interface using Python 3.12+ features
# ==========================================


async def run_migrations(action: str = "up", target_version: str | None = None) -> None:
    """執行遷移命令"""
    config = DatabaseConfig()
    manager = DatabaseMigrationManager(config)

    try:
        await manager.initialize()

        # 使用 match-case 語法處理不同動作
        match action.lower():
            case "up":
                await manager.migrate_up(target_version)
                print("✅ Database migration completed successfully")

            case "down":
                if not target_version:
                    raise ValueError("Target version required for down migration")
                await manager.migrate_down(target_version)
                print(f"✅ Database rolled back to version {target_version}")

            case "reset":
                await manager.reset_database()
                print("✅ Database reset completed")

            case "status":
                status = await manager.get_migration_status()
                print("📊 Migration Status:")
                print(f"   Total: {status['total_migrations']}")
                print(f"   Applied: {status['applied_migrations']}")
                print(f"   Pending: {status['pending_migrations']}")

                print("\n📋 Migration Details:")
                for detail in status["details"]:
                    status_icon = "✅" if detail["applied"] else "⏳"
                    print(f"   {status_icon} {detail['version']}: {detail['name']}")

            case _:
                raise ValueError(f"Unknown action: {action}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await manager.close()


# ==========================================
# Utility Functions
# ==========================================


async def verify_database_connection(config: DatabaseConfig) -> bool:
    """驗證資料庫連接"""
    try:
        engine = create_async_engine(config.url)

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        await engine.dispose()
        return True

    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return False


async def create_sample_data() -> None:
    """創建範例數據用於測試"""
    config = DatabaseConfig()
    manager = DatabaseMigrationManager(config)

    try:
        await manager.initialize()

        # 創建範例 Agent
        sample_agent_sql = text(
            """
        INSERT OR IGNORE INTO agents (
            id, name, description, instructions, initial_funds,
            investment_preferences, strategy_adjustment_criteria
        ) VALUES (
            'sample-agent-001',
            '保守型投資 Agent',
            '專注於大型股和高股息股票的保守投資策略',
            '你是一個保守型投資顧問，專注於穩健成長...',
            1000000.00,
            '偏好大型股、金融股，風險承受度低',
            '當連續三天虧損超過1%時轉為觀察模式'
        )
        """
        )

        async with manager.engine.begin() as conn:
            await conn.execute(sample_agent_sql)

        print("✅ Sample data created successfully")

    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        raise
    finally:
        await manager.close()


if __name__ == "__main__":
    import sys

    # 簡單的 CLI 介面
    if len(sys.argv) < 2:
        print("Usage: python migrations.py [up|down|reset|status] [target_version]")
        sys.exit(1)

    action = sys.argv[1]
    target_version = sys.argv[2] if len(sys.argv) > 2 else None

    # 使用 asyncio.run() 執行異步函數
    asyncio.run(run_migrations(action, target_version))
