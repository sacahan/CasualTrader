"""
Agent Session - 處理單個 Agent 執行會話
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from .models import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentMode,
    SessionStatus,
    generate_session_id,
)

# ==========================================
# Agent Session 類別
# ==========================================


class AgentSession:
    """
    Agent 執行會話管理器
    負責管理單個 Agent 的執行會話生命週期
    """

    def __init__(
        self,
        agent_id: str,
        mode: AgentMode = AgentMode.OBSERVATION,
        max_turns: int = 30,
        timeout: int = 300,
    ) -> None:
        self.agent_id = agent_id
        self.session_id = generate_session_id(agent_id)
        self.mode = mode
        self.max_turns = max_turns
        self.timeout = timeout

        # 會話狀態
        self._status = SessionStatus.PENDING
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._current_turn = 0

        # 執行資料
        self._initial_input: dict[str, Any] = {}
        self._execution_log: list[dict[str, Any]] = []
        self._tools_called: list[str] = []
        self._error_info: dict[str, Any] | None = None

        # 結果快取
        self._result: AgentExecutionResult | None = None

        # 日誌設定
        self.logger = logging.getLogger(f"session.{self.session_id}")
        self.logger.setLevel(logging.INFO)

    @property
    def status(self) -> SessionStatus:
        """獲取會話狀態"""
        return self._status

    @property
    def is_active(self) -> bool:
        """檢查會話是否處於活躍狀態"""
        return self._status in [SessionStatus.PENDING, SessionStatus.RUNNING]

    @property
    def execution_time_ms(self) -> int:
        """獲取執行時間（毫秒）"""
        if not self._start_time:
            return 0

        end_time = self._end_time or datetime.now()
        delta = end_time - self._start_time
        return int(delta.total_seconds() * 1000)

    @property
    def current_turn(self) -> int:
        """獲取當前回合數"""
        return self._current_turn

    # ==========================================
    # 會話生命週期管理
    # ==========================================

    async def start(
        self,
        initial_input: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> None:
        """啟動會話"""
        if self._status != SessionStatus.PENDING:
            raise RuntimeError(f"Session {self.session_id} already started")

        self._status = SessionStatus.RUNNING
        self._start_time = datetime.now()
        self._initial_input = initial_input or {}

        self.logger.info(f"Session started - Mode: {self.mode}, Max turns: {self.max_turns}")

        # 記錄初始輸入
        self._log_execution_step(
            {
                "step": "session_start",
                "mode": self.mode,
                "initial_input": self._initial_input,
                "user_message": user_message,
                "timestamp": self._start_time.isoformat(),
            }
        )

    async def complete(self, final_output: dict[str, Any] | None = None) -> AgentExecutionResult:
        """完成會話"""
        if self._status != SessionStatus.RUNNING:
            raise RuntimeError(f"Session {self.session_id} is not running")

        self._status = SessionStatus.COMPLETED
        self._end_time = datetime.now()

        # 記錄完成步驟
        self._log_execution_step(
            {
                "step": "session_complete",
                "final_output": final_output,
                "total_turns": self._current_turn,
                "timestamp": self._end_time.isoformat(),
            }
        )

        # 建構執行結果
        self._result = self._build_execution_result(
            status=SessionStatus.COMPLETED, final_output=final_output or {}
        )

        self.logger.info(
            f"Session completed successfully - "
            f"Turns: {self._current_turn}, "
            f"Time: {self.execution_time_ms}ms"
        )

        return self._result

    async def fail(
        self, error: Exception | str, error_type: str | None = None
    ) -> AgentExecutionResult:
        """標記會話失敗"""
        if self._status == SessionStatus.FAILED:
            return self._result  # type: ignore[return-value]

        self._status = SessionStatus.FAILED
        self._end_time = datetime.now()

        # 記錄錯誤資訊
        error_message = str(error)
        self._error_info = {
            "error_message": error_message,
            "error_type": (
                error_type or type(error).__name__
                if isinstance(error, Exception)
                else "UnknownError"
            ),
            "timestamp": self._end_time.isoformat(),
            "turn": self._current_turn,
        }

        self._log_execution_step(
            {
                "step": "session_failed",
                "error": self._error_info,
            }
        )

        # 建構錯誤結果
        self._result = self._build_execution_result(
            status=SessionStatus.FAILED,
            error_message=error_message,
            error_type=self._error_info["error_type"],
        )

        self.logger.error(f"Session failed: {error_message}")

        return self._result

    async def timeout(self) -> AgentExecutionResult:
        """標記會話超時"""
        if self._status in [SessionStatus.COMPLETED, SessionStatus.FAILED]:
            return self._result  # type: ignore[return-value]

        self._status = SessionStatus.TIMEOUT
        self._end_time = datetime.now()

        # 記錄超時資訊
        self._log_execution_step(
            {
                "step": "session_timeout",
                "timeout_after_ms": self.execution_time_ms,
                "turn": self._current_turn,
            }
        )

        # 建構超時結果
        self._result = self._build_execution_result(
            status=SessionStatus.TIMEOUT,
            error_message=f"Session timed out after {self.execution_time_ms}ms",
            error_type="TimeoutError",
        )

        self.logger.warning(f"Session timed out after {self.execution_time_ms}ms")

        return self._result

    # ==========================================
    # 執行追蹤
    # ==========================================

    def log_turn_start(self, turn_input: dict[str, Any]) -> None:
        """記錄回合開始"""
        self._current_turn += 1

        self._log_execution_step(
            {
                "step": "turn_start",
                "turn": self._current_turn,
                "input": turn_input,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self.logger.debug(f"Turn {self._current_turn} started")

    def log_turn_end(self, turn_output: dict[str, Any]) -> None:
        """記錄回合結束"""
        self._log_execution_step(
            {
                "step": "turn_end",
                "turn": self._current_turn,
                "output": turn_output,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self.logger.debug(f"Turn {self._current_turn} completed")

    def log_tool_call(
        self, tool_name: str, tool_input: dict[str, Any], tool_output: dict[str, Any]
    ) -> None:
        """記錄工具調用"""
        if tool_name not in self._tools_called:
            self._tools_called.append(tool_name)

        self._log_execution_step(
            {
                "step": "tool_call",
                "turn": self._current_turn,
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": tool_output,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self.logger.debug(f"Tool called: {tool_name}")

    def log_agent_decision(self, decision: dict[str, Any]) -> None:
        """記錄 Agent 決策"""
        self._log_execution_step(
            {
                "step": "agent_decision",
                "turn": self._current_turn,
                "decision": decision,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self.logger.info(f"Agent decision recorded in turn {self._current_turn}")

    def _log_execution_step(self, step_data: dict[str, Any]) -> None:
        """記錄執行步驟"""
        self._execution_log.append(step_data)

        # 限制日誌大小
        max_log_entries = 1000
        if len(self._execution_log) > max_log_entries:
            self._execution_log = self._execution_log[-max_log_entries:]

    # ==========================================
    # 執行控制
    # ==========================================

    def check_turn_limit(self) -> bool:
        """檢查是否達到回合數限制"""
        return self._current_turn >= self.max_turns

    def check_timeout(self) -> bool:
        """檢查是否超時"""
        if not self._start_time:
            return False

        elapsed = datetime.now() - self._start_time
        return elapsed.total_seconds() > self.timeout

    async def should_continue(self) -> bool:
        """檢查是否應該繼續執行"""
        if not self.is_active:
            return False

        if self.check_turn_limit():
            self.logger.warning(f"Turn limit reached: {self.max_turns}")
            return False

        if self.check_timeout():
            self.logger.warning(f"Session timeout: {self.timeout}s")
            return False

        return True

    # ==========================================
    # 資料存取
    # ==========================================

    def get_execution_context(self) -> AgentExecutionContext:
        """獲取執行上下文"""
        return AgentExecutionContext(
            agent_id=self.agent_id,
            session_id=self.session_id,
            mode=self.mode,
            start_time=self._start_time or datetime.now(),
            max_turns=self.max_turns,
            timeout=self.timeout,
            initial_input=self._initial_input,
        )

    def get_execution_summary(self) -> dict[str, Any]:
        """獲取執行摘要"""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "status": self._status,
            "mode": self.mode,
            "current_turn": self._current_turn,
            "max_turns": self.max_turns,
            "execution_time_ms": self.execution_time_ms,
            "tools_called": self._tools_called.copy(),
            "error_info": self._error_info,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "end_time": self._end_time.isoformat() if self._end_time else None,
        }

    def get_execution_log(self, limit: int = 0) -> list[dict[str, Any]]:
        """獲取執行日誌"""
        if limit > 0:
            return self._execution_log[-limit:]
        return self._execution_log.copy()

    def _build_execution_result(
        self,
        status: SessionStatus,
        final_output: dict[str, Any] | None = None,
        error_message: str | None = None,
        error_type: str | None = None,
    ) -> AgentExecutionResult:
        """建構執行結果"""
        return AgentExecutionResult(
            session_id=self.session_id,
            agent_id=self.agent_id,
            status=status,
            mode=self.mode,
            start_time=self._start_time or datetime.now(),
            end_time=self._end_time,
            execution_time_ms=self.execution_time_ms,
            turns_used=self._current_turn,
            initial_input=self._initial_input,
            final_output=final_output or {},
            tools_called=self._tools_called.copy(),
            error_message=error_message,
            error_type=error_type,
            trace_data={
                "execution_log": self._execution_log.copy(),
                "session_summary": self.get_execution_summary(),
            },
        )

    # ==========================================
    # 上下文管理器支援
    # ==========================================

    @asynccontextmanager
    async def execution_context(
        self,
        initial_input: dict[str, Any] | None = None,
        user_message: str | None = None,
    ) -> AsyncIterator[AgentSession]:
        """執行上下文管理器"""
        await self.start(initial_input, user_message)

        try:
            yield self
        except TimeoutError:
            await self.timeout()
            raise
        except Exception as e:
            await self.fail(e)
            raise
        finally:
            # 如果會話仍在運行中，自動完成
            if self.is_active:
                await self.complete()

    # ==========================================
    # 序列化支援
    # ==========================================

    def to_dict(self) -> dict[str, Any]:
        """轉換為字典格式"""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "mode": self.mode,
            "status": self._status,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "end_time": self._end_time.isoformat() if self._end_time else None,
            "execution_time_ms": self.execution_time_ms,
            "current_turn": self._current_turn,
            "max_turns": self.max_turns,
            "timeout": self.timeout,
            "tools_called": self._tools_called,
            "error_info": self._error_info,
            "initial_input": self._initial_input,
        }

    def to_json(self) -> str:
        """轉換為 JSON 格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentSession:
        """從字典創建會話"""
        session = cls(
            agent_id=data["agent_id"],
            mode=AgentMode(data["mode"]),
            max_turns=data["max_turns"],
            timeout=data["timeout"],
        )

        session.session_id = data["session_id"]
        session._status = SessionStatus(data["status"])
        session._current_turn = data["current_turn"]
        session._tools_called = data["tools_called"]
        session._error_info = data["error_info"]
        session._initial_input = data["initial_input"]

        # 解析時間
        if data["start_time"]:
            session._start_time = datetime.fromisoformat(data["start_time"])
        if data["end_time"]:
            session._end_time = datetime.fromisoformat(data["end_time"])

        return session

    def __repr__(self) -> str:
        return (
            f"AgentSession(id={self.session_id}, "
            f"agent={self.agent_id}, "
            f"status={self._status}, "
            f"mode={self.mode}, "
            f"turn={self._current_turn}/{self.max_turns})"
        )
