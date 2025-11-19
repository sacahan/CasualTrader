#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script

Migrates data from backend/casualtrader.db (SQLite) to PostgreSQL.

Usage:
    python migrate_sqlite_to_postgres.py

Environment Variables:
    POSTGRES_HOST: PostgreSQL host (default: localhost)
    POSTGRES_PORT: PostgreSQL port (default: 5432)
    POSTGRES_USER: PostgreSQL user (default: cstrader_user)
    POSTGRES_PASSWORD: PostgreSQL password (default: from .env)
    POSTGRES_DB: PostgreSQL database name (default: cstrader)
"""

import os
import sqlite3
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv


# ============================================
# Configuration
# ============================================

# Load environment variables
load_dotenv()

# Source (SQLite)
SQLITE_DB_PATH = Path(__file__).parent.parent / "backend" / "casualtrader.db"

# Target (PostgreSQL)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "sacahan-ubunto")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cstrader_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "2Ts9zM2%")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cstrader")

# Migration configuration
BATCH_SIZE = 100  # Number of rows to insert at once
VERBOSE = True


# ============================================
# Logging Functions
# ============================================


def log_info(msg: str) -> None:
    """Log info message"""
    print(f"[INFO] {datetime.now().strftime('%H:%M:%S')} {msg}")


def log_success(msg: str) -> None:
    """Log success message"""
    print(f"[✓] {datetime.now().strftime('%H:%M:%S')} {msg}")


def log_error(msg: str) -> None:
    """Log error message"""
    print(f"[✗] {datetime.now().strftime('%H:%M:%S')} {msg}", file=sys.stderr)


def log_warning(msg: str) -> None:
    """Log warning message"""
    print(f"[⚠] {datetime.now().strftime('%H:%M:%S')} {msg}")


# ============================================
# Database Connection Functions
# ============================================


def connect_sqlite(db_path: Path) -> sqlite3.Connection:
    """Connect to SQLite database"""
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        log_success(f"Connected to SQLite: {db_path}")
        return conn
    except sqlite3.Error as e:
        log_error(f"Failed to connect to SQLite: {e}")
        raise


def connect_postgres() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB,
        )
        log_success(f"Connected to PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        return conn
    except psycopg2.Error as e:
        log_error(f"Failed to connect to PostgreSQL: {e}")
        raise


# ============================================
# Migration Functions
# ============================================


def get_sqlite_tables(sqlite_conn: sqlite3.Connection) -> list[str]:
    """Get list of tables from SQLite database"""
    cursor = sqlite_conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
    )
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def get_table_schema(sqlite_conn: sqlite3.Connection, table_name: str) -> list[tuple]:
    """Get table schema from SQLite"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    cursor.close()
    return schema


def convert_sqlite_value(value: Any, col_type: str) -> Any:
    """Convert SQLite value to PostgreSQL compatible value"""
    if value is None:
        return None

    # SQLite doesn't have native boolean, so check for 0/1 or True/False
    if col_type.upper() in ("BOOLEAN", "BOOL"):
        if isinstance(value, bool):
            return value
        return bool(int(value)) if isinstance(value, (int, str)) else False

    # Handle numeric/decimal conversion
    if col_type.upper() in ("NUMERIC", "DECIMAL"):
        if isinstance(value, str):
            return Decimal(value)
        return Decimal(str(value))

    # Handle JSON fields - keep as is (SQLite stores as TEXT)
    if col_type.upper() == "JSON":
        return value

    return value


