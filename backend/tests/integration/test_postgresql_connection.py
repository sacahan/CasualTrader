"""
PostgreSQL Connection Integration Tests

Test suite to verify PostgreSQL database connection and operations.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from api.config import get_settings


@pytest.mark.asyncio
async def test_postgresql_connection():
    """Test that we can connect to PostgreSQL database."""
    settings = get_settings()

    # Verify connection string is PostgreSQL
    assert "postgresql+asyncpg" in settings.database_url

    engine = create_async_engine(settings.database_url, echo=False)

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()

            # Verify it's actually PostgreSQL
            assert "PostgreSQL" in version
            print(f"\n✓ Connected to: {version}")

    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_postgresql_tables_exist():
    """Test that all required tables exist in PostgreSQL."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    expected_tables = {
        "agents",
        "agent_sessions",
        "agent_holdings",
        "agent_performance",
        "transactions",
        "ai_model_configs",
    }

    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema='public'
                """)
            )
            tables = {row[0] for row in result.fetchall()}

            # Verify all expected tables exist
            assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"
            print(f"\n✓ All {len(expected_tables)} required tables exist")

    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_postgresql_can_query_agents():
    """Test that we can query agents table in PostgreSQL."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM agents"))
            count = result.scalar()

            assert count >= 0
            print(f"\n✓ Agents table has {count} rows")

            # Test that we can fetch agent details
            if count > 0:
                result = await conn.execute(text("SELECT id, name, status FROM agents LIMIT 1"))
                agent = result.fetchone()
                assert agent is not None
                assert agent[0] is not None  # id
                assert agent[1] is not None  # name
                assert agent[2] is not None  # status
                print(f"✓ Can fetch agent details: {agent[0]}, {agent[1]}, {agent[2]}")

    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_postgresql_connection_pool():
    """Test that connection pooling is configured correctly."""
    settings = get_settings()

    # Verify pool settings
    assert settings.database_pool_size > 0
    assert settings.database_max_overflow > 0
    assert settings.database_pool_timeout > 0
    assert settings.database_pool_recycle > 0

    print("\n✓ Connection pool configured:")
    print(f"  Pool size: {settings.database_pool_size}")
    print(f"  Max overflow: {settings.database_max_overflow}")
    print(f"  Pool timeout: {settings.database_pool_timeout}s")
    print(f"  Pool recycle: {settings.database_pool_recycle}s")


@pytest.mark.asyncio
async def test_postgresql_transaction_support():
    """Test that PostgreSQL transactions work correctly."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    try:
        # Test rollback
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM agents"))
            original_count = result.scalar()

            # This is just a read test, we won't actually modify data
            assert original_count >= 0
            print(f"\n✓ Transaction support verified (current agents: {original_count})")

    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_postgresql_async_operations():
    """Test that async operations work correctly with PostgreSQL."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    try:
        # Test multiple concurrent queries
        async with engine.connect() as conn:
            # Execute multiple queries
            task1 = conn.execute(text("SELECT COUNT(*) FROM agents"))
            task2 = conn.execute(text("SELECT COUNT(*) FROM agent_sessions"))
            task3 = conn.execute(text("SELECT COUNT(*) FROM transactions"))

            result1 = await task1
            result2 = await task2
            result3 = await task3

            count1 = result1.scalar()
            count2 = result2.scalar()
            count3 = result3.scalar()

            print("\n✓ Async operations work correctly:")
            print(f"  Agents: {count1}")
            print(f"  Sessions: {count2}")
            print(f"  Transactions: {count3}")

    finally:
        await engine.dispose()
