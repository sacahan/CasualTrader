"""
MCP 回應模型定義。

定義符合 MCP 協議的標準化回應格式和錯誤處理模型。
"""

from typing import Any

from pydantic import BaseModel, Field

from .stock_data import TWStockResponse


class MCPToolResponse(BaseModel):
    """
    MCP 工具回應基礎模型.

    提供標準化的回應格式，確保所有工具回應都符合 MCP 協議要求。
    """

    type: str = Field(default="text", description="回應類型")
    text: str = Field(..., description="回應內容")


class MCPSuccessResponse(MCPToolResponse):
    """
    MCP 成功回應模型.

    當工具執行成功時使用此模型回傳結果。
    """

    data: dict[str, Any] | None = Field(None, description="成功回應資料")
    metadata: dict[str, Any] | None = Field(None, description="回應元資料")

    def __init__(self, data: dict[str, Any], message: str = "操作成功", **kwargs):
        """
        初始化成功回應.

        Args:
            data: 回應資料
            message: 成功訊息
        """
        text_content = self._format_success_response(data, message)
        super().__init__(type="text", text=text_content, data=data, **kwargs)

    def _format_success_response(self, data: dict[str, Any], message: str) -> str:
        """格式化成功回應文字內容。"""
        return f"✅ {message}\n\n{self._format_data_for_display(data)}"

    def _format_data_for_display(self, data: dict[str, Any]) -> str:
        """將資料格式化為易讀的顯示格式。"""
        if not data:
            return "無資料"

        formatted_lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                formatted_lines.append(f"**{key}:**")
                for sub_key, sub_value in value.items():
                    formatted_lines.append(f"  - {sub_key}: {sub_value}")
            elif isinstance(value, list):
                formatted_lines.append(f"**{key}:** {', '.join(map(str, value))}")
            else:
                formatted_lines.append(f"**{key}:** {value}")

        return "\n".join(formatted_lines)


class MCPErrorResponse(MCPToolResponse):
    """
    MCP 錯誤回應模型.

    當工具執行失敗時使用此模型回傳錯誤資訊。
    """

    error_code: str = Field(..., description="錯誤代碼")
    error_type: str = Field(..., description="錯誤類型")
    details: dict[str, Any] | None = Field(None, description="錯誤詳細資訊")

    def __init__(
        self,
        error_code: str,
        error_message: str,
        error_type: str = "GENERAL_ERROR",
        details: dict[str, Any] | None = None,
        **kwargs,
    ):
        """
        初始化錯誤回應.

        Args:
            error_code: 錯誤代碼
            error_message: 錯誤訊息
            error_type: 錯誤類型
            details: 錯誤詳細資訊
        """
        text_content = self._format_error_response(
            error_code, error_message, error_type, details
        )
        super().__init__(
            type="text",
            text=text_content,
            error_code=error_code,
            error_type=error_type,
            details=details,
            **kwargs,
        )

    def _format_error_response(
        self,
        error_code: str,
        error_message: str,
        error_type: str,
        details: dict[str, Any] | None,
    ) -> str:
        """格式化錯誤回應文字內容。"""
        error_text = f"❌ 錯誤: {error_message}\n"
        error_text += f"🔍 錯誤代碼: {error_code}\n"
        error_text += f"📋 錯誤類型: {error_type}\n"

        if details:
            error_text += "\n📝 詳細資訊:\n"
            for key, value in details.items():
                error_text += f"  - {key}: {value}\n"

        return error_text.strip()


