"""
Basic integration test for the enhanced CasualTrader with TWSE financial analysis.
"""

import pytest
import asyncio
from market_mcp.tools.analysis.financials import FinancialAnalysisTool
from market_mcp.api.openapi_client import OpenAPIClient
from market_mcp.cache.rate_limited_cache_service import RateLimitedCacheService


class TestFinancialIntegration:
    """Test the integrated financial analysis functionality."""

    @pytest.fixture
    def cache_service(self):
        """Create a cache service for testing."""
        return RateLimitedCacheService()

    @pytest.fixture
    def financial_tool(self, cache_service):
        """Create a financial analysis tool for testing."""
        return FinancialAnalysisTool(cache_service)

    @pytest.fixture
    def openapi_client(self, cache_service):
        """Create an OpenAPI client for testing."""
        return OpenAPIClient(cache_service)

    def test_financial_tool_initialization(self, financial_tool):
        """Test that the financial tool initializes correctly."""
        assert financial_tool is not None
        assert hasattr(financial_tool, "api_client")
        assert isinstance(financial_tool.api_client, OpenAPIClient)

    def test_openapi_client_initialization(self, openapi_client):
        """Test that the OpenAPI client initializes correctly."""
        assert openapi_client is not None
        assert openapi_client.BASE_URL == "https://openapi.twse.com.tw/v1"
        assert openapi_client.USER_AGENT == "CasualTrader-MCP/2.0"

    def test_industry_suffix_mapping(self, openapi_client):
        """Test the industry suffix mapping logic."""
        # Test default case
        suffix = openapi_client.get_industry_api_suffix("INVALID")
        assert suffix == "_ci"  # Should default to general industry

    @pytest.mark.asyncio
    async def test_company_profile_structure(self, financial_tool):
        """Test the structure of company profile response."""
        # Test with Taiwan Semiconductor (2330) - a well-known stock
        result = await financial_tool.get_company_profile("2330")

        # Check response structure
        assert isinstance(result, dict)
        assert "success" in result
        assert "company_code" in result
        assert "source" in result

        # If successful, check data structure
        if result["success"]:
            assert "data" in result
            assert result["company_code"] == "2330"
            assert result["source"] == "TWSE OpenAPI"

    @pytest.mark.asyncio
    async def test_income_statement_structure(self, financial_tool):
        """Test the structure of income statement response."""
        # Test with Taiwan Semiconductor (2330)
        result = await financial_tool.get_income_statement("2330")

        # Check response structure
        assert isinstance(result, dict)
        assert "success" in result
        assert "company_code" in result
        assert "statement_type" in result

        # If successful, check specific fields
        if result["success"]:
            assert "data" in result
            assert "industry_format" in result
            assert result["statement_type"] == "綜合損益表"
            assert result["company_code"] == "2330"

    @pytest.mark.asyncio
    async def test_balance_sheet_structure(self, financial_tool):
        """Test the structure of balance sheet response."""
        # Test with Taiwan Semiconductor (2330)
        result = await financial_tool.get_balance_sheet("2330")

        # Check response structure
        assert isinstance(result, dict)
        assert "success" in result
        assert "company_code" in result
        assert "statement_type" in result

        # If successful, check specific fields
        if result["success"]:
            assert "data" in result
            assert "industry_format" in result
            assert result["statement_type"] == "資產負債表"
            assert result["company_code"] == "2330"

    def test_cache_integration(self, cache_service):
        """Test that cache service is properly integrated."""
        assert cache_service is not None
        # Test that cache service has required methods
        assert hasattr(cache_service, "get")
        assert hasattr(cache_service, "set")
        assert hasattr(cache_service, "can_make_request")

    @pytest.mark.asyncio
    async def test_error_handling_invalid_symbol(self, financial_tool):
        """Test error handling with invalid stock symbol."""
        result = await financial_tool.get_company_profile("INVALID_SYMBOL")

        # Should return a structured error response
        assert isinstance(result, dict)
        assert "success" in result
        assert "company_code" in result
        assert result["company_code"] == "INVALID_SYMBOL"

        # Should indicate failure for invalid symbol
        if not result["success"]:
            assert "error" in result


if __name__ == "__main__":
    # Run basic test manually if executed directly
    async def manual_test():
        cache_service = RateLimitedCacheService()
        financial_tool = FinancialAnalysisTool(cache_service)

        print("Testing CasualTrader Financial Integration...")

        # Test company profile
        result = await financial_tool.get_company_profile("2330")
        print(f"Company Profile Test: {'✓' if result['success'] else '✗'}")

        # Test income statement
        result = await financial_tool.get_income_statement("2330")
        print(f"Income Statement Test: {'✓' if result['success'] else '✗'}")

        # Test balance sheet
        result = await financial_tool.get_balance_sheet("2330")
        print(f"Balance Sheet Test: {'✓' if result['success'] else '✗'}")

        print("Integration test completed!")

    # Run the manual test
    asyncio.run(manual_test())
