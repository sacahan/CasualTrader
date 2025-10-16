"""
Agent 資料庫服務層

提供 Agent 配置的 CRUD 操作和錯誤處理
基於 POC 實作，增強功能和錯誤處理
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Agent, AgentMode, AgentStatus

logger = logging.getLogger(__name__)


# ==========================================
# Custom Exceptions
# ==========================================


class AgentNotFoundError(Exception):
    """Agent 不存在於資料庫"""

    pass


class AgentConfigurationError(Exception):
    """Agent 配置錯誤"""

    pass


class AgentDatabaseError(Exception):
    """資料庫操作錯誤"""

    pass


# ==========================================
# Agents Service
# ==========================================


class AgentsService:
    """
    Agents 資料庫服務

    提供 Agents 配置的完整 CRUD 操作
    """

    def __init__(self, session: AsyncSession):
        """
        初始化 Agents 資料庫服務

        Args:
            session: SQLAlchemy 異步 Session
        """
        self.session = session

    # ==========================================
    # Query Operations
    # ==========================================

    async def get_agent_config(self, agent_id: str) -> Agent:
        """
        載入 Agents 配置

        Args:
            agent_id: Agent ID

        Returns:
            Agent 模型實例

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentConfigurationError: 配置格式錯誤
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(Agent).where(Agent.id == agent_id)
            result = await self.session.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found in database")

            # 驗證必要欄位
            self._validate_agent_config(agent)

            logger.info(f"Loaded agent config: {agent_id} (model: {agent.ai_model})")
            return agent

        except AgentNotFoundError:
            raise
        except AgentConfigurationError:
            raise
        except Exception as e:
            logger.error(f"Database error loading agent {agent_id}: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to load agent config: {str(e)}")

    async def get_agent_with_holdings(self, agent_id: str) -> Agent:
        """
        載入 Agents 配置和持倉資料

        Args:
            agent_id: Agent ID

        Returns:
            Agent 模型實例（包含 holdings 關聯）

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(Agent).where(Agent.id == agent_id).options(selectinload(Agent.holdings))
            result = await self.session.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found")

            logger.info(f"Loaded agent with {len(agent.holdings)} holdings: {agent_id}")
            return agent

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Database error loading agent with holdings: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to load agent with holdings: {str(e)}")

    async def list_active_agents(self) -> list[Agent]:
        """
        取得所有 ACTIVE 狀態的 Agents

        Returns:
            Agent 列表

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(Agent).where(Agent.status == AgentStatus.ACTIVE)
            result = await self.session.execute(stmt)
            agents = list(result.scalars().all())

            logger.info(f"Found {len(agents)} active agents")
            return agents

        except Exception as e:
            logger.error(f"Database error listing active agents: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to list active agents: {str(e)}")

    async def list_agents_by_status(self, status: AgentStatus) -> list[Agent]:
        """
        取得指定狀態的 Agents

        Args:
            status: Agent 狀態

        Returns:
            Agent 列表

        Raises:
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(Agent).where(Agent.status == status)
            result = await self.session.execute(stmt)
            agents = list(result.scalars().all())

            logger.info(f"Found {len(agents)} agents with status {status.value}")
            return agents

        except Exception as e:
            logger.error(f"Database error listing agents by status: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to list agents by status: {str(e)}")

    # ==========================================
    # Update Operations
    # ==========================================

    async def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus,
        mode: AgentMode | None = None,
    ) -> None:
        """
        更新 Agent 狀態

        Args:
            agent_id: Agent ID
            status: 新狀態
            mode: 新模式（可選）

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentDatabaseError: 資料庫操作失敗
        """
        try:
            stmt = select(Agent).where(Agent.id == agent_id)
            result = await self.session.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found")

            agent.status = status
            if mode:
                agent.current_mode = mode

            await self.session.commit()
            logger.info(f"Updated agent {agent_id} status to {status.value}")

        except AgentNotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Database error updating agent status: {e}", exc_info=True)
            raise AgentDatabaseError(f"Failed to update agent status: {str(e)}")

    # ==========================================
    # Validation and Parsing
    # ==========================================

    def _validate_agent_config(self, agent: Agent) -> None:
        """
        驗證 Agent 配置完整性

        Args:
            agent: Agent 模型實例

        Raises:
            AgentConfigurationError: 配置驗證失敗
        """
        # 驗證必要欄位
        if not agent.name:
            raise AgentConfigurationError("Agent name is required")

        if not agent.instructions:
            raise AgentConfigurationError("Agent instructions are required")

        if not agent.ai_model:
            raise AgentConfigurationError("AI model is required")

        # 驗證 JSON 格式
        if agent.investment_preferences:
            try:
                json.loads(agent.investment_preferences)
            except json.JSONDecodeError as e:
                raise AgentConfigurationError(f"Invalid investment_preferences JSON: {str(e)}")

    def parse_investment_preferences(self, agent: Agent) -> dict[str, Any]:
        """
        解析 investment_preferences JSON

        Args:
            agent: Agent 模型實例

        Returns:
            解析後的字典（如果為空則返回預設值）
        """
        if not agent.investment_preferences:
            return self._get_default_preferences()

        try:
            return json.loads(agent.investment_preferences)
        except json.JSONDecodeError:
            logger.warning(
                f"Failed to parse investment_preferences for agent {agent.id}, using defaults"
            )
            return self._get_default_preferences()

    def _get_default_preferences(self) -> dict[str, Any]:
        """預設投資偏好"""
        return {
            "enabled_tools": {
                "fundamental_analysis": True,
                "technical_analysis": True,
                "risk_assessment": True,
                "sentiment_analysis": True,
                "web_search": True,
                "code_interpreter": True,
            },
            "risk_tolerance": "moderate",
            "max_single_position": 10.0,
            "stop_loss_percent": 8.0,
            "take_profit_percent": 15.0,
        }

    # ==========================================
    # Context Manager Support
    # ==========================================

    async def __aenter__(self):
        """進入異步上下文管理器"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出異步上下文管理器"""
        if exc_type is not None:
            await self.session.rollback()
        await self.session.close()
