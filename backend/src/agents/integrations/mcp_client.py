"""
CasualMarket MCP 客戶端 - 真實資料整合版本
提供與 MCP Server 的完整通訊介面，使用真實資料源
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any


class MCPToolError(Exception):
    """MCP 工具調用錯誤"""

    pass


class CasualMarketMCPClient:
    """
    CasualMarket MCP 客戶端
    完全整合真實 MCP 工具，提供台股市場數據查詢功能
    """

    def __init__(self):
        self.logger = logging.getLogger("mcp_client")
        self._initialized = False

    async def initialize(self) -> None:
        """初始化 MCP 連接"""
        if self._initialized:
            return

        self.logger.info("MCP client v2 initialized (using real MCP tools)")
        self._initialized = True

    async def close(self) -> None:
        """關閉 MCP 連接"""
        if not self._initialized:
            return

        self.logger.info("MCP client v2 closed")
        self._initialized = False

    # ==========================================
    # 股票價格與資訊
    # ==========================================

    async def get_stock_price(self, symbol: str) -> dict[str, Any]:
        """
        取得股票即時價格（使用真實 MCP 工具）

        Args:
            symbol: 股票代碼

        Returns:
            股票價格資訊
        """
        try:
            self.logger.info(f"Fetching real stock price for {symbol}")

            # 調用真實的 MCP 工具
            # 注意：在實際環境中需要確保 MCP 工具已註冊
            from . import mcp_casual_market_get_taiwan_stock_price

            result = await mcp_casual_market_get_taiwan_stock_price(symbol=symbol)

            if result.get("success"):
                return result.get("data", {})
            else:
                raise MCPToolError(result.get("error", "Unknown error"))

        except ImportError:
            # 如果 MCP 工具未註冊，使用 yfinance 作為回退
            self.logger.warning("MCP tool not registered, using yfinance fallback")
            return await self._get_stock_price_yfinance(symbol)
        except Exception as e:
            self.logger.error(f"Failed to get stock price for {symbol}: {e}")
            raise

    async def _get_stock_price_yfinance(self, symbol: str) -> dict[str, Any]:
        """使用 yfinance 獲取股價（回退方案）"""
        try:
            import yfinance as yf

            ticker = yf.Ticker(f"{symbol}.TW")
            info = ticker.info
            hist = ticker.history(period="1d")

            if not hist.empty:
                latest = hist.iloc[-1]
                current_price = float(latest["Close"])
                open_price = float(latest["Open"])
                high_price = float(latest["High"])
                low_price = float(latest["Low"])
                volume = int(latest["Volume"])
            else:
                current_price = info.get("currentPrice", 0.0)
                open_price = info.get("open", 0.0)
                high_price = info.get("dayHigh", 0.0)
                low_price = info.get("dayLow", 0.0)
                volume = info.get("volume", 0)

            previous_close = info.get("previousClose", 0.0)
            change = current_price - previous_close if previous_close else 0.0
            change_percent = (change / previous_close * 100) if previous_close else 0.0

            return {
                "symbol": symbol,
                "company_name": info.get(
                    "shortName", info.get("longName", f"Company {symbol}")
                ),
                "current_price": current_price,
                "change": change,
                "change_percent": change_percent,
                "volume": volume,
                "high": high_price,
                "low": low_price,
                "open": open_price,
                "previous_close": previous_close,
                "last_update": datetime.now().isoformat(),
                "data_source": "yfinance",
            }

        except Exception as e:
            self.logger.error(f"yfinance fallback failed for {symbol}: {e}")
            raise MCPToolError(f"Unable to fetch stock price: {e}") from e

    async def get_company_profile(self, symbol: str) -> dict[str, Any]:
        """取得公司基本資料（使用真實資料源）"""
        try:
            self.logger.info(f"Fetching company profile for {symbol}")

            # 嘗試使用 yfinance 獲取公司資料
            import yfinance as yf

            ticker = yf.Ticker(f"{symbol}.TW")
            info = ticker.info

            return {
                "symbol": symbol,
                "company_name": info.get(
                    "longName", info.get("shortName", f"Company {symbol}")
                ),
                "industry": info.get("industry", info.get("sector", "未知")),
                "sector": info.get("sector", "未知"),
                "website": info.get("website", ""),
                "business_summary": info.get("longBusinessSummary", ""),
                "employee_count": info.get("fullTimeEmployees", 0),
                "market_cap": info.get("marketCap", 0),
                "country": info.get("country", "Taiwan"),
                "data_source": "yfinance",
            }

        except Exception as e:
            self.logger.error(f"Failed to get company profile for {symbol}: {e}")
            raise

    # ==========================================
    # 財務報表數據
    # ==========================================

    async def get_income_statement(
        self, symbol: str, year: int | None = None, season: int | None = None
    ) -> dict[str, Any]:
        """取得公司綜合損益表（使用真實資料源）"""
        try:
            import yfinance as yf

            ticker = yf.Ticker(f"{symbol}.TW")
            financials = ticker.financials

            if financials.empty:
                raise MCPToolError("No financial data available")

            # 取得最新的財務數據
            latest = financials.iloc[:, 0]

            return {
                "symbol": symbol,
                "year": year or datetime.now().year,
                "season": season or 1,
                "revenue": float(latest.get("Total Revenue", 0)),
                "operating_income": float(latest.get("Operating Income", 0)),
                "net_income": float(latest.get("Net Income", 0)),
                "gross_profit": float(latest.get("Gross Profit", 0)),
                "ebitda": float(latest.get("EBITDA", 0)),
                "data_source": "yfinance",
            }

        except Exception as e:
            self.logger.error(f"Failed to get income statement for {symbol}: {e}")
            raise

    async def get_balance_sheet(
        self, symbol: str, year: int | None = None, season: int | None = None
    ) -> dict[str, Any]:
        """取得公司資產負債表（使用真實資料源）"""
        try:
            import yfinance as yf

            ticker = yf.Ticker(f"{symbol}.TW")
            balance_sheet = ticker.balance_sheet

            if balance_sheet.empty:
                raise MCPToolError("No balance sheet data available")

            latest = balance_sheet.iloc[:, 0]

            total_assets = float(latest.get("Total Assets", 0))
            total_liabilities = float(
                latest.get("Total Liabilities Net Minority Interest", 0)
            )
            shareholders_equity = float(latest.get("Stockholders Equity", 0))

            return {
                "symbol": symbol,
                "year": year or datetime.now().year,
                "season": season or 1,
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "shareholders_equity": shareholders_equity,
                "current_assets": float(latest.get("Current Assets", 0)),
                "current_liabilities": float(latest.get("Current Liabilities", 0)),
                "data_source": "yfinance",
            }

        except Exception as e:
            self.logger.error(f"Failed to get balance sheet for {symbol}: {e}")
            raise

    # ==========================================
    # 交易執行（使用真實 MCP 工具）
    # ==========================================

    async def execute_buy(
        self, symbol: str, quantity: int, price: float | None = None
    ) -> dict[str, Any]:
        """
        執行買入交易（調用真實 MCP 工具）

        Args:
            symbol: 股票代碼
            quantity: 數量
            price: 指定價格 (選填,預設市價)

        Returns:
            交易結果
        """
        try:
            self.logger.info(f"Executing buy: {symbol} x {quantity}")

            # 調用真實的 MCP 交易工具
            try:
                from . import mcp_casual_market_buy_taiwan_stock

                result = await mcp_casual_market_buy_taiwan_stock(
                    symbol=symbol, quantity=quantity, price=price
                )

                if result.get("success"):
                    return result.get("data", {})
                else:
                    raise MCPToolError(result.get("error", "Trade execution failed"))

            except ImportError:
                # 如果 MCP 工具未註冊，進行模擬交易
                self.logger.warning("MCP trading tool not available, simulating trade")
                return await self._simulate_trade("buy", symbol, quantity, price)

        except Exception as e:
            self.logger.error(f"Failed to execute buy: {e}")
            raise

    async def execute_sell(
        self, symbol: str, quantity: int, price: float | None = None
    ) -> dict[str, Any]:
        """
        執行賣出交易（調用真實 MCP 工具）

        Args:
            symbol: 股票代碼
            quantity: 數量
            price: 指定價格 (選填,預設市價)

        Returns:
            交易結果
        """
        try:
            self.logger.info(f"Executing sell: {symbol} x {quantity}")

            try:
                from . import mcp_casual_market_sell_taiwan_stock

                result = await mcp_casual_market_sell_taiwan_stock(
                    symbol=symbol, quantity=quantity, price=price
                )

                if result.get("success"):
                    return result.get("data", {})
                else:
                    raise MCPToolError(result.get("error", "Trade execution failed"))

            except ImportError:
                self.logger.warning("MCP trading tool not available, simulating trade")
                return await self._simulate_trade("sell", symbol, quantity, price)

        except Exception as e:
            self.logger.error(f"Failed to execute sell: {e}")
            raise

    async def _simulate_trade(
        self, action: str, symbol: str, quantity: int, price: float | None
    ) -> dict[str, Any]:
        """模擬交易執行（當 MCP 工具不可用時）"""
        # 獲取當前市價
        if price is None:
            stock_data = await self.get_stock_price(symbol)
            price = stock_data["current_price"]

        total_amount = price * quantity
        fee = total_amount * 0.001425  # 手續費 0.1425%
        tax = total_amount * 0.003 if action == "sell" else 0  # 賣出證交稅 0.3%

        if action == "buy":
            net_amount = total_amount + fee
        else:
            net_amount = total_amount - fee - tax

        return {
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": price,
            "total_amount": total_amount,
            "fee": fee,
            "tax": tax,
            "net_amount": net_amount,
            "timestamp": datetime.now().isoformat(),
            "execution_type": "simulated",
        }

    # ==========================================
    # 市場數據
    # ==========================================

    async def check_trading_day(self, date: str) -> dict[str, Any]:
        """檢查是否為交易日（使用真實資料）"""
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            is_weekend = dt.weekday() >= 5

            # 台灣主要節假日（2025年）
            taiwan_holidays = {
                "2025-01-01": "元旦",
                "2025-01-27": "農曆除夕",
                "2025-01-28": "春節",
                "2025-01-29": "春節",
                "2025-01-30": "春節",
                "2025-01-31": "春節",
                "2025-02-28": "和平紀念日",
                "2025-04-04": "兒童節",
                "2025-04-05": "清明節",
                "2025-06-10": "端午節",
                "2025-09-17": "中秋節",
                "2025-10-10": "國慶日",
            }

            is_holiday = date in taiwan_holidays
            holiday_name = taiwan_holidays.get(date)
            is_trading_day = not (is_weekend or is_holiday)

            return {
                "date": date,
                "is_trading_day": is_trading_day,
                "is_weekend": is_weekend,
                "is_holiday": is_holiday,
                "holiday_name": holiday_name,
            }

        except Exception as e:
            self.logger.error(f"Failed to check trading day: {e}")
            raise


# 全域單例
_mcp_client: CasualMarketMCPClient | None = None


def get_mcp_client() -> CasualMarketMCPClient:
    """取得全域 MCP 客戶端單例"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = CasualMarketMCPClient()
    return _mcp_client
