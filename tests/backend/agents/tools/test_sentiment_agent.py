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

    def test_as_tool_method_exists(self):
        """測試 as_tool 方法存在"""
        try:
            from src.agents.tools.sentiment_agent import SentimentAgent

            agent = SentimentAgent()
            tool_config = agent.as_tool("test_tool", "Test description")

            assert isinstance(tool_config, dict)
            assert tool_config["type"] == "function"
            assert "function" in tool_config
            assert tool_config["function"]["name"] == "test_tool"

        except ImportError:
            pytest.skip("SentimentAgent not available")

    def test_tool_configuration_parameters(self):
        """測試工具配置參數"""
        try:
            from src.agents.tools.sentiment_agent import SentimentAgent

            agent = SentimentAgent()
            tool_config = agent.as_tool("market_sentiment", "市場情緒分析")

            parameters = tool_config["function"]["parameters"]
            properties = parameters["properties"]

            # 檢查參數
            assert "symbol" in properties
            assert "market_scope" in properties
            assert "include_news" in properties
            assert "include_social" in properties

        except ImportError:
            pytest.skip("SentimentAgent not available")


if __name__ == "__main__":
    pytest.main([__file__])
