"""
CasualTrader API Layer

FastAPI backend for the CasualTrader AI trading simulator.
"""

from .app import create_app
from .websocket import WebSocketManager

__all__ = [
    "create_app",
    "WebSocketManager",
]
