#!/usr/bin/env python3
"""
Seed script: loads sources and schedules from YAML config into the database.

Usage:
    python scripts/seed_sources.py                   # seed everything
    python scripts/seed_sources.py --sources-only    # only seed sources
    python scripts/seed_sources.py --schedules-only  # only seed schedules
    python scripts/seed_sources.py --dry-run         # preview without writing
    python scripts/seed_sources.py --force           # overwrite all fields
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
# Always load .env from the project root (parent of scripts/), regardless of CWD.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=False)

import yaml


def seed_sources(session, sources_cfg: list, force: bool = False, dry_run: bool = False):
    from src.storage.models import DataSource

    created = updated = skipped = 0

    for cfg in sources_cfg:
        if not cfg.get("id") or not cfg.get("url"):
            print(f"  [SKIP] Missing id or url: {cfg.get('id', '?')}")
            skipped += 1
            continue

        existing = session.query(DataSource).filter_by(source_id=cfg["id"]).first()

        if existing and not force:
            skipped += 1
            continue

        fields = {
            "source_id":    cfg["id"],
            "name":         cfg.get("name", cfg["id"]),
            "state":        cfg.get("state", ""),
            "agency":       cfg.get("agency", ""),
            "category":     cfg.get("category", ""),
            "subcategory":  cfg.get("subcategory", ""),
            "format":       cfg.get("format", "json"),
            "url":          cfg.get("url", ""),
            "discovery_url": cfg.get("discovery_url", ""),
            "enabled":      cfg.get("enabled", True),
            "api_key_env":  cfg.get("api_key_env", ""),
            "website":      cfg.get("website", ""),
            "notes":        cfg.get("notes", ""),
            "tags":         cfg.get("tags", []),
            "params":       cfg.get("params", {}),
            "pagination":   cfg.get("pagination", {}),
            "field_mapping": cfg.get("field_mapping", {}),
            "headers":      cfg.get("headers", {}),
            "rate_limit_rpm": cfg.get("rate_limit_rpm", 60),
        }

        if dry_run:
            action = "UPDATE" if existing else "CREATE"
            print(f"  [DRY-RUN {action}] {cfg['id']} — {cfg.get('name','')}")
            if existing:
                updated += 1
            else:
                created += 1
            continue

        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            updated += 1
        else:
            session.add(DataSource(**fields))
            created += 1

    return created, updated, skipped


def seed_schedules(session, schedules_cfg: list, force: bool = False, dry_run: bool = False):
    from src.storage.models import DataSource, CollectionSchedule

    created = updated = skipped = 0

    for cfg in schedules_cfg:
        # Find the linked source
        source = session.query(DataSource).filter_by(source_id=cfg.get("source_id")).first()
        if not source:
            print(f"  [SKIP] Schedule {cfg['id']}: source '{cfg.get('source_id')}' not found")
            skipped += 1
            continue

        existing = session.query(CollectionSchedule).filter_by(
            schedule_id=cfg["id"]
        ).first()

        if existing and not force:
            skipped += 1
            continue

        cron = cfg.get("cron", {})
        intv = cfg.get("interval", {})

        fields = {
            "schedule_id":      cfg["id"],
            "source_id":        source.id,
            "name":             cfg.get("name", cfg["id"]),
            "schedule_type":    cfg.get("schedule_type", "cron"),
            "enabled":          cfg.get("enabled", True),
            "priority":         cfg.get("priority", 2),
            "notes":            cfg.get("notes", ""),
            "cron_minute":      str(cron.get("minute", "0")),
            "cron_hour":        str(cron.get("hour", "2")),
            "cron_day_of_month": str(cron.get("day_of_month", "*")),
            "cron_month":       str(cron.get("month", "*")),
            "cron_day_of_week": str(cron.get("day_of_week", "*")),
            "interval_value":   intv.get("value", 7),
            "interval_unit":    intv.get("unit", "days"),
        }

        if dry_run:
            action = "UPDATE" if existing else "CREATE"
            print(f"  [DRY-RUN {action}] {cfg['id']}")
            if existing:
                updated += 1
            else:
                created += 1
            continue

        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            updated += 1
        else:
            session.add(CollectionSchedule(**fields))
            created += 1

    return created, updated, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Seed data sources and schedules from YAML config"
    )
    parser.add_argument("--sources-only",   action="store_true")
    parser.add_argument("--schedules-only", action="store_true")
    parser.add_argument("--dry-run",        action="store_true",
                        help="Preview changes without writing to DB")
    parser.add_argument("--force",          action="store_true",
                        help="Overwrite existing records (by default, existing are skipped)")
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--config-dir", default=None,
                        help="Path to config directory (default: project_root/config)")
    args = parser.parse_args()

    db_url = args.db_url or os.environ.get(
        "DATABASE_URL", "sqlite:///data/cannabis_aggregator.db"
    )

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir   = args.config_dir or os.path.join(project_root, "config")

    sources_path   = os.path.join(config_dir, "sources.yaml")
    schedules_path = os.path.join(config_dir, "schedules.yaml")

    # Init DB
    from src.storage.database import init_db, session_scope

    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    init_db(db_url)
    print(f"Database: {db_url}")
    if args.dry_run:
        print("[DRY RUN — no changes will be written]")
    print()

    with session_scope() as session:
        # Seed sources
        if not args.schedules_only:
            if not os.path.exists(sources_path):
                print(f"[ERR] sources.yaml not found at {sources_path}")
                if not args.sources_only:
                    pass  # Continue to schedules
            else:
                print(f"Seeding sources from {sources_path}...")
                with open(sources_path) as f:
                    sources_cfg = yaml.safe_load(f).get("sources", [])
                print(f"  Found {len(sources_cfg)} source definitions")
                c, u, s = seed_sources(session, sources_cfg, args.force, args.dry_run)
                print(f"  [OK] Created: {c}  Updated: {u}  Skipped: {s}")
                print()

        # Seed schedules
        if not args.sources_only:
            if not os.path.exists(schedules_path):
                print(f"[ERR] schedules.yaml not found at {schedules_path}")
            else:
                print(f"Seeding schedules from {schedules_path}...")
                with open(schedules_path) as f:
                    schedules_cfg = yaml.safe_load(f).get("schedules", [])
                print(f"  Found {len(schedules_cfg)} schedule definitions")
                c, u, s = seed_schedules(session, schedules_cfg, args.force, args.dry_run)
                print(f"  [OK] Created: {c}  Updated: {u}  Skipped: {s}")
                print()

    print("Done.")


if __name__ == "__main__":
    main()
