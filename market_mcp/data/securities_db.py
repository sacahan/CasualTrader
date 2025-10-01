"""
證券資料庫查詢模組。

提供對 TWSE 證券資料庫的查詢功能，支援按股票代碼和公司名稱查詢。
"""

import sqlite3
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class SecurityRecord:
    """證券記錄資料類別。"""

    stock_code: str
    company_name: str
    isin_code: str
    listing_date: Optional[str] = None
    market_type: Optional[str] = None
    industry: Optional[str] = None
    cfi_code: Optional[str] = None
    security_type: str = "stock"


class SecuritiesDatabase:
    """證券資料庫查詢類別。"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化證券資料庫連接。

        Args:
            db_path: 資料庫檔案路徑，如果為 None 則使用預設路徑
        """
        if db_path is None:
            # 預設路徑相對於這個檔案的位置
            current_dir = Path(__file__).parent
            self.db_path = current_dir / "twse_securities.db"
        else:
            self.db_path = Path(db_path)

        self._validate_database()

    def _validate_database(self) -> None:
        """驗證資料庫檔案是否存在且可訪問。"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"證券資料庫檔案不存在: {self.db_path}")

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='securities'"
                )
                if not cursor.fetchone():
                    raise ValueError("資料庫中缺少 securities 表格")
        except sqlite3.Error as e:
            raise ValueError(f"資料庫檔案無效: {e}")

    def find_by_stock_code(self, stock_code: str) -> Optional[SecurityRecord]:
        """
        根據股票代碼查詢證券記錄。

        Args:
            stock_code: 股票代碼

        Returns:
            SecurityRecord 物件，如果找不到則返回 None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # 使結果可以按列名訪問
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM securities WHERE stock_code = ? LIMIT 1",
                    (stock_code.upper(),),
                )

                row = cursor.fetchone()
                if row:
                    return SecurityRecord(
                        stock_code=row["stock_code"],
                        company_name=row["company_name"],
                        isin_code=row["isin_code"],
                        listing_date=row["listing_date"],
                        market_type=row["market_type"],
                        industry=row["industry"],
                        cfi_code=row["cfi_code"],
                        security_type=row["security_type"] or "stock",
                    )
                return None

        except sqlite3.Error as e:
            raise ValueError(f"資料庫查詢錯誤: {e}")

    def find_by_company_name(
        self, company_name: str, exact_match: bool = False
    ) -> List[SecurityRecord]:
        """
        根據公司名稱查詢證券記錄。

        Args:
            company_name: 公司名稱
            exact_match: 是否精確匹配，否則使用模糊匹配

        Returns:
            SecurityRecord 物件列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if exact_match:
                    cursor.execute(
                        "SELECT * FROM securities WHERE company_name = ?",
                        (company_name,),
                    )
                else:
                    # 模糊匹配，支援部分名稱搜尋
                    cursor.execute(
                        "SELECT * FROM securities WHERE company_name LIKE ? ORDER BY company_name",
                        (f"%{company_name}%",),
                    )

                rows = cursor.fetchall()
                results = []

                for row in rows:
                    results.append(
                        SecurityRecord(
                            stock_code=row["stock_code"],
                            company_name=row["company_name"],
                            isin_code=row["isin_code"],
                            listing_date=row["listing_date"],
                            market_type=row["market_type"],
                            industry=row["industry"],
                            cfi_code=row["cfi_code"],
                            security_type=row["security_type"] or "stock",
                        )
                    )

                return results

        except sqlite3.Error as e:
            raise ValueError(f"資料庫查詢錯誤: {e}")

    def search_securities(self, query: str) -> List[SecurityRecord]:
        """
        智能搜尋證券，支援股票代碼和公司名稱。

        Args:
            query: 搜尋查詢字串

        Returns:
            SecurityRecord 物件列表，按相關度排序
        """
        query = query.strip()

        # 首先檢查是否為股票代碼格式
        if self._is_stock_code_format(query):
            # 嘗試精確匹配股票代碼
            result = self.find_by_stock_code(query)
            return [result] if result else []

        # 否則按公司名稱搜尋
        results = self.find_by_company_name(query, exact_match=False)

        # 如果模糊搜尋沒有結果，嘗試更寬鬆的搜尋
        if not results:
            # 移除常見的公司形式詞彙後再搜尋
            cleaned_query = self._clean_company_name(query)
            if cleaned_query != query:
                results = self.find_by_company_name(cleaned_query, exact_match=False)

        return results

    def _is_stock_code_format(self, query: str) -> bool:
        """
        檢查查詢字串是否像股票代碼。

        Args:
            query: 查詢字串

        Returns:
            True 如果看起來像股票代碼
        """
        # 移除空白
        query = query.strip()

        # 檢查是否符合股票代碼格式：4-6位數字 + 可選字母
        return bool(re.match(r"^[0-9]{4,6}[A-Z]*$", query.upper()))

    def _clean_company_name(self, name: str) -> str:
        """
        清理公司名稱，移除常見的公司形式詞彙。

        Args:
            name: 原始公司名稱

        Returns:
            清理後的公司名稱
        """
        # 常見的公司形式詞彙
        company_suffixes = [
            "股份有限公司",
            "有限公司",
            "公司",
            "股份",
            "Ltd",
            "Inc",
            "Corp",
            "Co.",
            "Ltd.",
            "Inc.",
            "Corp.",
        ]

        cleaned_name = name
        for suffix in company_suffixes:
            if cleaned_name.endswith(suffix):
                cleaned_name = cleaned_name[: -len(suffix)]

        return cleaned_name.strip()

    def get_all_stock_codes(self) -> List[str]:
        """
        取得所有股票代碼列表。

        Returns:
            股票代碼列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT stock_code FROM securities ORDER BY stock_code"
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise ValueError(f"資料庫查詢錯誤: {e}")

    def get_database_info(self) -> Dict[str, Any]:
        """
        取得資料庫基本資訊。

        Returns:
            包含資料庫統計資訊的字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 總記錄數
                cursor.execute("SELECT COUNT(*) FROM securities")
                total_count = cursor.fetchone()[0]

                # 股票代碼長度分佈
                cursor.execute(
                    """
                    SELECT LENGTH(stock_code) as len, COUNT(*) as count
                    FROM securities
                    GROUP BY LENGTH(stock_code)
                    ORDER BY len
                """
                )
                length_distribution = dict(cursor.fetchall())

                # 包含字母的代碼數量
                cursor.execute(
                    "SELECT COUNT(*) FROM securities WHERE stock_code GLOB '*[A-Z]*'"
                )
                codes_with_letters = cursor.fetchone()[0]

                # 最新更新時間
                cursor.execute("SELECT MAX(updated_at) FROM securities")
                last_updated = cursor.fetchone()[0]

                return {
                    "total_securities": total_count,
                    "length_distribution": length_distribution,
                    "codes_with_letters": codes_with_letters,
                    "last_updated": last_updated,
                    "database_path": str(self.db_path),
                }

        except sqlite3.Error as e:
            raise ValueError(f"資料庫查詢錯誤: {e}")


# 建立全域資料庫實例
try:
    db = SecuritiesDatabase()
except (FileNotFoundError, ValueError):
    # 如果資料庫不可用，設為 None
    db = None


def get_securities_database() -> Optional[SecuritiesDatabase]:
    """
    取得證券資料庫實例。

    Returns:
        SecuritiesDatabase 實例，如果資料庫不可用則返回 None
    """
    return db


def resolve_stock_symbol(query: str) -> Optional[str]:
    """
    解析股票查詢為標準股票代碼。

    這是一個便利函數，支援股票代碼和公司名稱查詢。

    Args:
        query: 股票代碼或公司名稱

    Returns:
        標準化的股票代碼，如果找不到則返回 None
    """
    securities_db = get_securities_database()
    if not securities_db:
        # 如果資料庫不可用，假設輸入就是股票代碼
        return query.strip().upper() if query.strip() else None

    try:
        results = securities_db.search_securities(query)

        if results:
            # 返回第一個匹配結果的股票代碼
            return results[0].stock_code

        return None

    except Exception:
        # 如果查詢失敗，回退到原始查詢
        return query.strip().upper() if query.strip() else None
