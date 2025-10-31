"""
TradingService - 交易服務層

提供 Agent 單一模式執行的服務（手動觸發設計）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from trading.trading_agent import TradingAgent
from service.agents_service import AgentsService, AgentNotFoundError
from common.enums import AgentMode, AgentStatus, SessionStatus
from common.logger import logger
from service.session_service import AgentSessionService


# ==========================================
# Custom Exceptions
# ==========================================


class TradingServiceError(Exception):
    """TradingService 基礎錯誤"""

    pass


class AgentBusyError(TradingServiceError):
    """Agent 正在執行中"""

    pass


class InvalidOperationError(TradingServiceError):
    """無效操作"""

    pass


# ==========================================
# TradingService
# ==========================================


class TradingService:
    """
    交易服務層

    提供單一模式執行功能（手動觸發）：
    - 執行指定模式並完成後立即返回
    - 資源清理（finally 塊確保）
    - 會話管理
    """

    def __init__(self, db_session: AsyncSession):
        """
        初始化 TradingService

        Args:
            db_session: SQLAlchemy 異步 session
        """
        self.db_session = db_session
        self.agents_service = AgentsService(db_session)
        self.session_service = AgentSessionService(db_session)

        # 活躍的 TradingAgent 實例（記憶體中）
        self.active_agents: dict[str, TradingAgent] = {}

        logger.info("TradingService initialized")

    async def execute_single_mode(
        self,
        agent_id: str,
        mode: AgentMode,
        max_turns: int | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        執行單一模式（執行完後立即返回，不再循環轉換）

        Args:
            agent_id: Agent ID
            mode: 執行模式 (TRADING/REBALANCING)
            max_turns: 最大輪數（可選）
            session_id: 既存的 session ID（可選）。如果提供，使用該 session 而不創建新的

        Returns:
            執行結果：
            {
                "success": bool,
                "session_id": str,
                "mode": str,
                "execution_time_ms": int,
                "output": str (可選),
                "error": str (如果失敗)
            }

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentBusyError: Agent 正在執行中
            TradingServiceError: 執行失敗
        """
        start_time = datetime.now()
        agent = None

        try:
            # 1. 檢查 Agent 是否存在
            agent_config = await self.agents_service.get_agent_config(agent_id)

            # 2. 檢查 Agent 是否已在執行
            if agent_id in self.active_agents:
                raise AgentBusyError(f"Agent {agent_id} is already running")

            # 3. 取得或創建執行會話
            if session_id:
                # 使用既存的 session（由 API 層創建）
                session = await self.session_service.get_session(session_id)
                logger.info(f"Using existing session {session_id} for agent {agent_id}")
            else:
                # 創建新會話（直接調用服務層時使用）
                session = await self.session_service.create_session(
                    agent_id=agent_id,
                    mode=mode,
                    initial_input={},
                )
                session_id = session.id
                logger.info(
                    f"🆕 Created session {session_id} for agent {agent_id} ({mode.value}) 🎯"
                )

            # 4. 更新會Session狀態為 RUNNING
            await self.session_service.update_session_status(session_id, SessionStatus.RUNNING)

            # 5. 取得或創建 TradingAgent 實例
            agent = await self._get_or_create_agent(agent_id, agent_config)

            # 6. 標記為活躍
            self.active_agents[agent_id] = agent

            # 7. 初始化 Agent（載入工具、Sub-agents 等）
            logger.info(f"Initializing agent {agent_id}")
            await agent.initialize()

            # 8. 執行指定模式
            logger.info(f"Executing {mode.value} for agent {agent_id}")
            result = await agent.run(mode=mode)

            # 9. 更新會話狀態為 COMPLETED
            await self.session_service.update_session_status(session_id, SessionStatus.COMPLETED)

            # 10. 更新 Agent 狀態為 INACTIVE（執行完成）
            await self.agents_service.update_agent_status(agent_id, status=AgentStatus.INACTIVE)

            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.info(
                f"✅ Completed {mode.value} for agent {agent_id} in {execution_time_ms}ms 🚀"
            )

            return {
                "success": True,
                "session_id": session_id,
                "mode": mode.value,
                "execution_time_ms": execution_time_ms,
                "output": result.get("output") if result else None,
            }

        except AgentNotFoundError:
            raise
        except AgentBusyError:
            raise
        except Exception as e:
            logger.error(f"Error executing {mode.value} for {agent_id}: {e}", exc_info=True)

            # 更新會話狀態為 FAILED
            if session_id:
                try:
                    await self.session_service.update_session_status(
                        session_id, SessionStatus.FAILED, error_message=str(e)
                    )
                except Exception as cleanup_error:
                    logger.error(f"Error updating session {session_id}: {cleanup_error}")

            # 更新 Agent 狀態為 INACTIVE（即使執行失敗）
            await self.agents_service.update_agent_status(agent_id, status=AgentStatus.INACTIVE)

            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            raise TradingServiceError(f"Failed to execute {mode.value}: {str(e)}") from e

        finally:
            # 確保資源清理（即使發生異常）
            if agent_id in self.active_agents:
                try:
                    if agent is not None:
                        await agent.cleanup()
                    logger.debug(f"Cleaned up agent {agent_id}")
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up agent {agent_id}: {cleanup_error}")
                finally:
                    del self.active_agents[agent_id]

    async def stop_agent(self, agent_id: str) -> dict[str, Any]:
        """
        停止 Agent 正在執行的任務

        Args:
            agent_id: Agent ID

        Returns:
            停止結果：
            {
                "success": bool,
                "status": "stopped" | "not_running"
            }

        Raises:
            AgentNotFoundError: Agent 不存在
            TradingServiceError: 停止失敗
        """
        try:
            # 檢查 Agent 是否存在
            await self.agents_service.get_agent_config(agent_id)

            # 檢查是否有正在執行的 agent
            if agent_id not in self.active_agents:
                return {
                    "success": True,
                    "status": "not_running",
                }

            # 取得 agent 並停止
            agent = self.active_agents[agent_id]
            try:
                await agent.cancel()
                logger.info(f"Cancelled agent {agent_id}")
            except Exception as e:
                logger.error(f"Error cancelling agent {agent_id}: {e}")

            # 清理
            try:
                await agent.cleanup()
                logger.debug(f"Cleaned up agent {agent_id}")
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent_id}: {e}")
            finally:
                del self.active_agents[agent_id]

            # 更新 Agent 狀態為 INACTIVE（停止）
            await self.agents_service.update_agent_status(agent_id, status=AgentStatus.INACTIVE)

            return {
                "success": True,
                "status": "stopped",
            }

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
            raise TradingServiceError(f"Failed to stop agent: {str(e)}") from e

    async def _get_or_create_agent(
        self,
        agent_id: str,
        agent_config: Any,
    ) -> TradingAgent:
        """
        獲取或創建 TradingAgent 實例

        Args:
            agent_id: Agent ID
            agent_config: Agent 配置

        Returns:
            TradingAgent 實例

        Raises:
            TypeError: 如果 agents_service 類型不正確
        """
        # 防禦性驗證 - 確保依賴注入正確
        if not isinstance(self.agents_service, AgentsService):
            raise TypeError(
                f"agents_service must be AgentsService instance, "
                f"got {type(self.agents_service).__name__}"
            )

        if agent_id in self.active_agents:
            return self.active_agents[agent_id]

        logger.debug(f"Creating TradingAgent for {agent_id}")
        agent = TradingAgent(agent_id, agent_config, self.agents_service)
        self.active_agents[agent_id] = agent
        return agent

    async def cleanup(self) -> None:
        """清理所有活躍 agent"""
        logger.info(f"Cleaning up {len(self.active_agents)} active agents")

        for agent_id, agent in self.active_agents.items():
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent_id}: {e}")

        self.active_agents.clear()
