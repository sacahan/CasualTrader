"""
快速測試台灣證交所 API 回應格式。
"""

import asyncio
import httpx


async def test_api_response():
    """測試實際的 API 回應格式。"""
    url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    params = {
        "ex_ch": "tse_2330.tw",
        "json": "1",
        "delay": "0",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://mis.twse.com.tw/stock/fibest.jsp",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 200:
                data = response.json()
                print(f"JSON Keys: {list(data.keys())}")
                if "msgArray" in data:
                    print(f"msgArray: {data['msgArray']}")
                    if data["msgArray"]:
                        print(f"First item: {data['msgArray'][0]}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_api_response())
