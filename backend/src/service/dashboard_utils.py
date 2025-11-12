"""
Dashboard Utilities

提供儀表板相關的工具函數
"""

from datetime import timedelta, date


def get_date_range(time_period: str) -> tuple[date, date]:
    """
    根據時間段名稱計算開始和結束日期

    Args:
        time_period: 時間段 ('1D', '1W', '1M', '3M', '1Y', 'all')

    Returns:
        (start_date, end_date) 元組

    Raises:
        ValueError: 無效的時間段
    """
    today = date.today()
    period_mapping = {
        "1D": timedelta(days=1),
        "1W": timedelta(days=7),
        "1M": timedelta(days=30),
        "3M": timedelta(days=90),
        "1Y": timedelta(days=365),
    }

    if time_period == "all":
        # 返回很久以前的日期作為開始
        return date(2000, 1, 1), today

    if time_period not in period_mapping:
        raise ValueError(f"無效的時間段: {time_period}")

    delta = period_mapping[time_period]
    start_date = today - delta
    return start_date, today
