"""
CasualTrader Agent System
使用 OpenAI Agent SDK 實現的 AI 股票交易代理人系統
使用 Python 3.12+ 語法特性
"""

from __future__ import annotations

from .core.agent_manager import AgentManager
from .core.agent_session import AgentSession
from .core.base_agent import CasualTradingAgent
from .core.models import (
    AgentConfig,
    AgentCreationRequest,
    AgentCreationResponse,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentMode,
    AgentState,
    AgentStatus,
    AutoAdjustSettings,
    InvestmentPreferences,
    SessionStatus,
    StrategyChange,
    TradingSettings,
    create_default_agent_config,
    generate_agent_id,
    generate_session_id,
)
from .integrations import (
    AgentDatabaseService,
    DatabaseConfig,
    PersistentTradingAgent,
)
from .trading.trading_agent import TradingAgent

__all__ = [
    # Core Classes
    "CasualTradingAgent",
    "AgentManager",
    "AgentSession",
    "TradingAgent",
    # Integration Classes
    "AgentDatabaseService",
    "DatabaseConfig",
    "PersistentTradingAgent",
    # Models and Enums
    "AgentConfig",
    "AgentState",
    "AgentExecutionContext",
    "AgentExecutionResult",
    "AgentMode",
    "AgentStatus",
    "SessionStatus",
    "AutoAdjustSettings",
    "InvestmentPreferences",
    "TradingSettings",
    "StrategyChange",
    "AgentCreationRequest",
    "AgentCreationResponse",
    # Utility Functions
    "create_default_agent_config",
    "generate_agent_id",
    "generate_session_id",
]
