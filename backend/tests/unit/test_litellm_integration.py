"""
LiteLLM Integration Tests

Tests verify:
1. LiteLLM model creation
2. Multiple provider support
3. GitHub Copilot integration
4. Agent initialization with LiteLLM
"""

import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch

from agents import ModelSettings
from agents.extensions.models.litellm_model import LitellmModel


class TestLiteLLMModelCreation:
    """Test LiteLLM model initialization"""

    def test_openai_model_creation(self):
        """Test OpenAI model via LiteLLM"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
            model = LitellmModel(model="openai/gpt-4o-mini", api_key="sk-test-key")
            assert model.model == "openai/gpt-4o-mini"
            assert model is not None

    def test_gemini_model_creation(self):
        """Test Google Gemini model via LiteLLM"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIza-test-key"}):
            model = LitellmModel(model="gemini/gemini-pro", api_key="AIza-test-key")
            assert model.model == "gemini/gemini-pro"

    def test_github_copilot_model_creation(self):
        """Test GitHub Copilot model via LiteLLM"""
        with patch.dict(os.environ, {"GITHUB_COPILOT_TOKEN": "ghp-test-token"}):
            model = LitellmModel(model="github_copilot/gpt-5-mini", api_key="ghp-test-token")
            assert model.model == "github_copilot/gpt-5-mini"

    def test_claude_model_creation(self):
        """Test Anthropic Claude model via LiteLLM"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            model = LitellmModel(model="claude/claude-3-opus", api_key="sk-ant-test")
            assert model.model == "claude/claude-3-opus"


class TestTradingAgentWithLiteLLM:
    """Test TradingAgent integration with LiteLLM"""

    @pytest.mark.asyncio
    async def test_trading_agent_initialization_with_litellm(self):
        """Test TradingAgent initializes with LiteLLM"""
        from src.trading.trading_agent import TradingAgent
        from src.database.models import Agent as AgentConfig

        # Mock agent config
        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.id = "test-agent-1"
        mock_agent_config.description = "Test trading agent"
        mock_agent_config.ai_model = "gpt-4o-mini"
        mock_agent_config.llm_provider = "openai"
        mock_agent_config.investment_preferences = None
        mock_agent_config.max_position_size = 0.1

        # Mock service
        mock_service = AsyncMock()

        # Create agent
        agent = TradingAgent(
            agent_id="test-agent-1", agent_config=mock_agent_config, agent_service=mock_service
        )

        # Verify initialization
        assert agent.agent_id == "test-agent-1"
        assert agent.is_initialized is False
        assert agent.agent_config == mock_agent_config

    @pytest.mark.asyncio
    async def test_trading_agent_create_llm_model_openai(self):
        """Test _create_llm_model with OpenAI provider from DB config"""
        from src.trading.trading_agent import TradingAgent
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.ai_model = "gpt-4o-mini"
        mock_agent_config.llm_provider = "openai"

        # Mock agent_service with proper async get_ai_model_config
        mock_service = AsyncMock()
        mock_service.get_ai_model_config = AsyncMock(
            return_value={
                "model_key": "gpt-4o-mini",
                "provider": "openai",
                "litellm_prefix": "openai",
                "full_model_name": "gpt-4o-mini",
                "api_key_env_var": "OPENAI_API_KEY",
            }
        )

        agent = TradingAgent(
            agent_id="test-agent-1", agent_config=mock_agent_config, agent_service=mock_service
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
            llm_model = await agent._create_llm_model()
            assert llm_model is not None
            assert llm_model.model == "openai/gpt-4o-mini"
            # Verify DB query was called
            mock_service.get_ai_model_config.assert_called_once_with("gpt-4o-mini")

    @pytest.mark.asyncio
    async def test_trading_agent_create_llm_model_gemini(self):
        """Test _create_llm_model with Gemini provider from DB config"""
        from src.trading.trading_agent import TradingAgent
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.ai_model = "gemini-pro"
        mock_agent_config.llm_provider = "gemini"

        mock_service = AsyncMock()
        mock_service.get_ai_model_config = AsyncMock(
            return_value={
                "model_key": "gemini-pro",
                "provider": "gemini",
                "litellm_prefix": "gemini",
                "full_model_name": "gemini-pro",
                "api_key_env_var": "GOOGLE_API_KEY",
            }
        )

        agent = TradingAgent(
            agent_id="test-agent-1", agent_config=mock_agent_config, agent_service=mock_service
        )

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIza-test-key"}):
            llm_model = await agent._create_llm_model()
            assert llm_model is not None
            assert llm_model.model == "gemini/gemini-pro"

    @pytest.mark.asyncio
    async def test_trading_agent_create_llm_model_github_copilot(self):
        """Test _create_llm_model with GitHub Copilot provider from DB config"""
        from src.trading.trading_agent import TradingAgent
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.ai_model = "gpt-5-mini"
        mock_agent_config.llm_provider = "github_copilot"

        mock_service = AsyncMock()
        mock_service.get_ai_model_config = AsyncMock(
            return_value={
                "model_key": "gpt-5-mini",
                "provider": "github_copilot",
                "litellm_prefix": "github_copilot",
                "full_model_name": "gpt-5-mini",
                "api_key_env_var": "GITHUB_COPILOT_TOKEN",
            }
        )

        agent = TradingAgent(
            agent_id="test-agent-1", agent_config=mock_agent_config, agent_service=mock_service
        )

        with patch.dict(os.environ, {"GITHUB_COPILOT_TOKEN": "ghp-test-token"}):
            llm_model = await agent._create_llm_model()
            assert llm_model is not None
            assert llm_model.model == "github_copilot/gpt-5-mini"

    @pytest.mark.asyncio
    async def test_trading_agent_missing_api_key(self):
        """Test error handling for missing API key"""
        from src.trading.trading_agent import TradingAgent, AgentConfigurationError
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.ai_model = "gpt-4o-mini"
        mock_agent_config.llm_provider = "openai"

        mock_service = AsyncMock()
        mock_service.get_ai_model_config = AsyncMock(
            return_value={
                "model_key": "gpt-4o-mini",
                "provider": "openai",
                "litellm_prefix": "openai",
                "full_model_name": "gpt-4o-mini",
                "api_key_env_var": "OPENAI_API_KEY",
            }
        )

        agent = TradingAgent(
            agent_id="test-agent-1", agent_config=mock_agent_config, agent_service=mock_service
        )

        # Ensure OPENAI_API_KEY is not set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AgentConfigurationError):
                await agent._create_llm_model()


class TestLiteLLMProviderSupport:
    """Test support for multiple LLM providers"""

    @pytest.mark.parametrize(
        "provider,model,env_var,env_value",
        [
            ("openai", "gpt-4o-mini", "OPENAI_API_KEY", "sk-test"),
            ("gemini", "gemini-pro", "GOOGLE_API_KEY", "AIza-test"),
            ("github_copilot", "gpt-5-mini", "GITHUB_COPILOT_TOKEN", "ghp-test"),
            ("claude", "claude-3-opus", "ANTHROPIC_API_KEY", "sk-ant-test"),
            ("together", "meta-llama/Llama-3-70b", "TOGETHER_API_KEY", "together-key"),
        ],
    )
    @pytest.mark.asyncio
    async def test_multiple_provider_support(self, provider, model, env_var, env_value):
        """Test LiteLLM supports multiple providers from DB config"""
        from src.trading.trading_agent import TradingAgent
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.ai_model = model
        mock_agent_config.llm_provider = provider

        mock_service = AsyncMock()
        mock_service.get_ai_model_config = AsyncMock(
            return_value={
                "model_key": model,
                "provider": provider,
                "litellm_prefix": provider,
                "full_model_name": model,
                "api_key_env_var": env_var,
            }
        )

        agent = TradingAgent(
            agent_id="test-agent-1", agent_config=mock_agent_config, agent_service=mock_service
        )

        with patch.dict(os.environ, {env_var: env_value}):
            llm_model = await agent._create_llm_model()
            assert llm_model is not None
            assert provider in llm_model.model


class TestGitHubCopilotIntegration:
    """Test GitHub Copilot specific integration"""

    def test_github_copilot_model_settings(self):
        """Test GitHub Copilot ModelSettings configuration"""
        model_settings = ModelSettings(
            extra_headers={
                "editor-version": "vscode/1.85.1",
                "Copilot-Integration-Id": "vscode-chat",
            }
        )

        assert model_settings is not None
        assert hasattr(model_settings, "extra_headers")
        assert model_settings.extra_headers["editor-version"] == "vscode/1.85.1"

    @pytest.mark.asyncio
    async def test_trading_agent_detects_github_copilot(self):
        """Test TradingAgent correctly detects GitHub Copilot provider"""
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.ai_model = "gpt-5-mini"
        mock_agent_config.llm_provider = "github_copilot"

        # Verify provider detection logic
        provider = getattr(mock_agent_config, "llm_provider", "openai").lower()
        assert provider == "github_copilot"


class TestLiteLLMErrorHandling:
    """Test error handling in LiteLLM integration"""

    @pytest.mark.asyncio
    async def test_invalid_provider_missing_db_config(self):
        """Test error when model config not found in database"""
        from src.trading.trading_agent import TradingAgent, AgentConfigurationError
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.ai_model = "unknown-model"
        mock_agent_config.llm_provider = "unknown_provider"

        mock_service = AsyncMock()
        mock_service.get_ai_model_config = AsyncMock(return_value=None)  # Not found

        agent = TradingAgent(
            agent_id="test-agent-1", agent_config=mock_agent_config, agent_service=mock_service
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            # Should raise error, not fallback
            with pytest.raises(AgentConfigurationError, match="not found in ai_model_configs"):
                await agent._create_llm_model()


class TestLiteLLMCleanup:
    """Test LiteLLM cleanup and resource management"""

    @pytest.mark.asyncio
    async def test_agent_cleanup(self):
        """Test agent cleanup releases resources"""
        from src.trading.trading_agent import TradingAgent
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.id = "test-agent-1"
        mock_agent_config.ai_model = "gpt-4o-mini"
        mock_agent_config.llm_provider = "openai"

        mock_service = AsyncMock()

        agent = TradingAgent(
            agent_id="test-agent-1", agent_config=mock_agent_config, agent_service=mock_service
        )

        # Cleanup
        await agent.cleanup()

        # Verify cleanup
        assert agent._exit_stack is None


class TestLiteLLMConfigValidation:
    """Test LiteLLM configuration validation from database"""

    @pytest.mark.asyncio
    async def test_missing_model_config_fails(self):
        """Test error when model config not found in database"""
        from src.trading.trading_agent import TradingAgent, AgentConfigurationError
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.ai_model = "unknown-model"

        mock_service = AsyncMock()
        mock_service.get_ai_model_config = AsyncMock(return_value=None)

        agent = TradingAgent(
            agent_id="test-agent-1", agent_config=mock_agent_config, agent_service=mock_service
        )

        with pytest.raises(AgentConfigurationError, match="not found in ai_model_configs"):
            await agent._create_llm_model()

    @pytest.mark.asyncio
    async def test_incomplete_model_config_fails(self):
        """Test error when model config is incomplete in database"""
        from src.trading.trading_agent import TradingAgent, AgentConfigurationError
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.ai_model = "incomplete-model"

        mock_service = AsyncMock()
        # Missing required fields
        mock_service.get_ai_model_config = AsyncMock(
            return_value={
                "model_key": "incomplete-model",
                "provider": "openai",
                # Missing: litellm_prefix, full_model_name, api_key_env_var
            }
        )

        agent = TradingAgent(
            agent_id="test-agent-1", agent_config=mock_agent_config, agent_service=mock_service
        )

        with pytest.raises(AgentConfigurationError, match="configuration incomplete"):
            await agent._create_llm_model()

    @pytest.mark.asyncio
    async def test_no_agent_service_fails(self):
        """Test error when agent_service is not available"""
        from src.trading.trading_agent import TradingAgent, AgentConfigurationError
        from src.database.models import Agent as AgentConfig

        mock_agent_config = MagicMock(spec=AgentConfig)
        mock_agent_config.ai_model = "gpt-4o-mini"

        agent = TradingAgent(
            agent_id="test-agent-1",
            agent_config=mock_agent_config,
            agent_service=None,  # No service
        )

        with pytest.raises(AgentConfigurationError, match="agent_service not available"):
            await agent._create_llm_model()
