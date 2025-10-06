"""
CasualTrader Agent System
使用 OpenAI Agent SDK 實現的 AI 股票交易代理人系統
使用 Python 3.12+ 語法特性
"""

from __future__ import annotations

from .core.base_agent import CasualTradingAgent
from .core.agent_manager import AgentManager
from .core.agent_session import AgentSession
from .core.models import (
    AgentConfig,
    AgentState,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentMode,
    AgentStatus,
    SessionStatus,
    AutoAdjustSettings,
    InvestmentPreferences,
    TradingSettings,
    StrategyChange,
    AgentCreationRequest,
    AgentCreationResponse,
    create_default_agent_config,
    generate_agent_id,
    generate_session_id,
)
from .trading.trading_agent import TradingAgent
from .integrations import (
    AgentDatabaseService,
    DatabaseConfig,
    PersistentTradingAgent,
)

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
