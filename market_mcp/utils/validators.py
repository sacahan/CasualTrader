"""
輸入驗證工具模組。

提供各種資料驗證功能，確保 API 請求參數和回應資料的正確性。
"""

import re


def validate_taiwan_stock_symbol(symbol: str) -> bool:
    """
    驗證台灣股票代號格式。

    Args:
        symbol: 股票代號字串

    Returns:
        bool: 驗證結果，True 表示格式正確

    Examples:
        >>> validate_taiwan_stock_symbol("2330")
        True
        >>> validate_taiwan_stock_symbol("123")
        False
        >>> validate_taiwan_stock_symbol("abcd")
        False
    """
    if not isinstance(symbol, str):
        return False

    # 台灣股票代號必須是 4 位數字
    return bool(re.match(r"^\d{4}$", symbol))


def determine_market_type(symbol: str) -> str:
    """
    根據股票代號自動判斷市場類型。

    Args:
        symbol: 股票代號

    Returns:
        str: 市場類型 ("tse" 或 "otc")

    Examples:
        >>> determine_market_type("2330")  # 台積電
        'tse'
        >>> determine_market_type("3008")  # 大立光
        'tse'
        >>> determine_market_type("4938")  # 和碩
        'otc'
    """
    if not validate_taiwan_stock_symbol(symbol):
        raise ValueError(f"無效的股票代號: {symbol}")

    symbol_int = int(symbol)

    # 上市股票 (TSE) 代號範圍參考
    # 1000-1999: 水泥工業
    # 2000-2999: 食品工業, 塑膠工業, 紡織纖維, 電機機械, 電器電纜, 化學生技醫療, 玻璃陶瓷, 造紙工業, 鋼鐵工業, 橡膠工業, 汽車工業, 半導體業, 電腦及週邊設備業, 光電業, 通信網路業, 電子零組件業, 電子通路業, 資訊服務業, 其他電子業
    # 3000-3999: 建材營造, 航運業, 觀光事業, 金融保險, 貿易百貨業
    # 4000-4999: 其他
    # 5000-5999: 綠能環保
    # 6000-6999: 文化創意業
    # 8000-8999: 存託憑證
    # 9000-9999: 其他

    # 一般來說，較小的代號通常是上市股票
    # 但實際分類可能需要更精確的資料
    # 這裡採用簡化的規則
    if symbol_int <= 6999:
        return "tse"
    else:
        return "otc"


def validate_price(price: float) -> bool:
    """
    驗證股價是否合理。

    Args:
        price: 股價

    Returns:
        bool: 驗證結果
    """
    if not isinstance(price, (int, float)):
        return False

    # 股價必須為正數且在合理範圍內
    return 0.01 <= price <= 999999.99


def validate_volume(volume: int) -> bool:
    """
    驗證成交量是否合理。

    Args:
        volume: 成交量

    Returns:
        bool: 驗證結果
    """
    if not isinstance(volume, int):
        return False

    # 成交量必須為非負整數
    return volume >= 0


def parse_price_volume_string(price_volume_str: str) -> list[tuple[float, int]]:
    """
    解析證交所五檔價量字串。

    證交所 API 回傳的五檔資料格式為 "價格_成交量_價格_成交量_..."

    Args:
        price_volume_str: 價量字串，例如 "245.50_1000_245.00_500_244.50_300_"

    Returns:
        list[Tuple[float, int]]: 解析後的 (價格, 成交量) 配對清單

    Examples:
        >>> parse_price_volume_string("245.50_1000_245.00_500_")
        [(245.50, 1000), (245.00, 500)]
    """
    if not price_volume_str or price_volume_str == "_":
        return []

    # 移除開頭和結尾的下劃線，然後分割
    parts = price_volume_str.strip("_").split("_")

    result = []
    # 每兩個元素成對：價格、成交量
    for i in range(0, len(parts), 2):
        if i + 1 < len(parts):
            try:
                price = float(parts[i])
                volume = int(parts[i + 1])

                # 驗證解析結果
                if validate_price(price) and validate_volume(volume):
                    result.append((price, volume))
            except (ValueError, TypeError):
                # 跳過無效的價量資料
                continue

    return result


def extract_prices_and_volumes(
    price_volume_pairs: list[tuple[float, int]],
) -> tuple[list[float], list[int]]:
    """
    從價量配對清單中分離出價格和成交量清單。

    Args:
        price_volume_pairs: 價量配對清單

    Returns:
        Tuple[list[float], list[int]]: (價格清單, 成交量清單)
    """
    if not price_volume_pairs:
        return [], []

    prices, volumes = zip(*price_volume_pairs, strict=True)
    return list(prices), list(volumes)


def sanitize_company_name(name: str) -> str:
    """
    清理公司名稱，移除不必要的字符和空白。

    Args:
        name: 原始公司名稱

    Returns:
        str: 清理後的公司名稱
    """
    if not isinstance(name, str):
        return ""

    # 移除前後空白
    cleaned = name.strip()

    # 移除多餘的空白字符
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    格式化百分比顯示。

    Args:
        value: 百分比數值
        decimal_places: 小數位數

    Returns:
        str: 格式化後的百分比字串

    Examples:
        >>> format_percentage(0.0523, 2)
        '5.23%'
        >>> format_percentage(-0.0234, 2)
        '-2.34%'
    """
    return f"{value * 100:.{decimal_places}f}%"
