"""
Agent API Schemas
定義 Agent 相關的 Pydantic 模型用於 API 請求與回應驗證
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from common.enums import AgentMode
from api.models import ExecutionMode


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
    color_theme: str = Field(
        default="34, 197, 94",
        pattern=r"^\d{1,3},\s*\d{1,3},\s*\d{1,3}$",
        description="UI 卡片顏色 (RGB 格式，例如: 34, 197, 94)",
    )  # UI 卡片顏色
    initial_funds: float = Field(default=1000000.0, gt=0)  # 初始資金
    max_position_size: float = Field(default=50.0, ge=1, le=100)  # 最大持倉比例 (%)
    investment_preferences: list[str] = Field(default_factory=list)


class UpdateAgentRequest(BaseModel):
    """
    更新代理人設定請求模型。
    用於 API 更新代理人時的資料結構。
    """

    name: str | None = Field(None, min_length=1, max_length=100)  # 代理人名稱
    description: str | None = Field(None, max_length=500)  # 代理人描述
    color_theme: str | None = Field(
        None,
        pattern=r"^\d{1,3},\s*\d{1,3},\s*\d{1,3}$",
        description="UI 卡片顏色 (RGB 格式)",
    )  # UI 卡片顏色
    investment_preferences: list[str] | None = None  # 投資偏好
    ai_model: str | None = Field(None, description="AI 模型")  # AI 模型
    max_position_size: float | None = Field(None, ge=1, le=100)  # 最大持倉比例 (%)


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


class AgentResponse(BaseModel):
    """
    代理人資訊回應模型。
    用於 API 回傳代理人詳細資訊。
    """

    id: str  # 代理人 ID
    name: str  # 代理人名稱
    description: str  # 代理人描述
    ai_model: str  # 使用 AI 模型
    color_theme: str  # 顏色主題
    current_mode: str  # 目前交易模式
    max_position_size: float  # 最大持倉比例 (%)
    status: str  # 代理人持久化狀態 (active/inactive/error/suspended)
    initial_funds: float  # 初始資金
    current_funds: float | None = None  # 目前資金
    investment_preferences: list[str]  # 投資偏好
    created_at: datetime  # 建立時間
    updated_at: datetime  # 更新時間
    last_active_at: datetime | None = None  # 最後活動時間


class SessionResponse(BaseModel):
    """
    會話詳細資訊回應模型。
    用於 API 返回會話執行結果。
    """

    id: str  # 會話 ID
    agent_id: str  # Agent ID
    mode: str  # 執行模式
    status: str  # 會話狀態
    start_time: datetime  # 開始時間
    end_time: datetime | None = None  # 結束時間
    execution_time_ms: int | None = None  # 執行耗時（毫秒）
    initial_input: dict[str, Any] | None = None  # 初始輸入
    final_output: dict[str, Any] | None = None  # 最終輸出
    tools_called: list[str] | None = None  # 呼叫的工具列表
    error_message: str | None = None  # 錯誤訊息
    created_at: datetime  # 建立時間
    updated_at: datetime  # 更新時間


class AgentListResponse(BaseModel):
    """
    代理人列表回應模型。
    用於 API 回傳代理人清單。
    """

    agents: list[AgentResponse]  # 代理人清單
    total: int  # 代理人總數
