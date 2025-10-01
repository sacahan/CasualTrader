#!/usr/bin/env python3
"""
Analyze TWSE ISIN page structure to understand ETF organization.
"""

import re
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from market_mcp.scrapers.twse_isin_scraper import TWSeISINScraper
from market_mcp.utils.logging import setup_logging


def analyze_twse_structure():
    """Analyze the TWSE page structure."""
    print("🔍 Analyzing TWSE ISIN page structure")
    print("=" * 50)

    setup_logging()
    scraper = TWSeISINScraper()

    # Fetch raw HTML
    html_content = scraper.fetch_isin_data()

    # Look for section headers
    print("\n📝 Looking for section headers...")
    section_pattern = r"<td[^>]*colspan[^>]*>([^<]*)</td>"
    sections = re.findall(section_pattern, html_content)

    print(f"Found {len(sections)} section headers:")
    for i, section in enumerate(sections[:20]):  # Show first 20
        cleaned = section.strip()
        if cleaned:
            print(f"  {i+1}: {cleaned}")

    # Look for ETF-like entries
    print("\n🎯 Looking for potential ETF entries...")

    # Search for entries with codes that might be ETFs
    etf_patterns = [
        r"(00\d{2})[^\d]",  # Codes starting with 00xx
        r"(\d{4}).*ETF",  # Any code with ETF in name
        r"(\d{4}).*指數",  # Any code with "指數" (index)
        r"(\d{4}).*基金",  # Any code with "基金" (fund)
    ]

    for pattern_name, pattern in [
        ("00xx codes", etf_patterns[0]),
        ("ETF names", etf_patterns[1]),
        ("Index names", etf_patterns[2]),
        ("Fund names", etf_patterns[3]),
    ]:
        matches = re.findall(pattern, html_content)
        print(f"  {pattern_name}: {len(matches)} matches")
        if matches:
            print(f"    Examples: {matches[:5]}")

    # Analyze table structure more carefully
    print("\n📊 Analyzing table structure...")
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")

    for i, table in enumerate(tables):
        if table.get("class") == ["h4"]:
            print(f"Found main data table (table {i})")
            rows = table.find_all("tr")

            print(f"Total rows: {len(rows)}")

            # Analyze first few data rows and look for ETFs
            print("\nFirst 10 data rows:")
            for j, row in enumerate(rows[1:11]):  # Skip header
                cells = row.find_all("td")
                if len(cells) >= 6:
                    first_cell = cells[0].get_text(strip=True)
                    cfi_code = (
                        cells[5].get_text(strip=True) if len(cells) > 5 else "N/A"
                    )

                    # Check if it looks like ETF
                    is_etf_like = (
                        first_cell.startswith("00")
                        or "ETF" in first_cell
                        or "指數" in first_cell
                        or "基金" in first_cell
                    )

                    print(
                        f"  Row {j+1}: {first_cell[:30]:<30} CFI: {cfi_code:<10} ETF-like: {is_etf_like}"
                    )

            # Look specifically for 00xx codes (likely ETFs)
            print("\n🎯 Looking for 00xx codes (potential ETFs):")
            etf_count = 0
            for j, row in enumerate(rows[1:]):
                cells = row.find_all("td")
                if len(cells) >= 6:
                    first_cell = cells[0].get_text(strip=True)
                    if re.match(r"00\d{2}", first_cell):
                        etf_count += 1
                        if etf_count <= 10:  # Show first 10 ETFs
                            all_cells = [cell.get_text(strip=True) for cell in cells]
                            print(f"  ETF {etf_count}: {' | '.join(all_cells[:6])}")

            print(f"\nTotal 00xx entries found: {etf_count}")

            break

    print("\n✅ Analysis completed!")


if __name__ == "__main__":
    analyze_twse_structure()
