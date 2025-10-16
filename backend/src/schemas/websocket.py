"""
WebSocket API Schemas
定義 WebSocket 相關的 Pydantic 模型用於即時通訊
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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
