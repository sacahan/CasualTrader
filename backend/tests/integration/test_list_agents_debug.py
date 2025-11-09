#!/usr/bin/env python3
"""
Debug test for list_agents API endpoint

診斷 list_agents 為什麼可能返回空值
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# ruff: noqa: E402
from api.config import get_session_maker
from service.agents_service import AgentsService


async def test_create_and_list():
    """Test creating an agent and then listing it."""
    print("🧪 Testing Create and List Agents...\n")

    try:
        # Get database session
        session_maker = get_session_maker()

        async with session_maker() as session:
            agents_service = AgentsService(session)

            # Step 1: Create an agent
            print("1️⃣  Creating a test agent...")
            agent = await agents_service.create_agent(
                name="Test Agent 1",
                description="First test agent",
                ai_model="gpt-4o-mini",
                initial_funds=Decimal("100000"),
                color_theme="34, 197, 94",
                investment_preferences=["2330", "0050"],
            )
            print(f"   ✅ Agent created with ID: {agent.id}")

            # Commit the transaction
            await session.commit()
            print("   ✅ Changes committed to database")

            # Step 2: List agents
            print("\n2️⃣  Listing all agents...")
            agents = await agents_service.list_agents()
            print(f"   ✅ Found {len(agents)} agents")

            if agents:
                print("\n   Agent details:")
                for agent in agents:
                    print(f"     - ID: {agent.id}")
                    print(f"       Name: {agent.name}")
                    print(f"       AI Model: {agent.ai_model}")
                    print(f"       Status: {agent.status}")
            else:
                print("   ⚠️  WARNING: No agents found!")

            # Step 3: Create another agent to confirm
            print("\n3️⃣  Creating another test agent...")
            agent2 = await agents_service.create_agent(
                name="Test Agent 2",
                description="Second test agent",
                ai_model="gpt-4o",
                initial_funds=Decimal("50000"),
                color_theme="239, 68, 68",
                investment_preferences=["2454"],
            )
            print(f"   ✅ Second agent created with ID: {agent2.id}")

            await session.commit()
            print("   ✅ Changes committed to database")

            # Step 4: List agents again
            print("\n4️⃣  Listing agents again...")
            agents = await agents_service.list_agents()
            print(f"   ✅ Found {len(agents)} agents")

            if agents:
                print("\n   All agents:")
                for i, agent in enumerate(agents, 1):
                    print(f"     {i}. {agent.name} (ID: {agent.id})")
            else:
                print("   ⚠️  WARNING: Still no agents found!")

            return len(agents) > 0

    except Exception as e:
        print(f"   ❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    success = await test_create_and_list()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
