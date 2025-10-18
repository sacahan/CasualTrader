"""
E2E 測試：啟動 Agent 循環執行

測試使用 agent_id = agent-f11318ac 啟動 trade agent 的完整流程
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from httpx import AsyncClient

from api.app import create_app
from common.logger import logger


# ==========================================
# 測試配置
# ==========================================

TEST_AGENT_ID = "agent-f11318ac"
TEST_INTERVAL_MINUTES = 1  # 使用較短的間隔進行測試


# ==========================================
# Fixtures
# ==========================================


@pytest.fixture
async def async_client():
    """創建測試用的 async HTTP client"""
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ==========================================
# 測試案例
# ==========================================


class TestStartAgentE2E:
    """E2E 測試：啟動 Agent"""

    @pytest.mark.asyncio
    async def test_01_check_agent_exists(self, async_client: AsyncClient):
        """
        測試 1：檢查 Agent 是否存在

        目的：確認 agent-f11318ac 存在於系統中
        """
        logger.info(f"[測試 1] 檢查 Agent {TEST_AGENT_ID} 是否存在")

        response = await async_client.get(f"/api/v1/agents/{TEST_AGENT_ID}")

        logger.info(f"HTTP 狀態碼: {response.status_code}")
        logger.info(f"響應內容: {response.json()}")

        # 驗證
        if response.status_code == 404:
            logger.error(f"❌ Agent {TEST_AGENT_ID} 不存在")
            pytest.fail(f"Agent {TEST_AGENT_ID} 不存在，請先創建此 Agent")

        assert response.status_code == 200, f"預期狀態碼 200，實際: {response.status_code}"

        data = response.json()
        assert data["agent_id"] == TEST_AGENT_ID
        logger.success(f"✅ Agent {TEST_AGENT_ID} 存在")

    @pytest.mark.asyncio
    async def test_02_check_initial_status(self, async_client: AsyncClient):
        """
        測試 2：檢查 Agent 初始狀態

        目的：確認 Agent 當前狀態，是否已在運行中
        """
        logger.info(f"[測試 2] 檢查 Agent {TEST_AGENT_ID} 初始狀態")

        response = await async_client.get(f"/api/v1/agent-execution/{TEST_AGENT_ID}/status")

        logger.info(f"HTTP 狀態碼: {response.status_code}")
        logger.info(f"響應內容: {response.json()}")

        # 驗證
        assert response.status_code == 200, f"預期狀態碼 200，實際: {response.status_code}"

        data = response.json()
        logger.info(f"Agent 狀態: {data['status']}")
        logger.info(f"是否運行中: {data['is_running']}")
        logger.info(f"是否已初始化: {data['is_initialized']}")

        # 如果已在運行中，先停止
        if data["is_running"]:
            logger.warning("⚠️ Agent 已在運行中，先停止")
            await self._stop_agent(async_client)

    @pytest.mark.asyncio
    async def test_03_start_agent(self, async_client: AsyncClient):
        """
        測試 3：啟動 Agent

        目的：呼叫 start_agent API 啟動循環執行
        """
        logger.info(f"[測試 3] 啟動 Agent {TEST_AGENT_ID}")

        # 發送啟動請求
        response = await async_client.post(
            f"/api/v1/agent-execution/{TEST_AGENT_ID}/start",
            params={"interval_minutes": TEST_INTERVAL_MINUTES},
        )

        logger.info(f"HTTP 狀態碼: {response.status_code}")
        logger.info(f"響應內容: {response.json()}")

        # 驗證
        if response.status_code != 200:
            logger.error(f"❌ 啟動失敗: {response.json()}")
            pytest.fail(f"啟動 Agent 失敗: {response.json()}")

        assert response.status_code == 200, f"預期狀態碼 200，實際: {response.status_code}"

        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == TEST_AGENT_ID
        assert data["status"] == "running"
        assert data["interval_minutes"] == TEST_INTERVAL_MINUTES

        logger.success(f"✅ Agent {TEST_AGENT_ID} 啟動成功")

    @pytest.mark.asyncio
    async def test_04_verify_running_status(self, async_client: AsyncClient):
        """
        測試 4：驗證運行狀態

        目的：確認 Agent 確實在運行中
        """
        logger.info(f"[測試 4] 驗證 Agent {TEST_AGENT_ID} 運行狀態")

        # 等待一小段時間讓後台任務啟動
        await asyncio.sleep(2)

        response = await async_client.get(f"/api/v1/agent-execution/{TEST_AGENT_ID}/status")

        logger.info(f"HTTP 狀態碼: {response.status_code}")
        logger.info(f"響應內容: {response.json()}")

        # 驗證
        assert response.status_code == 200

        data = response.json()
        assert data["is_running"] is True, "Agent 應該在運行中"
        assert data["interval_minutes"] == TEST_INTERVAL_MINUTES

        logger.success(f"✅ Agent {TEST_AGENT_ID} 確認運行中")
        logger.info(f"當前執行階段: {data.get('current_mode')}")
        logger.info(f"已完成循環次數: {data.get('cycle_count')}")

    @pytest.mark.asyncio
    async def test_05_monitor_execution(self, async_client: AsyncClient):
        """
        測試 5：監控執行過程

        目的：觀察 Agent 執行一段時間，確認循環正常運作
        """
        logger.info(f"[測試 5] 監控 Agent {TEST_AGENT_ID} 執行過程")

        # 監控 10 秒，每 2 秒檢查一次狀態
        for i in range(5):
            await asyncio.sleep(2)

            response = await async_client.get(f"/api/v1/agent-execution/{TEST_AGENT_ID}/status")

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"[{i + 1}/5] "
                    f"狀態: {data['status']}, "
                    f"執行階段: {data.get('current_mode')}, "
                    f"循環次數: {data.get('cycle_count')}, "
                    f"上次循環: {data.get('last_cycle_at')}"
                )
            else:
                logger.warning(f"無法取得狀態: {response.status_code}")

        logger.success("✅ 監控完成")

    @pytest.mark.asyncio
    async def test_06_check_execution_history(self, async_client: AsyncClient):
        """
        測試 6：檢查執行歷史

        目的：確認執行記錄被正確保存
        """
        logger.info(f"[測試 6] 檢查 Agent {TEST_AGENT_ID} 執行歷史")

        response = await async_client.get(
            f"/api/v1/agent-execution/{TEST_AGENT_ID}/history",
            params={"limit": 10},
        )

        logger.info(f"HTTP 狀態碼: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info(f"總會話數: {data['total_sessions']}")
            logger.info(f"返回會話數: {data['returned_sessions']}")

            if data["sessions"]:
                logger.info("最近的會話:")
                for session in data["sessions"][:3]:
                    logger.info(
                        f"  - {session['session_id']}: "
                        f"模式={session['mode']}, "
                        f"狀態={session['status']}, "
                        f"開始時間={session['start_time']}"
                    )
            else:
                logger.warning("⚠️ 尚無執行歷史（可能循環尚未完成第一次執行）")
        else:
            logger.warning(f"無法取得執行歷史: {response.json()}")

    @pytest.mark.asyncio
    async def test_07_stop_agent(self, async_client: AsyncClient):
        """
        測試 7：停止 Agent

        目的：正常停止 Agent 循環執行
        """
        logger.info(f"[測試 7] 停止 Agent {TEST_AGENT_ID}")

        response = await async_client.post(f"/api/v1/agent-execution/{TEST_AGENT_ID}/stop")

        logger.info(f"HTTP 狀態碼: {response.status_code}")
        logger.info(f"響應內容: {response.json()}")

        # 驗證
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == TEST_AGENT_ID
        assert data["status"] == "stopped"

        logger.success(f"✅ Agent {TEST_AGENT_ID} 已停止")

    @pytest.mark.asyncio
    async def test_08_verify_stopped_status(self, async_client: AsyncClient):
        """
        測試 8：驗證停止狀態

        目的：確認 Agent 確實已停止
        """
        logger.info(f"[測試 8] 驗證 Agent {TEST_AGENT_ID} 停止狀態")

        # 等待一小段時間讓後台任務完全停止
        await asyncio.sleep(1)

        response = await async_client.get(f"/api/v1/agent-execution/{TEST_AGENT_ID}/status")

        logger.info(f"HTTP 狀態碼: {response.status_code}")
        logger.info(f"響應內容: {response.json()}")

        # 驗證
        assert response.status_code == 200

        data = response.json()
        assert data["is_running"] is False, "Agent 應該已停止"

        logger.success(f"✅ Agent {TEST_AGENT_ID} 確認已停止")

    # ==========================================
    # 輔助方法
    # ==========================================

    async def _stop_agent(self, async_client: AsyncClient):
        """停止 Agent（輔助方法）"""
        response = await async_client.post(f"/api/v1/agent-execution/{TEST_AGENT_ID}/stop")
        if response.status_code == 200:
            logger.success(f"✅ 已停止 Agent {TEST_AGENT_ID}")
        else:
            logger.error(f"❌ 停止失敗: {response.json()}")


# ==========================================
# 錯誤診斷測試
# ==========================================


class TestErrorDiagnosis:
    """錯誤診斷測試"""

    @pytest.mark.asyncio
    async def test_diagnose_start_error(self, async_client: AsyncClient):
        """
        診斷測試：分析啟動錯誤

        目的：捕獲並分析啟動過程中的錯誤
        """
        logger.info("[診斷] 分析啟動錯誤")

        try:
            # 嘗試啟動
            response = await async_client.post(
                f"/api/v1/agent-execution/{TEST_AGENT_ID}/start",
                params={"interval_minutes": TEST_INTERVAL_MINUTES},
            )

            if response.status_code != 200:
                error_data = response.json()
                logger.error("❌ 啟動錯誤:")
                logger.error(f"  - 狀態碼: {response.status_code}")
                logger.error(f"  - 錯誤訊息: {error_data.get('detail')}")

                # 分析可能的原因
                if response.status_code == 404:
                    logger.error("  - 原因: Agent 不存在")
                    logger.error("  - 解決方案: 確認 Agent ID 是否正確，或先創建此 Agent")

                elif response.status_code == 409:
                    logger.error("  - 原因: Agent 已在運行中")
                    logger.error("  - 解決方案: 先停止 Agent 再重新啟動")

                elif response.status_code == 500:
                    logger.error("  - 原因: 內部伺服器錯誤")
                    logger.error("  - 解決方案: 檢查後端日誌獲取詳細錯誤資訊")

                    # 嘗試取得更多診斷資訊
                    await self._diagnose_server_error(async_client)

            else:
                logger.success("✅ 啟動成功，無錯誤")

        except Exception as e:
            logger.error(f"❌ 測試過程發生異常: {e}")
            logger.exception(e)

    async def _diagnose_server_error(self, async_client: AsyncClient):
        """診斷伺服器錯誤（輔助方法）"""
        logger.info("[診斷] 嘗試取得更多診斷資訊")

        # 檢查 Agent 狀態
        try:
            response = await async_client.get(f"/api/v1/agent-execution/{TEST_AGENT_ID}/status")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Agent 狀態: {data['status']}")
                logger.info(f"是否初始化: {data['is_initialized']}")
                logger.info(f"當前會話: {data.get('current_session_id')}")
            else:
                logger.warning("無法取得 Agent 狀態")
        except Exception as e:
            logger.error(f"取得狀態時發生錯誤: {e}")


# ==========================================
# 直接執行測試（不使用 pytest）
# ==========================================


async def run_manual_test():
    """手動執行測試（不依賴 pytest）"""
    logger.info("=" * 80)
    logger.info("開始手動 E2E 測試")
    logger.info("=" * 80)

    # 使用實際的 API server
    base_url = "http://localhost:8000"
    logger.info(f"連接到 API Server: {base_url}")
    logger.info("請確認 API Server 已啟動 (python backend/run_server.py)")
    logger.info("")

    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        test = TestStartAgentE2E()

        try:
            logger.info("\n" + "=" * 80)
            await test.test_01_check_agent_exists(client)

            logger.info("\n" + "=" * 80)
            await test.test_02_check_initial_status(client)

            logger.info("\n" + "=" * 80)
            await test.test_03_start_agent(client)

            logger.info("\n" + "=" * 80)
            await test.test_04_verify_running_status(client)

            logger.info("\n" + "=" * 80)
            await test.test_05_monitor_execution(client)

            logger.info("\n" + "=" * 80)
            await test.test_06_check_execution_history(client)

            logger.info("\n" + "=" * 80)
            await test.test_07_stop_agent(client)

            logger.info("\n" + "=" * 80)
            await test.test_08_verify_stopped_status(client)

            logger.info("\n" + "=" * 80)
            logger.success("✅ 所有測試完成")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"\n❌ 測試失敗: {e}")
            logger.exception(e)

            # 執行錯誤診斷
            logger.info("\n" + "=" * 80)
            logger.info("執行錯誤診斷")
            logger.info("=" * 80)
            diagnosis = TestErrorDiagnosis()
            await diagnosis.test_diagnose_start_error(client)


if __name__ == "__main__":
    # 直接執行測試
    asyncio.run(run_manual_test())
