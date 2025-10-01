"""
輸入驗證器模組。

提供 MCP 工具參數的驗證邏輯，確保輸入資料的正確性和安全性。
"""

import re
from typing import Any

from pydantic import BaseModel, Field, validator

from ..models.mcp_responses import MCPErrorCodes, MCPErrorTypes


class StockSymbolValidator(BaseModel):
    """
    台灣股票代號驗證器。

    驗證股票代號格式是否符合台灣股市規範。
    """

    symbol: str = Field(..., description="股票代號")

    @validator("symbol")
    def validate_symbol_format(cls, v):
        """
        驗證股票/ETF代號格式。

        基於 TWSE 證券資料庫的實際格式：
        - 4位數字：如 2330 (一般股票)、0050 (ETF)
        - 5位數字：如 00636 (某些ETF)
        - 6位數字：如 006204 (某些ETF)
        - 4-6位數字 + 字母：如 00625K、00632R (特殊ETF)
        """
        from ..data.securities_db import get_securities_database

        if not isinstance(v, str):
            raise ValueError("股票/ETF代號必須是字串類型")

        # 移除空白字符並轉大寫
        v = v.strip().upper()

        if not v:
            raise ValueError("股票/ETF代號不能為空")

        # 檢查基本格式：4-6位數字 + 可選字母
        if not re.match(r"^[0-9]{4,6}[A-Z]*$", v):
            raise ValueError("代號格式錯誤 (範例: 2330、0050、00625K、006204)")

        # 如果有資料庫，驗證代號是否存在
        securities_db = get_securities_database()
        if securities_db:
            try:
                record = securities_db.find_by_stock_code(v)
                if not record:
                    raise ValueError(f"股票/ETF代號 '{v}' 不存在於證券資料庫中")
            except Exception:
                # 如果資料庫查詢失敗，僅進行格式驗證
                pass

        return v


class MCPToolInputValidator:
    """
    MCP 工具輸入驗證器。

    提供統一的參數驗證邏輯和錯誤處理。
    """

    @staticmethod
    def validate_get_taiwan_stock_price_input(
        arguments: dict[str, Any],
    ) -> dict[str, str]:
        """
        驗證 get_taiwan_stock_price 工具的輸入參數。

        支援股票代碼或公司名稱查詢。

        Args:
            arguments: 工具參數字典

        Returns:
            驗證後的參數字典，包含標準化的股票代碼

        Raises:
            ValidationError: 當參數驗證失敗時
        """
        from ..data.securities_db import resolve_stock_symbol

        errors = []
        validated_args = {}

        # 檢查必要參數
        if "symbol" not in arguments:
            errors.append(
                {
                    "field": "symbol",
                    "message": "缺少必要參數 'symbol' (支援股票代碼或公司名稱)",
                    "code": MCPErrorCodes.INVALID_PARAMETERS,
                }
            )
            raise MCPValidationError(
                message="缺少必要參數",
                errors=errors,
                error_code=MCPErrorCodes.INVALID_PARAMETERS,
            )

        # 取得原始查詢
        query = arguments["symbol"]
        if not isinstance(query, str):
            errors.append(
                {
                    "field": "symbol",
                    "message": "參數 'symbol' 必須是字串類型",
                    "code": MCPErrorCodes.INVALID_PARAMETERS,
                }
            )
            raise MCPValidationError(
                message="參數類型錯誤",
                errors=errors,
                error_code=MCPErrorCodes.INVALID_PARAMETERS,
            )

        query = query.strip()
        if not query:
            errors.append(
                {
                    "field": "symbol",
                    "message": "參數 'symbol' 不能為空",
                    "code": MCPErrorCodes.INVALID_PARAMETERS,
                }
            )
            raise MCPValidationError(
                message="參數值無效",
                errors=errors,
                error_code=MCPErrorCodes.INVALID_PARAMETERS,
            )

        # 嘗試解析股票代碼或公司名稱
        try:
            stock_code = resolve_stock_symbol(query)
            if not stock_code:
                errors.append(
                    {
                        "field": "symbol",
                        "message": f"找不到股票/ETF: '{query}' (請檢查代碼或公司名稱是否正確)",
                        "code": MCPErrorCodes.INVALID_SYMBOL,
                    }
                )
                raise MCPValidationError(
                    message="股票/ETF 不存在",
                    errors=errors,
                    error_code=MCPErrorCodes.INVALID_SYMBOL,
                )

            # 如果解析成功，進一步驗證股票代碼格式
            validator = StockSymbolValidator(symbol=stock_code)
            validated_args["symbol"] = validator.symbol
            validated_args["original_query"] = query  # 保留原始查詢以供日誌記錄

        except ValueError as e:
            # 如果是格式驗證錯誤
            errors.append(
                {
                    "field": "symbol",
                    "message": str(e),
                    "code": MCPErrorCodes.INVALID_SYMBOL,
                }
            )
            raise MCPValidationError(
                message="股票代號格式錯誤或不存在",
                errors=errors,
                error_code=MCPErrorCodes.INVALID_SYMBOL,
            ) from e

        # 檢查額外參數 (如果有的話)
        allowed_params = {"symbol"}
        extra_params = set(arguments.keys()) - allowed_params
        if extra_params:
            errors.append(
                {
                    "field": "extra_parameters",
                    "message": f"不支援的參數: {', '.join(extra_params)}",
                    "code": MCPErrorCodes.INVALID_PARAMETERS,
                }
            )
            raise MCPValidationError(
                message="包含不支援的參數",
                errors=errors,
                error_code=MCPErrorCodes.INVALID_PARAMETERS,
            )

        return validated_args

    @staticmethod
    def sanitize_input(value: Any) -> Any:
        """
        清理輸入資料，移除潛在的安全風險。

        Args:
            value: 待清理的值

        Returns:
            清理後的值
        """
        if isinstance(value, str):
            # 移除前後空白
            value = value.strip()

            # 移除潛在的 SQL 注入字符
            dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
            for char in dangerous_chars:
                value = value.replace(char, "")

        return value


