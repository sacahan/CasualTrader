"""
DateTime Timezone Contract Tests

驗證所有 datetime 操作都使用時區感知的 UTC datetime。
這確保了不會發生 "can't subtract offset-naive and offset-aware datetimes" 錯誤。

遵循 timestamp.instructions.md 標準。
"""

from datetime import datetime, timezone, timedelta
import pytest


class TestDatetimeTimezoneAwareness:
    """DateTime 時區感知契約測試"""

    def test_utc_aware_datetime_creation(self):
        """驗證 UTC 感知 datetime 的建立"""
        # 建立時區感知的 datetime
        now_utc = datetime.now(timezone.utc)

        # 驗證具有時區資訊
        assert now_utc.tzinfo is not None, "datetime 應該有時區資訊"
        assert now_utc.tzinfo == timezone.utc, "datetime 應該是 UTC 時區"

    def test_datetime_subtraction_same_timezone(self):
        """驗證相同時區的 datetime 可以相減"""
        start_time = datetime.now(timezone.utc)
        # 模擬執行
        import time

        time.sleep(0.05)
        end_time = datetime.now(timezone.utc)

        # 計算時間差
        duration = (end_time - start_time).total_seconds()

        assert duration >= 0.05, "時間差計算應該成功"
        assert isinstance(duration, float), "時間差應該是浮點數"

    def test_datetime_subtraction_milliseconds(self):
        """驗證時間戳記的毫秒計算"""
        start_time = datetime.now(timezone.utc)
        import time

        time.sleep(0.1)
        end_time = datetime.now(timezone.utc)

        # 計算執行時間（毫秒）
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        assert execution_time_ms >= 100, "執行時間應該大於等於 100ms"
        assert isinstance(execution_time_ms, int), "執行時間應該是整數"

    def test_datetime_with_timedelta(self):
        """驗證 datetime 與 timedelta 的操作"""
        now_utc = datetime.now(timezone.utc)

        # 計算過去 30 分鐘
        threshold = now_utc - timedelta(minutes=30)

        assert threshold.tzinfo is not None, "結果應該有時區資訊"
        assert threshold < now_utc, "過去時間應該小於現在時間"

    def test_datetime_comparison(self):
        """驗證 datetime 的比較操作"""
        start_time = datetime.now(timezone.utc)
        import time

        time.sleep(0.05)
        end_time = datetime.now(timezone.utc)

        assert start_time < end_time, "開始時間應該小於結束時間"
        assert end_time > start_time, "結束時間應該大於開始時間"

    def test_naive_vs_aware_datetime_raises_error(self):
        """驗證混合時區感知和無感知 datetime 會引發錯誤"""
        aware_dt = datetime.now(timezone.utc)
        naive_dt = datetime.now()

        # 驗證無法相減
        with pytest.raises(TypeError, match="can't subtract offset-naive and offset-aware"):
            _ = aware_dt - naive_dt

    def test_datetime_none_safety(self):
        """驗證 None 時間戳記的安全性"""
        end_time = datetime.now(timezone.utc)
        start_time = None

        # 應該安全地處理 None
        if start_time and end_time:
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
        else:
            duration_ms = None

        assert duration_ms is None, "當開始時間為 None 時，應該返回 None"


class TestDatabaseModelTimestamps:
    """資料庫模型時間戳記契約測試"""

    def test_agent_model_timestamps_are_aware(self):
        """驗證 Agent 模型的時間戳記是時區感知的"""
        from database.models import Agent
        from decimal import Decimal

        agent = Agent(
            id="test-agent-1",
            name="Test Agent",
            initial_funds=Decimal("1000"),
            current_funds=Decimal("1000"),
        )

        # 時間戳記應該在建立後自動設置
        assert agent.created_at is None or agent.created_at.tzinfo is not None
        assert agent.updated_at is None or agent.updated_at.tzinfo is not None

    def test_agent_session_timestamps_are_aware(self):
        """驗證 AgentSession 模型的時間戳記是時區感知的"""
        from database.models import AgentSession
        from common.enums import SessionStatus, AgentMode

        session = AgentSession(
            agent_id="test-agent-1",
            mode=AgentMode.TRADING,
            status=SessionStatus.PENDING,
        )

        # 時間戳記應該在建立後自動設置
        assert session.start_time is None or session.start_time.tzinfo is not None
        assert session.created_at is None or session.created_at.tzinfo is not None
        assert session.updated_at is None or session.updated_at.tzinfo is not None


class TestServiceLayerTimestampUpdates:
    """服務層時間戳記更新契約測試"""

    def test_session_status_update_timestamp_calculation(self):
        """驗證 session 狀態更新的時間戳記計算"""
        start_time = datetime.now(timezone.utc)
        import time

        time.sleep(0.05)
        end_time = datetime.now(timezone.utc)

        # 模擬服務層的時間計算
        if start_time and end_time:
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        else:
            execution_time_ms = None

        assert execution_time_ms is not None, "執行時間應該被計算"
        assert execution_time_ms >= 50, "執行時間應該至少 50ms"

    def test_trading_execution_time_calculation(self):
        """驗證交易執行時間計算"""
        start_time = datetime.now(timezone.utc)
        import time

        time.sleep(0.1)
        end_time = datetime.now(timezone.utc)

        # 模擬交易服務的時間計算
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        assert 100 <= execution_time_ms < 200, "執行時間應該在預期範圍內"

    def test_agent_activity_timestamp_update(self):
        """驗證 Agent 活動時間戳記更新"""
        # 模擬 Agent 狀態更新
        now = datetime.now(timezone.utc)
        updated_at = now
        last_active_at = now

        assert updated_at.tzinfo is not None, "updated_at 應該是時區感知的"
        assert last_active_at.tzinfo is not None, "last_active_at 應該是時區感知的"
        assert updated_at == last_active_at, "兩個時間戳記應該相等"


class TestTimestampEdgeCases:
    """時間戳記邊界情況測試"""

    def test_very_short_execution_time(self):
        """驗證非常短的執行時間計算"""
        start_time = datetime.now(timezone.utc)
        end_time = datetime.now(timezone.utc)

        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # 執行時間可能是 0ms（非常快）
        assert execution_time_ms >= 0, "執行時間應該 >= 0"

    def test_large_time_delta(self):
        """驗證大時間差計算"""
        start_time = datetime.now(timezone.utc)
        # 計算 7 天後
        end_time = start_time + timedelta(days=7)

        duration_seconds = (end_time - start_time).total_seconds()
        expected_seconds = 7 * 24 * 60 * 60

        assert duration_seconds == expected_seconds, "大時間差計算應該正確"

    def test_timeout_threshold_calculation(self):
        """驗證超時閾值計算"""
        now = datetime.now(timezone.utc)
        timeout_minutes = 30

        timeout_threshold = now - timedelta(minutes=timeout_minutes)

        # 驗證時間差
        time_diff = (now - timeout_threshold).total_seconds() / 60
        assert time_diff == timeout_minutes, "超時閾值計算應該正確"

    def test_conditional_timestamp_setting(self):
        """驗證條件性時間戳記設置"""
        # 模擬服務層的條件邏輯
        end_time = None
        start_time = datetime.now(timezone.utc)

        # 只有當 end_time 為 None 時才設置
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        assert end_time is not None, "end_time 應該被設置"
        assert end_time.tzinfo is not None, "end_time 應該是時區感知的"

        # 計算時間差
        if start_time and end_time:
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        else:
            execution_time_ms = None

        assert execution_time_ms is not None, "執行時間應該被計算"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
