"""
MarketStatusChecker MCP 整合簡單測試
"""

import asyncio
import importlib.util
import sys
from datetime import datetime
from pathlib import Path

# 添加 src 到路徑
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# 直接導入 market_status 模組
spec = importlib.util.spec_from_file_location(
    "market_status", src_path / "agents" / "functions" / "market_status.py"
)
market_status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(market_status)

MarketStatusChecker = market_status.MarketStatusChecker


class MockMCPClient:
    """模擬 MCP 客戶端"""

    def __init__(self, holidays: dict[str, str] | None = None):
        self.holidays = holidays or {
            "2025-01-01": "元旦",
            "2025-10-10": "國慶日",
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


async def test_basic_without_mcp():
    """測試沒有 MCP 工具時的基本功能"""
    print("🧪 測試基本功能 (無 MCP)...")
    checker = MarketStatusChecker()
    status = await checker.get_market_status()

    assert status is not None
    assert isinstance(status.is_open, bool)
    assert status.timezone == "Asia/Taipei"
    print("   ✓ 基本功能正常")


async def test_with_mcp_tools():
    """測試整合 MCP 工具"""
    print("🧪 測試 MCP 整合...")
    mock_client = MockMCPClient()

    checker = MarketStatusChecker(
        mcp_check_trading_day=mock_client.check_trading_day,
        mcp_get_holiday_info=mock_client.get_holiday_info,
    )

    # 測試工作日
    test_date = datetime(2025, 10, 7, 10, 0)  # 週二 上午盤
    status = await checker.get_market_status(test_date)

    assert status is not None
    assert status.market_date == "2025-10-07"
    print(f"   ✓ 狀態查詢成功: 開盤={status.is_open}, 時段={status.current_session}")


async def test_holiday_detection():
    """測試假日偵測"""
    print("🧪 測試假日偵測...")
    mock_client = MockMCPClient()

    checker = MarketStatusChecker(
        mcp_check_trading_day=mock_client.check_trading_day,
        mcp_get_holiday_info=mock_client.get_holiday_info,
    )

    # 測試國慶日
    test_date = datetime(2025, 10, 10, 10, 0)
    status = await checker.get_market_status(test_date)

    assert not status.is_open, "國慶日應該休市"
    print("   ✓ 國慶日正確識別為休市")


async def test_weekend_detection():
    """測試週末偵測"""
    print("🧪 測試週末偵測...")
    mock_client = MockMCPClient()

    checker = MarketStatusChecker(
        mcp_check_trading_day=mock_client.check_trading_day,
        mcp_get_holiday_info=mock_client.get_holiday_info,
    )

    # 測試週六
    test_date = datetime(2025, 10, 11, 10, 0)
    status = await checker.get_market_status(test_date)

    assert not status.is_open, "週六應該休市"
    print("   ✓ 週末正確識別為休市")


async def test_trading_hours():
    """測試交易時段"""
    print("🧪 測試交易時段...")
    mock_client = MockMCPClient(holidays={})

    checker = MarketStatusChecker(
        mcp_check_trading_day=mock_client.check_trading_day,
        mcp_get_holiday_info=mock_client.get_holiday_info,
    )

    # 測試上午盤
    test_date = datetime(2025, 10, 7, 9, 30)
    status = await checker.get_market_status(test_date)
    assert status.is_open
    assert status.current_session == "morning_session"
    print("   ✓ 上午盤正確識別")

    # 測試午休
    test_date = datetime(2025, 10, 7, 12, 30)
    status = await checker.get_market_status(test_date)
    assert not status.is_open
    assert status.current_session == "lunch_break"
    print("   ✓ 午休時段正確識別")


async def test_market_calendar():
    """測試交易日曆"""
    print("🧪 測試交易日曆整合...")
    mock_client = MockMCPClient()

    checker = MarketStatusChecker(
        mcp_check_trading_day=mock_client.check_trading_day,
        mcp_get_holiday_info=mock_client.get_holiday_info,
    )

    calendar = await checker.get_market_calendar("2025-10-01", "2025-10-15")

    assert calendar is not None
    assert calendar["total_days"] == 15
    print(
        f"   ✓ 日曆查詢成功: 總天數={calendar['total_days']}, 交易日={calendar['trading_days_count']}"
    )

    # 檢查國慶日
    non_trading_dates = [day["date"] for day in calendar["non_trading_days"]]
    assert "2025-10-10" in non_trading_dates
    print("   ✓ 國慶日正確標記為非交易日")


async def test_holiday_cache():
    """測試快取機制"""
    print("🧪 測試假日快取...")
    mock_client = MockMCPClient()

    checker = MarketStatusChecker(
        mcp_check_trading_day=mock_client.check_trading_day,
        mcp_get_holiday_info=mock_client.get_holiday_info,
    )

    # 第一次查詢
    holiday1 = await checker._get_holiday_info("2025-10-10")
    assert holiday1 is not None
    assert holiday1.name == "國慶日"

    # 檢查快取
    assert "2025-10-10" in checker._holiday_cache
    print("   ✓ 快取機制正常")

    # 清除快取
    checker.clear_holiday_cache()
    assert len(checker._holiday_cache) == 0
    print("   ✓ 快取清除成功")


async def test_mcp_failure_fallback():
    """測試 MCP 失敗 fallback"""
    print("🧪 測試 MCP 失敗 fallback...")

    async def failing_check(date: str) -> dict:
        return {"success": False, "error": "Connection failed"}

    checker = MarketStatusChecker(mcp_check_trading_day=failing_check)

    # 即使 MCP 失敗也應該能運作
    test_date = datetime(2025, 10, 7, 10, 0)  # 週二
    status = await checker.get_market_status(test_date)

    assert status is not None
    print("   ✓ Fallback 機制正常")


async def main():
    """執行所有測試"""
    print("\n" + "=" * 60)
    print("MarketStatusChecker MCP 整合測試")
    print("=" * 60 + "\n")

    tests = [
        test_basic_without_mcp,
        test_with_mcp_tools,
        test_holiday_detection,
        test_weekend_detection,
        test_trading_hours,
        test_market_calendar,
        test_holiday_cache,
        test_mcp_failure_fallback,
    ]

    failed = []

    for test in tests:
        try:
            await test()
        except AssertionError as e:
            print(f"   ✗ 失敗: {e}")
            failed.append((test.__name__, e))
        except Exception as e:
            print(f"   ✗ 錯誤: {e}")
            failed.append((test.__name__, e))

    print("\n" + "=" * 60)
    if not failed:
        print("✓ 所有測試通過!")
    else:
        print(f"✗ {len(failed)} 個測試失敗:")
        for name, error in failed:
            print(f"  - {name}: {error}")
    print("=" * 60 + "\n")

    return len(failed) == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
