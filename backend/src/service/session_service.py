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
from common.time_utils import ensure_utc, utc_now


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
        mode: str,
        initial_input: dict[str, Any] | None = None,
    ) -> AgentSession:
        """
        創建新的執行會話

        Args:
            agent_id: Agent ID
            mode: 執行模式（AgentMode）
            initial_input: 初始輸入資料

        Returns:
            創建的 AgentSession 實例

        Raises:
            SessionError: 創建失敗
        """
        try:
            # Ensure mode is string value
            mode_value = mode.value if hasattr(mode, "value") else str(mode)

            session = AgentSession(
                agent_id=agent_id,
                mode=mode_value,
                status=SessionStatus.PENDING,
                initial_input=initial_input or {},
                start_time=utc_now(),
            )

            self.db_session.add(session)
            await self.db_session.commit()
            await self.db_session.refresh(session)

            logger.info(f"Created session {session.id} for agent {agent_id} (mode: {mode_value})")
            return session

        except Exception as e:
            await self.db_session.rollback()
            error_msg = f"Failed to create session for agent {agent_id}"
            logger.error(f"{error_msg}: {type(e).__name__}")
            raise SessionError(f"Failed to create session: {str(e)}")

    async def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        final_output: str | None = None,
        end_time: datetime | None = None,
        execution_time_ms: int | None = None,
        error_message: str | None = None,
    ) -> AgentSession:
        """
        更新會話狀態

        Args:
            session_id: Session ID
            status: 新狀態
            final_output: 最終輸出資料（可選，應為字串）
            end_time: 結束時間（可選）
            execution_time_ms: 執行時間（毫秒）
            error_message: 錯誤訊息（如果失敗）

        Returns:
            更新後的 AgentSession

        Raises:
            SessionNotFoundError: Session 不存在
            SessionError: 更新失敗

        Timestamps Updated:
            - updated_at: Set to current time
        """
        try:
            session = await self.get_session(session_id)

            session.status = status
            if final_output is not None:
                session.final_output = final_output

            # 明確設置 updated_at（遵循 timestamp.instructions.md）
            now = utc_now()
            session.updated_at = now

            normalized_end_time = ensure_utc(end_time) if end_time else None
            normalized_start_time = ensure_utc(session.start_time)

            # 如果是終止狀態，必須設置 end_time
            if status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.TIMEOUT]:
                if normalized_end_time is None:
                    normalized_end_time = now
                session.end_time = normalized_end_time

                # 自動計算執行時間
                if execution_time_ms is None and normalized_start_time:
                    execution_time_ms = int(
                        (normalized_end_time - normalized_start_time).total_seconds() * 1000
                    )
                session.execution_time_ms = execution_time_ms
            elif normalized_end_time:
                session.end_time = normalized_end_time

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
            logger.error(f"Failed to update session {session_id}: {type(e).__name__}")
            raise SessionError(f"Failed to update session: {str(e)}")

    async def update_session_output(
        self,
        session_id: str,
        final_output: dict[str, Any],
        tools_called: list[str] | None = None,
    ) -> AgentSession:
        """
        更新會話輸出結果

        Args:
            session_id: Session ID
            final_output: 最終輸出資料
            tools_called: 呼叫的工具列表（例如: ['get_stock_price', 'analyze_trend']）

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

            # 明確設置 updated_at（遵循 timestamp.instructions.md）
            now = utc_now()
            session.updated_at = now

            # 如果還沒設置 end_time，現在設置，並確保為 UTC aware
            if session.end_time is None:
                session.end_time = now
            else:
                session.end_time = ensure_utc(session.end_time)

            normalized_start = ensure_utc(session.start_time)
            normalized_end = ensure_utc(session.end_time)

            # 計算執行時間
            if session.execution_time_ms is None and normalized_start and normalized_end:
                execution_time_ms = int((normalized_end - normalized_start).total_seconds() * 1000)
                session.execution_time_ms = execution_time_ms

            await self.db_session.commit()
            await self.db_session.refresh(session)

            logger.debug(f"Updated session {session_id} output")
            return session

        except SessionNotFoundError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update session output {session_id}: " f"{type(e).__name__}")
            raise SessionError(f"Failed to update session output: {str(e)}")

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
            logger.error(f"Error retrieving session {session_id}: {type(e).__name__}")
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
            logger.error(f"Failed to list sessions for agent {agent_id}: " f"{type(e).__name__}")
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
            logger.error(
                f"Failed to get latest session for agent {agent_id}: " f"{type(e).__name__}"
            )
            raise SessionError(f"Failed to get latest session: {str(e)}")

    async def abort_running_sessions(
        self, agent_id: str, reason: str = "Manually aborted"
    ) -> list[str]:
        """
        強制中斷所有正在執行的 RUNNING 會話

        立即將所有 RUNNING 狀態的 session 標記為 FAILED，
        用於手動中斷正在執行中的 session

        Args:
            agent_id: Agent ID
            reason: 中斷原因

        Returns:
            被中斷的 session ID 列表
        """
        try:
            # 查詢所有 RUNNING 狀態的 session（不管執行多久）
            stmt = (
                select(AgentSession)
                .where(AgentSession.agent_id == agent_id)
                .where(AgentSession.status == SessionStatus.RUNNING)
            )

            result = await self.db_session.execute(stmt)
            running_sessions = list(result.scalars().all())

            aborted_ids = []
            for session in running_sessions:
                start_time = ensure_utc(session.start_time)
                now = utc_now()
                duration = (now - start_time).total_seconds() if start_time else 0.0
                logger.warning(
                    f"Aborting running session {session.id} "
                    f"(was running for {duration:.0f}s) - Reason: {reason}"
                )

                # 標記為 FAILED
                session.status = SessionStatus.FAILED
                session.end_time = now
                session.execution_time_ms = int(duration * 1000)
                session.error_message = f"Aborted: {reason}"

                aborted_ids.append(session.id)

            if aborted_ids:
                await self.db_session.commit()
                logger.info(
                    f"Aborted {len(aborted_ids)} running sessions for agent {agent_id}: {aborted_ids}"
                )
            else:
                logger.debug(f"No running sessions found for agent {agent_id}")

            return aborted_ids

        except Exception as e:
            await self.db_session.rollback()
            logger.error(
                f"Failed to abort running sessions for agent {agent_id}: " f"{type(e).__name__}"
            )
            raise SessionError(f"Failed to abort running sessions: {str(e)}")

    async def cleanup_stuck_sessions(self, agent_id: str, timeout_minutes: int = 30) -> list[str]:
        """
        清理卡住的 RUNNING 會話（超時的）

        將執行時間超過 timeout_minutes 的 RUNNING session 標記為 FAILED
        這是一個自動清理機制，用於處理異常卡住的 session

        Args:
            agent_id: Agent ID
            timeout_minutes: 超時時間（分鐘）

        Returns:
            被清理的 session ID 列表
        """
        try:
            from datetime import timedelta

            # 計算超時時間點
            timeout_threshold = utc_now() - timedelta(minutes=timeout_minutes)

            # 查詢所有 RUNNING 狀態的 session
            stmt = (
                select(AgentSession)
                .where(AgentSession.agent_id == agent_id)
                .where(AgentSession.status == SessionStatus.RUNNING)
                .where(AgentSession.start_time < timeout_threshold)
            )

            result = await self.db_session.execute(stmt)
            stuck_sessions = list(result.scalars().all())

            cleaned_ids = []
            for session in stuck_sessions:
                start_time = ensure_utc(session.start_time)
                now_dt = utc_now()
                duration = (now_dt - start_time).total_seconds() if start_time else 0.0
                logger.warning(
                    f"Cleaning up stuck session {session.id} "
                    f"(running for {duration:.0f}s, timeout: {timeout_minutes * 60}s)"
                )

                # 標記為 FAILED
                session.status = SessionStatus.FAILED
                session.end_time = now_dt
                session.execution_time_ms = int(duration * 1000)
                session.error_message = f"Session timeout after {timeout_minutes} minutes"

                cleaned_ids.append(session.id)

            if cleaned_ids:
                await self.db_session.commit()
                logger.info(
                    f"Cleaned up {len(cleaned_ids)} stuck sessions for agent {agent_id}: {cleaned_ids}"
                )
            else:
                logger.debug(f"No stuck sessions found for agent {agent_id}")

            return cleaned_ids

        except Exception as e:
            await self.db_session.rollback()
            logger.error(
                f"Failed to cleanup stuck sessions for agent {agent_id}: " f"{type(e).__name__}"
            )
            raise SessionError(f"Failed to cleanup stuck sessions: {str(e)}")

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
            logger.error(f"Failed to count sessions for agent {agent_id}: " f"{type(e).__name__}")
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
            logger.error(f"Failed to delete session {session_id}: {type(e).__name__}")
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
            logger.error(f"Failed to get statistics for agent {agent_id}: " f"{type(e).__name__}")
            raise SessionError(f"Failed to get session statistics: {str(e)}")
