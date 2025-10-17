"""
Agent Core Models
使用 Python 3.12+ 語法的 Agent 系統資料模型
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ==========================================
# Agent 狀態枚舉 (Python 3.12+ Enum)
# ==========================================


class AgentStatus(str, Enum):
    """Agent 運行狀態"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SUSPENDED = "suspended"


class AgentMode(str, Enum):
    """Agent 執行模式"""

    TRADING = "TRADING"  # 尋找和執行交易機會
    REBALANCING = "REBALANCING"  # 調整投資組合配置
    OBSERVATION = "OBSERVATION"  # 監控市場但不交易


class SessionStatus(str, Enum):
    """Agent 會話狀態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# ==========================================
# Agent 配置資料結構 (Python 3.12+ dataclass)
# ==========================================


@dataclass
class TradingSettings:
    """交易相關設定"""

    max_daily_trades: int = 5
    max_simultaneous_positions: int = 10
    enable_stop_loss: bool = True
    default_stop_loss_percent: float = 5.0
    enable_take_profit: bool = True
    default_take_profit_percent: float = 15.0
    min_trade_amount: int = 50000  # 最小交易金額 (TWD)


@dataclass
class AgentConfig:
    """Agent 完整配置資料結構"""

    # 基本資訊
    name: str
    description: str
    agent_type: str = "trading"
    ai_model: str = "gpt-4o-mini"
    color_theme: str = "34, 197, 94"  # UI 顏色主題 (RGB 格式)

    # 資金配置
    initial_funds: float = 1000000.0
    current_funds: float | None = None

    # 投資配置
    investment_preferences: list[str] = Field(default_factory=list)
    trading_settings: TradingSettings = field(default_factory=TradingSettings)
    max_position_size: int = 50  # 最大持倉比例 (%)

    # Agent 行為設定
    instructions: str = ""
    additional_instructions: str = ""

    # 執行參數
    max_turns: int = 30
    execution_timeout: int = 300  # 執行超時時間 (秒)

    # 工具配置
    enabled_tools: dict[str, bool] = field(
        default_factory=lambda: {
            "fundamental_analysis": True,
            "technical_analysis": True,
            "risk_assessment": True,
            "sentiment_analysis": True,
            "web_search": True,
            "code_interpreter": True,
            "casualmarket_tools": True,
        }
    )

    def __post_init__(self) -> None:
        """初始化後處理"""
        if self.current_funds is None:
            self.current_funds = self.initial_funds


# ==========================================
# Agent 運行時資料模型 (Pydantic BaseModel)
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
# 響應模型 (API Response Models)
# ==========================================


class AgentCreationRequest(BaseModel):
    """Agent 創建請求"""

    # 基本資訊
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    initial_funds: float = Field(gt=0, le=100000000)

    # 投資設定 (股票代碼列表)
    investment_preferences: list[str] = Field(default_factory=list)

    # 進階設定 (可選)
    max_position_size: float | None = Field(default=None, gt=0, le=100)
    excluded_tickers: list[str] = Field(default_factory=list)
    additional_instructions: str | None = None


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
# 工具配置模型
# ==========================================


@dataclass
class ToolConfig:
    """Agent 工具配置"""

    name: str
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)
    description: str = ""


class AgentToolsConfig(BaseModel):
    """Agent 完整工具配置"""

    fundamental_analysis: ToolConfig = Field(
        default_factory=lambda: ToolConfig(
            name="fundamental_analysis",
            description="Analyze company fundamentals and financial health",
        )
    )
    technical_analysis: ToolConfig = Field(
        default_factory=lambda: ToolConfig(
            name="technical_analysis",
            description="Perform technical analysis and chart patterns",
        )
    )
    risk_assessment: ToolConfig = Field(
        default_factory=lambda: ToolConfig(
            name="risk_assessment",
            description="Evaluate portfolio risk and position sizing",
        )
    )
    sentiment_analysis: ToolConfig = Field(
        default_factory=lambda: ToolConfig(
            name="market_sentiment",
            description="Analyze market sentiment and news impact",
        )
    )

    model_config = {"arbitrary_types_allowed": True}


# ==========================================
# 實用工具函數
# ==========================================


def generate_agent_id() -> str:
    """生成 Agent ID"""
    return f"agent-{uuid.uuid4().hex[:8]}"


def generate_session_id(agent_id: str) -> str:
    """生成 Session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{agent_id}_session_{timestamp}_{uuid.uuid4().hex[:6]}"


def create_default_agent_config(
    name: str, description: str, initial_funds: float = 1000000.0
) -> AgentConfig:
    """創建預設 Agent 配置"""
    return AgentConfig(
        name=name,
        description=description,
        initial_funds=initial_funds,
        instructions="",  # 將由 instruction_generator 生成
    )


def validate_agent_config(config: AgentConfig) -> list[str]:
    """驗證 Agent 配置"""
    errors: list[str] = []

    if not config.name or len(config.name.strip()) == 0:
        errors.append("Agent name is required")

    if config.initial_funds <= 0:
        errors.append("Initial funds must be positive")

    if config.max_position_size <= 0:
        errors.append("Max position size must be positive")

    if config.trading_settings.max_daily_trades <= 0:
        errors.append("Max daily trades must be positive")

    return errors
