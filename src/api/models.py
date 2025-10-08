"""
API Data Models

Pydantic models for request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AIModel(str, Enum):
    """Supported AI models."""

    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    CLAUDE_SONNET_4_5 = "claude-sonnet-4.5"
    CLAUDE_OPUS_4 = "claude-opus-4"
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    DEEPSEEK_V3 = "deepseek-v3"
    GROK_2 = "grok-2"


class StrategyType(str, Enum):
    """Investment strategy types."""

    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class ExecutionMode(str, Enum):
    """Agent execution modes."""

    CONTINUOUS = "continuous"
    SINGLE_CYCLE = "single_cycle"


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    ERROR = "error"


class TradingMode(str, Enum):
    """Trading mode enum."""

    TRADING = "TRADING"
    REBALANCING = "REBALANCING"
    STRATEGY_REVIEW = "STRATEGY_REVIEW"
    OBSERVATION = "OBSERVATION"


class EnabledTools(BaseModel):
    """Tool enablement configuration."""

    fundamental_analysis: bool = True
    technical_analysis: bool = True
    risk_assessment: bool = True
    sentiment_analysis: bool = False
    web_search: bool = True
    code_interpreter: bool = False


class InvestmentPreferences(BaseModel):
    """Investment preferences configuration."""

    preferred_sectors: list[str] = Field(default_factory=list)
    excluded_stocks: list[str] = Field(default_factory=list)
    max_position_size: float = Field(default=0.15, ge=0.0, le=1.0)
    rebalance_frequency: str = "weekly"


class CreateAgentRequest(BaseModel):
    """Request to create a new trading agent."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    ai_model: AIModel = Field(default=AIModel.GPT_4O)
    strategy_type: StrategyType = Field(default=StrategyType.BALANCED)
    strategy_prompt: str = Field(..., min_length=10)
    color_theme: str = Field(default="#007bff", pattern=r"^#[0-9A-Fa-f]{6}$")
    initial_funds: float = Field(default=1000000.0, gt=0)
    max_turns: int = Field(default=50, ge=1, le=1000)
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    enabled_tools: EnabledTools = Field(default_factory=EnabledTools)
    investment_preferences: InvestmentPreferences = Field(
        default_factory=InvestmentPreferences
    )
    custom_instructions: str = Field(default="")


class UpdateAgentRequest(BaseModel):
    """Request to update agent configuration."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    strategy_prompt: str | None = Field(None, min_length=10)
    color_theme: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    risk_tolerance: float | None = Field(None, ge=0.0, le=1.0)
    enabled_tools: EnabledTools | None = None
    investment_preferences: InvestmentPreferences | None = None
    custom_instructions: str | None = None


class StartAgentRequest(BaseModel):
    """Request to start an agent."""

    execution_mode: ExecutionMode = Field(default=ExecutionMode.CONTINUOUS)
    max_cycles: int = Field(default=100, ge=1, le=10000)
    stop_on_loss_threshold: float = Field(default=0.15, ge=0.0, le=1.0)


class UpdateModeRequest(BaseModel):
    """Request to update agent trading mode."""

    mode: TradingMode
    reason: str = Field(..., min_length=1)
    trigger: str = Field(default="manual")


class PortfolioSnapshot(BaseModel):
    """Portfolio snapshot data."""

    cash: float
    positions: dict[str, Any]
    total_value: float
    timestamp: datetime


class AgentResponse(BaseModel):
    """Agent information response."""

    id: str
    name: str
    description: str
    ai_model: str
    strategy_type: str
    strategy_prompt: str
    color_theme: str
    current_mode: str
    status: str
    initial_funds: float
    current_funds: float | None = None
    max_turns: int
    risk_tolerance: float
    enabled_tools: EnabledTools
    investment_preferences: InvestmentPreferences
    custom_instructions: str
    created_at: datetime
    updated_at: datetime
    portfolio: dict[str, Any] | None = None
    performance: dict[str, Any] | None = None


class AgentListResponse(BaseModel):
    """List of agents response."""

    agents: list[AgentResponse]
    total: int


class TradeRecord(BaseModel):
    """Trading record."""

    id: str
    agent_id: str
    symbol: str
    action: str
    quantity: int
    price: float
    total_amount: float
    fee: float
    timestamp: datetime
    reason: str | None = None


class StrategyChange(BaseModel):
    """Strategy change record."""

    id: str
    agent_id: str
    trigger_reason: str
    change_content: str
    agent_explanation: str
    performance_at_change: dict[str, Any]
    timestamp: datetime


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""

    type: str
    agent_id: str | None = None
    data: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response structure."""

    error: str
    message: str
    details: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
