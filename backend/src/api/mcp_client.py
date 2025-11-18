"""
MCP Client 服務

提供與 casual-market MCP Server 的集成，用於獲取市場數據。

實作說明：
- 使用 agents.mcp.MCPServerStdio 管理 MCP Server 連接
- 透過 stdio 協議與 casual-market-mcp 通信
- 提供完整的錯誤處理和重試機制
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from agents.mcp import MCPServerStdio

from common.logger import logger


class MCPMarketClient:
    """
    MCP Market 客戶端

    用於調用 casual-market MCP Server 獲取台灣股市數據。
    支援 21 個專業工具。
    """

    def __init__(self, timeout: int = 30):
        """
        初始化 MCP Market 客戶端

        Args:
            timeout: 超時時間（秒）
        """
        self.timeout = timeout

        # 優先使用環境變數路徑，若無則使用硬編碼的本地開發路徑
        casual_market_path = os.getenv("CASUAL_MARKET_PATH")

        if casual_market_path and os.path.isabs(casual_market_path):
            # 使用絕對路徑（本地開發）
            self.server_params = {
                "command": "uvx",
                "args": [
                    "--from",
                    casual_market_path,
                    "casual-market-mcp",
                ],
            }
            logger.info(f"MCP Market Client 使用本地路徑: {casual_market_path}")
        else:
            # 使用已安裝的包（生產環境）
            self.server_params = {
                "command": "uvx",
                "args": ["casual-market-mcp"],
            }
            logger.info("MCP Market Client 使用已安裝的 casual-market-mcp 包")

        self._server: MCPServerStdio | None = None
        logger.info("MCP Market Client 已初始化")

    async def __aenter__(self):
        """異步上下文管理器進入"""
        logger.debug("創建 MCP Server 連接")
        self._server = await MCPServerStdio(
            self.server_params, client_session_timeout_seconds=self.timeout
        ).__aenter__()
        logger.info("MCP Server 連接已建立")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self._server:
            try:
                await self._server.__aexit__(exc_type, exc_val, exc_tb)
                logger.debug("MCP Server 連接已關閉")
            except Exception as e:
                logger.warning(f"關閉 MCP Server 時發生錯誤: {e}")
        self._server = None

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None, retries: int = 2
    ) -> dict[str, Any]:
        """
        調用 MCP 工具

        Args:
            tool_name: MCP 工具名稱
            arguments: 工具參數
            retries: 重試次數

        Returns:
            工具執行結果

        Raises:
            RuntimeError: 當 server 未初始化時
            Exception: 調用失敗時拋出異常
        """
        if not self._server:
            raise RuntimeError("MCP Server 未初始化，請使用 async with 語法")

        arguments = arguments or {}
        last_error = None

        for attempt in range(retries + 1):
            try:
                logger.info(f"調用 MCP 工具: {tool_name} (嘗試 {attempt + 1}/{retries + 1})")

                # 使用 MCPServerStdio 的 call_tool 方法
                result = await asyncio.wait_for(
                    self._server.call_tool(tool_name, arguments), timeout=self.timeout
                )

                # 解析結果
                if result.content:
                    content = result.content[0]
                    if hasattr(content, "text"):
                        text = content.text
                        logger.debug(f"收到回應: {text[:200]}...")  # 記錄前200字符

                        # 嘗試解析 JSON
                        try:
                            data = json.loads(text)
                            logger.debug(f"MCP 工具調用成功: {tool_name}")
                            return data
                        except json.JSONDecodeError:
                            # 如果不是 JSON，直接返回文本
                            logger.debug("回應不是 JSON，返回原始文本")
                            return {"text": text, "success": True}
                    else:
                        logger.warning(f"未預期的內容類型: {type(content)}")
                        return {"error": "Unexpected content type", "content": str(content)}
                else:
                    logger.warning(f"MCP 工具返回空結果: {tool_name}")
                    return {"error": "Empty result", "tool": tool_name}

            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(f"MCP 工具調用超時: {tool_name} (嘗試 {attempt + 1}/{retries + 1})")
                if attempt < retries:
                    await asyncio.sleep(1 * (attempt + 1))  # 指數退避

            except Exception as e:
                last_error = e
                logger.error(
                    f"MCP 工具調用失敗: {tool_name} - {str(e)} (嘗試 {attempt + 1}/{retries + 1})"
                )
                if attempt < retries:
                    await asyncio.sleep(1 * (attempt + 1))

        # 所有重試都失敗
        error_msg = f"MCP 工具調用失敗（已重試 {retries} 次）: {tool_name}"
        logger.error(error_msg)
        raise Exception(error_msg) from last_error

    # ==========================================
    # 股票報價
    # ==========================================

    async def get_stock_price(self, symbol: str) -> dict[str, Any]:
        """
        獲取台灣股票即時報價

        Args:
            symbol: 股票代碼或公司名稱（如 "2330" 或 "台積電"）

        Returns:
            股票報價資訊
        """
        return await self.call_tool("get_taiwan_stock_price", {"symbol": symbol})

    # ==========================================
    # 市場指數
    # ==========================================

    async def get_market_indices(self) -> dict[str, Any]:
        """
        獲取市場指數資訊

        Returns:
            市場指數資訊，包含發行量加權股價指數的即時資訊
        """
        return await self.call_tool("get_market_index_info", {})

    async def get_historical_index(self) -> dict[str, Any]:
        """
        獲取歷史指數資料

        Returns:
            歷史指數資料
        """
        return await self.call_tool("get_market_historical_index", {})

    # ==========================================
    # 交易日檢查
    # ==========================================

    async def check_trading_day(self, date: str) -> dict[str, Any]:
        """
        檢查是否為交易日

        Args:
            date: 日期 (YYYY-MM-DD 格式)

        Returns:
            交易日資訊
        """
        return await self.call_tool("check_taiwan_trading_day", {"date": date})

    async def get_holiday_info(self, date: str) -> dict[str, Any]:
        """
        獲取節假日資訊

        Args:
            date: 日期 (YYYY-MM-DD 格式)

        Returns:
            節假日資訊
        """
        return await self.call_tool("get_taiwan_holiday_info", {"date": date})

    # ==========================================
    # 模擬交易
    # ==========================================

    async def buy_stock(
        self, symbol: str, quantity: int, price: float | None = None
    ) -> dict[str, Any]:
        """
        模擬買入股票

        Args:
            symbol: 股票代碼
            quantity: 數量（必須是 1000 的倍數）
            price: 指定價格（可選，不指定則為市價）

        Returns:
            交易結果
        """
        args = {"symbol": symbol, "quantity": quantity}
        if price is not None:
            args["price"] = price

        return await self.call_tool("buy_taiwan_stock", args)

    async def sell_stock(
        self, symbol: str, quantity: int, price: float | None = None
    ) -> dict[str, Any]:
        """
        模擬賣出股票

        Args:
            symbol: 股票代碼
            quantity: 數量（必須是 1000 的倍數）
            price: 指定價格（可選，不指定則為市價）

        Returns:
            交易結果
        """
        args = {"symbol": symbol, "quantity": quantity}
        if price is not None:
            args["price"] = price

        return await self.call_tool("sell_taiwan_stock", args)

    # ==========================================
    # 財務報表
    # ==========================================

    async def get_balance_sheet(
        self, symbol: str, year: int | None = None, season: int | None = None
    ) -> dict[str, Any]:
        """
        獲取公司資產負債表

        Args:
            symbol: 股票代碼
            year: 年度（可選）
            season: 季度（可選）

        Returns:
            資產負債表
        """
        args = {"symbol": symbol}
        if year:
            args["year"] = year
        if season:
            args["season"] = season

        return await self.call_tool("get_company_balance_sheet", args)

    async def get_income_statement(
        self, symbol: str, year: int | None = None, season: int | None = None
    ) -> dict[str, Any]:
        """
        獲取公司損益表

        Args:
            symbol: 股票代碼
            year: 年度（可選）
            season: 季度（可選）

        Returns:
            損益表
        """
        args = {"symbol": symbol}
        if year:
            args["year"] = year
        if season:
            args["season"] = season

        return await self.call_tool("get_company_income_statement", args)

    async def get_dividend(self, symbol: str) -> dict[str, Any]:
        """
        獲取股利資訊

        Args:
            symbol: 股票代碼

        Returns:
            股利資訊
        """
        return await self.call_tool("get_company_dividend", {"symbol": symbol})

    async def get_monthly_revenue(
        self, symbol: str, year: int | None = None, month: int | None = None
    ) -> dict[str, Any]:
        """
        獲取月營收

        Args:
            symbol: 股票代碼
            year: 年度（可選）
            month: 月份（可選）

        Returns:
            月營收資訊
        """
        args = {"symbol": symbol}
        if year:
            args["year"] = year
        if month:
            args["month"] = month

        return await self.call_tool("get_company_monthly_revenue", args)

    async def get_valuation_ratios(self, symbol: str) -> dict[str, Any]:
        """
        獲取估值比率（本益比、殖利率等）

        Args:
            symbol: 股票代碼

        Returns:
            估值比率
        """
        return await self.call_tool("get_stock_valuation_ratios", {"symbol": symbol})

    async def get_company_profile(self, symbol: str) -> dict[str, Any]:
        """
        獲取公司基本資料

        Args:
            symbol: 股票代碼

        Returns:
            公司基本資料
        """
        return await self.call_tool("get_company_profile", {"symbol": symbol})

    # ==========================================
    # 市場統計
    # ==========================================

    async def get_real_time_trading_stats(self) -> dict[str, Any]:
        """
        獲取即時交易統計

        Returns:
            即時交易統計
        """
        return await self.call_tool("get_real_time_trading_stats", {})

    async def get_daily_trading(self, symbol: str, date: str | None = None) -> dict[str, Any]:
        """
        獲取日交易資料

        Args:
            symbol: 股票代碼
            date: 日期（可選，格式 YYYY-MM-DD）

        Returns:
            日交易資料
        """
        args = {"symbol": symbol}
        if date:
            args["date"] = date

        return await self.call_tool("get_stock_daily_trading", args)

    async def get_monthly_trading(
        self, symbol: str, year: int | None = None, month: int | None = None
    ) -> dict[str, Any]:
        """
        獲取月交易資料

        Args:
            symbol: 股票代碼
            year: 年度（可選）
            month: 月份（可選）

        Returns:
            月交易資料
        """
        args = {"symbol": symbol}
        if year:
            args["year"] = year
        if month:
            args["month"] = month

        return await self.call_tool("get_stock_monthly_trading", args)

    async def get_margin_trading_info(self) -> dict[str, Any]:
        """
        獲取市場融資融券統計資訊

        Returns:
            融資融券資訊，包含整體市場籌碼面分析
        """
        return await self.call_tool("get_margin_trading_info", {})

    # ==========================================
    # 外資動向
    # ==========================================

    async def get_foreign_investment_by_industry(self, count: int | None = None) -> dict[str, Any]:
        """
        獲取外資產業持股分布

        Args:
            count: 限制返回的產業數量（可選，預設為 10）

        Returns:
            外資產業持股資訊
        """
        args = {}
        if count is not None:
            args["count"] = count

        return await self.call_tool("get_foreign_investment_by_industry", args)

    async def get_top_foreign_holdings(self) -> dict[str, Any]:
        """
        獲取外資持股前 20 名

        Returns:
            外資持股排名
        """
        return await self.call_tool("get_top_foreign_holdings", {})

    # ==========================================
    # 其他
    # ==========================================

    async def get_dividend_schedule(self, symbol: str = "") -> dict[str, Any]:
        """
        獲取除權息行事曆

        Args:
            symbol: 股票代碼（可選，空字串表示查詢全部）

        Returns:
            除權息行事曆
        """
        return await self.call_tool("get_dividend_rights_schedule", {"symbol": symbol})

    async def get_etf_ranking(self) -> dict[str, Any]:
        """
        獲取 ETF 定期定額排名

        Returns:
            ETF 排名
        """
        return await self.call_tool("get_etf_regular_investment_ranking", {})


# 工廠函數
def create_mcp_market_client(timeout: int = 30) -> MCPMarketClient:
    """
    建立 MCP Market 客戶端實例

    Args:
        timeout: 超時時間（秒）

    Returns:
        MCPMarketClient 實例

    Usage:
        async with create_mcp_market_client() as client:
            result = await client.get_stock_price("2330")
    """
    return MCPMarketClient(timeout)
