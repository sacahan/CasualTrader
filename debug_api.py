#!/usr/bin/env python3

import asyncio
import json
import httpx
from datetime import datetime

async def test_raw_api():
    """直接測試證交所 API 回應格式"""
    
    # API 參數
    base_url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    symbol = "1101"
    ex_ch = f"tse_{symbol}.tw"
    
    params = {
        "ex_ch": ex_ch,
        "json": "1",
        "delay": "0",
        "_": str(int(datetime.now().timestamp() * 1000))
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://mis.twse.com.tw/stock/fibest.jsp",
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(base_url, params=params, headers=headers)
            print(f"HTTP 狀態碼: {response.status_code}")
            print(f"回應內容:")
            
            json_data = response.json()
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
            
            # 檢查 msgArray 內容
            if "msgArray" in json_data and json_data["msgArray"]:
                stock_info = json_data["msgArray"][0]
                print(f"\n=== 欄位解析 ===")
                print(f"股票代號 (c): {stock_info.get('c', 'N/A')}")
                print(f"公司名稱 (n): {stock_info.get('n', 'N/A')}")
                print(f"成交價 (z): {stock_info.get('z', 'N/A')}")
                print(f"開盤價 (o): {stock_info.get('o', 'N/A')}")
                print(f"最高價 (h): {stock_info.get('h', 'N/A')}")
                print(f"最低價 (l): {stock_info.get('l', 'N/A')}")
                print(f"昨收價 (y): {stock_info.get('y', 'N/A')}")
                print(f"成交量 (v): {stock_info.get('v', 'N/A')}")
                
        except Exception as e:
            print(f"錯誤: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_raw_api())
