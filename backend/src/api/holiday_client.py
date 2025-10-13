"""
台灣節假日 API 客戶端

提供台灣節假日查詢服務，支援檢查指定日期是否為節假日。
API 來源：https://doggy8088.github.io/holidaybook/
"""

import asyncio
from datetime import date, datetime
from typing import Any

import httpx
from loguru import logger


class HolidayData:
    """節假日資料模型"""

    def __init__(self, data: dict[str, Any]):
        self.id: int = data.get("_id", 0)
        self.date: str = data.get("date", "")
        self.name: str = data.get("name", "")
        self.is_holiday: bool = bool(data.get("isHoliday", 0))
        self.holiday_category: str = data.get("holidaycategory", "")
        self.description: str = data.get("description", "")

    def to_dict(self) -> dict[str, Any]:
        """轉換為字典格式"""
        return {
            "id": self.id,
            "date": self.date,
            "name": self.name,
            "is_holiday": self.is_holiday,
            "holiday_category": self.holiday_category,
            "description": self.description,
        }


class TaiwanHolidayAPIClient:
    """
    台灣節假日 API 客戶端

    使用 https://doggy8088.github.io/holidaybook/ API 查詢台灣節假日資訊
    """

    def __init__(self, timeout: int = 10):
        """
        初始化節假日API客戶端

        Args:
            timeout: HTTP 請求超時時間（秒）
        """
        self.base_url = "https://doggy8088.github.io/holidaybook"
        self.timeout = timeout
        self.session = httpx.AsyncClient(timeout=timeout)

        logger.debug(f"初始化台灣節假日API客戶端 - 基礎URL: {self.base_url}")

    async def get_holiday_info(self, check_date: date | str) -> HolidayData | None:
        """
        查詢指定日期的節假日資訊

        Args:
            check_date: 要查詢的日期，可以是 date 物件或 YYYY-MM-DD 格式字串

        Returns:
            HolidayData | None: 節假日資訊，如果不是節假日則返回 None

        Raises:
            httpx.HTTPError: HTTP 請求失敗
            ValueError: 日期格式錯誤
        """
        # 統一日期格式
        if isinstance(check_date, str):
            try:
                date_obj = datetime.strptime(check_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"日期格式錯誤，請使用 YYYY-MM-DD 格式: {check_date}") from None
        elif isinstance(check_date, date):
            date_obj = check_date
        else:
            raise ValueError(f"不支援的日期類型: {type(check_date)}")

        # 格式化日期為 API 所需格式
        date_str = date_obj.strftime("%Y-%m-%d")
        url = f"{self.base_url}/{date_str}.json"

        logger.debug(f"查詢節假日資訊: {url}")

        try:
            response = await self.session.get(url)

            # 如果是 404，表示該日期不是節假日
            if response.status_code == 404:
                logger.debug(f"日期 {date_str} 不是節假日")
                return None

            response.raise_for_status()
            data = response.json()

            holiday_data = HolidayData(data)
            logger.info(f"查詢到節假日資訊: {holiday_data.name} ({date_str})")

            return holiday_data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"日期 {date_str} 不是節假日")
                return None
            logger.error(f"查詢節假日API失敗: {e}")
            raise e from None
        except Exception as e:
            logger.error(f"查詢節假日資訊時發生錯誤: {e}")
            raise e from None

    async def is_holiday(self, check_date: date | str) -> bool:
        """
        檢查指定日期是否為節假日

        Args:
            check_date: 要檢查的日期

        Returns:
            bool: True 表示是節假日，False 表示不是節假日
        """
        holiday_info = await self.get_holiday_info(check_date)
        return holiday_info is not None and holiday_info.is_holiday

    async def get_holiday_name(self, check_date: date | str) -> str | None:
        """
        取得指定日期的節假日名稱

        Args:
            check_date: 要查詢的日期

        Returns:
            Optional[str]: 節假日名稱，如果不是節假日則返回 None
        """
        holiday_info = await self.get_holiday_info(check_date)
        return holiday_info.name if holiday_info else None

    def is_weekend(self, check_date: date | str) -> bool:
        """
        檢查指定日期是否為週末

        Args:
            check_date: 要檢查的日期

        Returns:
            bool: True 表示是週末，False 表示不是週末
        """
        if isinstance(check_date, str):
            date_obj = datetime.strptime(check_date, "%Y-%m-%d").date()
        else:
            date_obj = check_date

        # weekday() 返回 0-6，其中 0=Monday, 6=Sunday
        # 台灣週末是週六(5)和週日(6)
        return date_obj.weekday() in [5, 6]

    async def is_trading_day(self, check_date: date | str) -> bool:
        """
        檢查指定日期是否為股市交易日

        股市交易日的條件：
        1. 不是週末
        2. 不是國定假日

        Args:
            check_date: 要檢查的日期

        Returns:
            bool: True 表示是交易日，False 表示不是交易日
        """
        # 檢查是否為週末
        if self.is_weekend(check_date):
            return False

        # 檢查是否為國定假日
        is_national_holiday = await self.is_holiday(check_date)
        return not is_national_holiday

    async def close(self):
        """關閉HTTP客戶端"""
        await self.session.aclose()
        logger.info("節假日API客戶端已關閉")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 建立全域實例的工廠函數
def create_holiday_client() -> TaiwanHolidayAPIClient:
    """建立節假日API客戶端實例"""
    return TaiwanHolidayAPIClient()


# 測試函數
async def test_holiday_api():
    """測試節假日API功能"""
    async with create_holiday_client() as client:
        # 測試一些已知的節假日
        test_dates = [
            "2025-01-01",  # 元旦
            "2025-01-28",  # 春節
            "2025-10-06",  # 可能的假日
            "2025-12-25",  # 聖誕節
            "2025-10-07",  # 一般工作日
        ]

        for test_date in test_dates:
            try:
                holiday_info = await client.get_holiday_info(test_date)
                is_weekend = client.is_weekend(test_date)
                is_trading = await client.is_trading_day(test_date)

                print(f"日期: {test_date}")
                print(f"  節假日: {holiday_info.name if holiday_info else '否'}")
                print(f"  週末: {'是' if is_weekend else '否'}")
                print(f"  交易日: {'是' if is_trading else '否'}")
                print()
            except Exception as e:
                print(f"測試日期 {test_date} 時發生錯誤: {e}")


if __name__ == "__main__":
    asyncio.run(test_holiday_api())
