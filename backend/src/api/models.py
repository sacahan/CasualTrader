"""
API 資料模型

本檔案定義 API 所用的 Pydantic 資料模型，
用於請求與回應的資料驗證。
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AIModel(str, Enum):
    """
    支援的 AI 模型列舉。
    用於指定交易代理人所使用的 AI 模型。
    """

    GPT_4O = "gpt-4o"  # GPT-4o 模型
    GPT_4O_MINI = "gpt-4o-mini"  # GPT-4o Mini 模型
    GPT_4_TURBO = "gpt-4-turbo"  # GPT-4 Turbo 模型
    CLAUDE_SONNET_4_5 = "claude-sonnet-4.5"  # Claude Sonnet 4.5
    CLAUDE_OPUS_4 = "claude-opus-4"  # Claude Opus 4
    GEMINI_2_5_PRO = "gemini-2.5-pro"  # Gemini 2.5 Pro
    GEMINI_2_0_FLASH = "gemini-2.0-flash"  # Gemini 2.0 Flash
    DEEPSEEK_V3 = "deepseek-v3"  # DeepSeek V3
    GROK_2 = "grok-2"  # Grok 2


class StrategyType(str, Enum):
    """
    投資策略類型列舉。
    用於指定代理人投資風格。
    """

    CONSERVATIVE = "conservative"  # 保守型
    BALANCED = "balanced"  # 均衡型
    AGGRESSIVE = "aggressive"  # 積極型
    CUSTOM = "custom"  # 自訂型


class ExecutionMode(str, Enum):
    """
    代理人執行模式列舉。
    決定代理人執行方式。
    """

    CONTINUOUS = "continuous"  # 連續執行
    SINGLE_CYCLE = "single_cycle"  # 單次執行


class AgentStatus(str, Enum):
    """
    代理人執行狀態列舉。
    用於標示代理人目前狀態。
    """

    IDLE = "idle"  # 閒置
    RUNNING = "running"  # 執行中
    STOPPED = "stopped"  # 已停止
    PAUSED = "paused"  # 已暫停
    ERROR = "error"  # 錯誤


class TradingMode(str, Enum):
    """
    交易模式列舉。
    用於標示代理人目前交易狀態。
    """

    TRADING = "TRADING"  # 正常交易
    REBALANCING = "REBALANCING"  # 資產再平衡
    STRATEGY_REVIEW = "STRATEGY_REVIEW"  # 策略檢討
    OBSERVATION = "OBSERVATION"  # 觀察中


class EnabledTools(BaseModel):
    """
    工具啟用設定。
    用於指定代理人可用的分析工具。
    """

    fundamental_analysis: bool = True  # 是否啟用基本面分析
    technical_analysis: bool = True  # 是否啟用技術分析
    risk_assessment: bool = True  # 是否啟用風險評估
    sentiment_analysis: bool = False  # 是否啟用市場情緒分析
    web_search: bool = True  # 是否啟用網路搜尋
    code_interpreter: bool = False  # 是否啟用程式碼解譯器


class InvestmentPreferences(BaseModel):
    """
    投資偏好設定。
    用於指定代理人投資偏好與限制。
    """

    preferred_sectors: list[str] = Field(default_factory=list)  # 優先投資產業
    excluded_tickers: list[str] = Field(default_factory=list)  # 排除股票清單
    max_position_size: float = Field(default=0.15, ge=0.0, le=1.0)  # 最大單一持股比例
    rebalance_frequency: str = "weekly"  # 再平衡頻率


class CreateAgentRequest(BaseModel):
    """
    建立新交易代理人請求模型。
    用於 API 建立代理人時的資料結構。
    """

    name: str = Field(..., min_length=1, max_length=100)  # 代理人名稱
    description: str = Field(default="", max_length=500)  # 代理人描述
    ai_model: AIModel = Field(default=AIModel.GPT_4O)  # 使用 AI 模型
    strategy_type: StrategyType = Field(default=StrategyType.BALANCED)  # 投資策略類型
    strategy_prompt: str = Field(..., min_length=10)  # 策略提示語
    color_theme: str = Field(default="#007bff", pattern=r"^#[0-9A-Fa-f]{6}$")  # 顏色主題
    initial_funds: float = Field(default=1000000.0, gt=0)  # 初始資金
    max_turns: int = Field(default=50, ge=1, le=1000)  # 最大回合數
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)  # 風險容忍度
    enabled_tools: EnabledTools = Field(default_factory=EnabledTools)  # 啟用工具
    investment_preferences: InvestmentPreferences = Field(
        default_factory=InvestmentPreferences
    )  # 投資偏好
    custom_instructions: str = Field(default="")  # 自訂指令


class UpdateAgentRequest(BaseModel):
    """
    更新代理人設定請求模型。
    用於 API 更新代理人時的資料結構。
    """

    name: str | None = Field(None, min_length=1, max_length=100)  # 代理人名稱
    description: str | None = Field(None, max_length=500)  # 代理人描述
    strategy_prompt: str | None = Field(None, min_length=10)  # 策略提示語
    color_theme: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")  # 顏色主題
    risk_tolerance: float | None = Field(None, ge=0.0, le=1.0)  # 風險容忍度
    enabled_tools: EnabledTools | None = None  # 啟用工具
    investment_preferences: InvestmentPreferences | None = None  # 投資偏好
    custom_instructions: str | None = None  # 自訂指令


class StartAgentRequest(BaseModel):
    """
    啟動代理人請求模型。
    用於 API 啟動代理人時的資料結構。
    """

    execution_mode: ExecutionMode = Field(default=ExecutionMode.CONTINUOUS)  # 執行模式
    max_cycles: int = Field(default=100, ge=1, le=10000)  # 最大執行週期
    stop_on_loss_threshold: float = Field(default=0.15, ge=0.0, le=1.0)  # 停損門檻


class UpdateModeRequest(BaseModel):
    """
    更新代理人交易模式請求模型。
    用於 API 更新代理人交易模式時的資料結構。
    """

    mode: TradingMode  # 新交易模式
    reason: str = Field(..., min_length=1)  # 變更原因
    trigger: str = Field(default="manual")  # 觸發來源


class PortfolioSnapshot(BaseModel):
    """
    投資組合快照資料。
    用於記錄代理人當前資產狀態。
    """

    cash: float  # 現金餘額
    positions: dict[str, Any]  # 持股明細
    total_value: float  # 總資產價值
    timestamp: datetime  # 快照時間


class AgentResponse(BaseModel):
    """
    代理人資訊回應模型。
    用於 API 回傳代理人詳細資訊。
    """

    id: str  # 代理人 ID
    name: str  # 代理人名稱
    description: str  # 代理人描述
    ai_model: str  # 使用 AI 模型
    strategy_type: str  # 投資策略類型
    strategy_prompt: str  # 策略提示語
    color_theme: str  # 顏色主題
    current_mode: str  # 目前交易模式
    status: str  # 代理人狀態
    initial_funds: float  # 初始資金
    current_funds: float | None = None  # 目前資金
    max_turns: int  # 最大回合數
    risk_tolerance: float  # 風險容忍度
    enabled_tools: EnabledTools  # 啟用工具
    investment_preferences: InvestmentPreferences  # 投資偏好
    custom_instructions: str  # 自訂指令
    created_at: datetime  # 建立時間
    updated_at: datetime  # 更新時間
    portfolio: dict[str, Any] | None = None  # 投資組合
    performance: dict[str, Any] | None = None  # 績效資料


class AgentListResponse(BaseModel):
    """
    代理人列表回應模型。
    用於 API 回傳代理人清單。
    """

    agents: list[AgentResponse]  # 代理人清單
    total: int  # 代理人總數


class TradeRecord(BaseModel):
    """
    交易紀錄模型。
    用於記錄代理人每筆交易。
    """

    id: str  # 交易紀錄 ID
    agent_id: str  # 代理人 ID
    ticker: str  # 股票代號
    action: str  # 買賣動作
    quantity: int  # 交易股數
    price: float  # 交易價格
    total_amount: float  # 交易總金額
    fee: float  # 手續費
    timestamp: datetime  # 交易時間
    reason: str | None = None  # 交易原因


class StrategyChange(BaseModel):
    """
    策略變更紀錄模型。
    用於記錄代理人策略調整。
    """

    id: str  # 變更紀錄 ID
    agent_id: str  # 代理人 ID
    trigger_reason: str  # 觸發原因
    change_content: str  # 變更內容
    agent_explanation: str  # 代理人說明
    performance_at_change: dict[str, Any]  # 當下績效
    timestamp: datetime  # 變更時間


class WebSocketMessage(BaseModel):
    """
    WebSocket 訊息結構模型。
    用於 API WebSocket 通訊。
    """

    type: str  # 訊息類型
    agent_id: str | None = None  # 代理人 ID
    data: dict[str, Any]  # 訊息資料
    timestamp: datetime = Field(default_factory=datetime.now)  # 訊息時間


class ErrorResponse(BaseModel):
    """
    錯誤回應結構模型。
    用於 API 回傳錯誤訊息。
    """

    error: str  # 錯誤類型
    message: str  # 錯誤訊息
    details: dict[str, Any] | None = None  # 錯誤細節
    timestamp: datetime = Field(default_factory=datetime.now)  # 回應時間
