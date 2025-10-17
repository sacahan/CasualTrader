"""
Common package for CasualTrader Backend

包含所有模組共用的基礎定義。
"""

from .enums import (
    AgentMode,
    AgentStatus,
    ModelType,
    SessionStatus,
    TransactionAction,
    TransactionStatus,
    get_all_agent_modes,
    get_all_agent_statuses,
    get_all_session_statuses,
    validate_agent_mode,
    validate_agent_status,
    validate_session_status,
)

__all__ = [
    # Enums
    "AgentStatus",
    "AgentMode",
    "SessionStatus",
    "TransactionAction",
    "TransactionStatus",
    "ModelType",
    # Utility functions
    "validate_agent_status",
    "validate_agent_mode",
    "validate_session_status",
    "get_all_agent_statuses",
    "get_all_agent_modes",
    "get_all_session_statuses",
]
