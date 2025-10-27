#!/usr/bin/env python3
"""
End-to-end test for list_agents API endpoint

完整測試 API 層的 list_agents 端點
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# ruff: noqa: E402
from fastapi.testclient import TestClient
from api.app import create_app
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database.models import Base
from service.agents_service import AgentsService


async def setup_test_db():
    """Setup in-memory test database with sample data."""
    # Create in-memory SQLite database
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create some test agents
    async with async_session() as session:
        agents_service = AgentsService(session)

        # Create 3 test agents
        for i in range(1, 4):
            agent = await agents_service.create_agent(
                name=f"Test Agent {i}",
                description=f"Test agent {i} for API testing",
                ai_model="gpt-4o-mini" if i % 2 == 0 else "gpt-4o",
                strategy_prompt=f"Test strategy {i}",
                initial_funds=Decimal(str(100000 * i)),
                color_theme="34, 197, 94" if i % 2 == 0 else "239, 68, 68",
                investment_preferences=["2330", "0050"] if i % 2 == 0 else ["2454"],
            )
            print(f"✅ Created agent: {agent.id}")

        # Commit the changes
        await session.commit()

    return engine, async_session


async def test_api():
    """Test the list_agents API endpoint."""
    print("🧪 Testing list_agents API endpoint...\n")

    # Setup test database
    engine, async_session = await setup_test_db()

    try:
        # Create app with mock database dependency
        app = create_app()

        # Override the database dependency
        async def override_get_db_session():
            async with async_session() as session:
                yield session

        from api.config import get_db_session

        app.dependency_overrides[get_db_session] = override_get_db_session

        # Create test client
        client = TestClient(app)

        # Test: List agents
        print("Calling GET /api/agents...")
        response = client.get("/api/agents")

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            agents = response.json()
            print(f"\n✅ Success! Found {len(agents)} agents\n")

            if agents:
                print("Agents:")
                for i, agent in enumerate(agents, 1):
                    print(f"\n  {i}. {agent.get('name')} (ID: {agent.get('id')})")
                    print(f"     - AI Model: {agent.get('ai_model')}")
                    print(f"     - Status: {agent.get('status')}")
                    print(f"     - Current Funds: {agent.get('current_funds')}")
                    print(f"     - Investment Prefs: {agent.get('investment_preferences')}")
            else:
                print("⚠️  WARNING: No agents returned!")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        return len(agents) > 0

    finally:
        # Cleanup
        await engine.dispose()


async def main():
    """Main entry point."""
    success = await test_api()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
