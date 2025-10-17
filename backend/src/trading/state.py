"""
Agent State Models
Agent 運行時狀態相關的資料模型（使用 Pydantic BaseModel）
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from trading.config import AgentConfig
from common.enums import AgentMode, AgentStatus, SessionStatus


# ==========================================
# Agent 運行時資料模型
# ==========================================


class AgentState(BaseModel):
    """Agent 運行時狀態"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    status: AgentStatus = AgentStatus.INACTIVE
    current_mode: AgentMode = AgentMode.OBSERVATION
    config: AgentConfig

    # 狀態資訊
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_active_at: datetime | None = None
    last_execution_id: str | None = None

    # 執行統計
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time: float = 0.0

    # 績效摘要
    current_portfolio_value: float = 0.0
    total_return: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    model_config = {"arbitrary_types_allowed": True}

    def update_activity(self) -> None:
        """更新活動時間"""
        self.last_active_at = datetime.now()
        self.updated_at = datetime.now()


class AgentExecutionContext(BaseModel):
    """Agent 執行上下文"""

    agent_id: str
    session_id: str
    mode: AgentMode
    start_time: datetime = Field(default_factory=datetime.now)
    max_turns: int = 30
    timeout: int = 300

    # 執行環境
    market_is_open: bool = False
    available_cash: float = 0.0
    current_holdings: dict[str, Any] = Field(default_factory=dict)

    # 輸入參數
    initial_input: dict[str, Any] = Field(default_factory=dict)
    user_message: str | None = None

    model_config = {"arbitrary_types_allowed": True}


class AgentExecutionResult(BaseModel):
    """Agent 執行結果"""

    session_id: str
    agent_id: str
    status: SessionStatus
    mode: AgentMode

    # 執行資訊
    start_time: datetime
    end_time: datetime | None = None
    execution_time_ms: int = 0
    turns_used: int = 0

    # 執行內容
    initial_input: dict[str, Any] = Field(default_factory=dict)
    final_output: dict[str, Any] = Field(default_factory=dict)
    tools_called: list[str] = Field(default_factory=list)

    # 錯誤處理
    error_message: str | None = None
    error_type: str | None = None

    # 追蹤資料
    trace_data: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    def calculate_execution_time(self) -> None:
        """計算執行時間"""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            self.execution_time_ms = int(delta.total_seconds() * 1000)


# ==========================================
# API 響應模型
# ==========================================


class AgentCreationResponse(BaseModel):
    """Agent 創建響應"""

    success: bool
    agent_id: str | None = None
    message: str
    agent_state: AgentState | None = None


class AgentStatusResponse(BaseModel):
    """Agent 狀態響應"""

    agent_id: str
    status: AgentStatus
    current_mode: AgentMode
    is_active: bool
    last_execution: datetime | None
    performance_summary: dict[str, Any]
    recent_activities: list[dict[str, Any]]


# ==========================================
# 工具函數
# ==========================================


def generate_agent_id() -> str:
    """生成 Agent ID"""
    return f"agent-{uuid.uuid4().hex[:8]}"


def generate_session_id(agent_id: str) -> str:
    """生成 Session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{agent_id}_session_{timestamp}_{uuid.uuid4().hex[:6]}"
