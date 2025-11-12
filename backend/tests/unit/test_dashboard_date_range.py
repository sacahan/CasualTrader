"""
Dashboard Date Range Tests

測試時間段計算邏輯
"""

import pytest
from datetime import date

from service.dashboard_utils import get_date_range


# ==========================================
# Test: Date Range Calculation
# ==========================================


def test_get_date_range_1day():
    """測試 1 天時間段"""
    start, end = get_date_range("1D")
    assert (end - start).days == 1
    assert end == date.today()


def test_get_date_range_1week():
    """測試 1 週時間段"""
    start, end = get_date_range("1W")
    assert (end - start).days == 7
    assert end == date.today()


def test_get_date_range_1month():
    """測試 1 月時間段"""
    start, end = get_date_range("1M")
    assert (end - start).days == 30
    assert end == date.today()


def test_get_date_range_3months():
    """測試 3 月時間段"""
    start, end = get_date_range("3M")
    assert (end - start).days == 90
    assert end == date.today()


def test_get_date_range_1year():
    """測試 1 年時間段"""
    start, end = get_date_range("1Y")
    assert (end - start).days == 365
    assert end == date.today()


def test_get_date_range_all():
    """測試全部時間段"""
    start, end = get_date_range("all")
    # 開始日期應該很久以前
    assert (end - start).days > 1000
    assert start == date(2000, 1, 1)
    assert end == date.today()


def test_get_date_range_invalid():
    """測試無效的時間段"""
    with pytest.raises(ValueError):
        get_date_range("invalid")

    with pytest.raises(ValueError):
        get_date_range("2D")

    with pytest.raises(ValueError):
        get_date_range("")


def test_get_date_range_case_sensitive():
    """測試時間段大小寫敏感性"""
    # 小寫應該失敗
    with pytest.raises(ValueError):
        get_date_range("1m")

    # 正確的大寫應該成功
    start, end = get_date_range("1M")
    assert end == date.today()


def test_get_date_range_date_order():
    """測試返回的日期順序"""
    start, end = get_date_range("1M")
    assert start < end
    assert start < date.today()
    assert end == date.today()
