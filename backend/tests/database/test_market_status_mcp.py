"""
MarketStatusChecker MCP 整合測試
測試動態查詢交易日和假日的功能
"""

import asyncio
from datetime import datetime

from src.agents.functions.market_status import MarketStatusChecker


class MockMCPClient:
    """模擬 MCP 客戶端"""

    def __init__(self, holidays: dict[str, str] | None = None):
        """
        初始化模擬客戶端

        Args:
            holidays: 假日字典 {日期: 假日名稱}
        """
        self.holidays = holidays or {
            "2025-01-01": "元旦",
            "2025-10-10": "國慶日",
            "2025-10-11": "國慶補假",
        }

    async def check_trading_day(self, date: str) -> dict:
        """模擬 check_taiwan_trading_day"""
        dt = datetime.strptime(date, "%Y-%m-%d")
        is_weekend = dt.weekday() >= 5
        is_holiday = date in self.holidays

        return {
            "success": True,
            "data": {
                "date": date,
                "is_trading_day": not (is_weekend or is_holiday),
                "is_weekend": is_weekend,
                "is_holiday": is_holiday,
            },
        }

    async def get_holiday_info(self, date: str) -> dict:
        """模擬 get_taiwan_holiday_info"""
        if date in self.holidays:
            return {
                "success": True,
                "data": {
                    "date": date,
                    "is_holiday": True,
                    "name": self.holidays[date],
                    "holiday_category": "national",
                },
            }
        else:
            return {
                "success": True,
                "data": {
                    "date": date,
                    "is_holiday": False,
                },
            }


