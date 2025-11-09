"""
API 資料模型

本檔案定義 API 所用的 Pydantic 資料模型，
用於請求與回應的資料驗證。
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    """
    代理人執行模式列舉。
    決定代理人執行方式。
    """

    CONTINUOUS = "continuous"  # 連續執行
    SINGLE_CYCLE = "single_cycle"  # 單次執行


class AgentStatus(str, Enum):
    """
    代理人持久化狀態列舉 (對應資料庫)。
    用於標示代理人在資料庫中的狀態。
    """

    ACTIVE = "active"  # 活躍
    INACTIVE = "inactive"  # 未啟用
    ERROR = "error"  # 錯誤
    SUSPENDED = "suspended"  # 已暫停


class AgentRuntimeStatus(str, Enum):
    """
    代理人執行時狀態列舉 (記憶體中的執行狀態)。
    用於標示代理人目前執行狀態。
    """

    IDLE = "idle"  # 待命
    RUNNING = "running"  # 執行中
    STOPPED = "stopped"  # 已停止


class TradingMode(str, Enum):
    """
    交易模式列舉。
    用於標示代理人目前交易狀態。
    """

    TRADING = "TRADING"  # 正常交易
    REBALANCING = "REBALANCING"  # 資產再平衡


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
