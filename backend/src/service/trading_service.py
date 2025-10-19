"""
TradingService - 交易服務 API 層

整合 AgentDatabaseService、AgentSessionService 和 TradingAgent，
提供完整的 Agent 執行和管理功能。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from trading.trading_agent import TradingAgent
from service.agents_service import AgentsService, AgentNotFoundError
from common.enums import AgentMode, SessionStatus
from common.logger import logger
from database.models import Agent
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

    整合資料庫服務和 Trading Agent，提供：
    - Agent 任務執行
    - 會話管理
    - 狀態追蹤
    - 執行歷史
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

    async def execute_agent_task(
        self,
        agent_id: str,
        mode: AgentMode | None = None,
        context: dict[str, Any] | None = None,
        max_turns: int | None = None,
    ) -> dict[str, Any]:
        """
        執行 Agent 任務

        Args:
            agent_id: Agent ID
            mode: 執行模式（可選）
            context: 額外上下文（可選）
            max_turns: 最大輪數（可選）

        Returns:
            執行結果字典：
            {
                "success": bool,
                "session_id": str,
                "output": str,
                "trace_id": str,
                "execution_time_ms": int,
                "error": str (如果失敗)
            }

        Raises:
            AgentNotFoundError: Agent 不存在
            AgentBusyError: Agent 正在執行中
            TradingServiceError: 執行失敗
        """
        session_id = None
        start_time = datetime.now()

        try:
            # 1. 檢查 Agent 是否存在並取得配置
            agent_config = await self.agents_service.get_agent_config(agent_id)

            # 2. 檢查 Agent 是否正在執行
            latest_session = await self.session_service.get_latest_session(
                agent_id, status=SessionStatus.RUNNING
            )
            if latest_session:
                logger.warning(
                    f"Agent {agent_id} is busy - Found RUNNING session: {latest_session.id}, "
                    f"started at: {latest_session.start_time}, "
                    f"current time: {datetime.now()}, "
                    f"duration: {(datetime.now() - latest_session.start_time).total_seconds()}s"
                )
                raise AgentBusyError(
                    f"Agent {agent_id} is currently executing session {latest_session.id}"
                )

            # 3. 創建執行會話
            execution_mode = mode or agent_config.current_mode
            session = await self.session_service.create_session(
                agent_id=agent_id,
                session_type="manual_task",
                mode=execution_mode,
                initial_input={"context": context or {}},
            )
            session_id = session.id
            logger.info(f"Created session {session_id} for agent {agent_id}")

            # 4. 更新會話狀態為 RUNNING
            await self.session_service.update_session_status(session_id, SessionStatus.RUNNING)
            logger.debug(f"Session {session_id} status updated to RUNNING")

            # 5. 取得或創建 TradingAgent 實例
            trading_agent = await self._get_or_create_agent(agent_id, agent_config)

            # 6. 執行任務 (max_turns 已移至 Runner.run() 中指定)
            logger.info(f"Starting agent execution - session: {session_id}, mode: {execution_mode}")
            result = await trading_agent.run(mode=execution_mode, context=context)
            logger.info(f"Agent execution completed - session: {session_id}")

            # 7. 計算執行時間
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # 8. 更新會話結果
            await self.session_service.update_session_output(
                session_id,
                final_output={"result": result},
                tools_called=result.get("tools_used", ""),
            )

            # 9. 更新會話狀態為 COMPLETED
            await self.session_service.update_session_status(
                session_id,
                SessionStatus.COMPLETED,
                end_time=end_time,
                execution_time_ms=execution_time_ms,
            )
            logger.debug(f"Session {session_id} status updated to COMPLETED")

            # 10. 記錄追蹤資訊
            if result.get("trace_id"):
                await self.session_service.record_session_trace(
                    session_id, {"trace_id": result["trace_id"]}
                )

            logger.info(
                f"Task completed for agent {agent_id}, session {session_id} ({execution_time_ms}ms)"
            )

            return {
                "success": True,
                "session_id": session_id,
                "output": result.get("output", ""),
                "trace_id": result.get("trace_id", ""),
                "execution_time_ms": execution_time_ms,
            }

        except AgentBusyError:
            raise
        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Task execution failed for agent {agent_id}, session {session_id}: {e}",
                exc_info=True,
            )

            # 更新會話為失敗狀態
            if session_id:
                try:
                    end_time = datetime.now()
                    execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
                    await self.session_service.update_session_status(
                        session_id,
                        SessionStatus.FAILED,
                        end_time=end_time,
                        execution_time_ms=execution_time_ms,
                        error_message=str(e),
                    )
                    logger.info(f"Session {session_id} marked as FAILED due to exception")
                except Exception as update_error:
                    logger.error(
                        f"Failed to update session {session_id} to FAILED status: {update_error}",
                        exc_info=True,
                    )

            raise TradingServiceError(f"Task execution failed: {str(e)}")

    async def get_agent_status(self, agent_id: str) -> dict[str, Any]:
        """
        取得 Agent 當前狀態

        Args:
            agent_id: Agent ID

        Returns:
            狀態字典：
            {
                "agent_id": str,
                "name": str,
                "status": str,
                "mode": str,
                "is_initialized": bool,
                "is_running": bool,
                "current_session_id": str | None,
                "last_active_at": str | None
            }

        Raises:
            AgentNotFoundError: Agent 不存在
        """
        try:
            # 1. 取得資料庫配置
            agent_config = await self.agents_service.get_agent_config(agent_id)

            # 2. 檢查是否有運行中的會話
            running_session = await self.session_service.get_latest_session(
                agent_id, status=SessionStatus.RUNNING
            )

            # 3. 檢查記憶體中的狀態
            is_initialized = agent_id in self.active_agents

            return {
                "agent_id": agent_id,
                "name": agent_config.name,
                "status": agent_config.status
                if isinstance(agent_config.status, str)
                else agent_config.status.value,
                "mode": agent_config.current_mode
                if isinstance(agent_config.current_mode, str)
                else agent_config.current_mode.value,
                "is_initialized": is_initialized,
                "is_running": running_session is not None,
                "current_session_id": running_session.id if running_session else None,
                "last_active_at": (
                    agent_config.last_active_at.isoformat() if agent_config.last_active_at else None
                ),
            }

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get agent status {agent_id}: {e}", exc_info=True)
            raise TradingServiceError(f"Failed to get agent status: {str(e)}")

    async def get_execution_history(
        self, agent_id: str, limit: int = 20, status: SessionStatus | None = None
    ) -> dict[str, Any]:
        """
        取得 Agent 執行歷史

        Args:
            agent_id: Agent ID
            limit: 最大返回數量
            status: 過濾狀態（可選）

        Returns:
            歷史記錄字典：
            {
                "agent_id": str,
                "total_sessions": int,
                "sessions": [
                    {
                        "session_id": str,
                        "session_type": str,
                        "mode": str,
                        "status": str,
                        "start_time": str,
                        "end_time": str | None,
                        "execution_time_ms": int | None,
                        "error_message": str | None
                    }
                ]
            }

        Raises:
            AgentNotFoundError: Agent 不存在
        """
        try:
            # 1. 驗證 Agent 存在
            await self.agents_service.get_agent_config(agent_id)

            # 2. 取得會話列表
            sessions = await self.session_service.list_agent_sessions(
                agent_id, limit=limit, status=status
            )

            # 3. 格式化會話資訊
            session_list = [
                {
                    "session_id": s.id,
                    "session_type": s.session_type,
                    "mode": s.mode if isinstance(s.mode, str) else s.mode.value,
                    "status": s.status if isinstance(s.status, str) else s.status.value,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                    "execution_time_ms": s.execution_time_ms,
                    "error_message": s.error_message,
                }
                for s in sessions
            ]

            # 4. 取得總會話數
            total_count = await self.session_service.count_agent_sessions(agent_id, status=status)

            return {
                "agent_id": agent_id,
                "total_sessions": total_count,
                "returned_sessions": len(session_list),
                "sessions": session_list,
            }

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to get execution history for agent {agent_id}: {e}", exc_info=True
            )
            raise TradingServiceError(f"Failed to get execution history: {str(e)}")

    async def get_session_details(self, session_id: str) -> dict[str, Any]:
        """
        取得會話詳細資訊

        Args:
            session_id: Session ID

        Returns:
            會話詳情字典

        Raises:
            SessionError: 會話不存在或查詢失敗
        """
        try:
            session = await self.session_service.get_session(session_id)

            return {
                "session_id": session.id,
                "agent_id": session.agent_id,
                "session_type": session.session_type,
                "mode": session.mode if isinstance(session.mode, str) else session.mode.value,
                "status": session.status
                if isinstance(session.status, str)
                else session.status.value,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "execution_time_ms": session.execution_time_ms,
                "initial_input": session.initial_input,
                "final_output": session.final_output,
                "tools_called": session.tools_called,
                "error_message": session.error_message,
                "trace_data": session.trace_data,
            }

        except Exception as e:
            logger.error(f"Failed to get session details {session_id}: {e}", exc_info=True)
            raise

    async def get_agent_statistics(self, agent_id: str) -> dict[str, Any]:
        """
        取得 Agent 統計資訊

        Args:
            agent_id: Agent ID

        Returns:
            統計資訊字典

        Raises:
            AgentNotFoundError: Agent 不存在
        """
        try:
            # 1. 驗證 Agent 存在
            await self.agents_service.get_agent_config(agent_id)

            # 2. 取得會話統計
            stats = await self.session_service.get_session_statistics(agent_id)

            return {
                "agent_id": agent_id,
                "statistics": stats,
            }

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get statistics for agent {agent_id}: {e}", exc_info=True)
            raise TradingServiceError(f"Failed to get agent statistics: {str(e)}")

    async def cleanup_stuck_sessions(
        self, agent_id: str, timeout_minutes: int = 30
    ) -> dict[str, Any]:
        """
        清理卡住的 RUNNING 會話

        Args:
            agent_id: Agent ID
            timeout_minutes: 超時時間（分鐘），預設 30 分鐘

        Returns:
            清理結果：
            {
                "success": bool,
                "agent_id": str,
                "cleaned_sessions": list[str],
                "count": int
            }

        Raises:
            AgentNotFoundError: Agent 不存在
            TradingServiceError: 清理失敗
        """
        try:
            # 1. 驗證 Agent 存在
            await self.agents_service.get_agent_config(agent_id)

            # 2. 清理卡住的 session
            cleaned_ids = await self.session_service.cleanup_stuck_sessions(
                agent_id, timeout_minutes
            )

            return {
                "success": True,
                "agent_id": agent_id,
                "cleaned_sessions": cleaned_ids,
                "count": len(cleaned_ids),
            }

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to cleanup stuck sessions for agent {agent_id}: {e}", exc_info=True
            )
            raise TradingServiceError(f"Failed to get agent statistics: {str(e)}")

    async def abort_running_sessions(
        self, agent_id: str, reason: str = "Manually aborted"
    ) -> dict[str, Any]:
        """
        強制中斷正在執行的會話

        立即終止所有正在執行的 session，用於手動中斷

        Args:
            agent_id: Agent ID
            reason: 中斷原因

        Returns:
            中斷結果：
            {
                "success": bool,
                "agent_id": str,
                "aborted_sessions": list[str],
                "count": int
            }

        Raises:
            AgentNotFoundError: Agent 不存在
            TradingServiceError: 中斷失敗
        """
        try:
            # 1. 驗證 Agent 存在
            await self.agents_service.get_agent_config(agent_id)

            # 2. 強制中斷所有 RUNNING session
            aborted_ids = await self.session_service.abort_running_sessions(agent_id, reason)

            return {
                "success": True,
                "agent_id": agent_id,
                "aborted_sessions": aborted_ids,
                "count": len(aborted_ids),
            }

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to abort running sessions for agent {agent_id}: {e}", exc_info=True
            )
            raise TradingServiceError(f"Failed to abort running sessions: {str(e)}")

    async def _get_or_create_agent(
        self, agent_id: str, agent_config: Agent | None = None
    ) -> TradingAgent:
        """
        取得或創建 TradingAgent 實例

        Args:
            agent_id: Agent ID
            agent_config: Agent 配置

        Returns:
            TradingAgent 實例

        Raises:
            AgentInitializationError: 初始化失敗
        """
        # 如果已經在記憶體中，直接返回
        if agent_id in self.active_agents:
            agent = self.active_agents[agent_id]
            if agent.is_initialized:
                return agent
            # 如果存在但未初始化，重新初始化
            logger.info(f"Re-initializing agent {agent_id}")
            await agent.initialize()
            return agent

        # 創建新的 TradingAgent 實例
        logger.info(f"Creating new TradingAgent instance for {agent_id}")
        agent = TradingAgent(agent_id, agent_config, self.agents_service)
        await agent.initialize()

        # 儲存到活躍列表
        self.active_agents[agent_id] = agent

        return agent

    async def cleanup(self) -> None:
        """
        清理資源（停止所有活躍的 Agent）
        """
        logger.info(f"Cleaning up TradingService ({len(self.active_agents)} active agents)")

        for agent_id, agent in list(self.active_agents.items()):
            try:
                await agent.stop()
                logger.debug(f"Stopped agent {agent_id}")
            except Exception as e:
                logger.error(f"Error stopping agent {agent_id}: {e}")

        self.active_agents.clear()
        logger.info("TradingService cleanup completed")

    def __repr__(self) -> str:
        return f"<TradingService active_agents={len(self.active_agents)}>"
