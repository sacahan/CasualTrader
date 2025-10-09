"""
交易參數驗證測試
測試 TradingValidator 的功能
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestTradingValidator:
    """TradingValidator 測試類"""

    def test_as_tool_method_exists(self):
        """測試 as_tool 方法存在"""
        try:
            from src.agents.functions.trading_validation import TradingValidator

            validator = TradingValidator()
            tool_config = validator.as_tool()

            assert isinstance(tool_config, dict)
            assert tool_config["type"] == "function"
            assert "function" in tool_config
            assert tool_config["function"]["name"] == "validate_trade_parameters"

        except ImportError:
            pytest.skip("TradingValidator not available")

    def test_tool_configuration_parameters(self):
        """測試工具配置參數"""
        try:
            from src.agents.functions.trading_validation import TradingValidator

            validator = TradingValidator()
            tool_config = validator.as_tool()

            parameters = tool_config["function"]["parameters"]
            properties = parameters["properties"]
            required = parameters["required"]

            # 檢查必要參數
            assert "symbol" in properties
            assert "action" in properties
            assert "quantity" in properties
            assert "symbol" in required
            assert "action" in required
            assert "quantity" in required

        except ImportError:
            pytest.skip("TradingValidator not available")


if __name__ == "__main__":
    pytest.main([__file__])
