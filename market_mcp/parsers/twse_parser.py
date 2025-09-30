"""
台灣證券交易所資料解析器。

負責解析證交所 API 回傳的 JSON 資料，轉換為標準化的股票資料模型。
"""

from datetime import datetime


from ..models.stock_data import TWAPIRawResponse, TWStockResponse, ValidationError
from ..utils.validators import (
    parse_price_volume_string,
    extract_prices_and_volumes,
    sanitize_company_name,
    validate_price,
    validate_volume,
)


class TWStockDataParser:
    """
    台灣證交所股票資料解析器。

    負責將證交所 API 的原始 JSON 回應轉換為結構化的股票資料模型。
    """

    def __init__(self):
        """初始化解析器。"""
        self._field_mapping = self._get_field_mapping()

    def _get_field_mapping(self) -> dict[str, str]:
        """
        取得證交所 API 回應欄位對應。

        證交所 API 回傳的 msgArray 每個元素是一個字典，
        包含各種欄位的鍵值對。

        Returns:
            dict: 欄位名稱對應 API 鍵的字典
        """
        return {
            "symbol": "c",  # 股票代號
            "name": "n",  # 股票名稱
            "full_name": "nf",  # 完整公司名稱
            "current_price": "z",  # 成交價
            "open_price": "o",  # 開盤價
            "high_price": "h",  # 最高價
            "low_price": "l",  # 最低價
            "previous_close": "y",  # 昨收價
            "change": None,  # 漲跌 (需計算)
            "volume": "v",  # 成交量
            "bid_data": "b",  # 買價_買量串接字串
            "ask_data": "a",  # 賣價_賣量串接字串
            "last_trade_time": "t",  # 成交時刻
            "upper_limit": "u",  # 漲停價
            "lower_limit": "w",  # 跌停價
            "update_date": "d",  # 更新日期
            "update_time": "%",  # 更新時間
        }

    def parse_raw_response(self, raw_data: dict) -> TWAPIRawResponse:
        """
        解析證交所 API 原始回應。

        Args:
            raw_data: API 原始回應字典

        Returns:
            TWAPIRawResponse: 解析後的原始回應模型

        Raises:
            ValidationError: 回應格式不正確時拋出
        """
        try:
            return TWAPIRawResponse(**raw_data)
        except Exception as e:
            raise ValidationError(f"無法解析 API 回應格式: {e}") from e

    def parse_stock_data(self, raw_response: TWAPIRawResponse) -> list[TWStockResponse]:
        """
        解析股票資料陣列。

        Args:
            raw_response: 原始 API 回應

        Returns:
            list[TWStockResponse]: 解析後的股票資料清單

        Raises:
            ValidationError: 資料解析失敗時拋出
        """
        if not raw_response.msgArray:
            return []

        results = []
        for msg_data in raw_response.msgArray:
            try:
                stock_data = self._parse_single_stock(msg_data)
                if stock_data:
                    results.append(stock_data)
            except ValidationError:
                # 跳過無效的資料，繼續處理其他股票
                continue

        return results

    def _parse_single_stock(self, msg_data: dict) -> TWStockResponse | None:
        """
        解析單一股票資料。

        Args:
            msg_data: 單一股票的原始資料字典

        Returns:
            TWStockResponse | None: 解析後的股票資料，失敗時返回 None

        Raises:
            ValidationError: 必要欄位缺失或格式錯誤時拋出
        """
        try:
            # 檢查是否為字典
            if not isinstance(msg_data, dict):
                raise ValidationError("股票資料格式不正確")

            # 解析基本欄位
            symbol = self._extract_symbol_from_dict(msg_data)
            company_name = self._extract_company_name_from_dict(msg_data)
            current_price = self._extract_price_from_dict(msg_data, "current_price")
            previous_close = self._extract_price_from_dict(msg_data, "previous_close")
            change = (
                current_price - previous_close
                if current_price is not None and previous_close is not None
                else 0.0
            )
            change_percent = self._calculate_change_percent(current_price, change)
            volume = self._extract_volume_from_dict(msg_data)

            # 解析價格欄位
            open_price = self._extract_price_from_dict(msg_data, "open_price")
            high_price = self._extract_price_from_dict(msg_data, "high_price")
            low_price = self._extract_price_from_dict(msg_data, "low_price")
            upper_limit = self._extract_price_from_dict(msg_data, "upper_limit")
            lower_limit = self._extract_price_from_dict(msg_data, "lower_limit")

            # 解析五檔資料
            bid_prices, bid_volumes, ask_prices, ask_volumes = (
                self._parse_bid_ask_data_from_dict(msg_data)
            )

            # 解析時間欄位
            update_time = self._parse_update_time_from_dict(msg_data)
            last_trade_time = self._extract_last_trade_time_from_dict(msg_data)

            return TWStockResponse(
                symbol=symbol,
                company_name=company_name,
                current_price=current_price,
                change=change,
                change_percent=change_percent,
                volume=volume,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                previous_close=previous_close,
                upper_limit=upper_limit,
                lower_limit=lower_limit,
                bid_prices=bid_prices,
                bid_volumes=bid_volumes,
                ask_prices=ask_prices,
                ask_volumes=ask_volumes,
                update_time=update_time,
                last_trade_time=last_trade_time,
            )

        except (KeyError, TypeError) as e:
            raise ValidationError(f"資料欄位存取錯誤: {e}") from e
        except Exception as e:
            raise ValidationError(f"股票資料解析失敗: {e}") from e

    def _extract_symbol_from_dict(self, data: dict) -> str:
        """從字典中提取股票代號。"""
        symbol = data.get(self._field_mapping["symbol"], "")
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("無法提取股票代號")
        return symbol

    def _extract_company_name_from_dict(self, data: dict) -> str:
        """從字典中提取公司名稱。"""
        # 優先使用完整名稱，如果沒有則使用簡稱
        name = data.get(self._field_mapping["full_name"]) or data.get(
            self._field_mapping["name"], ""
        )
        if not isinstance(name, str) or not name:
            raise ValidationError("公司名稱格式不正確")
        return sanitize_company_name(name)

    def _extract_price_from_dict(self, data: dict, price_type: str) -> float:
        """從字典中提取價格欄位。"""
        field_key = self._field_mapping[price_type]
        price_str = data.get(field_key, "0")
        try:
            price = float(price_str) if price_str and price_str != "-" else 0.0
            if not validate_price(price) and price != 0.0:
                raise ValidationError(f"{price_type} 價格無效: {price}")
            return price
        except (ValueError, TypeError) as e:
            raise ValidationError(f"無法解析 {price_type}: {price_str}") from e

    def _calculate_change_percent(self, current_price: float, change: float) -> float:
        """計算漲跌幅百分比。"""
        if current_price == 0 or change == 0:
            return 0.0

        previous_price = current_price - change
        if previous_price == 0:
            return 0.0

        return change / previous_price

    def _extract_volume_from_dict(self, data: dict) -> int:
        """從字典中提取成交量。"""
        volume_str = data.get(self._field_mapping["volume"], "0")
        try:
            volume = int(volume_str) if volume_str and volume_str != "-" else 0
            if not validate_volume(volume):
                raise ValidationError(f"成交量無效: {volume}")
            return volume
        except (ValueError, TypeError) as e:
            raise ValidationError(f"無法解析成交量: {volume_str}") from e

    def _parse_bid_ask_data_from_dict(
        self, data: dict
    ) -> tuple[list[float], list[int], list[float], list[int]]:
        """從字典中解析五檔買賣資料。"""
        try:
            # 解析買盤資料 (bid)
            bid_str = data.get(self._field_mapping["bid_data"], "")
            bid_pairs = parse_price_volume_string(bid_str) if bid_str else []
            bid_prices, bid_volumes = extract_prices_and_volumes(bid_pairs)

            # 解析賣盤資料 (ask)
            ask_str = data.get(self._field_mapping["ask_data"], "")
            ask_pairs = parse_price_volume_string(ask_str) if ask_str else []
            ask_prices, ask_volumes = extract_prices_and_volumes(ask_pairs)

            return bid_prices, bid_volumes, ask_prices, ask_volumes

        except Exception:
            # 五檔資料解析失敗時，返回空清單
            return [], [], [], []

    def _parse_update_time_from_dict(self, data: dict) -> datetime:
        """從字典中解析更新時間。"""
        try:
            # 取得日期和時間
            date_str = data.get(self._field_mapping["update_date"], "")
            time_str = data.get(self._field_mapping["update_time"], "")

            if date_str and time_str:
                # 組合日期和時間: "20231201" + "14:30:00"
                datetime_str = f"{date_str} {time_str}"
                return datetime.strptime(datetime_str, "%Y%m%d %H:%M:%S")
            else:
                # 如果時間格式異常，使用當前時間
                return datetime.now()
        except (ValueError, TypeError):
            return datetime.now()

    def _extract_last_trade_time_from_dict(self, data: dict) -> str:
        """從字典中提取最後交易時間。"""
        time_str = data.get(self._field_mapping["last_trade_time"], "")
        return str(time_str) if time_str else ""


def create_parser() -> TWStockDataParser:
    """
    建立股票資料解析器實例。

    Returns:
        TWStockDataParser: 解析器實例
    """
    return TWStockDataParser()
