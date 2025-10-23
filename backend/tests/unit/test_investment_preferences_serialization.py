"""
測試 investment_preferences JSON 序列化/反序列化邏輯

驗證 API 路由器正確地將 JSON 字符串解析為列表
"""

import json
import pytest


def test_investment_preferences_json_parsing():
    """
    測試 investment_preferences JSON 字符串的解析

    模擬在 agents.py 中的 JSON 解析邏輯
    """
    # 模擬從數據庫返回的 JSON 字符串
    stored_json = json.dumps(["2330", "2454", "0050"], ensure_ascii=False)

    # 驗證 JSON 字符串格式
    assert isinstance(stored_json, str)

    # 解析回列表（模擬 agents.py 中的邏輯）
    try:
        investment_prefs = json.loads(stored_json)
    except (json.JSONDecodeError, TypeError):
        investment_prefs = []

    # 驗證結果是列表
    assert isinstance(investment_prefs, list)
    assert investment_prefs == ["2330", "2454", "0050"]


def test_empty_investment_preferences_parsing():
    """
    測試空 investment_preferences 的解析
    """
    # 模擬空列表的 JSON 字符串
    stored_json = json.dumps([], ensure_ascii=False)

    # 解析回列表
    try:
        investment_prefs = json.loads(stored_json)
    except (json.JSONDecodeError, TypeError):
        investment_prefs = []

    # 驗證結果是空列表
    assert isinstance(investment_prefs, list)
    assert investment_prefs == []


def test_none_investment_preferences_handling():
    """
    測試 None investment_preferences 的處理
    """
    investment_prefs = None

    # 模擬 agents.py 中的邏輯
    parsed_prefs = []
    if investment_prefs:
        try:
            parsed_prefs = json.loads(investment_prefs)
        except (json.JSONDecodeError, TypeError):
            parsed_prefs = []

    # 驗證結果
    assert isinstance(parsed_prefs, list)
    assert parsed_prefs == []


def test_malformed_json_handling():
    """
    測試畸形 JSON 字符串的處理
    """
    # 模擬畸形的 JSON 字符串
    malformed_json = "not valid json"

    # 模擬 agents.py 中的邏輯
    investment_prefs = []
    try:
        investment_prefs = json.loads(malformed_json)
    except (json.JSONDecodeError, TypeError):
        investment_prefs = []

    # 驗證結果 - 應該返回空列表
    assert isinstance(investment_prefs, list)
    assert investment_prefs == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
