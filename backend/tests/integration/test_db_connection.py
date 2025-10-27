#!/usr/bin/env python3
"""
測試資料庫連線和基本查詢功能

用於驗證資料庫欄位和查詢功能
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# ruff: noqa: E402
from api.config import get_session_maker
from service.agents_service import AgentsService


async def test_list_agents():
    """Test listing agents from the database."""
    print("🧪 Testing Agent List API...")

    try:
        # Get database session
        session_maker = get_session_maker()
        async with session_maker() as session:
            # Create agents service
            agents_service = AgentsService(session)

            # List agents
            print("   Querying agents from database...")
            agents = await agents_service.list_agents()

            print(f"   ✅ Successfully retrieved {len(agents)} agents")

            if agents:
                print("\n   Agent details:")
                for agent in agents:
                    print(f"     - ID: {agent.id}")
                    print(f"       Name: {agent.name}")
                    print(f"       AI Model: {agent.ai_model}")
            else:
                print("   (No agents in database)")

            return True

    except Exception as e:
        print(f"   ❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    success = await test_list_agents()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
