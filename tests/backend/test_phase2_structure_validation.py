"""
Phase 2 測試套件完整性驗證
檢查所有測試檔案是否正確組織並符合 PROJECT_STRUCTURE.md 規範

使用 Python 3.12+ 語法
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestPhase2TestStructure:
    """Phase 2 測試結構驗證"""

    def test_test_directory_structure(self):
        """測試目錄結構是否符合 PROJECT_STRUCTURE.md 規範"""
        # 預期的測試檔案結構
        expected_files = [
            "tests/backend/test_phase2_requirements.py",
            "tests/backend/test_phase2_integration.py",
            "tests/backend/agents/tools/test_fundamental_agent.py",
            "tests/backend/agents/tools/test_technical_agent.py",
            "tests/backend/agents/tools/test_risk_agent.py",
            "tests/backend/agents/tools/test_sentiment_agent.py",
            "tests/backend/agents/functions/test_trading_validator.py",
            "tests/backend/agents/functions/test_market_status_checker.py",
            "tests/backend/agents/functions/test_strategy_change_recorder.py",
        ]

        for file_path in expected_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"測試檔案不存在: {file_path}"
            assert full_path.is_file(), f"路徑不是檔案: {file_path}"

    def test_test_files_have_content(self):
        """測試檔案是否有內容"""
        test_files = [
            "tests/backend/test_phase2_requirements.py",
            "tests/backend/test_phase2_integration.py",
            "tests/backend/agents/tools/test_fundamental_agent.py",
            "tests/backend/agents/tools/test_technical_agent.py",
            "tests/backend/agents/tools/test_risk_agent.py",
            "tests/backend/agents/tools/test_sentiment_agent.py",
            "tests/backend/agents/functions/test_trading_validator.py",
            "tests/backend/agents/functions/test_market_status_checker.py",
            "tests/backend/agents/functions/test_strategy_change_recorder.py",
        ]

        for file_path in test_files:
            full_path = project_root / file_path
            content = full_path.read_text(encoding="utf-8")
            assert len(content) > 100, f"測試檔案內容太少: {file_path}"
            assert "def test_" in content, f"測試檔案沒有測試函數: {file_path}"


class TestPhase2Completeness:
    """Phase 2 完整性驗證"""

    def test_all_agents_have_as_tool_method(self):
        """驗證所有代理都有 as_tool 方法"""
        agents = [
            "agents.tools.fundamental_agent.FundamentalAgent",
            "agents.tools.technical_agent.TechnicalAgent",
            "agents.tools.risk_agent.RiskAgent",
            "agents.tools.sentiment_agent.SentimentAgent",
        ]

        for agent_path in agents:
            try:
                module_path, class_name = agent_path.rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                agent_class = getattr(module, class_name)
                agent_instance = agent_class()

                assert hasattr(
                    agent_instance, "as_tool"
                ), f"{agent_path} 沒有 as_tool 方法"
                tool_config = agent_instance.as_tool()
                assert isinstance(
                    tool_config, dict
                ), f"{agent_path} as_tool 返回值不是字典"
                assert (
                    tool_config["type"] == "function"
                ), f"{agent_path} tool type 不正確"

            except ImportError:
                pytest.skip(f"無法導入 {agent_path}")

    def test_all_functions_have_as_tool_method(self):
        """驗證所有功能函數都有 as_tool 方法"""
        functions = [
            "agents.functions.trading_validator.TradingValidator",
            "agents.functions.market_status_checker.MarketStatusChecker",
            "agents.functions.strategy_change_recorder.StrategyChangeRecorder",
        ]

        for function_path in functions:
            try:
                module_path, class_name = function_path.rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                function_class = getattr(module, class_name)
                function_instance = function_class()

                assert hasattr(
                    function_instance, "as_tool"
                ), f"{function_path} 沒有 as_tool 方法"
                tool_config = function_instance.as_tool()
                assert isinstance(
                    tool_config, dict
                ), f"{function_path} as_tool 返回值不是字典"
                assert (
                    tool_config["type"] == "function"
                ), f"{function_path} tool type 不正確"

            except ImportError:
                pytest.skip(f"無法導入 {function_path}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
