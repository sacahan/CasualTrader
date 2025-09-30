"""
股票資料模型定義。

使用 Pydantic 模型定義台灣股票的各種資料結構，
確保資料的型別安全和驗證。
"""

from datetime import datetime

from pydantic import BaseModel, Field, validator


class TWStockResponse(BaseModel):
    """
    台灣股票即時資料回應模型。

    包含從台灣證券交易所 API 取得的完整股票資訊。
    """

    symbol: str = Field(..., description="股票代號")
    company_name: str = Field(..., description="公司名稱")
    current_price: float = Field(..., description="當前價格")
    change: float = Field(..., description="漲跌幅")
    change_percent: float = Field(..., description="漲跌幅百分比")
    volume: int = Field(..., description="成交量")
    open_price: float = Field(..., description="開盤價")
    high_price: float = Field(..., description="最高價")
    low_price: float = Field(..., description="最低價")
    previous_close: float = Field(..., description="昨收價")
    upper_limit: float = Field(..., description="漲停價")
    lower_limit: float = Field(..., description="跌停價")
    bid_prices: list[float] = Field(default=[], description="買價 (五檔)")
    bid_volumes: list[int] = Field(default=[], description="買量 (五檔)")
    ask_prices: list[float] = Field(default=[], description="賣價 (五檔)")
    ask_volumes: list[int] = Field(default=[], description="賣量 (五檔)")
    update_time: datetime = Field(..., description="更新時間")
    last_trade_time: str = Field(..., description="最後交易時間")

    @validator("symbol")
    def validate_symbol(cls, v):
        """驗證股票代號格式。"""
        if not v.isdigit() or len(v) != 4:
            raise ValueError("股票代號必須是 4 位數字")
        return v

    @validator(
        "current_price", "open_price", "high_price", "low_price", "previous_close"
    )
    def validate_prices(cls, v):
        """驗證價格必須為正數。"""
        if v < 0:
            raise ValueError("價格不能為負數")
        return v

    @validator("volume")
    def validate_volume(cls, v):
        """驗證成交量必須為非負數。"""
        if v < 0:
            raise ValueError("成交量不能為負數")
        return v

    class Config:
        """Pydantic 配置。"""

        json_encoders = {datetime: lambda v: v.isoformat()}


class TWAPIRawResponse(BaseModel):
    """
    台灣證交所 API 原始回應模型。

    用於解析 API 返回的原始 JSON 結構。
    """

    msgArray: list[dict] = Field(default=[], description="股票資料陣列")
    referer: str = Field(default="", description="來源參考")
    userDelay: int = Field(default=0, description="使用者延遲")
    rtcode: str = Field(default="", description="回應代碼")
    queryTime: dict = Field(default={}, description="查詢時間資訊")


class StockQuoteRequest(BaseModel):
    """
    股票報價請求模型。
    """

    symbol: str = Field(..., description="股票代號")
    market: str | None = Field("tse", description="市場類型 (tse/otc)")

    @validator("symbol")
    def validate_symbol(cls, v):
        """驗證股票代號格式。"""
        if not v.isdigit() or len(v) != 4:
            raise ValueError("股票代號必須是 4 位數字")
        return v

    @validator("market")
    def validate_market(cls, v):
        """驗證市場類型。"""
        if v not in ["tse", "otc"]:
            raise ValueError("市場類型必須是 tse 或 otc")
        return v


class APIError(Exception):
    """
    API 錯誤異常類別。
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class ValidationError(Exception):
    """
    資料驗證錯誤異常類別。
    """

    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(self.message)
