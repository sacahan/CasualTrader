"""
CasualTrader Agent System Database Models
使用 Python 3.12+ 語法特性和 SQLAlchemy 2.0+ 異步支援
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models using Python 3.12+ syntax"""

    pass


# ==========================================
# Enums for type safety (Python 3.12+ style)
# ==========================================


class AgentStatus(str, Enum):
    """Agent 執行狀態枚舉"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SUSPENDED = "suspended"


class AgentMode(str, Enum):
    """Agent 交易模式枚舉"""

    TRADING = "TRADING"
    REBALANCING = "REBALANCING"
    STRATEGY_REVIEW = "STRATEGY_REVIEW"
    OBSERVATION = "OBSERVATION"


class SessionStatus(str, Enum):
    """執行會話狀態枚舉"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TransactionAction(str, Enum):
    """交易動作枚舉"""

    BUY = "BUY"
    SELL = "SELL"


class TransactionStatus(str, Enum):
    """交易狀態枚舉"""

    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StrategyChangeType(str, Enum):
    """策略變更類型枚舉"""

    AUTO = "auto"
    MANUAL = "manual"
    PERFORMANCE_DRIVEN = "performance_driven"


class ModelType(str, Enum):
    """AI 模型類型枚舉"""

    OPENAI = "openai"
    LITELLM = "litellm"


# ==========================================
# Dataclasses for type-safe data structures
# ==========================================


@dataclass
class AgentConfig:
    """Agent 配置資料結構 (Python 3.12+ dataclass)"""

    max_turns: int = 30
    execution_timeout: int = 300
    trace_retention_days: int = 30
    additional_settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class AutoAdjustSettings:
    """自動調整設定資料結構"""

    triggers: str = "連續三天虧損超過2% ; 單日跌幅超過3% ; 最大回撤超過10%"
    auto_apply: bool = True
    review_frequency: str = "daily"


@dataclass
class PerformanceMetrics:
    """績效指標資料結構"""

    total_return: float
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float | None = None
    total_trades: int = 0
    winning_trades: int = 0


# ==========================================
# Database Models (SQLAlchemy 2.0+ with Python 3.12+)
# ==========================================


class Agent(Base):
    """Agent 資料模型 - 使用最新 SQLAlchemy 2.0 mapped_column 語法"""

    __tablename__ = "agents"

    # 主要欄位
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(50), default="gpt-4o-mini")

    # 投資配置
    initial_funds: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    max_position_size: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("5.0"))

    # Agent 狀態 (使用 Enum)
    status: Mapped[AgentStatus] = mapped_column(String(20), default=AgentStatus.INACTIVE)
    current_mode: Mapped[AgentMode] = mapped_column(String(30), default=AgentMode.OBSERVATION)

    # JSON 配置欄位
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    investment_preferences: Mapped[str | None] = mapped_column(Text)
    strategy_adjustment_criteria: Mapped[str | None] = mapped_column(Text)
    auto_adjust_settings: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # 時間戳記
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime)

    # 關聯關係
    sessions: Mapped[list[AgentSession]] = relationship(
        "AgentSession", back_populates="agent", cascade="all, delete-orphan"
    )
    holdings: Mapped[list[AgentHolding]] = relationship(
        "AgentHolding", back_populates="agent", cascade="all, delete-orphan"
    )
    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="agent", cascade="all, delete-orphan"
    )
    strategy_changes: Mapped[list[StrategyChange]] = relationship(
        "StrategyChange", back_populates="agent", cascade="all, delete-orphan"
    )
    performance_records: Mapped[list[AgentPerformance]] = relationship(
        "AgentPerformance", back_populates="agent", cascade="all, delete-orphan"
    )

    # 表約束
    __table_args__ = (
        CheckConstraint(status.in_([s.value for s in AgentStatus]), name="check_agent_status"),
        CheckConstraint(current_mode.in_([m.value for m in AgentMode]), name="check_agent_mode"),
        Index("idx_agents_status", "status"),
        Index("idx_agents_created_at", "created_at"),
    )


