"""
Manual diagnostic script to verify Unicode handling in session final_output.

Moved under tests/manual to keep manual checks co-located with other testing assets.
"""

import asyncio
import json

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.common.enums import AgentMode, SessionStatus
from src.database.models import Base
from src.service.session_service import AgentSessionService


async def test_chinese_output_storage() -> bool:
    """Ensure Chinese characters persist without unicode escape sequences."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        session_service = AgentSessionService(session)

        test_session = await session_service.create_session(
            agent_id="test_agent_001",
            mode=AgentMode.TRADING.value,
            initial_input={"test": "data"},
        )
        print(f"✅ Created session: {test_session.id}")

        final_output_with_chinese = {
            "summary": "摘要（500字內）— 投組檢視與重新平衡建議...",
            "trace_id": "trace_12345",
            "mode": "TRADING",
            "recommendations": [
                "買進 2330 台積電",
                "賣出 0050 台灣50",
                "持有 2308 台達電",
            ],
        }

        updated_session = await session_service.update_session_status(
            session_id=test_session.id,
            status=SessionStatus.COMPLETED,
            final_output=final_output_with_chinese,
        )

        print("✅ Updated session status to COMPLETED")
        print(f"✅ Stored final_output: {updated_session.final_output}")

        retrieved_session = await session_service.get_session(test_session.id)

        print("\n📋 Retrieved session from database:")
        print(f"   Session ID: {retrieved_session.id}")
        print(f"   Status: {retrieved_session.status}")
        print(f"   Final Output: {retrieved_session.final_output}")

        if retrieved_session.final_output:
            summary = retrieved_session.final_output.get("summary", "")
            print("\n✨ Summary (should contain Chinese characters):")
            print(f"   {summary}")

            if "\\u" in str(retrieved_session.final_output):
                print("\n❌ ERROR: Found Unicode escape sequences in stored data!")
                print(f"   Raw data: {json.dumps(retrieved_session.final_output)}")
                await engine.dispose()
                return False

            print("\n✅ PASS: Chinese characters stored correctly (no escape sequences)")
            await engine.dispose()
            return True

        print("\n❌ ERROR: final_output is None")
        await engine.dispose()
        return False


async def test_json_column_behavior() -> None:
    """Demonstrate JSON serialization differences for manual verification."""
    print("\n" + "=" * 60)
    print("Testing SQLAlchemy JSON Column Behavior")
    print("=" * 60 + "\n")

    test_data_string = "摘要（500字內）— 投組檢視與重新平衡建議..."
    test_data_dict = {
        "summary": test_data_string,
        "recommendations": ["買進 2330", "賣出 0050"],
    }

    print("Original string (should use dict, not string):")
    print(f"  Type: {type(test_data_string)}")
    print(f"  Value: {test_data_string}")

    print("\nRecommended dict format:")
    print(f"  Type: {type(test_data_dict)}")
    print(f"  Value: {test_data_dict}")

    json_str = json.dumps(test_data_dict, ensure_ascii=False)
    print("\nJSON serialized (ensure_ascii=False):")
    print(f"  {json_str}")

    json_str_escaped = json.dumps(test_data_dict, ensure_ascii=True)
    print("\nJSON serialized (ensure_ascii=True - problematic):")
    print(f"  {json_str_escaped}")


def main() -> None:
    """Entry point for manual execution."""
    print("=" * 60)
    print("Unicode Chinese Character Storage Test")
    print("=" * 60 + "\n")

    try:
        asyncio.run(test_json_column_behavior())
        success = asyncio.run(test_chinese_output_storage())

        if success:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ TESTS FAILED")
            print("=" * 60)
    except Exception as exc:  # noqa: BLE001 - manual diagnostic script
        print(f"\n❌ Test error: {exc}")


if __name__ == "__main__":
    main()
