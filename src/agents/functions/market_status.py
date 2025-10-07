"""
市場狀態檢查功能
檢查台股市場開盤狀態和交易時間
使用 Python 3.12+ 語法
"""

import logging
from collections.abc import Callable
from datetime import datetime, time
from typing import Any

import pytz
from pydantic import BaseModel, ConfigDict


class MarketSession(BaseModel):
    """交易時段定義"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    start_time: time
    end_time: time
    is_trading: bool = True


class MarketStatus(BaseModel):
    """市場狀態"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    is_open: bool
    current_session: str | None = None
    next_session: str | None = None
    time_to_next_session: int | None = None  # 秒數
    market_date: str
    current_time: datetime
    timezone: str = "Asia/Taipei"


class MarketHoliday(BaseModel):
    """市場假日"""

    date: str
    name: str
    type: str  # "national", "market_specific"


class MarketStatusChecker:
    """
    市場狀態檢查器
    使用 MCP tool 動態查詢台股交易日和假日資訊
    """

    def __init__(
        self,
        mcp_check_trading_day: Callable[[str], Any] | None = None,
        mcp_get_holiday_info: Callable[[str], Any] | None = None,
    ) -> None:
        """
        初始化市場狀態檢查器

        Args:
            mcp_check_trading_day: MCP tool 函數,用於檢查是否為交易日
            mcp_get_holiday_info: MCP tool 函數,用於取得假日資訊
        """
        self.logger = logging.getLogger("market_status_checker")
        self.timezone = pytz.timezone("Asia/Taipei")
        self.mcp_check_trading_day = mcp_check_trading_day
        self.mcp_get_holiday_info = mcp_get_holiday_info

        # 台股交易時段定義
        self.trading_sessions = {
            "pre_market": MarketSession(
                name="盤前",
                start_time=time(8, 30),
                end_time=time(9, 0),
                is_trading=False,
            ),
            "morning_session": MarketSession(
                name="上午盤",
                start_time=time(9, 0),
                end_time=time(12, 0),
                is_trading=True,
            ),
            "lunch_break": MarketSession(
                name="中午休息",
                start_time=time(12, 0),
                end_time=time(13, 0),
                is_trading=False,
            ),
            "afternoon_session": MarketSession(
                name="下午盤",
                start_time=time(13, 0),
                end_time=time(13, 30),
                is_trading=True,
            ),
            "after_market": MarketSession(
                name="盤後",
                start_time=time(13, 30),
                end_time=time(14, 30),
                is_trading=False,
            ),
        }

        # 假日資訊快取 (避免重複 MCP 查詢)
        self._holiday_cache: dict[str, MarketHoliday | None] = {}

    async def get_market_status(
        self, check_time: datetime | None = None
    ) -> MarketStatus:
        """
        獲取市場狀態

        Args:
            check_time: 檢查時間 (None 表示當前時間)

        Returns:
            市場狀態
        """
        try:
            # 使用指定時間或當前時間
            if check_time is None:
                current_time = datetime.now(self.timezone)
            else:
                current_time = check_time.astimezone(self.timezone)

            date_str = current_time.strftime("%Y-%m-%d")

            # 使用 MCP tool 檢查是否為交易日
            is_trading_day = await self._check_is_trading_day(date_str)

            # 確定當前交易時段
            current_session = self._get_current_session(current_time)
            next_session = self._get_next_session(current_time)
            time_to_next = self._calculate_time_to_next_session(
                current_time, next_session
            )

            # 判斷市場是否開盤 (必須是交易日且在交易時段內)
            is_open = (
                is_trading_day
                and current_session is not None
                and self.trading_sessions[current_session].is_trading
            )

            self.logger.info(
                f"Market status checked: open={is_open}, session={current_session}, is_trading_day={is_trading_day}"
            )

            return MarketStatus(
                is_open=is_open,
                current_session=current_session,
                next_session=next_session,
                time_to_next_session=time_to_next,
                market_date=date_str,
                current_time=current_time,
            )

        except Exception as e:
            self.logger.error(f"Failed to get market status: {e}")
            raise

    async def _check_is_trading_day(self, date: str) -> bool:
        """
        使用 MCP tool 檢查是否為交易日

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            是否為交易日
        """
        try:
            if self.mcp_check_trading_day is None:
                # 如果沒有提供 MCP tool,使用基本邏輯判斷 (週末)
                self.logger.warning(
                    "MCP tool not provided, falling back to basic weekday check"
                )
                from datetime import datetime as dt

                check_date = dt.strptime(date, "%Y-%m-%d")
                return check_date.weekday() < 5

            # 呼叫 MCP tool: check_taiwan_trading_day
            result = await self.mcp_check_trading_day(date)

            if result.get("success"):
                data = result.get("data", {})
                return data.get("is_trading_day", False)
            else:
                self.logger.warning(
                    f"MCP check_trading_day failed: {result.get('error')}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Failed to check trading day via MCP: {e}")
            # 發生錯誤時,fallback 到基本判斷
            from datetime import datetime as dt

            check_date = dt.strptime(date, "%Y-%m-%d")
            return check_date.weekday() < 5

    async def _get_holiday_info(self, date: str) -> MarketHoliday | None:
        """
        使用 MCP tool 取得假日資訊

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            假日資訊,如果不是假日則返回 None
        """
        # 檢查快取
        if date in self._holiday_cache:
            return self._holiday_cache[date]

        try:
            if self.mcp_get_holiday_info is None:
                self.logger.warning("MCP tool get_holiday_info not provided")
                return None

            # 呼叫 MCP tool: get_taiwan_holiday_info
            result = await self.mcp_get_holiday_info(date)

            if result.get("success"):
                data = result.get("data", {})
                if data.get("is_holiday"):
                    holiday = MarketHoliday(
                        date=date,
                        name=data.get("name", "未知假日"),
                        type=data.get("holiday_category", "national"),
                    )
                    self._holiday_cache[date] = holiday
                    return holiday
                else:
                    self._holiday_cache[date] = None
                    return None
            else:
                self.logger.warning(
                    f"MCP get_holiday_info failed: {result.get('error')}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Failed to get holiday info via MCP: {e}")
            return None

    def _get_current_session(self, current_time: datetime) -> str | None:
        """獲取當前交易時段"""
        current_time_only = current_time.time()

        for session_id, session in self.trading_sessions.items():
            if session.start_time <= current_time_only < session.end_time:
                return session_id

        # 如果不在任何定義的時段內，返回 None
        return None

    def _get_next_session(self, current_time: datetime) -> str | None:
        """獲取下一個交易時段"""
        current_time_only = current_time.time()

        # 按時間順序排序的時段
        sorted_sessions = sorted(
            self.trading_sessions.items(), key=lambda x: x[1].start_time
        )

        # 尋找下一個時段
        for session_id, session in sorted_sessions:
            if current_time_only < session.start_time:
                return session_id

        # 如果已經過了所有時段，則下一個是明天的第一個時段
        return sorted_sessions[0][0]

    def _calculate_time_to_next_session(
        self, current_time: datetime, next_session: str | None
    ) -> int | None:
        """計算到下一個時段的時間（秒）"""
        if next_session is None:
            return None

        session = self.trading_sessions[next_session]
        current_time_only = current_time.time()

        # 構建下一個時段的完整時間
        if current_time_only < session.start_time:
            # 今天的下一個時段
            next_datetime = current_time.replace(
                hour=session.start_time.hour,
                minute=session.start_time.minute,
                second=0,
                microsecond=0,
            )
        else:
            # 明天的第一個時段
            from datetime import timedelta

            next_date = current_time.date() + timedelta(days=1)
            next_datetime = datetime.combine(next_date, session.start_time)
            next_datetime = self.timezone.localize(next_datetime)

        time_difference = (next_datetime - current_time).total_seconds()
        return int(time_difference)

    async def is_trading_hours(self, check_time: datetime | None = None) -> bool:
        """
        簡化的交易時間檢查

        Args:
            check_time: 檢查時間

        Returns:
            是否在交易時間內
        """
        status = await self.get_market_status(check_time)
        return status.is_open

    async def get_next_trading_session(
        self, check_time: datetime | None = None
    ) -> dict[str, Any]:
        """
        獲取下一個交易時段資訊

        Args:
            check_time: 檢查時間

        Returns:
            下一個交易時段資訊
        """
        status = await self.get_market_status(check_time)

        if status.next_session:
            session = self.trading_sessions[status.next_session]
            return {
                "session_name": session.name,
                "session_id": status.next_session,
                "start_time": session.start_time.strftime("%H:%M"),
                "end_time": session.end_time.strftime("%H:%M"),
                "is_trading": session.is_trading,
                "time_to_start": status.time_to_next_session,
                "time_to_start_formatted": self._format_duration(
                    status.time_to_next_session
                ),
            }

        return {}

    def _format_duration(self, seconds: int | None) -> str:
        """格式化時間長度"""
        if seconds is None:
            return "未知"

        if seconds < 60:
            return f"{seconds} 秒"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} 分鐘"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours} 小時 {minutes} 分鐘"
            else:
                return f"{hours} 小時"

    async def get_market_calendar(
        self, start_date: str, end_date: str
    ) -> dict[str, Any]:
        """
        獲取市場交易日曆

        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            交易日曆資訊
        """
        try:
            from datetime import datetime, timedelta

            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            trading_days = []
            non_trading_days = []

            current_date = start
            while current_date <= end:
                date_str = current_date.strftime("%Y-%m-%d")

                # 使用 MCP tool 檢查是否為交易日
                is_trading_day = await self._check_is_trading_day(date_str)

                # 取得假日資訊
                holiday_info = await self._get_holiday_info(date_str)

                if is_trading_day:
                    trading_days.append(
                        {
                            "date": date_str,
                            "day_of_week": current_date.strftime("%A"),
                            "is_trading_day": True,
                        }
                    )
                else:
                    reason = []
                    is_weekday = current_date.weekday() < 5

                    if not is_weekday:
                        reason.append("週末")
                    if holiday_info:
                        reason.append(f"假日({holiday_info.name})")

                    non_trading_days.append(
                        {
                            "date": date_str,
                            "day_of_week": current_date.strftime("%A"),
                            "is_trading_day": False,
                            "reason": ", ".join(reason) if reason else "非交易日",
                            "holiday_info": (
                                holiday_info.dict() if holiday_info else None
                            ),
                        }
                    )

                current_date += timedelta(days=1)

            return {
                "period": f"{start_date} to {end_date}",
                "total_days": (end - start).days + 1,
                "trading_days": trading_days,
                "non_trading_days": non_trading_days,
                "trading_days_count": len(trading_days),
                "non_trading_days_count": len(non_trading_days),
            }

        except Exception as e:
            self.logger.error(f"Failed to get market calendar: {e}")
            raise

    def clear_holiday_cache(self) -> None:
        """
        清除假日快取
        在需要重新載入最新假日資訊時使用
        """
        self._holiday_cache.clear()
        self.logger.info("Holiday cache cleared")

    def get_trading_sessions_info(self) -> dict[str, Any]:
        """獲取交易時段資訊"""
        sessions_info = {}

        for session_id, session in self.trading_sessions.items():
            sessions_info[session_id] = {
                "name": session.name,
                "start_time": session.start_time.strftime("%H:%M"),
                "end_time": session.end_time.strftime("%H:%M"),
                "is_trading": session.is_trading,
                "duration_minutes": (
                    datetime.combine(datetime.today(), session.end_time)
                    - datetime.combine(datetime.today(), session.start_time)
                ).total_seconds()
                / 60,
            }

        return {
            "timezone": "Asia/Taipei",
            "trading_sessions": sessions_info,
            "total_trading_hours": sum(
                info["duration_minutes"] / 60
                for info in sessions_info.values()
                if sessions_info[session_id]["is_trading"]
                for session_id in sessions_info
            ),
        }

    async def wait_for_market_open(self, check_interval: int = 60) -> None:
        """
        等待市場開盤

        Args:
            check_interval: 檢查間隔（秒）
        """
        import asyncio

        while True:
            status = await self.get_market_status()

            if status.is_open:
                self.logger.info("Market is now open")
                break

            if status.time_to_next_session:
                wait_time = min(check_interval, status.time_to_next_session)
                self.logger.info(
                    f"Market closed, waiting {self._format_duration(status.time_to_next_session)} for next trading session"
                )
                await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(check_interval)
