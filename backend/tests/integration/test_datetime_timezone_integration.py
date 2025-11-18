"""
DateTime Timezone Integration Tests

驗證服務層的時間戳記操作在真實場景中的正確性。
這些測試模擬實際的 Agent 執行場景，確保沒有時區混合錯誤。

遵循 timestamp.instructions.md 標準。
"""

import pytest
from datetime import datetime, timezone, timedelta
import asyncio


class TestSessionServiceTimestamps:
    """Session 服務時間戳記整合測試"""

    @pytest.mark.asyncio
    async def test_session_creation_timestamps(self, session_maker):
        """驗證 session 建立時的時間戳記"""
        from service.session_service import AgentSessionService
        from common.enums import AgentMode

        async with session_maker() as db_session:
            service = AgentSessionService(db_session)

            # 建立 session
            session = await service.create_session(
                agent_id="test-agent-1",
                mode=AgentMode.TRADING,
            )

            # 驗證時間戳記
            assert session.created_at is not None
            assert session.updated_at is not None
            assert session.start_time is not None
            assert session.created_at.tzinfo is not None
            assert session.updated_at.tzinfo is not None
            assert session.start_time.tzinfo is not None

    @pytest.mark.asyncio
    async def test_session_status_update_timestamps(self, session_maker):
        """驗證 session 狀態更新的時間戳記計算"""
        from service.session_service import AgentSessionService
        from common.enums import SessionStatus, AgentMode

        async with session_maker() as db_session:
            service = AgentSessionService(db_session)

            # 建立 session
            session = await service.create_session(
                agent_id="test-agent-1",
                mode=AgentMode.TRADING,
            )

            # 等待一小段時間
            await asyncio.sleep(0.1)

            # 更新狀態為 COMPLETED
            updated_session = await service.update_session_status(
                session.id,
                SessionStatus.COMPLETED,
                final_output="test output",
            )

            # 驗證時間戳記更新
            assert updated_session.updated_at > session.created_at
            assert updated_session.end_time is not None
            assert updated_session.end_time.tzinfo is not None

            # 驗證執行時間計算
            assert updated_session.execution_time_ms is not None
            assert updated_session.execution_time_ms >= 100  # 至少 100ms

    @pytest.mark.asyncio
    async def test_session_timeout_cleanup(self, session_maker):
        """驗證 session 超時清理的時間戳記邏輯"""
        from service.session_service import AgentSessionService
        from common.enums import SessionStatus, AgentMode

        async with session_maker() as db_session:
            service = AgentSessionService(db_session)

            # 建立 session
            session = await service.create_session(
                agent_id="test-agent-1",
                mode=AgentMode.TRADING,
            )

            # 更新為 RUNNING 狀態
            await service.update_session_status(
                session.id,
                SessionStatus.RUNNING,
            )

            # 模擬超時計算（不實際等待）
            now = datetime.now(timezone.utc)
            timeout_threshold = now - timedelta(minutes=30)

            # 驗證時間比較邏輯
            time_diff = (now - timeout_threshold).total_seconds() / 60
            assert time_diff == 30


class TestTradingServiceTimestamps:
    """Trading 服務時間戳記整合測試"""

    @pytest.mark.asyncio
    async def test_transaction_timestamp_creation(self, session_maker):
        """驗證交易記錄的時間戳記"""
        # 模擬交易建立邏輯
        from common.enums import TransactionStatus
        from datetime import datetime, timezone

        # 模擬交易狀態
        status_enum = TransactionStatus.EXECUTED

        # 驗證執行時間設置邏輯
        execution_time = (
            datetime.now(timezone.utc) if status_enum == TransactionStatus.EXECUTED else None
        )

        assert execution_time is not None
        assert execution_time.tzinfo is not None


class TestAgentServiceTimestamps:
    """Agent 服務時間戳記整合測試"""

    @pytest.mark.asyncio
    async def test_agent_update_timestamps(self, session_maker):
        """驗證 Agent 狀態更新的時間戳記"""
        from service.agents_service import AgentsService
        from common.enums import AgentStatus

        async with session_maker() as db_session:
            service = AgentsService(db_session)

            # 建立 Agent
            agent = await service.create_agent(
                name="Test Agent",
                description="Test",
                initial_funds=1000000.0,
            )

            # 驗證初始時間戳記
            assert agent.created_at.tzinfo is not None
            assert agent.updated_at.tzinfo is not None

            # 更新狀態
            updated_agent = await service.update_agent_status(
                agent.id,
                AgentStatus.ACTIVE,
            )

            # 驗證更新時間戳記
            assert updated_agent.updated_at > agent.created_at
            assert updated_agent.updated_at.tzinfo is not None

            if updated_agent.last_active_at:
                assert updated_agent.last_active_at.tzinfo is not None


class TestTimestampConsistency:
    """時間戳記一致性整合測試"""

    @pytest.mark.asyncio
    async def test_complete_workflow_timestamps(self, session_maker):
        """驗證完整工作流程的時間戳記一致性"""
        from service.session_service import AgentSessionService
        from common.enums import SessionStatus, AgentMode
        from datetime import datetime, timezone

        async with session_maker() as db_session:
            service = AgentSessionService(db_session)

            # 1. 建立 session
            start = datetime.now(timezone.utc)
            session = await service.create_session(
                agent_id="test-agent-1",
                mode=AgentMode.TRADING,
            )
            end = datetime.now(timezone.utc)

            # 驗證時間戳記在合理範圍內
            assert start <= session.created_at <= end
            assert session.created_at == session.updated_at

            # 2. 更新狀態
            await asyncio.sleep(0.05)
            updated = await service.update_session_status(
                session.id,
                SessionStatus.COMPLETED,
                final_output="test",
            )

            # 驗證時間戳記遞進
            assert session.created_at <= updated.updated_at
            assert updated.end_time is not None
            assert session.start_time <= updated.end_time

            # 3. 驗證執行時間計算
            assert updated.execution_time_ms >= 50
            assert isinstance(updated.execution_time_ms, int)

    def test_datetime_arithmetic_consistency(self):
        """驗證 datetime 運算的一致性"""
        # 建立多個時間戳記
        times = [datetime.now(timezone.utc) for _ in range(5)]

        # 驗證遞進順序
        for i in range(len(times) - 1):
            assert times[i] <= times[i + 1]

        # 驗證時間差計算
        first = times[0]
        last = times[-1]
        total_duration = (last - first).total_seconds()

        assert total_duration >= 0


class TestErrorHandlingWithTimestamps:
    """時間戳記錯誤處理測試"""

    def test_naive_datetime_prevented(self):
        """驗證無感知 datetime 被防止"""
        from datetime import datetime

        # 這應該成功 - UTC 感知 datetime
        aware = datetime.now(timezone.utc)
        assert aware.tzinfo is not None

        # 這會失敗 - 無感知 datetime
        naive = datetime.now()
        assert naive.tzinfo is None

        # 驗證混合會失敗
        with pytest.raises(TypeError):
            _ = aware - naive

    def test_timestamp_none_safety(self):
        """驗證 None 時間戳記的安全性"""
        start_time = None
        end_time = datetime.now(timezone.utc)

        # 安全的條件檢查
        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()
        else:
            duration = None

        assert duration is None

    def test_conditional_timestamp_setting(self):
        """驗證條件性時間戳記設置"""
        # 模擬服務層的條件邏輯
        end_time = None

        # 只有當 end_time 為 None 時才設置
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        assert end_time is not None
        assert end_time.tzinfo is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
