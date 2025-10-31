"""
工具配置測試

驗證 ToolConfig 和 ToolRequirements 的正確性。
"""

import pytest

from common.enums import AgentMode
from trading.tool_config import ToolConfig, ToolRequirements, get_tool_config


class TestToolRequirements:
    """測試 ToolRequirements 數據類"""

    def test_trading_requirements_complete(self):
        """測試：TRADING 模式包含完整工具集"""
        config = ToolConfig.get_requirements(AgentMode.TRADING)

        # OpenAI 工具 (已禁用 - LiteLLM 不支持)
        assert config.include_web_search is False
        assert config.include_code_interpreter is False

        # MCP 伺服器
        assert config.include_memory_mcp is True
        assert config.include_casual_market_mcp is True
        assert config.include_tavily_mcp is True

        # 交易工具
        assert config.include_buy_sell_tools is True
        assert config.include_portfolio_tools is True

        # Sub-agents
        assert config.include_fundamental_agent is True
        assert config.include_technical_agent is True
        assert config.include_risk_agent is True
        assert config.include_sentiment_agent is True

    def test_rebalancing_requirements_simplified(self):
        """測試：REBALANCING 模式包含簡化工具集"""
        config = ToolConfig.get_requirements(AgentMode.REBALANCING)

        # OpenAI 工具 (已禁用 - LiteLLM 不支持)
        assert config.include_web_search is False
        assert config.include_code_interpreter is False

        # MCP 伺服器
        assert config.include_memory_mcp is True
        assert config.include_casual_market_mcp is True
        assert config.include_tavily_mcp is False  # ❌ 不需要

        # 交易工具
        assert config.include_buy_sell_tools is False  # ❌ 不執行買賣
        assert config.include_portfolio_tools is True

        # Sub-agents
        assert config.include_fundamental_agent is False  # ❌ 不需要
        assert config.include_technical_agent is True
        assert config.include_risk_agent is True
        assert config.include_sentiment_agent is False  # ❌ 不需要

    def test_requirements_immutable(self):
        """測試：ToolRequirements 不可修改（frozen dataclass）"""
        config = ToolConfig.get_requirements(AgentMode.TRADING)

        with pytest.raises(Exception):  # frozen dataclass 會拋出 FrozenInstanceError
            config.include_web_search = False

    def test_requirements_str_representation(self):
        """測試：ToolRequirements 字串表示"""
        config = ToolConfig.get_requirements(AgentMode.TRADING)
        str_repr = str(config)

        assert "Tools:" in str_repr
        assert "MCPs:" in str_repr
        assert "Agents:" in str_repr


class TestToolConfig:
    """測試 ToolConfig 管理器"""

    def test_get_requirements_trading_mode(self):
        """測試：取得 TRADING 模式配置"""
        config = ToolConfig.get_requirements(AgentMode.TRADING)

        assert isinstance(config, ToolRequirements)
        # OpenAI Tools 已禁用
        assert config.include_web_search is False
        assert config.include_buy_sell_tools is True

    def test_get_requirements_rebalancing_mode(self):
        """測試：取得 REBALANCING 模式配置"""
        config = ToolConfig.get_requirements(AgentMode.REBALANCING)

        assert isinstance(config, ToolRequirements)
        assert config.include_web_search is False
        assert config.include_buy_sell_tools is False

    def test_get_requirements_default_trading(self):
        """測試：預設模式為 TRADING"""
        config = ToolConfig.get_requirements(None)

        # OpenAI Tools 已禁用
        assert config.include_web_search is False
        assert config.include_buy_sell_tools is True

    def test_get_requirements_invalid_mode(self):
        """測試：無效模式拋出異常"""
        with pytest.raises(ValueError, match="Unsupported agent mode"):
            ToolConfig.get_requirements("INVALID_MODE")

    def test_compare_configurations_trading_vs_rebalancing(self):
        """測試：比較 TRADING 和 REBALANCING 配置差異"""
        diff = ToolConfig.compare_configurations(AgentMode.TRADING, AgentMode.REBALANCING)

        # 應該有多項差異
        assert len(diff) > 0

        # 檢查特定差異（OpenAI Tools 都禁用了，所以不再有差異）
        assert diff.get("include_tavily_mcp") is True
        assert diff.get("include_buy_sell_tools") is True
        assert diff.get("include_fundamental_agent") is True
        assert diff.get("include_sentiment_agent") is True

    def test_compare_configurations_same_mode(self):
        """測試：相同模式無差異"""
        diff = ToolConfig.compare_configurations(AgentMode.TRADING, AgentMode.TRADING)

        assert len(diff) == 0

    def test_convenience_function_get_tool_config(self):
        """測試：便利函數 get_tool_config()"""
        # 測試 TRADING 模式
        config = get_tool_config(AgentMode.TRADING)
        assert config.include_web_search is False  # OpenAI Tools 已禁用

        # 測試 REBALANCING 模式
        config = get_tool_config(AgentMode.REBALANCING)
        assert config.include_web_search is False

        # 測試預設值
        config = get_tool_config()
        assert config.include_web_search is False  # OpenAI Tools 已禁用

    def test_config_caching(self):
        """測試：配置快取確保一致性"""
        config1 = ToolConfig.get_requirements(AgentMode.TRADING)
        config2 = ToolConfig.get_requirements(AgentMode.TRADING)

        # 應該是同一個物件（快取）
        assert config1 is config2


class TestToolConfigIntegration:
    """整合測試"""

    def test_all_modes_have_required_tools(self):
        """測試：所有模式都有必需工具"""
        for mode in [AgentMode.TRADING, AgentMode.REBALANCING]:
            config = ToolConfig.get_requirements(mode)

            # 所有模式都應有這些基本工具
            # OpenAI Tools 已禁用
            assert config.include_code_interpreter is False
            assert config.include_memory_mcp is True
            assert config.include_casual_market_mcp is True
            assert config.include_portfolio_tools is True

            # 所有模式都應至少有一個分析工具
            has_analysis = (
                config.include_technical_agent
                or config.include_risk_agent
                or config.include_fundamental_agent
            )
            assert has_analysis is True

    def test_trading_has_all_agents(self):
        """測試：TRADING 模式擁有所有 Sub-agents"""
        config = ToolConfig.get_requirements(AgentMode.TRADING)

        agents_enabled = [
            config.include_fundamental_agent,
            config.include_technical_agent,
            config.include_risk_agent,
            config.include_sentiment_agent,
        ]

        assert all(agents_enabled)

    def test_rebalancing_has_core_agents_only(self):
        """測試：REBALANCING 模式只有核心 Sub-agents"""
        config = ToolConfig.get_requirements(AgentMode.REBALANCING)

        # 應有核心分析 agents
        assert config.include_technical_agent is True
        assert config.include_risk_agent is True

        # 不應有情緒相關 agents
        assert config.include_sentiment_agent is False
        assert config.include_fundamental_agent is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
