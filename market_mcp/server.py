"""
簡化的 MCP Server 實作 - 使用 FastMCP 框架
使用 @mcp.tool() 裝飾器模式，大幅簡化架構
"""

from typing import Any

from fastmcp import FastMCP

from .api.twse_client import TWStockAPIClient
from .utils.logging import get_logger, setup_logging

# 設置日誌
setup_logging()
logger = get_logger(__name__)

# 創建 FastMCP 實例
mcp = FastMCP(name="market-mcp-server")

# 全域 API 客戶端
api_client = TWStockAPIClient()


@mcp.tool
async def get_taiwan_stock_price(symbol: str) -> dict[str, Any]:
    """
    取得台灣股票即時價格資訊。

    支援股票代碼或公司名稱查詢：
    - 股票代碼: 4-6位數字 + 可選字母 (例如: 2330, 0050, 00648R)
    - 公司名稱: 完整或部分公司名稱 (例如: "台積電", "鴻海")

    Args:
        symbol: 台灣股票代號或公司名稱

    Returns:
        包含股票價格資訊的字典
    """
    try:
        logger.info(f"查詢股票價格: {symbol}")

        # 呼叫 API 取得股票資料
        stock_data = await api_client.get_stock_quote(symbol)

        # 格式化回應
        result = {
            "status": "success",
            "data": {
                "symbol": stock_data.symbol,
                "name": stock_data.company_name,
                "price": stock_data.current_price,
                "change": stock_data.change,
                "change_percent": stock_data.change_percent,
                "volume": stock_data.volume,
                "high": stock_data.high_price,
                "low": stock_data.low_price,
                "open": stock_data.open_price,
                "previous_close": stock_data.previous_close,
                "last_update": (
                    stock_data.update_time.isoformat()
                    if stock_data.update_time
                    else None
                ),
            },
        }

        logger.info(f"成功取得 {symbol} 股票資料")
        return result

    except Exception as e:
        logger.error(f"查詢股票 {symbol} 失敗: {e}")
        return {"status": "error", "error": str(e), "symbol": symbol}


@mcp.tool
async def buy_taiwan_stock(
    symbol: str, quantity: int, price: float | None = None
) -> dict[str, Any]:
    """
    模擬台灣股票買入操作。

    Args:
        symbol: 股票代碼
        quantity: 購買股數 (台股最小單位為1000股)
        price: 指定價格 (可選，不指定則為市價)

    Returns:
        交易結果資訊
    """
    try:
        logger.info(f"模擬買入: {symbol} x {quantity} 股")

        # 驗證股數 (台股最小單位1000股)
        if quantity % 1000 != 0:
            return {"status": "error", "error": "台股交易最小單位為1000股"}

        # 取得目前股價作為參考
        stock_data = await api_client.get_stock_quote(symbol)
        current_price = stock_data.current_price

        # 如果未指定價格，使用當前價格（市價單）
        if price is None:
            # 市價單：立即以當前價格成交
            order_price = current_price
            total_amount = order_price * quantity
            order_type = "market"
            executed = True
            execution_message = "市價單立即成交"
        else:
            # 限價單：檢查是否符合成交條件
            order_price = price
            total_amount = order_price * quantity
            order_type = "limit"

            # 買入限價單：出價必須 >= 當前賣價才能成交
            if order_price >= current_price:
                executed = True
                execution_message = (
                    f"限價買單成交（出價 {order_price} >= 市價 {current_price}）"
                )
            else:
                executed = False
                execution_message = (
                    f"限價買單無法成交（出價 {order_price} < 市價 {current_price}）"
                )

        if executed:
            result = {
                "status": "success",
                "order": {
                    "action": "buy",
                    "symbol": symbol,
                    "name": stock_data.company_name,
                    "quantity": quantity,
                    "price": order_price,
                    "total_amount": total_amount,
                    "current_price": current_price,
                    "order_type": order_type,
                    "executed": True,
                    "message": execution_message,
                    "timestamp": (
                        stock_data.update_time.isoformat()
                        if stock_data.update_time
                        else None
                    ),
                },
            }
            logger.info(f"買入交易成功: {symbol} x {quantity} @ {order_price}")
        else:
            result = {
                "status": "failed",
                "order": {
                    "action": "buy",
                    "symbol": symbol,
                    "name": stock_data.company_name,
                    "quantity": quantity,
                    "price": order_price,
                    "current_price": current_price,
                    "order_type": order_type,
                    "executed": False,
                    "message": execution_message,
                    "reason": "出價低於市價，無法立即成交",
                },
            }
            logger.info(f"買入交易失敗: {symbol} - {execution_message}")

        return result

    except Exception as e:
        logger.error(f"買入操作失敗: {e}")
        return {"status": "error", "error": str(e), "symbol": symbol}