class MCPValidationError(Exception):
    """
    MCP 驗證錯誤異常。

    當輸入驗證失敗時拋出此異常。
    """

    def __init__(
        self,
        message: str,
        errors: list[dict[str, str]] | None = None,
        error_code: str = MCPErrorCodes.INVALID_PARAMETERS,
        error_type: str = MCPErrorTypes.VALIDATION_ERROR,
    ):
        """
        初始化驗證錯誤。

        Args:
            message: 錯誤訊息
            errors: 詳細錯誤列表
            error_code: 錯誤代碼
            error_type: 錯誤類型
        """
        self.message = message
        self.errors = errors or []
        self.error_code = error_code
        self.error_type = error_type
        super().__init__(self.message)

    def to_details_dict(self) -> dict[str, Any]:
        """
        將錯誤資訊轉換為詳細字典。

        Returns:
            包含錯誤詳細資訊的字典
        """
        return {
            "validation_errors": self.errors,
            "total_errors": len(self.errors),
            "error_code": self.error_code,
            "error_type": self.error_type,
        }


# 預定義的驗證規則
class ValidationRules:
    """驗證規則常數。"""

    TAIWAN_STOCK_SYMBOL_PATTERN = r"^[0-9]{4,6}[A-Z]*$"
    TAIWAN_STOCK_SYMBOL_MIN = 1000
    TAIWAN_STOCK_SYMBOL_MAX = 9999

    # 支援的市場類型
    SUPPORTED_MARKETS = {"tse", "otc"}

    # 最大字串長度
    MAX_STRING_LENGTH = 100

    # 危險字符清單 (防止注入攻擊)
    DANGEROUS_CHARS = [
        "'",
        '"',
        ";",
        "--",
        "/*",
        "*/",
        "xp_",
        "sp_",
        "<script",
        "</script>",
    ]


def validate_market_hours() -> bool:
    """
    檢查當前是否在股市交易時間。

    台灣股市交易時間：
    - 週一至週五
    - 上午 9:00 - 下午 1:30
    - 不包含國定假日 (簡化版，實際需要假日日曆)

    Returns:
        True 如果在交易時間內
    """
    from datetime import datetime, time
    from zoneinfo import ZoneInfo

    # 台灣時區
    tw_tz = ZoneInfo("Asia/Taipei")
    now = datetime.now(tw_tz)

    # 檢查是否為工作日 (週一至週五)
    if now.weekday() > 4:  # 週六(5) 和 週日(6)
        return False

    # 檢查時間範圍 (9:00 - 13:30)
    market_open = time(9, 0)
    market_close = time(13, 30)
    current_time = now.time()

    return market_open <= current_time <= market_close


def get_validation_help_text() -> str:
    """
    取得參數驗證說明文字。

    Returns:
        參數驗證的說明文字
    """
    return """
📋 **股票/ETF代號格式說明**

✅ **正確格式:**
- 股票: 4 位數字 (例如: 2330, 1101)
- ETF: 4-6 位數字 + 可選字母 (例如: 0050, 00648R, 00670L)

❌ **錯誤格式:**
- 包含小寫字母: 2330a, 0050r
- 長度不正確: 330, 23301
- 包含特殊字符: 2330!, @2330

🕐 **交易時間:**
- 週一至週五 09:00-13:30 (台灣時間)
- 國定假日休市

💡 **常用代號範例:**
- 台積電: 2330
- 鴻海: 2317
- 聯發科: 2454
- 台塑: 1301
- 元大台灣50: 0050
- 元大S&P500反1: 00648R
- 富邦NASDAQ正2: 00670L
"""