def migrate_table(
    sqlite_conn: sqlite3.Connection,
    postgres_conn: psycopg2.extensions.connection,
    table_name: str,
) -> int:
    """Migrate a single table from SQLite to PostgreSQL"""
    log_info(f"Migrating table: {table_name}")

    try:
        # Get schema info
        schema = get_table_schema(sqlite_conn, table_name)
        if not schema:
            log_warning(f"Table {table_name} has no columns, skipping...")
            return 0

        # Get column info
        columns = [(col[1], col[2]) for col in schema]  # (name, type)
        column_names = [col[0] for col in columns]

        # Get data from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        sqlite_cursor.close()

        if not rows:
            log_info(f"  Table {table_name} is empty, no rows to migrate")
            return 0

        # Insert into PostgreSQL
        postgres_cursor = postgres_conn.cursor()
        inserted_count = 0

        for batch_start in range(0, len(rows), BATCH_SIZE):
            batch = rows[batch_start : batch_start + BATCH_SIZE]

            # Convert values for batch
            values_list = []
            for row in batch:
                row_dict = dict(row)
                converted_values = []
                for col_name, col_type in columns:
                    value = row_dict.get(col_name)
                    converted_value = convert_sqlite_value(value, col_type)
                    converted_values.append(converted_value)
                values_list.append(tuple(converted_values))

            # Build INSERT statement
            placeholders = ", ".join(["%s"] * len(column_names))
            columns_str = ", ".join([f'"{col}"' for col in column_names])
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

            try:
                psycopg2.extras.execute_batch(
                    postgres_cursor, insert_sql, values_list, page_size=BATCH_SIZE
                )
                postgres_conn.commit()
                inserted_count += len(batch)

                if VERBOSE:
                    log_info(
                        f"  Inserted batch {batch_start // BATCH_SIZE + 1}, "
                        f"total: {inserted_count}/{len(rows)}"
                    )
            except psycopg2.Error as e:
                postgres_conn.rollback()
                log_error(f"Error inserting batch into {table_name}: {e}")
                raise

        postgres_cursor.close()
        log_success(f"Table {table_name}: {inserted_count} rows migrated")
        return inserted_count

    except Exception as e:
        log_error(f"Error migrating table {table_name}: {e}")
        raise


def clear_postgres_tables(postgres_conn: psycopg2.extensions.connection) -> None:
    """Clear all data from PostgreSQL tables (keeping schema)"""
    try:
        cursor = postgres_conn.cursor()

        # Get all tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_type='BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        # Disable triggers and constraints
        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")

        # Delete all data
        for table in tables:
            log_info(f"Clearing PostgreSQL table: {table}")
            cursor.execute(f'DELETE FROM "{table}"')

        postgres_conn.commit()
        log_success(f"Cleared {len(tables)} PostgreSQL tables")
        cursor.close()

    except psycopg2.Error as e:
        postgres_conn.rollback()
        log_error(f"Error clearing PostgreSQL tables: {e}")
        raise


# ============================================
# Main Migration Function
# ============================================


def main() -> None:
    """Main migration function"""
    print("\n" + "=" * 60)
    print("SQLite to PostgreSQL Migration")
    print("=" * 60)
    print(f"Source:      {SQLITE_DB_PATH}")
    print(
        f"Target:      postgresql://{POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    print("=" * 60 + "\n")

    # Check source database exists
    if not SQLITE_DB_PATH.exists():
        log_error(f"SQLite database not found: {SQLITE_DB_PATH}")
        sys.exit(1)

    try:
        # Connect to databases
        sqlite_conn = connect_sqlite(SQLITE_DB_PATH)
        postgres_conn = connect_postgres()

        # Get tables from SQLite
        tables = get_sqlite_tables(sqlite_conn)

        if not tables:
            log_warning("No tables found in SQLite database")
            sqlite_conn.close()
            postgres_conn.close()
            return

        # Sort tables by dependency (parents first)
        # ai_model_configs and agents are independent
        # agent_sessions, agent_holdings, agent_performance depend on agents
        # transactions depend on agents and agent_sessions
        dependency_order = [
            "ai_model_configs",  # Independent
            "agents",  # Independent
            "agent_sessions",  # Depends on agents
            "agent_holdings",  # Depends on agents
            "agent_performance",  # Depends on agents
            "transactions",  # Depends on agents and agent_sessions
        ]

        # Sort tables based on dependency order, keeping any unknown tables at the end
        tables_sorted = []
        for table in dependency_order:
            if table in tables:
                tables_sorted.append(table)
        for table in tables:
            if table not in tables_sorted:
                tables_sorted.append(table)
        tables = tables_sorted

        print(f"\nFound {len(tables)} tables to migrate: {', '.join(tables)}\n")

        # Ask for confirmation
        response = input("Clear existing PostgreSQL data and proceed with migration? (yes/no): ")
        if response.lower() not in ("yes", "y"):
            log_info("Migration cancelled by user")
            sqlite_conn.close()
            postgres_conn.close()
            return

        # Clear existing data
        print()
        clear_postgres_tables(postgres_conn)

        # Migrate each table
        print()
        total_rows = 0
        for table_name in tables:
            rows = migrate_table(sqlite_conn, postgres_conn, table_name)
            total_rows += rows

        # Final commit
        postgres_conn.commit()

        print("\n" + "=" * 60)
        log_success(f"Migration completed! Total rows: {total_rows}")
        print("=" * 60 + "\n")

        # Close connections
        sqlite_conn.close()
        postgres_conn.close()

    except Exception as e:
        log_error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
