"""
市場狀態檢查器測試
測試 MarketStatusChecker 的功能
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestMarketStatusChecker:
    """MarketStatusChecker 測試類"""

    def test_as_tool_method_exists(self):
        """測試 as_tool 方法存在"""
        try:
            from agents.functions.market_status_checker import MarketStatusChecker

            checker = MarketStatusChecker()
            tool_config = checker.as_tool()

            assert isinstance(tool_config, dict)
            assert tool_config["type"] == "function"
            assert "function" in tool_config
            assert tool_config["function"]["name"] == "check_market_status"

        except ImportError:
            pytest.skip("MarketStatusChecker not available")

    def test_tool_configuration_parameters(self):
        """測試工具配置參數"""
        try:
            from agents.functions.market_status_checker import MarketStatusChecker

            checker = MarketStatusChecker()
            tool_config = checker.as_tool()

            parameters = tool_config["function"]["parameters"]

            # 檢查參數結構存在
            assert "properties" in parameters
            assert "required" in parameters

        except ImportError:
            pytest.skip("MarketStatusChecker not available")


if __name__ == "__main__":
    pytest.main([__file__])
