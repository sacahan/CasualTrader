"""
台灣證交所 API 整合測試。

測試證交所 API 客戶端的各種功能，包含成功案例和錯誤處理。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from market_mcp.api.twse_client import create_client
from market_mcp.models.stock_data import APIError, ValidationError, TWStockResponse


class TestTWStockAPIClient:
    """測試台灣證交所 API 客戶端。"""

    @pytest.fixture
    def client(self):
        """建立測試用 API 客戶端。"""
        return create_client()

    @pytest.fixture
    def mock_api_response(self):
        """模擬 API 回應資料。"""
        return {
            "msgArray": [
                {
                    "c": "2330",  # 股票代號
                    "n": "台積電",  # 股票名稱
                    "nf": "台灣積體電路製造股份有限公司",  # 完整公司名稱
                    "z": "245.50",  # 成交價
                    "o": "245.00",  # 開盤價
                    "h": "246.00",  # 最高價
                    "l": "244.50",  # 最低價
                    "y": "245.00",  # 昨收價
                    "v": "1000",  # 成交量
                    "b": "245.00_500_244.50_300_",  # 買價_買量串接字串
                    "a": "246.00_400_246.50_200_",  # 賣價_賣量串接字串
                    "t": "14:30:00",  # 成交時刻
                    "u": "269.00",  # 漲停價
                    "w": "221.00",  # 跌停價
                    "d": "20231201",  # 更新日期
                    "%": "14:30:00",  # 更新時間
                }
            ],
            "referer": "",
            "userDelay": 0,
            "rtcode": "0000",
            "queryTime": {"sysTime": "14:30:00", "stockInfoItem": 1},
        }

    @pytest.mark.asyncio
    async def test_get_stock_quote_success(self, client, mock_api_response):
        """測試成功取得股票報價。"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # 設定 mock HTTP 回應
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_api_response

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # 執行測試
            result = await client.get_stock_quote("2330")

            # 驗證結果
            assert isinstance(result, TWStockResponse)
            assert result.symbol == "2330"
            assert result.company_name == "台灣積體電路製造股份有限公司"
            assert result.current_price == 245.50
            assert result.change == 0.50
            assert result.volume == 1000
            assert len(result.bid_prices) > 0
            assert len(result.ask_prices) > 0

    @pytest.mark.asyncio
    async def test_get_stock_quote_invalid_symbol(self, client):
        """測試無效股票代號。"""
        with pytest.raises(ValidationError, match="無效的股票代號格式"):
            await client.get_stock_quote("123")  # 只有3位數

        with pytest.raises(ValidationError, match="無效的股票代號格式"):
            await client.get_stock_quote("abcd")  # 非數字

    @pytest.mark.asyncio
    async def test_get_stock_quote_api_error(self, client):
        """測試 API 錯誤處理。"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # 設定 mock HTTP 錯誤回應
            mock_response = MagicMock()
            mock_response.status_code = 500

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # 執行測試並驗證異常
            with pytest.raises(APIError, match="API 回應錯誤"):
                await client.get_stock_quote("2330")

    @pytest.mark.asyncio
    async def test_get_stock_quote_timeout_retry(self, client):
        """測試超時重試機制。"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # 設定 mock 超時異常
            import httpx

            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # 執行測試並驗證重試後拋出異常
            with pytest.raises(APIError, match="API 請求失敗"):
                await client.get_stock_quote("2330")

            # 驗證有重試行為
            assert mock_client.get.call_count >= 1

    @pytest.mark.asyncio
    async def test_get_multiple_quotes(self, client, mock_api_response):
        """測試取得多支股票報價。"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # 設定 mock HTTP 回應
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_api_response

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # 執行測試
            symbols = ["2330", "2317", "2454"]
            results = await client.get_multiple_quotes(symbols)

            # 驗證結果
            assert len(results) == len(symbols)
            for result in results:
                assert isinstance(result, TWStockResponse)

    @pytest.mark.asyncio
    async def test_check_api_health_success(self, client, mock_api_response):
        """測試 API 健康檢查成功。"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # 設定 mock HTTP 回應
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_api_response

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # 執行測試
            is_healthy = await client.check_api_health()

            # 驗證結果
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_check_api_health_failure(self, client):
        """測試 API 健康檢查失敗。"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # 設定 mock HTTP 錯誤
            import httpx

            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # 執行測試
            is_healthy = await client.check_api_health()

            # 驗證結果
            assert is_healthy is False

    def test_build_query_params(self, client):
        """測試查詢參數建構。"""
        from market_mcp.models.stock_data import StockQuoteRequest

        request = StockQuoteRequest(symbol="2330", market="tse")
        params = client._build_query_params(request)

        # 驗證參數
        assert params["ex_ch"] == "tse_2330.tw"
        assert params["json"] == "1"
        assert params["delay"] == "0"
        assert "_" in params  # 時間戳參數

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_api_response):
        """測試異步內容管理器。"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # 設定 mock HTTP 回應
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_api_response

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # 使用異步內容管理器
            async with create_client() as client:
                result = await client.get_stock_quote("2330")
                assert isinstance(result, TWStockResponse)


@pytest.mark.asyncio
async def test_real_api_connection():
    """
    真實 API 連線測試（可選）。

    這個測試會實際呼叫證交所 API，只在需要時執行。
    可以透過環境變量 ENABLE_REAL_API_TEST=1 來啟用。
    """
    import os

    if not os.getenv("ENABLE_REAL_API_TEST"):
        pytest.skip("跳過真實 API 測試，使用 ENABLE_REAL_API_TEST=1 啟用")

    client = create_client()

    try:
        # 測試台積電股價查詢
        result = await client.get_stock_quote("2330")

        # 驗證基本資料結構
        assert isinstance(result, TWStockResponse)
        assert result.symbol == "2330"
        assert result.company_name is not None
        assert result.current_price > 0
        print(
            f"✅ 真實 API 測試成功: {result.symbol} - {result.company_name} - ${result.current_price}"
        )

    except Exception as e:
        pytest.fail(f"真實 API 測試失敗: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    # 執行真實 API 測試的簡單範例
    async def quick_test():
        client = create_client()
        try:
            result = await client.get_stock_quote("2330")
            print(f"台積電 (2330): {result.current_price} 元")
            print(f"漲跌: {result.change:+.2f} ({result.change_percent:+.2%})")
        except Exception as e:
            print(f"測試失敗: {e}")
        finally:
            await client.close()

    # 執行測試
    asyncio.run(quick_test())