@mcp.tool
async def sell_taiwan_stock(
    symbol: str, quantity: int, price: float | None = None
) -> dict[str, Any]:
    """
    模擬台灣股票賣出操作。

    Args:
        symbol: 股票代碼
        quantity: 賣出股數 (台股最小單位為1000股)
        price: 指定價格 (可選，不指定則為市價)

    Returns:
        交易結果資訊
    """
    try:
        logger.info(f"模擬賣出: {symbol} x {quantity} 股")

        # 驗證股數 (台股最小單位1000股)
        if quantity % 1000 != 0:
            return {"status": "error", "error": "台股交易最小單位為1000股"}

        # 取得目前股價作為參考
        stock_data = await api_client.get_stock_quote(symbol)
        current_price = stock_data.current_price

        # 如果未指定價格，使用當前價格（市價單）
        if price is None:
            # 市價單：立即以當前價格成交
            order_price = current_price
            total_amount = order_price * quantity
            order_type = "market"
            executed = True
            execution_message = "市價單立即成交"
        else:
            # 限價單：檢查是否符合成交條件
            order_price = price
            total_amount = order_price * quantity
            order_type = "limit"

            # 賣出限價單：售價必須 <= 當前買價才能成交
            if order_price <= current_price:
                executed = True
                execution_message = (
                    f"限價賣單成交（售價 {order_price} <= 市價 {current_price}）"
                )
            else:
                executed = False
                execution_message = (
                    f"限價賣單無法成交（售價 {order_price} > 市價 {current_price}）"
                )

        if executed:
            result = {
                "status": "success",
                "order": {
                    "action": "sell",
                    "symbol": symbol,
                    "name": stock_data.company_name,
                    "quantity": quantity,
                    "price": order_price,
                    "total_amount": total_amount,
                    "current_price": current_price,
                    "order_type": order_type,
                    "executed": True,
                    "message": execution_message,
                    "timestamp": (
                        stock_data.update_time.isoformat()
                        if stock_data.update_time
                        else None
                    ),
                },
            }
            logger.info(f"賣出交易成功: {symbol} x {quantity} @ {order_price}")
        else:
            result = {
                "status": "failed",
                "order": {
                    "action": "sell",
                    "symbol": symbol,
                    "name": stock_data.company_name,
                    "quantity": quantity,
                    "price": order_price,
                    "current_price": current_price,
                    "order_type": order_type,
                    "executed": False,
                    "message": execution_message,
                    "reason": "售價高於市價，無法立即成交",
                },
            }
            logger.info(f"賣出交易失敗: {symbol} - {execution_message}")

        return result

    except Exception as e:
        logger.error(f"賣出操作失敗: {e}")
        return {"status": "error", "error": str(e), "symbol": symbol}


def main() -> None:
    """主程式入口點"""
    logger.info("啟動 Market MCP Server (FastMCP 模式)")

    # 啟動 FastMCP 伺服器
    mcp.run()


if __name__ == "__main__":
    main()
