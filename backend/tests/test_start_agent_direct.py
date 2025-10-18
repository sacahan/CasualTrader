"""
直接測試 Agent 啟動功能

不需要 API Server，直接測試內部邏輯
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from common.logger import logger
from service.agent_executor import AgentExecutor
from api.websocket import WebSocketManager
from api.config import Settings


TEST_AGENT_ID = "agent-f11318ac"


async def main():
    """主測試函數"""
    logger.info("=" * 80)
    logger.info("直接測試 Agent 啟動功能")
    logger.info("=" * 80)

    # 1. 初始化數據庫
    logger.info("\n[步驟 1] 初始化數據庫連接")
    engine = create_async_engine(
        "sqlite+aiosqlite:///casualtrader.db",
        echo=False,
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    logger.success("✅ 數據庫連接已建立")

    # 2. 初始化 WebSocket Manager
    logger.info("\n[步驟 2] 初始化 WebSocket Manager")
    websocket_manager = WebSocketManager()
    await websocket_manager.startup()
    logger.success("✅ WebSocket Manager 已初始化")

    # 3. 初始化設定
    logger.info("\n[步驟 3] 載入設定")
    settings = Settings()
    logger.info(f"循環間隔: {settings.default_cycle_interval_minutes} 分鐘")
    logger.info(f"跳過市場檢查: {settings.skip_market_check}")
    logger.success("✅ 設定已載入")

    # 4. 初始化 AgentExecutor
    logger.info("\n[步驟 4] 初始化 AgentExecutor")
    executor = AgentExecutor(
        session_maker=session_maker,
        websocket_manager=websocket_manager,
        settings=settings,
    )
    logger.success("✅ AgentExecutor 已初始化")

    # 5. 檢查 Agent 是否存在
    logger.info(f"\n[步驟 5] 檢查 Agent {TEST_AGENT_ID} 是否存在")
    async with session_maker() as session:
        from service.agents_service import AgentsService

        agents_service = AgentsService(session)

        try:
            agent = await agents_service.get_agent_config(TEST_AGENT_ID)
            logger.success(f"✅ Agent {TEST_AGENT_ID} 存在")
            logger.info(f"   名稱: {agent.name}")
            logger.info(f"   狀態: {agent.status}")
            logger.info(f"   模式: {agent.current_mode}")
        except Exception as e:
            logger.error(f"❌ Agent {TEST_AGENT_ID} 不存在: {e}")
            logger.error("請先創建此 Agent 再進行測試")
            await websocket_manager.shutdown()
            await engine.dispose()
            return

    # 6. 嘗試啟動 Agent
    logger.info(f"\n[步驟 6] 嘗試啟動 Agent {TEST_AGENT_ID}")
    try:
        await executor.start(TEST_AGENT_ID, interval_minutes=1)
        logger.success(f"✅ Agent {TEST_AGENT_ID} 啟動成功")

        # 7. 檢查運行狀態
        logger.info("\n[步驟 7] 檢查 Agent 運行狀態")
        await asyncio.sleep(2)  # 等待後台任務啟動

        status = executor.get_status(TEST_AGENT_ID)
        logger.info("運行狀態:")
        logger.info(f"   is_running: {status['is_running']}")
        logger.info(f"   current_mode: {status['current_mode']}")
        logger.info(f"   cycle_count: {status['cycle_count']}")
        logger.info(f"   interval_minutes: {status['interval_minutes']}")
        logger.info(f"   last_cycle_at: {status['last_cycle_at']}")

        if status["is_running"]:
            logger.success("✅ Agent 確認正在運行中")
        else:
            logger.warning("⚠️ Agent 未在運行中")

        # 8. 監控執行 10 秒
        logger.info("\n[步驟 8] 監控 Agent 執行過程 (10 秒)")
        for i in range(5):
            await asyncio.sleep(2)
            status = executor.get_status(TEST_AGENT_ID)
            logger.info(
                f"[{i + 1}/5] "
                f"模式: {status.get('current_mode')}, "
                f"循環次數: {status.get('cycle_count')}"
            )

        # 9. 停止 Agent
        logger.info(f"\n[步驟 9] 停止 Agent {TEST_AGENT_ID}")
        await executor.stop(TEST_AGENT_ID)
        logger.success(f"✅ Agent {TEST_AGENT_ID} 已停止")

        # 10. 驗證停止狀態
        logger.info("\n[步驟 10] 驗證停止狀態")
        await asyncio.sleep(1)
        status = executor.get_status(TEST_AGENT_ID)
        if not status["is_running"]:
            logger.success("✅ Agent 確認已停止")
        else:
            logger.error("❌ Agent 仍在運行中")

    except Exception as e:
        logger.error("\n❌ 啟動 Agent 時發生錯誤:")
        logger.error(f"   錯誤類型: {type(e).__name__}")
        logger.error(f"   錯誤訊息: {str(e)}")
        logger.exception(e)

        # 診斷錯誤
        logger.info("\n[診斷] 分析錯誤原因")

        # 檢查是否是找不到 Agent
        if "not found" in str(e).lower():
            logger.error("診斷結果: Agent 不存在")
            logger.error("解決方案: 請先使用 API 或管理工具創建 Agent")

        # 檢查是否是已經在運行
        elif "already running" in str(e).lower():
            logger.error("診斷結果: Agent 已經在運行中")
            logger.error("解決方案: 先停止 Agent 再重新啟動")

        # 其他錯誤
        else:
            logger.error("診斷結果: 未知錯誤")
            logger.error("建議: 查看完整的堆疊追蹤來定位問題")

    finally:
        # 清理資源
        logger.info("\n[清理] 關閉資源")
        await websocket_manager.shutdown()
        await engine.dispose()
        logger.success("✅ 資源已清理")

    logger.info("\n" + "=" * 80)
    logger.info("測試完成")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
