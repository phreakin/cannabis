#!/usr/bin/env python3
"""
CLI script to manually run data collection for one or more sources.

Usage:
    python scripts/run_collector.py --source co_med_licensees
    python scripts/run_collector.py --source co_med_licensees wa_wslcb_licensees
    python scripts/run_collector.py --all
    python scripts/run_collector.py --all --state CO
    python scripts/run_collector.py --all --category dispensary
    python scripts/run_collector.py --list         # list all enabled sources
"""
import argparse
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
# Always load .env from the project root (parent of scripts/), regardless of CWD.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=False)


def list_sources(state=None, category=None, enabled_only=True):
    from src.storage.database import session_scope
    from src.storage.models import DataSource

    with session_scope() as session:
        q = session.query(DataSource)
        if enabled_only:
            q = q.filter(DataSource.enabled == True)
        if state:
            q = q.filter(DataSource.state == state.upper())
        if category:
            q = q.filter(DataSource.category.ilike(f"%{category}%"))
        sources = q.order_by(DataSource.state, DataSource.name).all()
        return [s.to_dict() for s in sources]


def run_source(source_id_str: str, dry_run: bool = False):
    """Run collection for a single source by source_id string."""
    from src.storage.database import session_scope
    from src.storage.models import DataSource
    from src.scheduler.manager import run_collection_job

    with session_scope() as session:
        source = session.query(DataSource).filter_by(source_id=source_id_str).first()
        if not source:
            print(f"  [ERR] Source not found: {source_id_str}")
            return None
        source_dict = source.to_dict()

    print(f"\n{'='*60}")
    print(f"Source: {source_dict['name']} ({source_id_str})")
    print(f"State:    {source_dict['state']} | Category: {source_dict['category']}")
    print(f"Format:   {source_dict['format']} | URL: {source_dict['url'][:80]}")
    print(f"{'='*60}")

    if dry_run:
        print("[DRY RUN] Skipping actual collection.")
        return {"status": "dry_run", "source_id": source_id_str}

    start = time.time()
    try:
        result = run_collection_job(
            source_db_id=source_dict["id"],
            triggered_by="cli",
        )
        elapsed = time.time() - start
        status = result.get("status", "unknown")
        icon = "[OK]" if status == "success" else "[FAIL]" if status == "failed" else "[WARN]"
        print(f"\n{icon} Status: {status.upper()} ({elapsed:.1f}s)")
        print(f"  Fetched: {result.get('records_fetched', 0):,}")
        print(f"  Stored:  {result.get('records_stored', 0):,}")
        if result.get("error"):
            print(f"  Error: {result['error']}")
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n[FAIL] EXCEPTION after {elapsed:.1f}s: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e), "source_id": source_id_str}


def main():
    parser = argparse.ArgumentParser(
        description="Run data collection for cannabis data sources"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", nargs="+", metavar="SOURCE_ID",
                       help="Specific source ID(s) to collect")
    group.add_argument("--all", action="store_true",
                       help="Run all enabled sources")
    group.add_argument("--list", action="store_true",
                       help="List available sources and exit")

    parser.add_argument("--state", help="Filter by state (with --all)")
    parser.add_argument("--category", help="Filter by category (with --all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List what would run without actually collecting")
    parser.add_argument("--db-url", default=None)
    args = parser.parse_args()

    db_url = args.db_url or os.environ.get(
        "DATABASE_URL", "sqlite:///data/cannabis_aggregator.db"
    )

    from src.storage.database import init_db
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    init_db(db_url)

    # --list
    if args.list:
        sources = list_sources(state=args.state, category=args.category)
        print(f"\nEnabled sources ({len(sources)} total):\n")
        print(f"{'ID':<40} {'State':<6} {'Category':<20} {'Format':<8} Name")
        print("-" * 100)
        for s in sources:
            print(f"{s['source_id']:<40} {s['state']:<6} {s['category']:<20} "
                  f"{s['format']:<8} {s['name']}")
        return

    # Determine sources to run
    if args.all:
        sources = list_sources(state=args.state, category=args.category)
        source_ids = [s["source_id"] for s in sources]
        print(f"\nRunning {len(source_ids)} sources" +
              (f" in state {args.state}" if args.state else "") +
              (f" with category '{args.category}'" if args.category else ""))
    else:
        source_ids = args.source

    if not source_ids:
        print("No sources to run.")
        return

    start_time = datetime.utcnow()
    results = []
    for sid in source_ids:
        result = run_source(sid, dry_run=args.dry_run)
        if result:
            results.append(result)

    # Summary
    elapsed_total = (datetime.utcnow() - start_time).total_seconds()
    success = sum(1 for r in results if r.get("status") == "success")
    failed  = sum(1 for r in results if r.get("status") == "failed")
    total_fetched = sum(r.get("records_fetched", 0) for r in results)
    total_stored  = sum(r.get("records_stored", 0) for r in results)

    print(f"\n{'='*60}")
    print(f"SUMMARY - {len(results)} sources in {elapsed_total:.1f}s")
    print(f"  Success: {success} | Failed: {failed}")
    print(f"  Total fetched: {total_fetched:,} | Stored: {total_stored:,}")
    print(f"{'='*60}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