class AgentSession(Base):
    """Agent 執行會話模型"""

    __tablename__ = "agent_sessions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(50), ForeignKey("agents.id"), nullable=False)
    session_type: Mapped[str] = mapped_column(String(50), nullable=False)
    mode: Mapped[AgentMode] = mapped_column(String(30), nullable=False)

    # 執行狀態
    status: Mapped[SessionStatus] = mapped_column(String(20), default=SessionStatus.PENDING)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer)

    # 執行內容
    initial_input: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    final_output: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    tools_called: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)

    # 追蹤資訊
    trace_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # 關聯關係
    agent: Mapped[Agent] = relationship("Agent", back_populates="sessions")
    transactions: Mapped[list[Transaction]] = relationship("Transaction", back_populates="session")

    # 表約束
    __table_args__ = (
        CheckConstraint(status.in_([s.value for s in SessionStatus]), name="check_session_status"),
        Index("idx_sessions_agent_id", "agent_id"),
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_start_time", "start_time"),
    )


class AgentHolding(Base):
    """Agent 持倉模型"""

    __tablename__ = "agent_holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(50), ForeignKey("agents.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(200))

    # 持倉資訊
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    average_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # 時間戳記
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    # 關聯關係
    agent: Mapped[Agent] = relationship("Agent", back_populates="holdings")

    # 表約束
    __table_args__ = (
        UniqueConstraint("agent_id", "ticker", name="uq_agent_ticker"),
        Index("idx_holdings_agent_id", "agent_id"),
        Index("idx_holdings_ticker", "ticker"),
    )


class Transaction(Base):
    """交易記錄模型"""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(50), ForeignKey("agents.id"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("agent_sessions.id"))

    # 交易基本資訊
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(200))
    action: Mapped[TransactionAction] = mapped_column(String(10), nullable=False)

    # 交易數量和價格
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))

    # 交易狀態
    status: Mapped[TransactionStatus] = mapped_column(String(20), default=TransactionStatus.PENDING)
    execution_time: Mapped[datetime | None] = mapped_column(DateTime)

    # 決策背景
    decision_reason: Mapped[str | None] = mapped_column(Text)
    market_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # 時間戳記
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    # 關聯關係
    agent: Mapped[Agent] = relationship("Agent", back_populates="transactions")
    session: Mapped[AgentSession | None] = relationship(
        "AgentSession", back_populates="transactions"
    )

    # 表約束
    __table_args__ = (
        CheckConstraint(
            action.in_([a.value for a in TransactionAction]),
            name="check_transaction_action",
        ),
        CheckConstraint(
            status.in_([s.value for s in TransactionStatus]),
            name="check_transaction_status",
        ),
        Index("idx_transactions_agent_id", "agent_id"),
        Index("idx_transactions_ticker", "ticker"),
        Index("idx_transactions_created_at", "created_at"),
        Index("idx_transactions_status", "status"),
    )


class StrategyChange(Base):
    """策略變更記錄模型"""

    __tablename__ = "strategy_changes"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(50), ForeignKey("agents.id"), nullable=False)

    # 變更觸發資訊
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[StrategyChangeType] = mapped_column(String(30), nullable=False)

    # 策略內容變更
    old_strategy: Mapped[str | None] = mapped_column(Text)
    new_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)

    # 績效背景資料
    performance_at_change: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Agent 說明
    agent_explanation: Mapped[str | None] = mapped_column(Text)

    # 時間戳記
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    # 關聯關係
    agent: Mapped[Agent] = relationship("Agent", back_populates="strategy_changes")

    # 表約束
    __table_args__ = (
        CheckConstraint(
            change_type.in_([c.value for c in StrategyChangeType]),
            name="check_strategy_change_type",
        ),
        Index("idx_strategy_changes_agent_id", "agent_id"),
        Index("idx_strategy_changes_timestamp", "timestamp"),
    )


