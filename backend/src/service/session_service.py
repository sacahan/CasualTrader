"""
AgentSessionService - AgentSession 資料庫服務層

提供 Agent 執行會話的 CRUD 操作、狀態追蹤和歷史記錄管理。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AgentSession
from common.enums import SessionStatus
from common.logger import logger


# ==========================================
# Custom Exceptions
# ==========================================


class SessionError(Exception):
    """Session 基礎錯誤"""

    pass


class SessionNotFoundError(SessionError):
    """Session 不存在"""

    pass


class SessionStatusError(SessionError):
    """Session 狀態錯誤"""

    pass


# ==========================================
# AgentSessionService
# ==========================================


class AgentSessionService:
    """
    AgentSession 資料庫服務

    提供執行會話的完整生命週期管理：
    - 創建會話
    - 更新狀態和結果
    - 查詢會話歷史
    - 記錄追蹤資訊
    """

    def __init__(self, db_session: AsyncSession):
        """
        初始化 Session 服務

        Args:
            db_session: SQLAlchemy 異步 session
        """
        self.db_session = db_session

    async def create_session(
        self,
        agent_id: str,
        session_type: str,
        mode: str,
        initial_input: dict[str, Any] | None = None,
    ) -> AgentSession:
        """
        創建新的執行會話

        Args:
            agent_id: Agent ID
            session_type: 會話類型（如 "manual_task", "scheduled_task"）
            mode: 執行模式（AgentMode）
            initial_input: 初始輸入資料

        Returns:
            創建的 AgentSession 實例

        Raises:
            SessionError: 創建失敗
        """
        try:
            session = AgentSession(
                agent_id=agent_id,
                session_type=session_type,
                mode=mode,
                status=SessionStatus.PENDING,
                initial_input=initial_input or {},
                start_time=datetime.now(),
            )

            self.db_session.add(session)
            await self.db_session.commit()
            await self.db_session.refresh(session)

            logger.info(
                f"Created session: {session.id} for agent {agent_id} "
                f"(type: {session_type}, mode: {mode})"
            )
            return session

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to create session for agent {agent_id}: {e}", exc_info=True)
            raise SessionError(f"Failed to create session: {str(e)}")

    async def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        end_time: datetime | None = None,
        execution_time_ms: int | None = None,
        error_message: str | None = None,
    ) -> AgentSession:
        """
        更新會話狀態

        Args:
            session_id: Session ID
            status: 新狀態
            end_time: 結束時間（可選）
            execution_time_ms: 執行時間（毫秒）
            error_message: 錯誤訊息（如果失敗）

        Returns:
            更新後的 AgentSession

        Raises:
            SessionNotFoundError: Session 不存在
            SessionError: 更新失敗
        """
        try:
            session = await self.get_session(session_id)

            session.status = status
            if end_time:
                session.end_time = end_time
            if execution_time_ms is not None:
                session.execution_time_ms = execution_time_ms
            if error_message:
                session.error_message = error_message

            await self.db_session.commit()
            await self.db_session.refresh(session)

            logger.info(f"Updated session {session_id} status to {status.value}")
            return session

        except SessionNotFoundError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update session {session_id}: {e}", exc_info=True)
            raise SessionError(f"Failed to update session: {str(e)}")

    async def update_session_output(
        self,
        session_id: str,
        final_output: dict[str, Any],
        tools_called: str | None = None,
    ) -> AgentSession:
        """
        更新會話輸出結果

        Args:
            session_id: Session ID
            final_output: 最終輸出資料
            tools_called: 呼叫的工具列表（文字）

        Returns:
            更新後的 AgentSession

        Raises:
            SessionNotFoundError: Session 不存在
            SessionError: 更新失敗
        """
        try:
            session = await self.get_session(session_id)

            session.final_output = final_output
            if tools_called:
                session.tools_called = tools_called

            await self.db_session.commit()
            await self.db_session.refresh(session)

            logger.debug(f"Updated session {session_id} output")
            return session

        except SessionNotFoundError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update session output {session_id}: {e}", exc_info=True)
            raise SessionError(f"Failed to update session output: {str(e)}")

    async def record_session_trace(
        self, session_id: str, trace_data: dict[str, Any]
    ) -> AgentSession:
        """
        記錄會話追蹤資訊

        Args:
            session_id: Session ID
            trace_data: 追蹤資料（包含 trace_id, spans 等）

        Returns:
            更新後的 AgentSession

        Raises:
            SessionNotFoundError: Session 不存在
            SessionError: 記錄失敗
        """
        try:
            session = await self.get_session(session_id)

            session.trace_data = trace_data

            await self.db_session.commit()
            await self.db_session.refresh(session)

            logger.debug(f"Recorded trace data for session {session_id}")
            return session

        except SessionNotFoundError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to record trace for session {session_id}: {e}", exc_info=True)
            raise SessionError(f"Failed to record trace: {str(e)}")

    async def get_session(self, session_id: str) -> AgentSession:
        """
        取得單一會話

        Args:
            session_id: Session ID

        Returns:
            AgentSession 實例

        Raises:
            SessionNotFoundError: Session 不存在
        """
        try:
            stmt = select(AgentSession).where(AgentSession.id == session_id)
            result = await self.db_session.execute(stmt)
            session = result.scalar_one_or_none()

            if not session:
                raise SessionNotFoundError(f"Session '{session_id}' not found")

            return session

        except SessionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}", exc_info=True)
            raise SessionError(f"Failed to retrieve session: {str(e)}")

    async def list_agent_sessions(
        self,
        agent_id: str,
        limit: int = 50,
        status: SessionStatus | None = None,
    ) -> list[AgentSession]:
        """
        列出 Agent 的執行會話

        Args:
            agent_id: Agent ID
            limit: 最大返回數量
            status: 過濾狀態（可選）

        Returns:
            AgentSession 列表（按時間倒序）

        Raises:
            SessionError: 查詢失敗
        """
        try:
            stmt = select(AgentSession).where(AgentSession.agent_id == agent_id)

            if status:
                stmt = stmt.where(AgentSession.status == status)

            stmt = stmt.order_by(desc(AgentSession.start_time)).limit(limit)

            result = await self.db_session.execute(stmt)
            sessions = list(result.scalars().all())

            logger.debug(f"Retrieved {len(sessions)} sessions for agent {agent_id}")
            return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions for agent {agent_id}: {e}", exc_info=True)
            raise SessionError(f"Failed to list sessions: {str(e)}")

    async def get_latest_session(
        self, agent_id: str, status: SessionStatus | None = None
    ) -> AgentSession | None:
        """
        取得 Agent 最新的會話

        Args:
            agent_id: Agent ID
            status: 過濾狀態（可選）

        Returns:
            最新的 AgentSession 或 None

        Raises:
            SessionError: 查詢失敗
        """
        try:
            stmt = select(AgentSession).where(AgentSession.agent_id == agent_id)

            if status:
                stmt = stmt.where(AgentSession.status == status)

            stmt = stmt.order_by(desc(AgentSession.start_time)).limit(1)

            result = await self.db_session.execute(stmt)
            session = result.scalar_one_or_none()

            return session

        except Exception as e:
            logger.error(f"Failed to get latest session for agent {agent_id}: {e}", exc_info=True)
            raise SessionError(f"Failed to get latest session: {str(e)}")

    async def count_agent_sessions(self, agent_id: str, status: SessionStatus | None = None) -> int:
        """
        計算 Agent 的會話數量

        Args:
            agent_id: Agent ID
            status: 過濾狀態（可選）

        Returns:
            會話數量

        Raises:
            SessionError: 查詢失敗
        """
        try:
            stmt = select(AgentSession).where(AgentSession.agent_id == agent_id)

            if status:
                stmt = stmt.where(AgentSession.status == status)

            result = await self.db_session.execute(stmt)
            sessions = result.scalars().all()
            count = len(list(sessions))

            return count

        except Exception as e:
            logger.error(f"Failed to count sessions for agent {agent_id}: {e}", exc_info=True)
            raise SessionError(f"Failed to count sessions: {str(e)}")

    async def delete_session(self, session_id: str) -> None:
        """
        刪除會話

        Args:
            session_id: Session ID

        Raises:
            SessionNotFoundError: Session 不存在
            SessionError: 刪除失敗
        """
        try:
            session = await self.get_session(session_id)

            await self.db_session.delete(session)
            await self.db_session.commit()

            logger.info(f"Deleted session: {session_id}")

        except SessionNotFoundError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to delete session {session_id}: {e}", exc_info=True)
            raise SessionError(f"Failed to delete session: {str(e)}")

    async def get_session_statistics(self, agent_id: str) -> dict[str, Any]:
        """
        取得 Agent 的會話統計資訊

        Args:
            agent_id: Agent ID

        Returns:
            統計資料字典：
            {
                "total_sessions": int,
                "completed": int,
                "failed": int,
                "running": int,
                "avg_execution_time_ms": float,
            }

        Raises:
            SessionError: 查詢失敗
        """
        try:
            sessions = await self.list_agent_sessions(agent_id, limit=1000)

            total = len(sessions)
            completed = sum(1 for s in sessions if s.status == SessionStatus.COMPLETED)
            failed = sum(1 for s in sessions if s.status == SessionStatus.FAILED)
            running = sum(1 for s in sessions if s.status == SessionStatus.RUNNING)

            # 計算平均執行時間（僅包含已完成的會話）
            execution_times = [
                s.execution_time_ms for s in sessions if s.execution_time_ms is not None
            ]
            avg_execution_time = (
                sum(execution_times) / len(execution_times) if execution_times else 0
            )

            return {
                "total_sessions": total,
                "completed": completed,
                "failed": failed,
                "running": running,
                "avg_execution_time_ms": avg_execution_time,
            }

        except Exception as e:
            logger.error(f"Failed to get statistics for agent {agent_id}: {e}", exc_info=True)
            raise SessionError(f"Failed to get session statistics: {str(e)}")
