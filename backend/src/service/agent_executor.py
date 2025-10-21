"""
AgentExecutor - Agent 執行器（已簡化，不再支持循環）

該類已簡化為最小功能，主要用於狀態追蹤。
實際執行由 TradingService.execute_single_mode() 負責。
"""

from __future__ import annotations

from common.logger import logger


# ==========================================
# Custom Exceptions
# ==========================================


class AgentExecutorError(Exception):
    """AgentExecutor 基礎錯誤"""

    pass


class NotRunningError(AgentExecutorError):
    """Agent 未執行中"""

    pass


# ==========================================
# AgentExecutor
# ==========================================


class AgentExecutor:
    """
    Agent 執行器（已簡化）

    注意：該類已簡化為最小功能。不再支持循環執行。
    實際執行由 TradingService.execute_single_mode() 負責。
    """

    def __init__(self):
        """初始化 AgentExecutor"""
        logger.info("AgentExecutor initialized (simplified, no cycling)")

    def get_status(self, agent_id: str) -> dict:
        """
        獲取 Agent 狀態（簡化版本）

        Args:
            agent_id: Agent ID

        Returns:
            狀態字典（已簡化，不再包含循環相關信息）
        """
        return {
            "is_running": False,  # 不再支持長時間循環
            "current_mode": None,
            "last_cycle_at": None,
            "cycle_count": 0,
            "interval_minutes": None,
        }

    async def stop_all(self) -> None:
        """停止所有 agent（已成為空操作）"""
        logger.info("stop_all called (no-op, use TradingService.stop_agent instead)")
