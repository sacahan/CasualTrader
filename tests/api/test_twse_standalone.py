#!/usr/bin/env python3
"""
獨立測試腳本，用於測試 TWSE API 客戶端
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 直接引入需要的模組，避免 market_mcp 包的初始化問題
from market_mcp.models.stock_data import (
    StockQuoteRequest,
    TWStockResponse,
    APIError,
    ValidationError,
)
from market_mcp.parsers.twse_parser import create_parser
from market_mcp.utils.validators import (
    determine_market_type,
    validate_taiwan_stock_symbol,
)

# 複製 TWStockAPIClient 的核心邏輯
import httpx
from datetime import datetime


class SimpleTWStockAPIClient:
    """簡化版的台灣證交所 API 客戶端"""

    def __init__(self):
        self.base_url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
        self.timeout = 5.0
        self.max_retries = 3
        self.parser = create_parser()

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
        """取得股票報價"""
        if not validate_taiwan_stock_symbol(symbol):
            raise ValidationError(f"無效的股票代號格式: {symbol}")

        if market is None:
            market = determine_market_type(symbol)

        request = StockQuoteRequest(symbol=symbol, market=market)
        raw_response = await self._make_api_request(request)
        stock_data_list = self.parser.parse_stock_data(raw_response)

        if not stock_data_list:
            raise APIError(f"找不到股票 {symbol} 的資料")

        return stock_data_list[0]

    async def _make_api_request(self, request: StockQuoteRequest):
        """發送 API 請求"""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return await self._send_http_request(request)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break
            except Exception as e:
                raise APIError(f"API 請求失敗: {e}") from e

        raise APIError(
            f"API 請求失敗，已重試 {self.max_retries} 次"
        ) from last_exception

    async def _send_http_request(self, request: StockQuoteRequest):
        """發送 HTTP 請求"""
        ex_ch = f"{request.market}_{request.symbol}.tw"
        params = {
            "ex_ch": ex_ch,
            "json": "1",
            "delay": "0",
            "_": str(int(datetime.now().timestamp() * 1000)),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    self.base_url, params=params, headers=self.headers
                )

                if response.status_code != 200:
                    raise APIError(
                        f"API 回應錯誤，狀態碼: {response.status_code}",
                        status_code=response.status_code,
                    )

                try:
                    json_data = response.json()
                except Exception as e:
                    raise APIError(f"無法解析 JSON 回應: {e}") from e

                return self.parser.parse_raw_response(json_data)

            except httpx.TimeoutException as e:
                raise APIError(f"請求超時: {e}") from e
            except httpx.ConnectError as e:
                raise APIError(f"連線錯誤: {e}") from e
            except Exception as e:
                raise APIError(f"HTTP 請求失敗: {e}") from e

    def close(self):
        """關閉客戶端"""
        pass


async def main():
    """測試主函數"""
    client = SimpleTWStockAPIClient()
    try:
        print("正在查詢股票 3231 (緯創)...")
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


if __name__ == "__main__":
    asyncio.run(main())
