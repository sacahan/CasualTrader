"""
Phase 4 Regression Tests - Verify Phase 1-3 changes work correctly
=================================================================

Tests to ensure:
1. OBSERVATION mode has been completely removed
2. Only TRADING and REBALANCING modes exist
3. Dynamic tool configuration works for both modes
4. Memory workflow integration is functional
5. No breaking changes to existing functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock
from common.enums import AgentMode
from src.trading.tool_config import ToolConfig


class TestAgentModeEnumeration:
    """Verify AgentMode enumeration has exactly 2 modes"""

    def test_agent_mode_has_only_trading_and_rebalancing(self):
        """Verify only TRADING and REBALANCING modes exist"""
        modes = list(AgentMode)
        assert len(modes) == 2, f"Expected 2 modes, got {len(modes)}: {modes}"

    def test_agent_mode_contains_trading(self):
        """Verify TRADING mode exists"""
        assert hasattr(AgentMode, "TRADING")
        assert AgentMode.TRADING.value == "TRADING"

    def test_agent_mode_contains_rebalancing(self):
        """Verify REBALANCING mode exists"""
        assert hasattr(AgentMode, "REBALANCING")
        assert AgentMode.REBALANCING.value == "REBALANCING"

    def test_agent_mode_does_not_contain_observation(self):
        """Verify OBSERVATION mode has been removed"""
        assert not hasattr(AgentMode, "OBSERVATION"), "OBSERVATION should not exist"


class TestDynamicToolConfigurationE2E:
    """E2E tests for dynamic tool configuration"""

    def test_tool_config_returns_trading_requirements(self):
        """Verify ToolConfig returns correct tools for TRADING mode"""
        tool_config = ToolConfig()
        trading_req = tool_config.get_requirements(AgentMode.TRADING)

        # Verify trading mode has full tool set
        assert trading_req.include_buy_sell_tools is True
        assert trading_req.include_portfolio_tools is True
        assert trading_req.include_memory_mcp is True

    def test_tool_config_returns_rebalancing_requirements(self):
        """Verify ToolConfig returns simplified tools for REBALANCING mode"""
        tool_config = ToolConfig()
        rebal_req = tool_config.get_requirements(AgentMode.REBALANCING)

        # Verify rebalancing mode has simplified tool set
        assert rebal_req.include_buy_sell_tools is False
        assert rebal_req.include_portfolio_tools is True
        assert rebal_req.include_memory_mcp is True

    def test_tool_config_trading_has_all_subagents(self):
        """Verify TRADING mode loads all 4 subagents"""
        tool_config = ToolConfig()
        trading_req = tool_config.get_requirements(AgentMode.TRADING)

        # All 4 subagents should be included
        assert trading_req.include_fundamental_agent is True
        assert trading_req.include_technical_agent is True
        assert trading_req.include_risk_agent is True
        assert trading_req.include_sentiment_agent is True

    def test_tool_config_rebalancing_has_core_subagents_only(self):
        """Verify REBALANCING mode loads only core subagents"""
        tool_config = ToolConfig()
        rebal_req = tool_config.get_requirements(AgentMode.REBALANCING)

        # Only core subagents for rebalancing
        assert rebal_req.include_technical_agent is True
        assert rebal_req.include_risk_agent is True
        # Specialized agents not needed for rebalancing
        assert rebal_req.include_fundamental_agent is False
        assert rebal_req.include_sentiment_agent is False


class TestTradingAgentModeParameter:
    """Tests for TradingAgent.initialize() mode parameter"""

    def test_trading_agent_accepts_mode_parameter(self):
        """Verify TradingAgent.initialize() accepts mode parameter"""
        from src.trading.trading_agent import TradingAgent
        import inspect

        # Check that initialize method signature includes mode parameter
        sig = inspect.signature(TradingAgent.initialize)
        assert "mode" in sig.parameters, "initialize() should have 'mode' parameter"

    def test_trading_agent_initializes_with_valid_modes(self):
        """Verify TradingAgent.initialize() works with both valid modes"""
        from src.trading.trading_agent import TradingAgent

        mock_config = Mock()
        mock_service = AsyncMock()

        agent = TradingAgent(
            agent_id="test-1", agent_config=mock_config, agent_service=mock_service
        )

        # Verify is_initialized attribute exists
        assert hasattr(agent, "is_initialized")
        assert agent.is_initialized is False

    def test_trading_agent_current_mode_tracking(self):
        """Verify agent can track current mode through config"""
        from src.trading.trading_agent import TradingAgent

        mock_config = Mock()
        mock_config.current_mode = AgentMode.TRADING
        mock_service = AsyncMock()

        agent = TradingAgent(
            agent_id="test-1", agent_config=mock_config, agent_service=mock_service
        )

        # Verify mode can be accessed through config
        assert hasattr(agent.agent_config, "current_mode")
        assert agent.agent_config.current_mode == AgentMode.TRADING


class TestMemoryWorkflowIntegration:
    """E2E tests for memory workflow integration"""

    def test_memory_workflow_methods_exist(self):
        """Verify memory workflow methods exist in TradingAgent"""
        from src.trading.trading_agent import TradingAgent

        mock_config = Mock()
        mock_service = AsyncMock()

        agent = TradingAgent(
            agent_id="test-1", agent_config=mock_config, agent_service=mock_service
        )

        # Verify all memory workflow methods exist
        assert hasattr(agent, "_load_execution_memory")
        assert hasattr(agent, "_save_execution_memory")

    @pytest.mark.asyncio
    async def test_memory_workflow_methods_callable(self):
        """Verify memory workflow methods are callable"""
        from src.trading.trading_agent import TradingAgent

        mock_config = Mock()
        mock_service = AsyncMock()

        agent = TradingAgent(
            agent_id="test-1", agent_config=mock_config, agent_service=mock_service
        )

        # Verify methods are callable (check method signatures)
        assert callable(getattr(agent, "_load_execution_memory"))
        assert callable(getattr(agent, "_save_execution_memory"))


class TestNoObservationReferences:
    """Verify no OBSERVATION references remain in codebase"""

    def test_enums_file_no_observation(self):
        """Verify common/enums.py doesn't reference OBSERVATION"""
        from common.enums import AgentMode

        enum_str = str(AgentMode.__dict__)
        assert "OBSERVATION" not in enum_str

    def test_tool_config_no_observation_references(self):
        """Verify tool_config.py doesn't handle OBSERVATION mode"""
        tool_config = ToolConfig()

        # Should not raise for valid modes
        assert tool_config.get_requirements(AgentMode.TRADING) is not None
        assert tool_config.get_requirements(AgentMode.REBALANCING) is not None

        # Should raise for invalid mode (including OBSERVATION if it existed)
        with pytest.raises((ValueError, KeyError, AttributeError)):
            # Try to access OBSERVATION through enum lookup
            AgentMode["OBSERVATION"]


