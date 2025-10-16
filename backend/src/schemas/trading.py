"""
Trading API Schemas
定義交易相關的 Pydantic 模型用於 API 請求與回應驗證
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


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
