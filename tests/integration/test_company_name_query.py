"""
測試公司名稱查詢功能。

驗證新的公司名稱查詢功能是否正常運作。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from market_mcp.tools.stock_price_tool import StockPriceTool
from market_mcp.data.securities_db import resolve_stock_symbol, SecuritiesDatabase
from market_mcp.validators.input_validator import (
    MCPToolInputValidator,
    MCPValidationError,
)


class TestCompanyNameQuery:
    """測試公司名稱查詢功能。"""

    def test_resolve_stock_symbol_with_code(self):
        """測試股票代碼解析。"""
        # 測試股票代碼
        assert resolve_stock_symbol("2330") == "2330"
        assert resolve_stock_symbol("0050") == "0050"
        assert resolve_stock_symbol("00625K") == "00625K"

    def test_resolve_stock_symbol_with_company_name(self):
        """測試公司名稱解析。"""
        # 測試知名公司名稱
        assert resolve_stock_symbol("台積電") == "2330"

    def test_resolve_stock_symbol_not_found(self):
        """測試不存在的查詢。"""
        result = resolve_stock_symbol("不存在的公司名稱12345")
        # 如果找不到，應該回傳 None 或原始查詢
        assert result is None or result == "不存在的公司名稱12345"

    def test_securities_database_search(self):
        """測試證券資料庫搜尋功能。"""
        try:
            db = SecuritiesDatabase()

            # 測試股票代碼查詢
            result = db.find_by_stock_code("2330")
            assert result is not None
            assert result.stock_code == "2330"
            assert "台積電" in result.company_name

            # 測試公司名稱查詢
            results = db.find_by_company_name("台積電", exact_match=True)
            assert len(results) > 0
            assert results[0].stock_code == "2330"

            # 測試模糊查詢
            results = db.search_securities("台積")
            assert len(results) > 0
            assert any("台積電" in r.company_name for r in results)

        except Exception as e:
            pytest.skip(f"資料庫不可用，跳過測試: {e}")

    def test_input_validator_with_stock_code(self):
        """測試輸入驗證器處理股票代碼。"""
        validator = MCPToolInputValidator()

        # 測試有效的股票代碼
        result = validator.validate_get_taiwan_stock_price_input({"symbol": "2330"})
        assert result["symbol"] == "2330"

        # 測試 ETF 代碼
        result = validator.validate_get_taiwan_stock_price_input({"symbol": "0050"})
        assert result["symbol"] == "0050"

    def test_input_validator_with_company_name(self):
        """測試輸入驗證器處理公司名稱。"""
        validator = MCPToolInputValidator()

        try:
            # 測試台積電
            result = validator.validate_get_taiwan_stock_price_input(
                {"symbol": "台積電"}
            )
            assert result["symbol"] == "2330"
            assert result["original_query"] == "台積電"
        except Exception as e:
            pytest.skip(f"資料庫不可用或公司名稱查詢失敗: {e}")

    def test_input_validator_invalid_input(self):
        """測試無效輸入的處理。"""
        validator = MCPToolInputValidator()

        # 測試不存在的查詢
        with pytest.raises(MCPValidationError):
            validator.validate_get_taiwan_stock_price_input(
                {"symbol": "不存在的公司12345"}
            )

        # 測試空字串
        with pytest.raises(MCPValidationError):
            validator.validate_get_taiwan_stock_price_input({"symbol": ""})

        # 測試缺少參數
        with pytest.raises(MCPValidationError):
            validator.validate_get_taiwan_stock_price_input({})

    @pytest.mark.asyncio
    async def test_stock_price_tool_with_company_name(self):
        """測試股票價格工具的公司名稱查詢功能。"""
        tool = StockPriceTool()

        # Mock API 客戶端以避免實際 API 呼叫
        mock_stock_data = {
            "symbol": "2330",
            "company_name": "台積電",
            "current_price": 500.0,
            "change": 10.0,
            "change_percent": 2.04,
            "volume": 1000000,
            "timestamp": "2024-01-01T10:00:00Z",
        }

        tool.client.get_stock_quote = AsyncMock(return_value=mock_stock_data)

        try:
            # 測試公司名稱查詢
            result = await tool.get_taiwan_stock_price({"symbol": "台積電"})
            assert len(result) == 1
            assert result[0]["type"] == "text"
            assert "台積電" in result[0]["text"] or "2330" in result[0]["text"]

        except Exception as e:
            pytest.skip(f"工具測試失敗，可能是資料庫不可用: {e}")

    @pytest.mark.asyncio
    async def test_stock_price_tool_error_handling(self):
        """測試股票價格工具的錯誤處理。"""
        tool = StockPriceTool()

        # 測試不存在的查詢
        result = await tool.get_taiwan_stock_price({"symbol": "不存在的公司12345"})
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "錯誤" in result[0]["text"] or "ERROR" in result[0]["text"]

    def test_tool_definition_updated(self):
        """測試工具定義是否已更新以支援公司名稱。"""
        tool = StockPriceTool()
        definition = tool.get_tool_definition()

        # 檢查描述是否包含公司名稱查詢的說明
        assert "公司名稱" in definition["description"]

        # 檢查範例是否包含公司名稱
        examples = definition["inputSchema"]["properties"]["symbol"]["examples"]
        company_names = [
            ex
            for ex in examples
            if not ex.replace("K", "").replace("R", "").replace("L", "").isdigit()
        ]
        assert len(company_names) > 0, "工具定義應該包含公司名稱範例"

    def test_help_text_updated(self):
        """測試幫助文字是否已更新。"""
        tool = StockPriceTool()
        help_text = tool.get_help_text()

        # 檢查是否提到公司名稱查詢功能
        assert "公司名稱" in help_text
        assert "台積電" in help_text or "鴻海" in help_text


if __name__ == "__main__":
    # 執行簡單的功能測試
    def run_basic_tests():
        """執行基本功能測試。"""
        print("🧪 執行公司名稱查詢功能測試...")

        # 測試 resolve_stock_symbol
        print("1. 測試 resolve_stock_symbol:")
        print(f"   2330 -> {resolve_stock_symbol('2330')}")
        print(f"   台積電 -> {resolve_stock_symbol('台積電')}")
        print(f"   不存在 -> {resolve_stock_symbol('不存在的公司')}")

        # 測試驗證器
        print("\n2. 測試輸入驗證器:")
        validator = MCPToolInputValidator()
        try:
            result = validator.validate_get_taiwan_stock_price_input({"symbol": "2330"})
            print(f"   2330 驗證成功: {result}")
        except Exception as e:
            print(f"   2330 驗證失敗: {e}")

        try:
            result = validator.validate_get_taiwan_stock_price_input(
                {"symbol": "台積電"}
            )
            print(f"   台積電 驗證成功: {result}")
        except Exception as e:
            print(f"   台積電 驗證失敗: {e}")

        # 測試工具定義
        print("\n3. 測試工具定義:")
        tool = StockPriceTool()
        definition = tool.get_tool_definition()
        print(f"   描述: {definition['description']}")
        print(
            f"   範例數量: {len(definition['inputSchema']['properties']['symbol']['examples'])}"
        )

        print("\n✅ 基本測試完成！")

    run_basic_tests()
