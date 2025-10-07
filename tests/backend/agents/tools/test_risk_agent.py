"""
風險評估工具測試
測試 RiskAgent 的功能
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestRiskAgent:
    """RiskAgent 測試類"""

    def test_as_tool_method_exists(self):
        """測試 as_tool 方法存在"""
        try:
            from src.agents.tools.risk_agent import RiskAgent

            agent = RiskAgent()
            tool_config = agent.as_tool("test_tool", "Test description")

            assert isinstance(tool_config, dict)
            assert tool_config["type"] == "function"
            assert "function" in tool_config
            assert tool_config["function"]["name"] == "test_tool"

        except ImportError:
            pytest.skip("RiskAgent not available")

    def test_tool_configuration_parameters(self):
        """測試工具配置參數"""
        try:
            from src.agents.tools.risk_agent import RiskAgent

            agent = RiskAgent()
            tool_config = agent.as_tool("risk_assessment", "風險評估")

            parameters = tool_config["function"]["parameters"]
            properties = parameters["properties"]

            # 檢查必要參數
            assert "portfolio_data" in properties
            assert "risk_tolerance" in properties
            assert "assessment_type" in properties

        except ImportError:
            pytest.skip("RiskAgent not available")


if __name__ == "__main__":
    pytest.main([__file__])
