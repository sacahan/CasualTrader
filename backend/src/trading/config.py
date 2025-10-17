"""
Agent Configuration Models
Agent 配置相關的資料模型（使用 dataclass）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


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
    investment_preferences: list[str] = field(default_factory=list)
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
# Agent 創建請求模型
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


# ==========================================
# 工具函數
# ==========================================


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
