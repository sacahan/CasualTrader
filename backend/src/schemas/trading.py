"""
Trading API Schemas
定義交易相關的 Pydantic 模型用於 API 請求與回應驗證
"""

from datetime import datetime

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
