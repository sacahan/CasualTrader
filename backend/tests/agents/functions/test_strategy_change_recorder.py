"""
策略變更記錄測試
測試 StrategyChangeRecorder 的功能
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestStrategyChangeRecorder:
    """StrategyChangeRecorder 測試類"""

    def test_as_tool_method_exists(self):
        """測試 as_tool 方法存在"""
        try:
            from agents.functions.strategy_change_recorder import StrategyChangeRecorder

            recorder = StrategyChangeRecorder()
            tool_config = recorder.as_tool()

            assert isinstance(tool_config, dict)
            assert tool_config["type"] == "function"
            assert "function" in tool_config
            assert tool_config["function"]["name"] == "record_strategy_change"

        except ImportError:
            pytest.skip("StrategyChangeRecorder not available")

    def test_tool_configuration_parameters(self):
        """測試工具配置參數"""
        try:
            from agents.functions.strategy_change_recorder import StrategyChangeRecorder

            recorder = StrategyChangeRecorder()
            tool_config = recorder.as_tool()

            parameters = tool_config["function"]["parameters"]
            properties = parameters["properties"]
            required = parameters["required"]

            # 檢查必要參數
            assert "trigger_reason" in properties
            assert "new_strategy_addition" in properties
            assert "change_summary" in properties
            assert "agent_explanation" in properties

            # 檢查必要欄位
            assert "trigger_reason" in required
            assert "new_strategy_addition" in required
            assert "change_summary" in required
            assert "agent_explanation" in required

        except ImportError:
            pytest.skip("StrategyChangeRecorder not available")


if __name__ == "__main__":
    pytest.main([__file__])
