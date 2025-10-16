"""
Common Enums for CasualTrader Backend

統一所有模組共用的枚舉定義，避免重複定義和不一致問題。
"""

from __future__ import annotations

from enum import Enum


# ==========================================
# Agent 相關枚舉
# ==========================================


class AgentStatus(str, Enum):
    """Agent 持久化狀態枚舉 (儲存在資料庫)

    用於標示 Agent 在資料庫中的狀態。
    """

    ACTIVE = "active"  # 活躍
    INACTIVE = "inactive"  # 未啟用
    ERROR = "error"  # 錯誤
    SUSPENDED = "suspended"  # 已暫停


class AgentRuntimeStatus(str, Enum):
    """Agent 執行時狀態枚舉 (僅存在於記憶體/前端)

    用於標示 Agent 目前的執行狀態。
    """

    IDLE = "idle"  # 待命
    RUNNING = "running"  # 執行中
    STOPPED = "stopped"  # 已停止


class AgentMode(str, Enum):
    """Agent 交易模式枚舉

    決定 Agent 的行為模式。
    """

    TRADING = "TRADING"  # 尋找和執行交易機會
    REBALANCING = "REBALANCING"  # 調整投資組合配置
    STRATEGY_REVIEW = "STRATEGY_REVIEW"  # 檢討策略和績效
    OBSERVATION = "OBSERVATION"  # 監控市場但不交易


# ==========================================
# 執行會話相關枚舉
# ==========================================


class SessionStatus(str, Enum):
    """執行會話狀態枚舉

    用於標示 Agent 執行會話的狀態。
    """

    PENDING = "pending"  # 待執行
    RUNNING = "running"  # 執行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 執行失敗
    TIMEOUT = "timeout"  # 執行逾時


class ExecutionMode(str, Enum):
    """執行模式枚舉

    決定 Agent 的執行方式。
    """

    CONTINUOUS = "continuous"  # 連續執行
    SINGLE_CYCLE = "single_cycle"  # 單次執行


# ==========================================
# 交易相關枚舉
# ==========================================


class TransactionAction(str, Enum):
    """交易動作枚舉"""

    BUY = "BUY"  # 買進
    SELL = "SELL"  # 賣出


class TransactionStatus(str, Enum):
    """交易狀態枚舉"""

    PENDING = "pending"  # 待執行
    EXECUTED = "executed"  # 已執行
    FAILED = "failed"  # 執行失敗
    CANCELLED = "cancelled"  # 已取消


# ==========================================
# 策略變更相關枚舉
# ==========================================


class StrategyChangeType(str, Enum):
    """策略變更類型枚舉"""

    AUTO = "auto"  # 自動調整
    MANUAL = "manual"  # 手動調整
    PERFORMANCE_DRIVEN = "performance_driven"  # 績效驅動調整


# ==========================================
# AI 模型相關枚舉
# ==========================================


class ModelType(str, Enum):
    """AI 模型類型枚舉"""

    OPENAI = "openai"  # OpenAI 原生模型
    LITELLM = "litellm"  # 透過 LiteLLM 代理的模型


# ==========================================
# 工具函數
# ==========================================


def validate_agent_status(status: str) -> AgentStatus | None:
    """驗證並轉換 Agent 狀態字串

    Args:
        status: 狀態字串

    Returns:
        AgentStatus 或 None (如果無效)
    """
    try:
        return AgentStatus(status.lower())
    except (ValueError, AttributeError):
        return None


def validate_agent_mode(mode: str) -> AgentMode | None:
    """驗證並轉換 Agent 模式字串

    Args:
        mode: 模式字串

    Returns:
        AgentMode 或 None (如果無效)
    """
    try:
        return AgentMode(mode.upper())
    except (ValueError, AttributeError):
        return None


def validate_session_status(status: str) -> SessionStatus | None:
    """驗證並轉換會話狀態字串

    Args:
        status: 狀態字串

    Returns:
        SessionStatus 或 None (如果無效)
    """
    try:
        return SessionStatus(status.lower())
    except (ValueError, AttributeError):
        return None


def get_all_agent_statuses() -> list[str]:
    """獲取所有 Agent 狀態值列表"""
    return [status.value for status in AgentStatus]


def get_all_agent_modes() -> list[str]:
    """獲取所有 Agent 模式值列表"""
    return [mode.value for mode in AgentMode]


def get_all_session_statuses() -> list[str]:
    """獲取所有會話狀態值列表"""
    return [status.value for status in SessionStatus]
