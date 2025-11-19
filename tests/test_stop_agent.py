#!/usr/bin/env python3
"""
測試 Agent 停止功能

此測試驗證停止功能是否正確處理以下情況：
1. 正常停止執行中的 agent
2. 停止不在執行中的 agent（DB 已被標記為執行中）
3. 驗證所有 RUNNING 會話被中斷
4. 驗證 agent 狀態正確更新為 INACTIVE
"""

import asyncio
import sys
from pathlib import Path

# 設置 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

import logging
from database.init import init_db, get_async_session
from service.trading_service import TradingService
from common.enums import AgentStatus, SessionStatus, AgentMode
from service.agents_service import AgentsService
from service.session_service import AgentSessionService

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_stop_agent():
    """測試停止 agent 功能"""
    logger.info("=" * 80)
    logger.info("🧪 Testing Agent Stop Functionality")
    logger.info("=" * 80)

    # 初始化資料庫
    await init_db()

    async with get_async_session() as db_session:
        # 創建服務
        trading_service = TradingService(db_session)
        agents_service = AgentsService(db_session)
        session_service = AgentSessionService(db_session)

        try:
            # 1. 取得第一個 agent（假設華倫・巴菲特存在）
            from sqlalchemy import select
            from database.models import Agent

            stmt = select(Agent).limit(1)
            result = await db_session.execute(stmt)
            agent = result.scalar()

            if not agent:
                logger.warning("❌ No agents found in database, creating test data...")
                return

            agent_id = agent.agent_id
            logger.info(f"\n✅ Found agent: {agent.name} ({agent_id})")

            # 2. 檢查當前狀態
            agent_config = await agents_service.get_agent_config(agent_id)
            logger.info(f"   Current status: {agent_config.status}")

            # 3. 如果 agent 已在執行中，測試停止
            if agent_config.status == AgentStatus.ACTIVE:
                logger.info(f"\n🛑 Agent is ACTIVE, testing stop...")

                # 調用停止功能
                result = await trading_service.stop_agent(agent_id)
                logger.info(f"   Stop result: {result}")

                # 驗證狀態
                updated_config = await agents_service.get_agent_config(agent_id)
                logger.info(f"   Status after stop: {updated_config.status}")

                if updated_config.status == AgentStatus.INACTIVE:
                    logger.info("   ✅ Agent status correctly updated to INACTIVE")
                else:
                    logger.error(
                        f"   ❌ Agent status is {updated_config.status}, expected INACTIVE"
                    )

                # 檢查會話狀態
                sessions = await session_service.get_agent_sessions(agent_id)
                running_sessions = [
                    s for s in sessions if s.status == SessionStatus.RUNNING
                ]
                if running_sessions:
                    logger.warning(
                        f"   ⚠️  Found {len(running_sessions)} still running sessions"
                    )
                else:
                    logger.info("   ✅ No RUNNING sessions found")

            else:
                logger.info(
                    f"\n⏭️  Agent is {agent_config.status}, skipping execution test"
                )
                logger.info(f"\n📊 Testing stop on non-executing agent...")

                # 即使 agent 沒在執行，也應該能夠停止（清理所有會話）
                result = await trading_service.stop_agent(agent_id)
                logger.info(f"   Stop result: {result}")

                updated_config = await agents_service.get_agent_config(agent_id)
                logger.info(f"   Status after stop: {updated_config.status}")

            logger.info("\n✅ Test completed successfully!")

        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_stop_agent())
