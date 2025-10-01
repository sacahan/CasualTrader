"""
TWSE ISIN scraper for fetching Taiwan securities ISIN codes and company information.

This module provides functionality to scrape the Taiwan Stock Exchange's
ISIN code listing page and extract stock information.
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from ..utils.logging import get_logger


class TWSeISINScraper:
    """
    Scraper for TWSE ISIN listings.

    Fetches and parses Taiwan Stock Exchange ISIN code listings
    from https://isin.twse.com.tw/isin/C_public.jsp?strMode=2
    """

    TWSE_ISIN_URL = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the TWSE ISIN scraper.

        Args:
            db_path: Path to SQLite database file. If None, uses default path.
        """
        self.logger = get_logger(__name__)
        self.db_path = db_path or self._get_default_db_path()
        self.session = requests.Session()

        # Set headers to mimic a browser
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )

    def _get_default_db_path(self) -> str:
        """Get default database path."""
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "twse_securities.db")

    def fetch_isin_data(self) -> str:
        """
        Fetch ISIN data from TWSE website.

        Returns:
            Raw HTML content from the TWSE ISIN page

        Raises:
            requests.RequestException: If request fails
        """
        self.logger.info(f"Fetching ISIN data from {self.TWSE_ISIN_URL}")

        try:
            response = self.session.get(self.TWSE_ISIN_URL, timeout=30)
            response.raise_for_status()

            # The content is in Big5 encoding
            response.encoding = "big5"

            self.logger.info(
                f"Successfully fetched ISIN data ({len(response.text)} characters)"
            )
            return response.text

        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch ISIN data: {e}")
            raise

    def parse_isin_data(self, html_content: str) -> List[Dict[str, str]]:
        """
        Parse ISIN data from HTML content.

        Args:
            html_content: Raw HTML content from TWSE ISIN page

        Returns:
            List of dictionaries containing stock information
        """
        self.logger.info("Parsing ISIN data from HTML content")

        soup = BeautifulSoup(html_content, "html.parser")

        # Find the main table
        tables = soup.find_all("table")
        data_table = None

        for table in tables:
            if table.get("class") == ["h4"]:
                data_table = table
                break

        if not data_table:
            self.logger.error("Could not find data table in HTML content")
            return []

        securities = []
        rows = data_table.find_all("tr")

        for row in rows[1:]:  # Skip header row
            cells = row.find_all("td")

            if len(cells) < 6:
                continue

            # Skip category header rows
            if cells[0].get("colspan"):
                continue

            try:
                # Extract stock code and company name from first cell
                first_cell_text = cells[0].get_text(strip=True)

                # Use regex to separate stock code and company name
                match = re.match(r"(\d{4})\s*(.+)", first_cell_text)
                if not match:
                    continue

                stock_code = match.group(1)
                company_name = match.group(2)

                # Extract other fields
                isin_code = cells[1].get_text(strip=True)
                listing_date = cells[2].get_text(strip=True)
                market_type = cells[3].get_text(strip=True)
                industry = cells[4].get_text(strip=True)
                cfi_code = cells[5].get_text(strip=True)

                security_info = {
                    "stock_code": stock_code,
                    "company_name": company_name,
                    "isin_code": isin_code,
                    "listing_date": listing_date,
                    "market_type": market_type,
                    "industry": industry,
                    "cfi_code": cfi_code,
                    "scraped_at": datetime.now().isoformat(),
                }

                securities.append(security_info)

            except Exception as e:
                self.logger.warning(f"Failed to parse row: {e}")
                continue

        self.logger.info(f"Successfully parsed {len(securities)} securities")
        return securities

    def init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        self.logger.info(f"Initializing database at {self.db_path}")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create securities table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS securities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    isin_code TEXT UNIQUE NOT NULL,
                    listing_date TEXT,
                    market_type TEXT,
                    industry TEXT,
                    cfi_code TEXT,
                    scraped_at TEXT NOT NULL,
                    updated_at TEXT,
                    UNIQUE(stock_code, isin_code)
                )
            """
            )

            # Create index for faster lookups
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stock_code
                ON securities(stock_code)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_isin_code
                ON securities(isin_code)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_company_name
                ON securities(company_name)
            """
            )

            conn.commit()

        self.logger.info("Database initialization completed")

    def save_to_database(self, securities: List[Dict[str, str]]) -> int:
        """
        Save securities data to SQLite database.

        Args:
            securities: List of security dictionaries

        Returns:
            Number of records inserted/updated
        """
        if not securities:
            self.logger.warning("No securities data to save")
            return 0

        self.logger.info(f"Saving {len(securities)} securities to database")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            inserted_count = 0
            updated_count = 0

            for security in securities:
                try:
                    # Try to insert new record
                    cursor.execute(
                        """
                        INSERT INTO securities (
                            stock_code, company_name, isin_code, listing_date,
                            market_type, industry, cfi_code, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            security["stock_code"],
                            security["company_name"],
                            security["isin_code"],
                            security["listing_date"],
                            security["market_type"],
                            security["industry"],
                            security["cfi_code"],
                            security["scraped_at"],
                        ),
                    )
                    inserted_count += 1

                except sqlite3.IntegrityError:
                    # Record exists, update it
                    cursor.execute(
                        """
                        UPDATE securities SET
                            company_name = ?,
                            listing_date = ?,
                            market_type = ?,
                            industry = ?,
                            cfi_code = ?,
                            updated_at = ?
                        WHERE stock_code = ? OR isin_code = ?
                    """,
                        (
                            security["company_name"],
                            security["listing_date"],
                            security["market_type"],
                            security["industry"],
                            security["cfi_code"],
                            datetime.now().isoformat(),
                            security["stock_code"],
                            security["isin_code"],
                        ),
                    )
                    updated_count += 1

            conn.commit()

        total_processed = inserted_count + updated_count
        self.logger.info(
            f"Database save completed: {inserted_count} inserted, {updated_count} updated"
        )
        return total_processed

    def get_company_by_code(self, stock_code: str) -> Optional[Dict[str, str]]:
        """
        Get company information by stock code.

        Args:
            stock_code: 4-digit stock code

        Returns:
            Dictionary with company information or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT stock_code, company_name, isin_code, listing_date,
                       market_type, industry, cfi_code
                FROM securities
                WHERE stock_code = ?
            """,
                (stock_code,),
            )

            row = cursor.fetchone()
            if row:
                return {
                    "stock_code": row[0],
                    "company_name": row[1],
                    "isin_code": row[2],
                    "listing_date": row[3],
                    "market_type": row[4],
                    "industry": row[5],
                    "cfi_code": row[6],
                }

        return None

    def search_companies(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Search companies by name or stock code.

        Args:
            query: Search query (company name or stock code)
            limit: Maximum number of results

        Returns:
            List of matching companies
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT stock_code, company_name, isin_code, listing_date,
                       market_type, industry, cfi_code
                FROM securities
                WHERE stock_code LIKE ? OR company_name LIKE ?
                ORDER BY stock_code
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            )

            rows = cursor.fetchall()
            return [
                {
                    "stock_code": row[0],
                    "company_name": row[1],
                    "isin_code": row[2],
                    "listing_date": row[3],
                    "market_type": row[4],
                    "industry": row[5],
                    "cfi_code": row[6],
                }
                for row in rows
            ]

    def scrape_and_save(self) -> int:
        """
        Complete scraping workflow: fetch, parse, and save data.

        Returns:
            Number of records processed
        """
        self.logger.info("Starting TWSE ISIN scraping workflow")

        try:
            # Initialize database
            self.init_database()

            # Fetch data
            html_content = self.fetch_isin_data()

            # Parse data
            securities = self.parse_isin_data(html_content)

            # Save to database
            processed_count = self.save_to_database(securities)

            self.logger.info(
                f"TWSE ISIN scraping completed successfully: {processed_count} records processed"
            )
            return processed_count

        except Exception as e:
            self.logger.error(f"TWSE ISIN scraping failed: {e}")
            raise
