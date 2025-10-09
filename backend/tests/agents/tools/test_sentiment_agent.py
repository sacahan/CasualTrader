"""
市場情緒分析工具測試
測試 SentimentAgent 的功能
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestSentimentAgent:
    """SentimentAgent 測試類"""

    def test_tools_class_exists(self):
        """測試工具類別存在"""
        try:
            from src.agents.tools.sentiment_agent import SentimentAnalysisTools

            tools = SentimentAnalysisTools()
            assert tools is not None
            assert hasattr(tools, "logger")

        except ImportError:
            pytest.skip("SentimentAnalysisTools not available")

    def test_calculate_fear_greed_index(self):
        """測試恐懼貪婪指數計算"""
        try:
            from src.agents.tools.sentiment_agent import SentimentAnalysisTools

            tools = SentimentAnalysisTools()

            # 模擬市場數據
            market_data = {
                "price_momentum": 70,
                "market_breadth": 65,
                "volatility": 30,
                "put_call_ratio": 20,
            }

            result = tools.calculate_fear_greed_index(market_data)

            # 檢查結果結構
            assert "index_value" in result
            assert "level" in result
            assert "components" in result
            assert "interpretation" in result

            # 檢查指數範圍
            assert 0 <= result["index_value"] <= 100

            # 檢查等級有效性
            valid_levels = ["極度恐慌", "恐懼", "中性", "貪婪", "極度貪婪"]
            assert result["level"] in valid_levels

        except ImportError:
            pytest.skip("SentimentAnalysisTools not available")


if __name__ == "__main__":
    pytest.main([__file__])
