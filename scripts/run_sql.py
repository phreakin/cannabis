#!/usr/bin/env python3
"""
Run a SQL file against the configured database.

Usage:
    python scripts/run_sql.py scripts/sql/seed_bookmark_categories.sql
    python scripts/run_sql.py scripts/sql/seed_bookmark_categories.sql --db-url mysql+pymysql://user:pass@host/dbname
    python scripts/run_sql.py scripts/sql/seed_bookmark_categories.sql --database mysite_db

Options:
    --db-url      Full SQLAlchemy database URL (overrides .env DATABASE_URL)
    --database    Override only the database name (uses host/user/pass from .env)
    --dry-run     Print statements without executing
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=False)


def split_statements(sql: str) -> list[str]:
    """Split SQL into individual statements (handles multi-line)."""
    statements = []
    buf = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith('--') or stripped == '':
            continue
        buf.append(line)
        if stripped.endswith(';'):
            stmt = '\n'.join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
    if buf:
        stmt = '\n'.join(buf).strip()
        if stmt:
            statements.append(stmt)
    return statements


def build_db_url(args) -> str:
    base = args.db_url or os.environ.get("DATABASE_URL", "sqlite:///data/cannabis_aggregator.db")

    if args.database and base.startswith("mysql"):
        # Replace the database name portion: scheme://user:pass@host:port/DBNAME
        parts = base.rsplit('/', 1)
        if len(parts) == 2:
            base = parts[0] + '/' + args.database

    return base


def main():
    parser = argparse.ArgumentParser(description="Run a SQL file against the database")
    parser.add_argument("sql_file", help="Path to the .sql file to execute")
    parser.add_argument("--db-url",  default=None, help="Full DB URL (overrides .env)")
    parser.add_argument("--database", default=None, help="Override database name only")
    parser.add_argument("--dry-run", action="store_true", help="Print statements, don't execute")
    args = parser.parse_args()

    sql_path = os.path.abspath(args.sql_file)
    if not os.path.exists(sql_path):
        print(f"[ERR] File not found: {sql_path}")
        sys.exit(1)

    with open(sql_path, encoding="utf-8") as f:
        sql_text = f.read()

    statements = split_statements(sql_text)
    print(f"SQL file: {sql_path}")
    print(f"Statements found: {len(statements)}")

    db_url = build_db_url(args)
    print(f"Database: {db_url.split('@')[-1] if '@' in db_url else db_url}")  # hide credentials

    if args.dry_run:
        print("\n[DRY RUN — no changes will be made]\n")
        for i, stmt in enumerate(statements, 1):
            print(f"-- Statement {i} --")
            print(stmt[:200] + ('...' if len(stmt) > 200 else ''))
            print()
        return

    # Execute
    from sqlalchemy import create_engine, text

    # For MySQL: disable autocommit so we can commit at the end
    engine = create_engine(db_url, echo=False)

    success = 0
    errors  = 0
    with engine.begin() as conn:
        for i, stmt in enumerate(statements, 1):
            try:
                result = conn.execute(text(stmt))
                rows = result.rowcount if result.rowcount >= 0 else 0
                print(f"  [OK] Statement {i}: {rows} row(s) affected")
                success += 1
            except Exception as e:
                print(f"  [ERR] Statement {i} FAILED: {e}")
                print(f"    SQL: {stmt[:120]}...")
                errors += 1

    print(f"\n{'='*50}")
    print(f"Done: {success} succeeded, {errors} failed")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
