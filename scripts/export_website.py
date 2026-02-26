#!/usr/bin/env python3
"""
Export cannabis aggregator data to a standardized format for website import.

Produces normalized records for: dispensaries, brands, licenses, sales, laws.
Each record includes a bookmark_category_id matching your website's bookmark_categories table.

Usage:
    python scripts/export_website.py                          # export all types, JSON
    python scripts/export_website.py --type dispensaries      # only dispensaries
    python scripts/export_website.py --type brands            # only brands/manufacturers
    python scripts/export_website.py --type licenses          # all license records
    python scripts/export_website.py --type sales             # sales data
    python scripts/export_website.py --type laws              # congressional bills
    python scripts/export_website.py --state CA               # filter by state
    python scripts/export_website.py --state CA --type dispensaries
    python scripts/export_website.py --format csv             # CSV output
    python scripts/export_website.py --format jsonl           # one JSON object per line
    python scripts/export_website.py --format json            # JSON array (default)
    python scripts/export_website.py --out data/export/       # output directory
    python scripts/export_website.py --limit 500              # cap records per type
    python scripts/export_website.py --status active          # only active licenses
    python scripts/export_website.py --summary                # print counts, no file output

Output files (default: data/export/):
    dispensaries.json / dispensaries.csv
    brands.json       / brands.csv
    licenses.json     / licenses.csv
    sales.json        / sales.csv
    laws.json         / laws.csv
    all.json          / all.csv  (only when --type is not specified)
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=False)


# ---------------------------------------------------------------------------
# Bookmark category IDs (from your website's bookmark_categories table).
# Update these if your IDs differ.
# ---------------------------------------------------------------------------
BOOKMARK_CATEGORY_IDS = {
    "cannabis":             243,
    "dispensaries":         244,
    "cannabis-products":    245,
    "cannabis-brands":      246,
    "cannabis-connecticut": 247,
    "cannabis-sales":       248,
    "datasets":             218,
    "legal":                232,
}

# ---------------------------------------------------------------------------
# License type keyword → export type + bookmark category
# Order matters: first match wins.
# ---------------------------------------------------------------------------
LICENSE_TYPE_MAP = [
    # Dispensary / retail keywords
    (["retail", "dispensary", "medical dispensary", "adult-use retail",
      "conditional adult-use retail", "conditional medical"],
     "dispensaries", "dispensaries"),

    # Producer / cultivator → brand
    (["cultivat", "producer", "grower", "nursery", "hemp"],
     "brands", "cannabis-brands"),

    # Manufacturer / processor → brand
    (["manufactur", "processor", "infuser", "extract", "concentrat", "edible",
      "product", "kitchen"],
     "brands", "cannabis-brands"),

    # Transporter / delivery
    (["transport", "delivery", "courier", "distributor"],
     "brands", "cannabis-brands"),

    # Testing lab
    (["lab", "testing", "laboratory"],
     "brands", "cannabis-brands"),

    # Microbusiness / social equity
    (["microbusiness", "social equity", "cooperative"],
     "dispensaries", "dispensaries"),
]


def classify_license(license_type: str, source_category: str):
    """Return (export_type, bookmark_slug) for a license record."""
    lt = (license_type or "").lower()

    if source_category == "dispensaries":
        return "dispensaries", "dispensaries"

    if source_category == "sales":
        return "sales", "cannabis-sales"

    if source_category == "laws":
        return "laws", "legal"

    for keywords, exp_type, bm_slug in LICENSE_TYPE_MAP:
        if any(kw in lt for kw in keywords):
            return exp_type, bm_slug

    # Default: generic license
    return "licenses", "cannabis"


def safe_str(val) -> str:
    if val is None:
        return ""
    return str(val).strip()


def safe_date(val) -> str:
    if val is None:
        return ""
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    return safe_str(val)


def build_tags(record, source_name: str, export_type: str) -> list:
    tags = ["cannabis"]
    state = safe_str(record.get("state"))
    if state:
        tags.append(state.upper())
    city = safe_str(record.get("city"))
    if city:
        tags.append(city.title())
    lt = safe_str(record.get("license_type"))
    if lt:
        tags.append(lt)
    tags.append(export_type)
    if source_name:
        tags.append(source_name)
    # Deduplicate, preserve order
    seen = set()
    out = []
    for t in tags:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def normalize_record(raw, source_name: str, source_id_str: str) -> dict:
    """
    Flatten a RawRecord ORM object into a plain dict for export.
    """
    rd = raw.record_data or {}

    state = safe_str(raw.state or rd.get("state", ""))
    city  = safe_str(raw.city  or rd.get("city",  ""))
    name  = safe_str(raw.name  or rd.get("name",  "") or rd.get("business_name", ""))

    license_type   = safe_str(raw.license_type   or rd.get("license_type",   ""))
    license_number = safe_str(raw.license_number or rd.get("license_number", ""))
    license_status = safe_str(raw.license_status or rd.get("license_status", ""))

    export_type, bm_slug = classify_license(license_type, raw.category or "")
    bookmark_category_id = BOOKMARK_CATEGORY_IDS.get(bm_slug, BOOKMARK_CATEGORY_IDS["cannabis"])

    # State-specific override for CT
    if state.upper() == "CT":
        bookmark_category_id = BOOKMARK_CATEGORY_IDS["cannabis-connecticut"]
        bm_slug = "cannabis-connecticut"

    # Build a human-readable description
    parts = []
    if license_type:
        parts.append(license_type)
    if license_status:
        parts.append(f"({license_status})")
    if city and state:
        parts.append(f"— {city}, {state.upper()}")
    elif state:
        parts.append(f"— {state.upper()}")
    if license_number:
        parts.append(f"License #{license_number}")
    description = " ".join(parts) if parts else name

    record = {
        "export_type":          export_type,
        "bookmark_category_id": bookmark_category_id,
        "bookmark_category":    bm_slug,
        "title":                name,
        "description":          description,
        "state":                state.upper() if state else "",
        "city":                 city.title() if city else "",
        "address":              safe_str(raw.address or rd.get("address", "")),
        "zip_code":             safe_str(raw.zip_code or rd.get("zip_code", "")),
        "county":               safe_str(raw.county  or rd.get("county",  "")),
        "latitude":             raw.latitude  if raw.latitude  is not None else rd.get("latitude"),
        "longitude":            raw.longitude if raw.longitude is not None else rd.get("longitude"),
        "phone":                safe_str(raw.phone or rd.get("phone", "")),
        "email":                safe_str(raw.email or rd.get("email", "")),
        "website":              safe_str(raw.website or rd.get("website", "")),
        "license_number":       license_number,
        "license_type":         license_type,
        "license_status":       license_status,
        "license_date":         safe_date(raw.license_date),
        "expiry_date":          safe_date(raw.expiry_date),
        "record_date":          safe_date(raw.record_date),
        "source":               source_id_str,
        "source_name":          source_name,
        "tags":                 build_tags(
            {"state": state, "city": city, "license_type": license_type},
            source_name, export_type
        ),
        "raw_id":               raw.id,
        "exported_at":          datetime.utcnow().isoformat() + "Z",
    }

    # For sales records, pull in numeric fields from record_data
    if raw.category == "sales":
        for key in ("med_sales", "rec_sales", "total_sales", "sale_amount",
                    "month", "year", "week", "period"):
            if key in rd:
                record[key] = rd[key]

    # For law/bill records
    if raw.category == "laws":
        for key in ("bill_number", "bill_type", "congress", "origin_chamber",
                    "latest_action", "url", "introduced_date", "update_date"):
            if key in rd:
                record[key] = rd[key]
        if rd.get("url"):
            record["website"] = rd["url"]

    return record


def export_records(
    session,
    export_types: list,
    state_filter: str = None,
    status_filter: str = None,
    limit: int = None,
) -> dict:
    """
    Query raw_records and return dict of {export_type: [records]}.
    """
    from src.storage.models import DataSource, RawRecord
    from sqlalchemy import and_

    # Pre-build source lookup
    sources = {s.id: s for s in session.query(DataSource).all()}

    q = session.query(RawRecord)
    if state_filter:
        q = q.filter(RawRecord.state == state_filter.upper())
    if status_filter:
        q = q.filter(RawRecord.license_status.ilike(f"%{status_filter}%"))

    q = q.order_by(RawRecord.state, RawRecord.name)

    results = {t: [] for t in ["dispensaries", "brands", "licenses", "sales", "laws"]}
    counts  = {t: 0  for t in results}

    for raw in q.yield_per(500):
        src = sources.get(raw.source_id)
        source_id_str = src.source_id if src else "unknown"
        source_name   = src.name      if src else "Unknown"

        norm = normalize_record(raw, source_name, source_id_str)
        exp_type = norm["export_type"]

        if export_types and exp_type not in export_types:
            # Try to put all non-matched license records in "licenses" bucket
            if "licenses" in export_types and raw.category == "licenses":
                exp_type = "licenses"
                norm["export_type"] = "licenses"
            else:
                continue

        if limit and counts[exp_type] >= limit:
            continue

        results[exp_type].append(norm)
        counts[exp_type] += 1

    return results


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "export_type", "bookmark_category_id", "bookmark_category",
    "title", "description", "state", "city", "address", "zip_code", "county",
    "latitude", "longitude", "phone", "email", "website",
    "license_number", "license_type", "license_status",
    "license_date", "expiry_date", "record_date",
    "source", "source_name", "tags", "raw_id", "exported_at",
]


def write_json(records: list, path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str, ensure_ascii=False)
    print(f"  [OK] {len(records):,} records -> {path}")


def write_jsonl(records: list, path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=str, ensure_ascii=False) + "\n")
    print(f"  [OK] {len(records):,} records -> {path}")


def write_csv(records: list, path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if not records:
        print(f"  [SKIP] No records for {path}")
        return
    # Collect all fields (base + any extras like med_sales, bill_number, etc.)
    all_keys = list(CSV_FIELDS)
    extra_keys = []
    for r in records:
        for k in r:
            if k not in all_keys and k not in extra_keys:
                extra_keys.append(k)
    fieldnames = all_keys + extra_keys

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            row = dict(r)
            if "tags" in row and isinstance(row["tags"], list):
                row["tags"] = "|".join(row["tags"])
            writer.writerow(row)
    print(f"  [OK] {len(records):,} records -> {path}")


def write_output(records: list, path: str, fmt: str):
    if fmt == "csv":
        write_csv(records, path)
    elif fmt == "jsonl":
        write_jsonl(records, path)
    else:
        write_json(records, path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Export cannabis aggregator data for website import"
    )
    parser.add_argument(
        "--type", nargs="+",
        choices=["dispensaries", "brands", "licenses", "sales", "laws", "all"],
        default=["all"],
        help="Export type(s). Default: all"
    )
    parser.add_argument("--state",  default=None,
                        help="Filter by state abbreviation (e.g. CA, CO)")
    parser.add_argument("--status", default=None,
                        help="Filter by license_status (e.g. active, approved)")
    parser.add_argument("--format", choices=["json", "jsonl", "csv"], default="json",
                        help="Output format. Default: json")
    parser.add_argument("--out",    default=None,
                        help="Output directory. Default: data/export/")
    parser.add_argument("--limit",  type=int, default=None,
                        help="Max records per type (no limit by default)")
    parser.add_argument("--summary", action="store_true",
                        help="Print record counts without writing files")
    parser.add_argument("--db-url", default=None)
    args = parser.parse_args()

    db_url = args.db_url or os.environ.get(
        "DATABASE_URL", "sqlite:///data/cannabis_aggregator.db"
    )

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = args.out or os.path.join(project_root, "data", "export")

    # Determine which types to export
    requested_types = args.type
    if "all" in requested_types:
        requested_types = ["dispensaries", "brands", "licenses", "sales", "laws"]

    from src.storage.database import init_db, session_scope

    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    init_db(db_url)

    print(f"Database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    print(f"Types:    {', '.join(requested_types)}")
    if args.state:
        print(f"State:    {args.state.upper()}")
    if args.status:
        print(f"Status:   {args.status}")
    if args.limit:
        print(f"Limit:    {args.limit:,} per type")
    print()

    with session_scope() as session:
        results = export_records(
            session,
            export_types=requested_types,
            state_filter=args.state,
            status_filter=args.status,
            limit=args.limit,
        )

    ext = args.format  # json, jsonl, csv
    total = 0

    # Print summary
    print("Export summary:")
    for exp_type in requested_types:
        recs = results.get(exp_type, [])
        n = len(recs)
        total += n
        print(f"  {exp_type:<15} {n:>6,} records")
    print(f"  {'TOTAL':<15} {total:>6,} records")
    print()

    if args.summary:
        print("[SUMMARY ONLY — no files written]")
        return

    if total == 0:
        print("[WARN] No records found. Run data collection first:")
        print("  python scripts/run_collector.py --all")
        return

    # Write individual type files
    state_suffix = f"_{args.state.upper()}" if args.state else ""
    for exp_type in requested_types:
        recs = results.get(exp_type, [])
        if not recs:
            print(f"  [SKIP] {exp_type} — 0 records")
            continue
        fname = f"{exp_type}{state_suffix}.{ext}"
        write_output(recs, os.path.join(out_dir, fname), args.format)

    # Write combined "all" file only when exporting all types
    if set(requested_types) == {"dispensaries", "brands", "licenses", "sales", "laws"} or len(requested_types) > 1:
        all_records = []
        for exp_type in requested_types:
            all_records.extend(results.get(exp_type, []))
        if all_records:
            fname = f"all{state_suffix}.{ext}"
            write_output(all_records, os.path.join(out_dir, fname), args.format)

    print(f"\nDone. Files written to: {out_dir}")


if __name__ == "__main__":
    main()
