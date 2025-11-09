"""
Schemas package
提供 Pydantic API 模型用於請求與回應驗證
"""

from .agent import (
    AgentListResponse,
    AgentResponse,
    CreateAgentRequest,
    SessionResponse,
    StartAgentRequest,
    UpdateAgentRequest,
    UpdateModeRequest,
)
from .trading import TradeRecord
from .websocket import ErrorResponse, WebSocketMessage

__all__ = [
    # Agent schemas
    "CreateAgentRequest",
    "UpdateAgentRequest",
    "StartAgentRequest",
    "UpdateModeRequest",
    "AgentResponse",
    "AgentListResponse",
    "SessionResponse",
    # Trading schemas
    "TradeRecord",
    # WebSocket schemas
    "WebSocketMessage",
    "ErrorResponse",
]
