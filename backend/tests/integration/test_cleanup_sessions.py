"""
測試 Session 清理功能

測試卡住的 session 清理邏輯
"""

import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from common.enums import SessionStatus
from database.models import AgentSession
from service.session_service import AgentSessionService


async def test_cleanup_stuck_sessions():
    """測試清理卡住的 session"""

    print("=" * 80)
    print("測試 Session 清理功能")
    print("=" * 80)
    print()

    # 1. 建立資料庫連接
    engine = create_async_engine(
        "sqlite+aiosqlite:///casualtrader.db",
        echo=False,
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as db_session:
        session_service = AgentSessionService(db_session)

        # 2. 查詢當前 RUNNING 狀態的 session
        print("📊 查詢當前 RUNNING 狀態的 session...")
        stmt = (
            select(AgentSession)
            .where(AgentSession.status == SessionStatus.RUNNING)
            .order_by(AgentSession.start_time.desc())
        )
        result = await db_session.execute(stmt)
        running_sessions = list(result.scalars().all())

        print(f"   找到 {len(running_sessions)} 個 RUNNING session\n")

        for session in running_sessions:
            duration = (datetime.now() - session.start_time).total_seconds()
            print(f"   Session ID: {session.id}")
            print(f"   Agent ID: {session.agent_id}")
            print(f"   Start Time: {session.start_time}")
            print(f"   Duration: {duration:.0f} seconds ({duration / 60:.1f} minutes)")
            print()

        if not running_sessions:
            print("   ✅ 沒有 RUNNING 狀態的 session\n")
            return

        # 3. 執行清理（超過 1 分鐘的 session）
        print("🧹 執行清理（超時閾值: 1 分鐘）...")
        agent_id = running_sessions[0].agent_id
        cleaned_ids = await session_service.cleanup_stuck_sessions(
            agent_id=agent_id,
            timeout_minutes=1,  # 測試用，設為 1 分鐘
        )

        print(f"   清理完成！共清理 {len(cleaned_ids)} 個 session")
        for sid in cleaned_ids:
            print(f"   - {sid}")
        print()

        # 4. 驗證清理結果
        print("✅ 驗證清理結果...")
        stmt = select(AgentSession).where(AgentSession.id.in_(cleaned_ids))
        result = await db_session.execute(stmt)
        cleaned_sessions = list(result.scalars().all())

        for session in cleaned_sessions:
            print(f"   Session {session.id}:")
            print(f"   - Status: {session.status.value}")
            print(f"   - Error: {session.error_message}")
            print()


if __name__ == "__main__":
    asyncio.run(test_cleanup_stuck_sessions())
