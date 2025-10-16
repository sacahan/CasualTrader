"""
Agent API Schemas
定義 Agent 相關的 Pydantic 模型用於 API 請求與回應驗證
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..common.enums import AgentMode, ExecutionMode


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


class CreateAgentRequest(BaseModel):
    """
    建立新交易代理人請求模型。
    用於 API 建立代理人時的資料結構。

    注意：ai_model 的有效值由 ai_model_configs 資料庫表動態決定，
    不在程式碼中硬編碼。API router 負責驗證模型是否存在於資料庫中。
    """

    name: str = Field(..., min_length=1, max_length=100)  # 代理人名稱
    description: str = Field(default="", max_length=500)  # 代理人描述
    ai_model: str = Field(
        default="gpt-4o-mini",
        min_length=1,
        max_length=50,
        description="AI 模型 key，必須存在於 ai_model_configs 表中",
    )  # 使用 AI 模型（從資料庫動態載入）
    strategy_prompt: str = Field(..., min_length=10)  # 策略提示語
    color_theme: str = Field(
        default="34, 197, 94",
        pattern=r"^\d{1,3},\s*\d{1,3},\s*\d{1,3}$",
        description="UI 卡片顏色 (RGB 格式，例如: 34, 197, 94)",
    )  # UI 卡片顏色
    initial_funds: float = Field(default=1000000.0, gt=0)  # 初始資金
    max_position_size: int = Field(default=50, ge=1, le=100)  # 最大持倉比例 (%)
    max_turns: int = Field(default=10, ge=1, le=30)  # 最大回合數
    enabled_tools: EnabledTools = Field(default_factory=EnabledTools)  # 啟用工具
    investment_preferences: list[str] = Field(default_factory=list)
    custom_instructions: str = Field(default="")  # 自訂指令


class UpdateAgentRequest(BaseModel):
    """
    更新代理人設定請求模型。
    用於 API 更新代理人時的資料結構。
    """

    name: str | None = Field(None, min_length=1, max_length=100)  # 代理人名稱
    description: str | None = Field(None, max_length=500)  # 代理人描述
    strategy_prompt: str | None = Field(None, min_length=10)  # 策略提示語
    color_theme: str | None = Field(
        None,
        pattern=r"^\d{1,3},\s*\d{1,3},\s*\d{1,3}$",
        description="UI 卡片顏色 (RGB 格式)",
    )  # UI 卡片顏色
    enabled_tools: EnabledTools | None = None  # 啟用工具
    investment_preferences: list[str] | None = None  # 投資偏好
    custom_instructions: str | None = None  # 自訂指令
    ai_model: str | None = Field(None, description="AI 模型")  # AI 模型
    max_position_size: int | None = Field(None, ge=1, le=100)  # 最大持倉比例 (%)


class StartAgentRequest(BaseModel):
    """
    啟動代理人請求模型。
    用於 API 啟動代理人時的資料結構。
    """

    execution_mode: ExecutionMode = Field(default=ExecutionMode.CONTINUOUS)  # 執行模式
    max_cycles: int = Field(default=10, ge=1, le=30)  # 最大執行週期
    stop_on_loss_threshold: float = Field(default=0.15, ge=0.0, le=1.0)  # 停損門檻


class UpdateModeRequest(BaseModel):
    """
    更新代理人交易模式請求模型。
    用於 API 更新代理人交易模式時的資料結構。
    """

    mode: AgentMode  # 新交易模式
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
    strategy_prompt: str  # 策略提示語
    color_theme: str  # 顏色主題
    current_mode: str  # 目前交易模式
    max_position_size: int  # 最大持倉比例 (%)
    status: str  # 代理人持久化狀態 (active/inactive/error/suspended)
    runtime_status: str | None = None  # 代理人執行時狀態 (idle/running/stopped)
    initial_funds: float  # 初始資金
    current_funds: float | None = None  # 目前資金
    max_turns: int  # 最大回合數
    enabled_tools: EnabledTools  # 啟用工具
    investment_preferences: list[str]  # 投資偏好
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
