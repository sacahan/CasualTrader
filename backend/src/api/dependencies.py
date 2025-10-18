"""
FastAPI Dependencies

Dependency injection functions for FastAPI routes.
"""

from service.agent_executor import AgentExecutor

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
        async def start_agent(
            agent_id: str,
            executor: AgentExecutor = Depends(get_executor)
        ):
            await executor.start(agent_id)
        ```
    """
    if _executor is None:
        raise RuntimeError("Agent Executor not initialized")
    return _executor
