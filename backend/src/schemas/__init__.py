"""
Schemas package
提供 Pydantic API 模型用於請求與回應驗證
"""

from .agent import (
    AgentListResponse,
    AgentResponse,
    CreateAgentRequest,
    EnabledTools,
    PortfolioSnapshot,
    StartAgentRequest,
    UpdateAgentRequest,
    UpdateModeRequest,
)
from .trading import StrategyChange, TradeRecord
from .websocket import ErrorResponse, WebSocketMessage

__all__ = [
    # Agent schemas
    "EnabledTools",
    "CreateAgentRequest",
    "UpdateAgentRequest",
    "StartAgentRequest",
    "UpdateModeRequest",
    "PortfolioSnapshot",
    "AgentResponse",
    "AgentListResponse",
    # Trading schemas
    "TradeRecord",
    "StrategyChange",
    # WebSocket schemas
    "WebSocketMessage",
    "ErrorResponse",
]
