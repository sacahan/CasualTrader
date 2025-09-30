"""
台灣證券交易所 API 客戶端。

提供與台灣證交所即時股價 API 的整合功能，包含請求發送、
回應處理、錯誤重試等機制。
"""

import asyncio
from datetime import datetime
from typing import Any

import httpx

from ..models.stock_data import (
    APIError,
    StockQuoteRequest,
    TWAPIRawResponse,
    TWStockResponse,
    ValidationError,
)
from ..parsers.twse_parser import create_parser
from ..utils.validators import determine_market_type, validate_taiwan_stock_symbol


class TWStockAPIClient:
    """
    台灣證券交易所 API 客戶端。

    負責處理與證交所 API 的通信，包含請求建構、發送、
    回應解析和錯誤處理。
    """

    def __init__(self):
        """初始化 API 客戶端。"""
        self.base_url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
        self.timeout = 5.0
        self.max_retries = 3
        self.parser = create_parser()

        # 設定 HTTP 客戶端標頭
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://mis.twse.com.tw/stock/fibest.jsp",
        }

    async def get_stock_quote(
        self, symbol: str, market: str | None = None
    ) -> TWStockResponse:
        """
        取得單一股票即時報價。

        Args:
            symbol: 股票代號 (4位數字)
            market: 市場類型 ('tse' 或 'otc')，如果未指定會自動判斷

        Returns:
            TWStockResponse: 股票報價資料

        Raises:
            ValidationError: 股票代號格式不正確
            APIError: API 請求失敗
        """
        # 驗證股票代號
        if not validate_taiwan_stock_symbol(symbol):
            raise ValidationError(f"無效的股票代號格式: {symbol}")

        # 自動判斷市場類型
        if market is None:
            market = determine_market_type(symbol)

        # 建立請求物件
        request = StockQuoteRequest(symbol=symbol, market=market)

        # 發送 API 請求
        raw_response = await self._make_api_request(request)

        # 解析回應資料
        stock_data_list = self.parser.parse_stock_data(raw_response)

        if not stock_data_list:
            raise APIError(f"找不到股票 {symbol} 的資料")

        return stock_data_list[0]

    async def get_multiple_quotes(self, symbols: list[str]) -> list[TWStockResponse]:
        """
        取得多支股票的即時報價。

        Args:
            symbols: 股票代號清單

        Returns:
            list[TWStockResponse]: 股票報價資料清單
        """
        tasks = []
        for symbol in symbols:
            task = self.get_stock_quote(symbol)
            tasks.append(task)

        # 並行處理多個請求
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 過濾掉異常結果，只返回成功的資料
        valid_results = []
        for result in results:
            if isinstance(result, TWStockResponse):
                valid_results.append(result)
            # 錯誤結果會在個別的 get_stock_quote 呼叫中處理

        return valid_results

    async def _make_api_request(self, request: StockQuoteRequest) -> TWAPIRawResponse:
        """
        發送 API 請求並處理重試邏輯。

        Args:
            request: 股票報價請求

        Returns:
            TWAPIRawResponse: API 原始回應

        Raises:
            APIError: API 請求失敗且重試次數用盡
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await self._send_http_request(request)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # 指數退避重試
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break
            except Exception as e:
                # 其他錯誤不重試
                raise APIError(f"API 請求失敗: {e}") from e

        # 所有重試都失敗
        raise APIError(
            f"API 請求失敗，已重試 {self.max_retries} 次"
        ) from last_exception

    async def _send_http_request(self, request: StockQuoteRequest) -> TWAPIRawResponse:
        """
        發送 HTTP 請求到證交所 API。

        Args:
            request: 股票報價請求

        Returns:
            TWAPIRawResponse: API 原始回應

        Raises:
            APIError: HTTP 請求失敗或回應格式錯誤
        """
        # 建構查詢參數
        params = self._build_query_params(request)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    self.base_url, params=params, headers=self.headers
                )

                # 檢查 HTTP 狀態碼
                if response.status_code != 200:
                    raise APIError(
                        f"API 回應錯誤，狀態碼: {response.status_code}",
                        status_code=response.status_code,
                    )

                # 解析 JSON 回應
                try:
                    json_data = response.json()
                except Exception as e:
                    raise APIError(f"無法解析 JSON 回應: {e}") from e

                # 驗證回應格式
                return self.parser.parse_raw_response(json_data)

            except httpx.TimeoutException as e:
                raise APIError(f"請求超時: {e}") from e
            except httpx.ConnectError as e:
                raise APIError(f"連線錯誤: {e}") from e
            except Exception as e:
                raise APIError(f"HTTP 請求失敗: {e}") from e

    def _build_query_params(self, request: StockQuoteRequest) -> dict[str, Any]:
        """
        建構 API 查詢參數。

        Args:
            request: 股票報價請求

        Returns:
            dict: 查詢參數字典
        """
        # 根據市場類型建構 ex_ch 參數
        ex_ch = f"{request.market}_{request.symbol}.tw"

        return {
            "ex_ch": ex_ch,
            "json": "1",
            "delay": "0",
            "_": str(int(datetime.now().timestamp() * 1000)),  # 時間戳避免快取
        }

    async def check_api_health(self) -> bool:
        """
        檢查 API 服務健康狀態。

        Returns:
            bool: API 是否可用

        Examples:
            >>> client = TWStockAPIClient()
            >>> await client.check_api_health()
            True
        """
        try:
            # 使用台積電 (2330) 作為健康檢查標的
            await self.get_stock_quote("2330")
            return True
        except Exception:
            return False

    def close(self):
        """關閉 HTTP 客戶端連線。"""
        # httpx AsyncClient 會自動清理連線
        pass

    async def __aenter__(self):
        """非同步內容管理器進入。"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同步內容管理器退出。"""
        self.close()


def create_client() -> TWStockAPIClient:
    """
    建立台灣證交所 API 客戶端實例。

    Returns:
        TWStockAPIClient: API 客戶端實例

    Examples:
        >>> client = create_client()
        >>> quote = await client.get_stock_quote("2330")
        >>> print(f"{quote.symbol}: {quote.current_price}")
        2330: 245.50
    """
    return TWStockAPIClient()


# 增加 main 函式以便直接執行測試
if __name__ == "__main__":
    import asyncio
    import os
    import sys

    # 將專案根目錄加入 Python 路徑，讓相對引入可以正常運作
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    async def main():
        client = create_client()
        try:
            quote = await client.get_stock_quote("3231")
            print("成功取得股票資料:")
            print(f"公司名稱: {quote.company_name}")
            print(f"股票代號: {quote.symbol}")
            print(f"目前價格: ${quote.current_price}")
            print(f"漲跌幅: {quote.change:+.2f} ({quote.change_percent * 100:+.2f}%)")
            print(f"成交量: {quote.volume:,}")
        except Exception as e:
            print(f"錯誤: {e}")
        finally:
            client.close()

    asyncio.run(main())
