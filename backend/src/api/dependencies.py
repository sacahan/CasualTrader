"""
FastAPI Dependencies

Dependency injection functions for FastAPI routes.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from service.agent_executor import AgentExecutor
from service.agents_service import AgentsService
from service.trading_service import TradingService
from api.config import get_db_session

# Global executor instance
_executor: AgentExecutor | None = None


def set_executor(executor: AgentExecutor) -> None:
    """Set the global executor instance."""
    global _executor
    _executor = executor


def get_executor() -> AgentExecutor:
    """
    FastAPI dependency for Agent Executor.

    Returns:
        AgentExecutor: Global agent executor instance

    Raises:
        RuntimeError: If executor is not initialized

    Example:
        ```python
        @router.post("/start")
        async def start_agent(agent_id: str, executor: AgentExecutor = Depends(get_executor)):
            await executor.start(agent_id)
        ```
    """
    if _executor is None:
        raise RuntimeError("Agent Executor not initialized")
    return _executor


def get_agents_service(db_session: AsyncSession = Depends(get_db_session)) -> AgentsService:
    """
    FastAPI dependency for AgentsService.

    Args:
        db_session: SQLAlchemy 異步 session

    Returns:
        AgentsService: Service instance for agent operations
    """
    return AgentsService(db_session)


def get_trading_service(db_session: AsyncSession = Depends(get_db_session)) -> TradingService:
    """
    FastAPI dependency for TradingService.

    Args:
        db_session: SQLAlchemy 異步 session

    Returns:
        TradingService: Service instance for trading operations
    """
    return TradingService(db_session)