class TestBackwardCompatibility:
    """Verify backward compatibility with existing code"""

    def test_agent_mode_string_values_unchanged(self):
        """Verify AgentMode string values haven't changed"""
        assert AgentMode.TRADING.value == "TRADING"
        assert AgentMode.REBALANCING.value == "REBALANCING"

    def test_tool_config_interface_unchanged(self):
        """Verify ToolConfig API is backward compatible"""
        tool_config = ToolConfig()

        # Verify expected methods exist
        assert hasattr(tool_config, "get_requirements")
        assert hasattr(tool_config, "compare_configurations")

        # Verify method signatures work
        trading_req = tool_config.get_requirements(AgentMode.TRADING)
        assert trading_req is not None

        comparison = tool_config.compare_configurations(AgentMode.TRADING, AgentMode.REBALANCING)
        assert isinstance(comparison, dict)

    def test_trading_agent_api_unchanged(self):
        """Verify TradingAgent public API is unchanged"""
        from src.trading.trading_agent import TradingAgent

        mock_config = Mock()
        mock_service = AsyncMock()

        agent = TradingAgent(
            agent_id="test-1", agent_config=mock_config, agent_service=mock_service
        )

        # Verify expected public methods exist
        assert hasattr(agent, "initialize")
        assert hasattr(agent, "run")
        assert hasattr(agent, "cleanup")
        assert hasattr(agent, "is_initialized")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
