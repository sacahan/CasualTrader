"""
MCP 服務器整合測試。

測試 MCP 服務器是否正確註冊和運行交易工具。
"""

import unittest
from unittest.mock import patch

from market_mcp.server import MCPServer
from market_mcp.tools.trading_tool import get_trading_tool_definitions


class TestServerIntegration(unittest.TestCase):
    """MCP 服務器整合測試類別。"""

    def setUp(self):
        """設置測試環境。"""
        with patch("market_mcp.server.setup_logging"):
            self.server = MCPServer()

    def test_trading_tools_registered(self):
        """測試交易工具是否正確註冊。"""
        # 取得交易工具定義
        trading_defs = get_trading_tool_definitions()

        # 驗證有兩個交易工具
        self.assertEqual(len(trading_defs), 2)

        # 驗證工具名稱
        tool_names = [tool_def["name"] for tool_def in trading_defs]
        self.assertIn("buy_taiwan_stock", tool_names)
        self.assertIn("sell_taiwan_stock", tool_names)

        # 驗證工具定義格式
        for tool_def in trading_defs:
            self.assertIn("name", tool_def)
            self.assertIn("description", tool_def)
            self.assertIn("inputSchema", tool_def)
            self.assertIn("properties", tool_def["inputSchema"])
            self.assertIn("required", tool_def["inputSchema"])

            # 檢查必要參數
            required_fields = tool_def["inputSchema"]["required"]
            self.assertIn("symbol", required_fields)
            self.assertIn("price", required_fields)

    def test_server_initialization(self):
        """測試服務器初始化。"""
        # 驗證服務器對象已創建
        self.assertIsNotNone(self.server.server)
        self.assertEqual(self.server.server.name, "market-mcp-server")


if __name__ == "__main__":
    unittest.main()
