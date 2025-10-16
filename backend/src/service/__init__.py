"""
Service Package
"""

from __future__ import annotations

# 新的簡化服務
from .agents_service import AgentsService
from .session_service import AgentSessionService
# TradingService 延遲導入以避免循環依賴

__all__ = [
    # 新架構
    "AgentsService",
    "AgentSessionService",
    "TradingService",
]


def __getattr__(name: str):
    """延遲導入以避免循環依賴"""
    if name == "TradingService":
        from .trading_service import TradingService

        return TradingService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