class StockPriceToolResponse(MCPSuccessResponse):
    """
    股票價格查詢工具專用回應模型.

    針對股票價格查詢結果提供格式化的回應。
    """

    def __init__(self, stock_data: TWStockResponse, **kwargs):
        """
        初始化股票價格回應.

        Args:
            stock_data: 股票資料
        """
        data = stock_data.dict()
        message = f"已取得 {stock_data.company_name} ({stock_data.symbol}) 的股價資訊"

        super().__init__(data=data, message=message, **kwargs)

    def _format_data_for_display(self, data: dict[str, Any]) -> str:
        """格式化股票資料為易讀格式。"""
        if not data:
            return "無股票資料"

        # 基本資訊
        output_lines = [
            f"📈 **{data.get('company_name', 'N/A')} ({data.get('symbol', 'N/A')})**",
            f"💰 **目前價格:** NT$ {data.get('current_price', 0):.2f}",
        ]

        # 漲跌資訊
        change = data.get("change", 0)
        change_percent = data.get("change_percent", 0)
        change_symbol = "📈" if change >= 0 else "📉"
        change_text = (
            f"{change_symbol} **漲跌:** {change:+.2f} ({change_percent:+.2f}%)"
        )
        output_lines.append(change_text)

        # 價格區間
        output_lines.extend(
            [
                f"📊 **開盤:** NT$ {data.get('open_price', 0):.2f}",
                f"📊 **最高:** NT$ {data.get('high_price', 0):.2f}",
                f"📊 **最低:** NT$ {data.get('low_price', 0):.2f}",
                f"📊 **昨收:** NT$ {data.get('previous_close', 0):.2f}",
            ]
        )

        # 成交資訊
        volume = data.get("volume", 0)
        if isinstance(volume, (int, float)):
            if volume >= 1000000:
                volume_text = f"{volume / 1000000:.1f}M"
            elif volume >= 1000:
                volume_text = f"{volume / 1000:.1f}K"
            else:
                volume_text = str(volume)
        else:
            volume_text = str(volume)

        output_lines.append(f"📦 **成交量:** {volume_text}")

        # 漲跌停資訊
        output_lines.extend(
            [
                f"🔺 **漲停價:** NT$ {data.get('upper_limit', 0):.2f}",
                f"🔻 **跌停價:** NT$ {data.get('lower_limit', 0):.2f}",
            ]
        )

        # 五檔買賣資訊 (如果有的話)
        bid_prices = data.get("bid_prices", [])
        ask_prices = data.get("ask_prices", [])

        if bid_prices or ask_prices:
            output_lines.append("\n📋 **五檔資訊:**")

            # 格式化五檔資訊
            max_rows = max(len(bid_prices), len(ask_prices))
            for i in range(max_rows):
                bid_price = bid_prices[i] if i < len(bid_prices) else 0
                ask_price = ask_prices[i] if i < len(ask_prices) else 0
                output_lines.append(
                    f"  買{i + 1}: {bid_price:.2f}  |  賣{i + 1}: {ask_price:.2f}"
                )

        # 更新時間
        update_time = data.get("update_time")
        if update_time:
            if isinstance(update_time, str):
                output_lines.append(f"⏰ **更新時間:** {update_time}")
            else:
                output_lines.append(f"⏰ **更新時間:** {update_time}")

        return "\n".join(output_lines)


# 預定義的錯誤類型
class MCPErrorTypes:
    """MCP 錯誤類型常數。"""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    API_ERROR = "API_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    SYMBOL_NOT_FOUND = "SYMBOL_NOT_FOUND"
    MARKET_CLOSED = "MARKET_CLOSED"
    GENERAL_ERROR = "GENERAL_ERROR"


# 預定義的錯誤代碼
class MCPErrorCodes:
    """MCP 錯誤代碼常數。"""

    INVALID_SYMBOL = "E001"
    SYMBOL_NOT_FOUND = "E002"
    API_UNAVAILABLE = "E003"
    RATE_LIMIT_EXCEEDED = "E004"
    NETWORK_TIMEOUT = "E005"
    INVALID_PARAMETERS = "E006"
    MARKET_CLOSED = "E007"
    AUTHENTICATION_FAILED = "E008"
    INTERNAL_SERVER_ERROR = "E009"
    DATA_PARSING_ERROR = "E010"
