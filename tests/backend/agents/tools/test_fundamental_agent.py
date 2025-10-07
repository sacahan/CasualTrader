"""
基本面分析工具測試
測試 FundamentalAgent 的功能
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestFundamentalAgent:
    """FundamentalAgent 測試類"""

    def test_as_tool_method_exists(self):
        """測試 as_tool 方法存在"""
        try:
            from src.agents.tools.fundamental_agent import FundamentalAgent

            agent = FundamentalAgent()
            tool_config = agent.as_tool("test_tool", "Test description")

            assert isinstance(tool_config, dict)
            assert tool_config["type"] == "function"
            assert "function" in tool_config
            assert tool_config["function"]["name"] == "test_tool"

        except ImportError:
            pytest.skip("FundamentalAgent not available")

    def test_tool_configuration_structure(self):
        """測試工具配置結構"""
        try:
            from src.agents.tools.fundamental_agent import FundamentalAgent

            agent = FundamentalAgent()
            tool_config = agent.as_tool("fundamental_analysis", "分析公司基本面")

            # 檢查必要的欄位
            assert "type" in tool_config
            assert "function" in tool_config
            assert "implementation" in tool_config

            function_config = tool_config["function"]
            assert "name" in function_config
            assert "description" in function_config
            assert "parameters" in function_config

            parameters = function_config["parameters"]
            assert "type" in parameters
            assert "properties" in parameters
            assert "required" in parameters

        except ImportError:
            pytest.skip("FundamentalAgent not available")


if __name__ == "__main__":
    pytest.main([__file__])
