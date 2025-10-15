"""
概念驗證: Agent 資料庫服務
展示從資料庫載入配置的核心流程
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Agent, AgentStatus

logger = logging.getLogger(__name__)


class AgentNotFoundError(Exception):
    """Agent 不存在於資料庫"""

    pass


class AgentConfigurationError(Exception):
    """Agent 配置錯誤"""

    pass


class POCAgentDatabaseService:
    """
    概念驗證: Agent 資料庫服務

    簡化版本，用於驗證資料庫整合流程
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_agent_config(self, agent_id: str) -> Agent:
        """
        載入 Agent 配置

        Args:
            agent_id: Agent ID

        Returns:
            Agent 模型實例

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentConfigurationError: 配置格式錯誤
        """
        try:
            stmt = select(Agent).where(Agent.id == agent_id)
            result = await self.session.execute(stmt)
            agent = result.scalar_one_or_none()

            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found in database")

            # 驗證配置
            self._validate_agent_config(agent)

            logger.info(f"Loaded agent config: {agent_id} (model: {agent.ai_model})")
            return agent

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error loading agent config: {e}", exc_info=True)
            raise AgentConfigurationError(f"Failed to load agent config: {str(e)}")

    async def list_active_agents(self) -> list[Agent]:
        """取得所有 ACTIVE 狀態的 Agents"""
        stmt = select(Agent).where(Agent.status == AgentStatus.ACTIVE)
        result = await self.session.execute(stmt)
        agents = list(result.scalars().all())
        logger.info(f"Found {len(agents)} active agents")
        return agents

    def _validate_agent_config(self, agent: Agent) -> None:
        """
        驗證 Agent 配置完整性

        Raises:
            AgentConfigurationError: 配置驗證失敗
        """
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
            解析後的字典
        """
        if not agent.investment_preferences:
            return self._get_default_preferences()

        try:
            return json.loads(agent.investment_preferences)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse preferences for {agent.id}, using defaults")
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
        }


# ==========================================
# POC Test Function
# ==========================================


async def test_poc_database_service():
    """測試 POC 資料庫服務"""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from .models import AgentMode, Base

    print("=" * 60)
    print("POC Database Service Test")
    print("=" * 60)

    # 建立測試用資料庫
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 建立測試 agent
        test_agent = Agent(
            id="test_agent_001",
            name="Test Trading Agent",
            description="POC test agent",
            instructions="Test instructions for POC",
            ai_model="gpt-4o-mini",
            initial_funds=100000.00,
            max_position_size=10.0,
            status=AgentStatus.ACTIVE,
            current_mode=AgentMode.OBSERVATION,
            investment_preferences=json.dumps(
                {"enabled_tools": {"web_search": True, "fundamental_analysis": True}}
            ),
        )

        session.add(test_agent)
        await session.commit()

        print("\n✓ Created test agent in database")

        # 測試載入配置
        service = POCAgentDatabaseService(session)

        print("\nLoading agent config...")
        loaded_agent = await service.get_agent_config("test_agent_001")

        print(f"\n✓ Loaded agent: {loaded_agent.name}")
        print(f"  - ID: {loaded_agent.id}")
        print(f"  - Model: {loaded_agent.ai_model}")
        print(f"  - Initial Funds: TWD {float(loaded_agent.initial_funds):,.0f}")
        print(f"  - Status: {loaded_agent.status.value}")

        # 測試解析偏好設定
        prefs = service.parse_investment_preferences(loaded_agent)
        print("\n✓ Parsed investment preferences:")
        print(f"  - Enabled tools: {list(prefs['enabled_tools'].keys())}")

        # 測試列出活躍 agents
        active_agents = await service.list_active_agents()
        print(f"\n✓ Found {len(active_agents)} active agent(s)")

        # 測試錯誤情況
        print("\nTesting error handling...")
        try:
            await service.get_agent_config("nonexistent")
        except AgentNotFoundError as e:
            print(f"✓ Correctly raised AgentNotFoundError: {e}")

    await engine.dispose()
    print("\n" + "=" * 60)
    print("POC Database Service Test Completed")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_poc_database_service())
