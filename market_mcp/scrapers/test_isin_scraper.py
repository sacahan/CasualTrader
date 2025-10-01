#!/usr/bin/env python3
"""
Test script for TWSE ISIN scraper.

This script tests the TWSE ISIN scraper functionality including
data fetching, parsing, and database operations.
"""

import sqlite3
import sys
import traceback
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from market_mcp.scrapers.twse_isin_scraper import TWSeISINScraper
from market_mcp.utils.logging import setup_logging


def test_scraper():
    """Test the TWSE ISIN scraper functionality."""
    print("🚀 Testing TWSE ISIN Scraper")
    print("=" * 50)

    # Setup logging
    setup_logging()

    # Initialize scraper
    scraper = TWSeISINScraper()

    try:
        # Test complete workflow
        print("\n📊 Starting complete scraping workflow...")
        processed_count = scraper.scrape_and_save()
        print(f"✅ Successfully processed {processed_count} securities")

        # Test database queries
        print("\n🔍 Testing database queries...")

        # Test get company by code
        test_codes = ["2330", "1101", "2317"]
        for code in test_codes:
            company = scraper.get_company_by_code(code)
            if company:
                print(f"✅ {code}: {company['company_name']} ({company['industry']})")
            else:
                print(f"❌ {code}: Not found")

        # Test search functionality
        print("\n🔎 Testing search functionality...")
        search_results = scraper.search_companies("台積", limit=5)
        print(f"📋 Search results for '台積' ({len(search_results)} found):")
        for result in search_results:
            print(f"   {result['stock_code']}: {result['company_name']}")

        # Test search by code
        search_results = scraper.search_companies("233", limit=5)
        print(f"📋 Search results for '233' ({len(search_results)} found):")
        for result in search_results:
            print(f"   {result['stock_code']}: {result['company_name']}")

        print("\n🎉 All tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False

    return True


def test_database_stats():
    """Test database statistics."""
    print("\n📈 Database Statistics")
    print("-" * 30)

    scraper = TWSeISINScraper()

    try:
        with sqlite3.connect(scraper.db_path) as conn:
            cursor = conn.cursor()

            # Count total securities
            cursor.execute("SELECT COUNT(*) FROM securities")
            total_count = cursor.fetchone()[0]
            print(f"Total securities: {total_count}")

            # Count by market type
            cursor.execute(
                """
                SELECT market_type, COUNT(*)
                FROM securities
                GROUP BY market_type
                ORDER BY COUNT(*) DESC
            """
            )
            market_stats = cursor.fetchall()
            print("\nBy market type:")
            for market, count in market_stats:
                print(f"  {market}: {count}")

            # Count by industry (top 10)
            cursor.execute(
                """
                SELECT industry, COUNT(*)
                FROM securities
                GROUP BY industry
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """
            )
            industry_stats = cursor.fetchall()
            print("\nTop 10 industries:")
            for industry, count in industry_stats:
                print(f"  {industry}: {count}")

    except Exception as e:
        print(f"❌ Database stats failed: {e}")


if __name__ == "__main__":
    print("🧪 TWSE ISIN Scraper Test Suite")
    print("=" * 60)

    success = test_scraper()

    if success:
        test_database_stats()
        print("\n✅ Test completed successfully!")
        print(f"📁 Database location: {TWSeISINScraper().db_path}")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
