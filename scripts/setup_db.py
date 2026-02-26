#!/usr/bin/env python3
"""
Setup script: initializes the database schema.
Run once before first use or after schema changes.

Usage:
    python scripts/setup_db.py
    python scripts/setup_db.py --check    # just check DB health
"""
import argparse
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def setup_database(db_url: str, check_only: bool = False):
    from src.storage.database import init_db, health_check, get_table_counts

    print(f"Database URL: {db_url}")

    if check_only:
        init_db(db_url)
        ok = health_check()
        if ok:
            counts = get_table_counts()
            print("[OK] Database is healthy")
            for table, count in counts.items():
                print(f"  {table}: {count:,} rows")
        else:
            print("[ERR] Database health check failed")
            sys.exit(1)
        return

    print("Initializing database schema...")
    init_db(db_url)
    print("[OK] Database schema created/verified")

    # Verify
    ok = health_check()
    if ok:
        counts = get_table_counts()
        print("[OK] Database is healthy")
        for table, count in counts.items():
            print(f"  {table}: {count:,} rows")
    else:
        print("[ERR] Post-init health check failed")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Setup the cannabis aggregator database")
    parser.add_argument("--db-url", default=None,
                        help="Database URL (defaults to DATABASE_URL env var)")
    parser.add_argument("--check", action="store_true",
                        help="Only check database health, don't create schema")
    args = parser.parse_args()

    db_url = args.db_url or os.environ.get(
        "DATABASE_URL", "sqlite:///data/cannabis_aggregator.db"
    )

    # Ensure data directory exists for SQLite
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    setup_database(db_url, check_only=args.check)


if __name__ == "__main__":
    main()
