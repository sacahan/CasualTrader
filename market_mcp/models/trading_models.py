"""
交易相關資料模型定義。

定義買賣訂單、交易結果等交易模擬功能所需的資料結構。
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class OrderType(str, Enum):
    """訂單類型枚舉。"""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """訂單狀態枚舉。"""

    SUCCESS = "success"
    FAILED = "failed"


class TradeOrder(BaseModel):
    """
    交易訂單模型。

    定義買入或賣出訂單的基本資訊。
    """

    symbol: str = Field(..., description="股票代號")
    order_type: OrderType = Field(..., description="訂單類型 (buy/sell)")
    price: float = Field(..., description="訂單價格")
    quantity: int = Field(..., description="交易數量 (張)")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v):
        """驗證股票代號格式。"""
        if not v or len(v) < 4:
            raise ValueError("股票代號格式錯誤")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        """驗證價格必須為正數。"""
        if v <= 0:
            raise ValueError("價格必須大於 0")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        """驗證數量必須為正整數。"""
        if v <= 0:
            raise ValueError("交易數量必須大於 0")
        return v


class TradeResult(BaseModel):
    """
    交易結果模型。

    包含交易是否成功、成交價格、手續費等完整資訊。
    """

    order: TradeOrder = Field(..., description="原始訂單")
    status: OrderStatus = Field(..., description="交易狀態")
    executed_price: float | None = Field(None, description="成交價格")
    executed_quantity: int | None = Field(None, description="成交數量")
    total_amount: float | None = Field(None, description="成交總金額")
    commission: float | None = Field(None, description="手續費")
    net_amount: float | None = Field(None, description="淨交易金額")
    market_data: dict = Field(default={}, description="當時市場資料")
    execution_time: datetime = Field(
        default_factory=datetime.now, description="執行時間"
    )
    message: str = Field(..., description="交易訊息或失敗原因")

    @field_validator("executed_price")
    @classmethod
    def validate_executed_price(cls, v):
        """驗證成交價格。"""
        if v is not None and v <= 0:
            raise ValueError("成交價格必須大於 0")
        return v

    @field_validator("executed_quantity")
    @classmethod
    def validate_executed_quantity(cls, v):
        """驗證成交數量。"""
        if v is not None and v <= 0:
            raise ValueError("成交數量必須大於 0")
        return v


class MarketOrderRequest(BaseModel):
    """
    市場訂單請求模型。

    用於接收買賣請求的輸入參數。
    """

    symbol: str = Field(..., description="股票代號或公司名稱")
    price: float = Field(..., description="願意買入/賣出的價格")
    quantity: int = Field(default=1, description="交易數量 (張，默認為1)")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v):
        """驗證股票代號格式。"""
        if not v or len(v.strip()) == 0:
            raise ValueError("股票代號不能為空")
        return v.strip()

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        """驗證價格必須為正數。"""
        if v <= 0:
            raise ValueError("價格必須大於 0")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        """驗證數量必須為正整數。"""
        if v <= 0:
            raise ValueError("交易數量必須大於 0")
        return v


class TradingError(Exception):
    """
    交易錯誤異常類別。
    """

    def __init__(
        self,
        message: str,
        order: TradeOrder | None = None,
        market_data: dict | None = None,
    ):
        self.message = message
        self.order = order
        self.market_data = market_data
        super().__init__(self.message)