class TestMarketStatusCheckerWithMCP:
    """測試 MarketStatusChecker 與 MCP 工具的整合"""

    async def test_basic_functionality_without_mcp(self):
        """測試沒有 MCP 工具時的基本功能 (fallback)"""
        checker = MarketStatusChecker()
        status = await checker.get_market_status()

        assert status is not None
        assert isinstance(status.is_open, bool)
        assert status.timezone == "Asia/Taipei"

    async def test_with_mcp_tools(self):
        """測試整合 MCP 工具"""
        mock_client = MockMCPClient()

        checker = MarketStatusChecker(
            mcp_check_trading_day=mock_client.check_trading_day,
            mcp_get_holiday_info=mock_client.get_holiday_info,
        )

        # 測試工作日
        test_date = datetime(2025, 10, 7)  # 週二
        status = await checker.get_market_status(test_date)

        assert status is not None
        assert status.market_date == "2025-10-07"

    async def test_holiday_detection(self):
        """測試假日偵測"""
        mock_client = MockMCPClient()

        checker = MarketStatusChecker(
            mcp_check_trading_day=mock_client.check_trading_day,
            mcp_get_holiday_info=mock_client.get_holiday_info,
        )

        # 測試國慶日 (假日)
        test_date = datetime(2025, 10, 10, 10, 0)  # 週五,但是假日
        status = await checker.get_market_status(test_date)

        # 即使在交易時段內,假日也不應開盤
        assert not status.is_open

    async def test_weekend_detection(self):
        """測試週末偵測"""
        mock_client = MockMCPClient()

        checker = MarketStatusChecker(
            mcp_check_trading_day=mock_client.check_trading_day,
            mcp_get_holiday_info=mock_client.get_holiday_info,
        )

        # 測試週六
        test_date = datetime(2025, 10, 11, 10, 0)  # 週六
        status = await checker.get_market_status(test_date)

        assert not status.is_open

    async def test_trading_hours_on_valid_day(self):
        """測試正常交易日的交易時段"""
        mock_client = MockMCPClient(holidays={})  # 沒有假日

        checker = MarketStatusChecker(
            mcp_check_trading_day=mock_client.check_trading_day,
            mcp_get_holiday_info=mock_client.get_holiday_info,
        )

        # 測試週二上午盤 (09:30)
        test_date = datetime(2025, 10, 7, 9, 30)
        status = await checker.get_market_status(test_date)

        assert status.is_open
        assert status.current_session == "morning_session"

        # 測試週二午休時間 (12:30)
        test_date = datetime(2025, 10, 7, 12, 30)
        status = await checker.get_market_status(test_date)

        assert not status.is_open
        assert status.current_session == "lunch_break"

    async def test_market_calendar_integration(self):
        """測試交易日曆整合"""
        mock_client = MockMCPClient()

        checker = MarketStatusChecker(
            mcp_check_trading_day=mock_client.check_trading_day,
            mcp_get_holiday_info=mock_client.get_holiday_info,
        )

        # 取得 2025 年 10 月 1-15 日的日曆
        calendar = await checker.get_market_calendar("2025-10-01", "2025-10-15")

        assert calendar is not None
        assert "trading_days" in calendar
        assert "non_trading_days" in calendar
        assert calendar["total_days"] == 15

        # 檢查國慶日是否被標記為非交易日
        non_trading_dates = [day["date"] for day in calendar["non_trading_days"]]
        assert "2025-10-10" in non_trading_dates
        assert "2025-10-11" in non_trading_dates  # 週六

    async def test_holiday_cache(self):
        """測試假日快取機制"""
        mock_client = MockMCPClient()

        checker = MarketStatusChecker(
            mcp_check_trading_day=mock_client.check_trading_day,
            mcp_get_holiday_info=mock_client.get_holiday_info,
        )

        # 第一次查詢
        holiday1 = await checker._get_holiday_info("2025-10-10")
        assert holiday1 is not None
        assert holiday1.name == "國慶日"

        # 第二次查詢 (應該使用快取)
        holiday2 = await checker._get_holiday_info("2025-10-10")
        assert holiday2 is not None
        assert holiday2.name == "國慶日"

        # 清除快取
        checker.clear_holiday_cache()

        # 快取清除後再次查詢
        holiday3 = await checker._get_holiday_info("2025-10-10")
        assert holiday3 is not None

    async def test_mcp_failure_fallback(self):
        """測試 MCP 呼叫失敗時的 fallback 機制"""

        async def failing_check_trading_day(date: str) -> dict:
            """總是失敗的 MCP 呼叫"""
            return {"success": False, "error": "Connection failed"}

        checker = MarketStatusChecker(
            mcp_check_trading_day=failing_check_trading_day,
        )

        # 即使 MCP 失敗,也應該能正常運作 (fallback 到基本邏輯)
        test_date = datetime(2025, 10, 7, 10, 0)  # 週二
        status = await checker.get_market_status(test_date)

        assert status is not None
        # fallback 會使用基本的週末判斷
        # 週二應該被認為是交易日

    async def test_trading_sessions_info(self):
        """測試交易時段資訊"""
        checker = MarketStatusChecker()

        sessions_info = checker.get_trading_sessions_info()

        assert "trading_sessions" in sessions_info
        assert "timezone" in sessions_info
        assert sessions_info["timezone"] == "Asia/Taipei"

        # 檢查各個時段是否定義正確
        sessions = sessions_info["trading_sessions"]
        assert "morning_session" in sessions
        assert "afternoon_session" in sessions
        assert sessions["morning_session"]["is_trading"] is True
        assert sessions["lunch_break"]["is_trading"] is False


def run_tests():
    """執行所有測試"""
    # 當安裝了 pytest 時才使用
    try:
        import pytest

        pytest.main([__file__, "-v", "-s"])
    except ImportError:
        print("pytest not installed, use: python -m test_market_status_mcp")


if __name__ == "__main__":
    # 執行單個測試範例
    async def main():
        test_suite = TestMarketStatusCheckerWithMCP()

        print("測試基本功能 (無 MCP)...")
        await test_suite.test_basic_functionality_without_mcp()
        print("✓ 通過\n")

        print("測試 MCP 整合...")
        await test_suite.test_with_mcp_tools()
        print("✓ 通過\n")

        print("測試假日偵測...")
        await test_suite.test_holiday_detection()
        print("✓ 通過\n")

        print("測試交易日曆整合...")
        await test_suite.test_market_calendar_integration()
        print("✓ 通過\n")

        print("測試假日快取...")
        await test_suite.test_holiday_cache()
        print("✓ 通過\n")

        print("所有測試通過!")

    asyncio.run(main())
