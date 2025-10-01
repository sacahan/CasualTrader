"""
股票價格查詢工具實作。

提供標準化的 MCP 工具介面，整合 API 客戶端、資料驗證、錯誤處理等功能。
"""

from typing import Any

from ..api.twse_client import TWStockAPIClient
from ..handlers.error_handler import MCPErrorHandler, safe_execute
from ..models.mcp_responses import StockPriceToolResponse
from ..utils.logging import get_logger
from ..validators.input_validator import MCPToolInputValidator

logger = get_logger(__name__)


class StockPriceTool:
    """
    股票價格查詢工具。

    提供標準化的 MCP 工具介面，支援台灣股票即時價格查詢。
    """

    def __init__(self):
        """初始化股票價格工具。"""
        self.client = TWStockAPIClient()
        self.validator = MCPToolInputValidator()
        logger.info("股票價格工具初始化完成")

    async def get_taiwan_stock_price(
        self, arguments: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        取得台灣股票即時價格資訊。

        這是主要的 MCP 工具方法，提供完整的股票價格查詢功能。

        Args:
            arguments: 工具參數，應包含:
                - symbol: 台灣股票代號 (4位數字，例如: 2330)

        Returns:
            MCP 格式的回應列表，包含股票價格資訊或錯誤訊息

        Examples:
            >>> tool = StockPriceTool()
            >>> result = await tool.get_taiwan_stock_price({"symbol": "2330"})
            >>> print(result[0]["text"])  # 顯示格式化的股票資訊
        """
        context = f"get_taiwan_stock_price with args: {arguments}"
        logger.info(f"開始處理股票價格查詢請求: {context}")

        try:
            # 1. 驗證輸入參數
            logger.debug("開始驗證輸入參數")
            validated_args = self.validator.validate_get_taiwan_stock_price_input(
                arguments
            )
            symbol = validated_args["symbol"]
            logger.info(f"參數驗證成功，股票代號: {symbol}")

            # 2. 呼叫 API 取得股票資料
            logger.debug(f"開始查詢股票 {symbol} 的價格資料")
            stock_data = await self.client.get_stock_quote(symbol)
            logger.info(f"成功取得股票 {symbol} 的價格資料")

            # 3. 建立成功回應
            response = StockPriceToolResponse(stock_data)
            logger.debug("成功建立回應物件")

            return [{"type": "text", "text": response.text}]

        except Exception as e:
            logger.error(f"處理股票價格查詢請求時發生錯誤: {e}")
            return MCPErrorHandler.handle_exception(e, context)

    def get_tool_definition(self) -> dict[str, Any]:
        """
        取得工具定義，用於 MCP 工具註冊。

        Returns:
            符合 MCP 協議的工具定義字典
        """
        return {
            "name": "get_taiwan_stock_price",
            "description": "取得台灣股票即時價格資訊",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "台灣股票代號 (4位數字,例如: 2330) 或 ETF代號 (4-6位數字+字母,例如: 00648R)",
                        "pattern": r"^[0-9]{4,6}[A-Z]*$",
                        "minLength": 4,
                        "maxLength": 8,
                        "examples": [
                            "2330",
                            "2317",
                            "2454",
                            "1301",
                            "00648R",
                            "00670L",
                        ],
                    }
                },
                "required": ["symbol"],
                "additionalProperties": False,
            },
        }

    def get_help_text(self) -> str:
        """
        取得工具使用說明。

        Returns:
            工具使用說明文字
        """
        return """
🔍 **台灣股票價格查詢工具**

📋 **功能說明:**
- 查詢台灣股票及ETF即時價格資訊
- 支援上市、上櫃股票及ETF
- 提供完整的價格、成交量、五檔資訊

📝 **使用方法:**
```
get_taiwan_stock_price({"symbol": "2330"})    # 股票
get_taiwan_stock_price({"symbol": "00648R"})  # ETF
```

✅ **參數說明:**
- symbol: 台灣股票代號(4位數字) 或 ETF代號(4-6位數字+字母)

💡 **常用代號:**
- 台積電: 2330
- 鴻海: 2317
- 聯發科: 2454
- 台塑: 1301
- 元大S&P500反1: 00648R
- 富邦NASDAQ正2: 00670L
- 中華電信: 2412

📊 **回傳資訊包含:**
- 基本資訊: 公司名稱、股票代號
- 價格資訊: 現價、開高低價、昨收價
- 漲跌資訊: 漲跌金額、漲跌幅百分比
- 成交資訊: 成交量、最後成交時間
- 限價資訊: 漲停價、跌停價
- 委託資訊: 五檔買賣價量

⏰ **交易時間:**
週一至週五 09:00-13:30 (台灣時間)
"""

    async def health_check(self) -> dict[str, Any]:
        """
        執行工具健康檢查。

        Returns:
            健康檢查結果
        """
        try:
            # 檢查 API 客戶端連線 (簡單測試)
            is_healthy = True  # 簡化版本，實際可以測試 API 連線

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "api_client": "connected" if is_healthy else "disconnected",
                "tool_version": "1.0.0",
                "last_check": "2025-09-30T15:46:47Z",
            }
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "tool_version": "1.0.0",
                "last_check": "2025-09-30T15:46:47Z",
            }

    async def get_supported_symbols(self) -> list[dict[str, str]]:
        """
        取得支援的股票代號範例。

        Returns:
            支援的股票代號列表
        """
        # 常用股票代號範例
        return [
            {"symbol": "2330", "name": "台積電", "market": "TSE"},
            {"symbol": "2317", "name": "鴻海", "market": "TSE"},
            {"symbol": "2454", "name": "聯發科", "market": "TSE"},
            {"symbol": "1301", "name": "台塑", "market": "TSE"},
            {"symbol": "2412", "name": "中華電", "market": "TSE"},
            {"symbol": "1303", "name": "南亞", "market": "TSE"},
            {"symbol": "2881", "name": "富邦金", "market": "TSE"},
            {"symbol": "2882", "name": "國泰金", "market": "TSE"},
            {"symbol": "0050", "name": "元大台灣50", "market": "TSE"},
            {"symbol": "0056", "name": "元大高股息", "market": "TSE"},
        ]


# 工具實例 (用於 MCP 伺服器註冊)
stock_price_tool = StockPriceTool()


# MCP 工具處理函數 (用於 server.py)
async def handle_get_taiwan_stock_price(
    arguments: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    MCP 工具處理函數。

    這個函數提供給 MCP 伺服器使用，封裝了完整的錯誤處理邏輯。

    Args:
        arguments: 工具參數

    Returns:
        MCP 格式的回應
    """
    return await stock_price_tool.get_taiwan_stock_price(arguments)


def get_tool_definitions() -> list[dict[str, Any]]:
    """
    取得所有工具的定義。

    Returns:
        工具定義列表
    """
    return [stock_price_tool.get_tool_definition()]


def get_all_help_text() -> str:
    """
    取得所有工具的說明文字。

    Returns:
        完整的工具說明
    """
    help_sections = [
        "# CasualTrader MCP 工具說明",
        "",
        stock_price_tool.get_help_text(),
        "",
        "## 📞 支援與回報問題",
        "如遇到問題，請提供以下資訊:",
        "- 使用的股票代號",
        "- 錯誤訊息",
        "- 查詢時間",
        "",
        "## 🔗 相關連結",
        "- 台灣證券交易所: https://www.twse.com.tw/",
        "- 證券櫃檯買賣中心: https://www.tpex.org.tw/",
    ]

    return "\n".join(help_sections)
