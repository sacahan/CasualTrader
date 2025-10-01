"""
交易工具測試。

測試買入、賣出工具的基本功能和邏輯。
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from market_mcp.models.stock_data import TWStockResponse
from market_mcp.models.trading_models import OrderStatus, OrderType
from market_mcp.tools.trading_tool import TradingTool


class TestTradingTools(unittest.TestCase):
    """交易工具測試類別。"""

    def setUp(self):
        """設置測試環境。"""
        self.trading_tool = TradingTool()

    def test_commission_calculation(self):
        """測試手續費計算。"""
        # 測試一般手續費 (0.06%)
        amount = 100000  # 10萬元
        commission = self.trading_tool._calculate_commission(amount)
        expected = 100000 * 0.0006  # 60元
        self.assertEqual(commission, expected)

        # 測試最低手續費 (20元)
        amount = 10000  # 1萬元
        commission = self.trading_tool._calculate_commission(amount)
        self.assertEqual(commission, 20.0)  # 最低手續費

    @patch("market_mcp.tools.trading_tool.TWStockAPIClient")
    @patch("market_mcp.tools.trading_tool.MCPToolInputValidator")
    async def test_buy_success(self, mock_validator, mock_client):
        """測試成功買入。"""
        # 模擬驗證器回傳
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_get_taiwan_stock_price_input.return_value = {
            "symbol": "2330"
        }
        mock_validator.return_value = mock_validator_instance

        # 模擬 API 客戶端回傳
        mock_client_instance = AsyncMock()
        mock_stock_data = TWStockResponse(
            symbol="2330",
            company_name="台積電",
            current_price=580.0,
            change=5.0,
            change_percent=0.87,
            volume=12345,
            open_price=575.0,
            high_price=585.0,
            low_price=570.0,
            previous_close=575.0,
            upper_limit=632.0,
            lower_limit=517.0,
            bid_prices=[579.0, 578.0, 577.0, 576.0, 575.0],
            bid_volumes=[100, 200, 150, 300, 250],
            ask_prices=[580.0, 581.0, 582.0, 583.0, 584.0],
            ask_volumes=[150, 100, 200, 180, 220],
            update_time="2024-01-01T10:30:00",
            last_trade_time="10:30:00",
        )
        mock_client_instance.get_stock_quote.return_value = mock_stock_data
        mock_client.return_value = mock_client_instance

        # 建立新的工具實例
        tool = TradingTool()

        # 測試買入：買價 >= 最低賣價
        arguments = {"symbol": "2330", "price": 580.0, "quantity": 1}
        result = await tool.buy_taiwan_stock(arguments)

        # 驗證結果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "text")
        self.assertIn("交易成功", result[0]["text"])
        self.assertIn("580", result[0]["text"])  # 成交價格

    @patch("market_mcp.tools.trading_tool.TWStockAPIClient")
    @patch("market_mcp.tools.trading_tool.MCPToolInputValidator")
    async def test_buy_failure(self, mock_validator, mock_client):
        """測試買入失敗 (價格不符)。"""
        # 模擬驗證器回傳
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_get_taiwan_stock_price_input.return_value = {
            "symbol": "2330"
        }
        mock_validator.return_value = mock_validator_instance

        # 模擬 API 客戶端回傳
        mock_client_instance = AsyncMock()
        mock_stock_data = TWStockResponse(
            symbol="2330",
            company_name="台積電",
            current_price=580.0,
            change=5.0,
            change_percent=0.87,
            volume=12345,
            open_price=575.0,
            high_price=585.0,
            low_price=570.0,
            previous_close=575.0,
            upper_limit=632.0,
            lower_limit=517.0,
            bid_prices=[579.0, 578.0, 577.0, 576.0, 575.0],
            bid_volumes=[100, 200, 150, 300, 250],
            ask_prices=[580.0, 581.0, 582.0, 583.0, 584.0],
            ask_volumes=[150, 100, 200, 180, 220],
            update_time="2024-01-01T10:30:00",
            last_trade_time="10:30:00",
        )
        mock_client_instance.get_stock_quote.return_value = mock_stock_data
        mock_client.return_value = mock_client_instance

        # 建立新的工具實例
        tool = TradingTool()

        # 測試買入失敗：買價 < 最低賣價
        arguments = {"symbol": "2330", "price": 575.0, "quantity": 1}
        result = await tool.buy_taiwan_stock(arguments)

        # 驗證結果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "text")
        self.assertIn("交易失敗", result[0]["text"])
        self.assertIn("低於市場最低賣價", result[0]["text"])

    @patch("market_mcp.tools.trading_tool.TWStockAPIClient")
    @patch("market_mcp.tools.trading_tool.MCPToolInputValidator")
    async def test_sell_success(self, mock_validator, mock_client):
        """測試成功賣出。"""
        # 模擬驗證器回傳
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_get_taiwan_stock_price_input.return_value = {
            "symbol": "2330"
        }
        mock_validator.return_value = mock_validator_instance

        # 模擬 API 客戶端回傳
        mock_client_instance = AsyncMock()
        mock_stock_data = TWStockResponse(
            symbol="2330",
            company_name="台積電",
            current_price=580.0,
            change=5.0,
            change_percent=0.87,
            volume=12345,
            open_price=575.0,
            high_price=585.0,
            low_price=570.0,
            previous_close=575.0,
            upper_limit=632.0,
            lower_limit=517.0,
            bid_prices=[579.0, 578.0, 577.0, 576.0, 575.0],
            bid_volumes=[100, 200, 150, 300, 250],
            ask_prices=[580.0, 581.0, 582.0, 583.0, 584.0],
            ask_volumes=[150, 100, 200, 180, 220],
            update_time="2024-01-01T10:30:00",
            last_trade_time="10:30:00",
        )
        mock_client_instance.get_stock_quote.return_value = mock_stock_data
        mock_client.return_value = mock_client_instance

        # 建立新的工具實例
        tool = TradingTool()

        # 測試賣出：賣價 <= 最高買價
        arguments = {"symbol": "2330", "price": 579.0, "quantity": 1}
        result = await tool.sell_taiwan_stock(arguments)

        # 驗證結果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "text")
        self.assertIn("交易成功", result[0]["text"])
        self.assertIn("579", result[0]["text"])  # 成交價格

    @patch("market_mcp.tools.trading_tool.TWStockAPIClient")
    @patch("market_mcp.tools.trading_tool.MCPToolInputValidator")
    async def test_sell_failure(self, mock_validator, mock_client):
        """測試賣出失敗 (價格不符)。"""
        # 模擬驗證器回傳
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_get_taiwan_stock_price_input.return_value = {
            "symbol": "2330"
        }
        mock_validator.return_value = mock_validator_instance

        # 模擬 API 客戶端回傳
        mock_client_instance = AsyncMock()
        mock_stock_data = TWStockResponse(
            symbol="2330",
            company_name="台積電",
            current_price=580.0,
            change=5.0,
            change_percent=0.87,
            volume=12345,
            open_price=575.0,
            high_price=585.0,
            low_price=570.0,
            previous_close=575.0,
            upper_limit=632.0,
            lower_limit=517.0,
            bid_prices=[579.0, 578.0, 577.0, 576.0, 575.0],
            bid_volumes=[100, 200, 150, 300, 250],
            ask_prices=[580.0, 581.0, 582.0, 583.0, 584.0],
            ask_volumes=[150, 100, 200, 180, 220],
            update_time="2024-01-01T10:30:00",
            last_trade_time="10:30:00",
        )
        mock_client_instance.get_stock_quote.return_value = mock_stock_data
        mock_client.return_value = mock_client_instance

        # 建立新的工具實例
        tool = TradingTool()

        # 測試賣出失敗：賣價 > 最高買價
        arguments = {"symbol": "2330", "price": 585.0, "quantity": 1}
        result = await tool.sell_taiwan_stock(arguments)

        # 驗證結果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "text")
        self.assertIn("交易失敗", result[0]["text"])
        self.assertIn("高於市場最高買價", result[0]["text"])

    def test_tool_definitions(self):
        """測試工具定義格式。"""
        buy_def = self.trading_tool.get_buy_tool_definition()
        sell_def = self.trading_tool.get_sell_tool_definition()

        # 檢查必要欄位
        for tool_def in [buy_def, sell_def]:
            self.assertIn("name", tool_def)
            self.assertIn("description", tool_def)
            self.assertIn("inputSchema", tool_def)
            self.assertIn("properties", tool_def["inputSchema"])
            self.assertIn("required", tool_def["inputSchema"])

        # 檢查工具名稱
        self.assertEqual(buy_def["name"], "buy_taiwan_stock")
        self.assertEqual(sell_def["name"], "sell_taiwan_stock")


def run_async_test(test_func):
    """運行異步測試的輔助函數。"""
    return asyncio.run(test_func())


if __name__ == "__main__":
    # 運行測試
    unittest.main()