class AgentPerformance(Base):
    """Agent 績效指標模型"""

    __tablename__ = "agent_performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(50), ForeignKey("agents.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # 投資組合指標
    total_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))

    # 績效指標
    daily_return: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    total_return: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    win_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    max_drawdown: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))

    # 交易統計
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0)

    # 關聯關係
    agent: Mapped[Agent] = relationship("Agent", back_populates="performance_records")

    # 表約束
    __table_args__ = (
        UniqueConstraint("agent_id", "date", name="uq_agent_date"),
        Index("idx_performance_agent_id", "agent_id"),
        Index("idx_performance_date", "date"),
    )


class MarketDataCache(Base):
    """市場數據快取模型"""

    __tablename__ = "market_data_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    cache_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())

    # 表約束
    __table_args__ = (
        Index("idx_cache_expires_at", "expires_at"),
        Index("idx_cache_key", "cache_key"),
    )


class AgentConfigCache(Base):
    """Agent 設定快取模型"""

    __tablename__ = "agent_config_cache"

    agent_id: Mapped[str] = mapped_column(String(50), ForeignKey("agents.id"), primary_key=True)
    config_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    config_value: Mapped[str | None] = mapped_column(Text)
    config_type: Mapped[str] = mapped_column(String(20), default="string")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )


class AIModelConfig(Base):
    """AI 模型配置模型 - 統一管理可用的 AI 模型"""

    __tablename__ = "ai_model_configs"

    # 主鍵
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 模型識別資訊
    model_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    group_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # 模型類型和配置
    model_type: Mapped[ModelType] = mapped_column(String(20), nullable=False)
    litellm_prefix: Mapped[str | None] = mapped_column(String(100))
    full_model_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 啟用和權限
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    requires_api_key: Mapped[bool] = mapped_column(default=True, nullable=False)
    api_key_env_var: Mapped[str | None] = mapped_column(String(100))

    # API 配置
    api_base_url: Mapped[str | None] = mapped_column(String(500))
    max_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_per_1k_tokens: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))

    # 顯示和排序
    display_order: Mapped[int] = mapped_column(Integer, default=999)
    description: Mapped[str | None] = mapped_column(Text)

    # 時間戳記
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    # 表約束
    __table_args__ = (
        CheckConstraint(
            model_type.in_([t.value for t in ModelType]),
            name="check_model_type",
        ),
        Index("idx_ai_models_model_key", "model_key"),
        Index("idx_ai_models_provider", "provider"),
        Index("idx_ai_models_is_enabled", "is_enabled"),
        Index("idx_ai_models_display_order", "display_order"),
    )


# ==========================================
# Utility functions using Python 3.12+ features
# ==========================================


def get_model_by_name(model_name: str) -> type[Base] | None:
    """根據模型名稱獲取模型類別 (使用 Python 3.12+ union syntax)"""
    model_mapping: dict[str, type[Base]] = {
        "agent": Agent,
        "session": AgentSession,
        "holding": AgentHolding,
        "transaction": Transaction,
        "strategy_change": StrategyChange,
        "performance": AgentPerformance,
        "cache": MarketDataCache,
        "config": AgentConfigCache,
        "ai_model": AIModelConfig,
    }
    return model_mapping.get(model_name.lower())


def validate_agent_status(status: str) -> AgentStatus | None:
    """驗證 Agent 狀態 (使用 match-case)"""
    match status.lower():
        case "active":
            return AgentStatus.ACTIVE
        case "inactive":
            return AgentStatus.INACTIVE
        case "error":
            return AgentStatus.ERROR
        case "suspended":
            return AgentStatus.SUSPENDED
        case _:
            return None


def validate_agent_mode(mode: str) -> AgentMode | None:
    """驗證 Agent 模式 (使用 match-case)"""
    match mode.upper():
        case "TRADING":
            return AgentMode.TRADING
        case "REBALANCING":
            return AgentMode.REBALANCING
        case "STRATEGY_REVIEW":
            return AgentMode.STRATEGY_REVIEW
        case "OBSERVATION":
            return AgentMode.OBSERVATION
        case _:
            return None
