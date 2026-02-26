#!/usr/bin/env python3
"""
Geocode raw_records that have address data but no lat/lng coordinates.

Uses the US Census Bureau Geocoder batch API (free, no API key required).
  https://geocoding.geo.census.gov/geocoder/

Usage:
    python scripts/geocode_records.py               # geocode all states
    python scripts/geocode_records.py --state NY    # one state
    python scripts/geocode_records.py --state NY CT # multiple states
    python scripts/geocode_records.py --dry-run     # show counts, no writes
    python scripts/geocode_records.py --limit 500   # cap records processed

The Census Geocoder accepts batches of up to 10,000 rows; this script uses
1,000 per batch with a short pause between calls to be polite.
"""
import argparse
import csv
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"), override=False)

import requests
from tqdm import tqdm

from src.storage.database import init_db, session_scope
from src.storage.models import RawRecord


# ---------------------------------------------------------------------------
# Census Geocoder constants
# ---------------------------------------------------------------------------
CENSUS_URL   = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BATCH_SIZE   = 1_000   # Census max is 10 000; 1 000 is safer and faster per call
PAUSE_SECS   = 1.0     # polite pause between batches
REQUEST_TIMEOUT = 120  # seconds — batch calls can be slow


# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------

def build_csv(records: list[RawRecord]) -> str:
    """Build the CSV payload the Census API expects:
       Unique ID, Street Address, City, State, ZIP
    """
    lines = []
    for r in records:
        # Sanitise each field: strip commas/quotes to keep CSV valid
        def clean(v):
            return str(v or "").replace('"', "'").replace(",", " ").strip()

        lines.append(
            f'{r.id},{clean(r.address)},{clean(r.city)},{clean(r.state)},{clean(r.zip_code)}'
        )
    return "\n".join(lines)


def call_census_geocoder(csv_text: str) -> dict[int, tuple[float, float]]:
    """POST a CSV batch to the Census Geocoder; returns {record_id: (lat, lng)}."""
    payload = {
        "benchmark": "Public_AR_Current",
    }
    files = {
        "addressFile": ("batch.csv", io.StringIO(csv_text), "text/csv"),
    }
    resp = requests.post(CENSUS_URL, data=payload, files=files, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    results: dict[int, tuple[float, float]] = {}
    # Use csv.reader so quoted fields (addresses with commas) are parsed correctly.
    # Response columns:
    #   0:ID  1:input_address  2:match_flag  3:match_type  4:matched_address  5:coords  6:tiger_id  7:side
    reader = csv.reader(io.StringIO(resp.text))
    for row in reader:
        if len(row) < 6:
            continue
        record_id_str = row[0].strip()
        match_flag    = row[2].strip()   # "Match" or "No_Match"
        coords_str    = row[5].strip()   # "longitude,latitude"

        if match_flag != "Match" or not coords_str:
            continue

        try:
            record_id = int(record_id_str)
            lng_s, lat_s = coords_str.split(",")
            results[record_id] = (float(lat_s), float(lng_s))
        except (ValueError, TypeError):
            continue

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Geocode records via US Census Geocoder")
    parser.add_argument("--state",   nargs="*", metavar="ST",
                        help="State code(s) to geocode, e.g. NY CT. Default: all states.")
    parser.add_argument("--limit",   type=int, default=0,
                        help="Max records to process (0 = unlimited).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be geocoded without writing to DB.")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        sys.exit("ERROR: DATABASE_URL not set. Run from project root or check .env")

    init_db(database_url=database_url)

    with session_scope() as session:
        q = session.query(RawRecord).filter(
            RawRecord.latitude == None,
            RawRecord.address  != None,
            RawRecord.address  != "",
        )
        if args.state:
            states_upper = [s.upper() for s in args.state]
            q = q.filter(RawRecord.state.in_(states_upper))
        if args.limit:
            q = q.limit(args.limit)

        records = q.all()

    if not records:
        print("No un-geocoded records found matching your criteria.")
        return

    # Show state breakdown
    from collections import Counter
    state_counts = Counter(r.state for r in records)
    print(f"\nRecords to geocode: {len(records):,}")
    for state, cnt in sorted(state_counts.items()):
        print(f"  {state}: {cnt:,}")

    if args.dry_run:
        print("\n[dry-run] No changes written.")
        return

    batches      = [records[i:i+BATCH_SIZE] for i in range(0, len(records), BATCH_SIZE)]
    total_matched = 0
    total_failed  = 0

    print(f"\nProcessing {len(batches)} batch(es) of up to {BATCH_SIZE} …\n")

    with tqdm(total=len(records), unit="rec") as bar:
        for batch_num, batch in enumerate(batches, 1):
            csv_text = build_csv(batch)

            try:
                geo_results = call_census_geocoder(csv_text)
            except requests.RequestException as e:
                print(f"\n  Batch {batch_num}: HTTP error — {e}. Skipping.")
                total_failed += len(batch)
                bar.update(len(batch))
                time.sleep(PAUSE_SECS * 3)
                continue

            matched = len(geo_results)
            failed  = len(batch) - matched
            total_matched += matched
            total_failed  += failed

            # Write results back to DB
            if geo_results:
                with session_scope() as session:
                    ids = list(geo_results.keys())
                    rows = session.query(RawRecord).filter(RawRecord.id.in_(ids)).all()
                    for row in rows:
                        lat, lng = geo_results[row.id]
                        row.latitude  = lat
                        row.longitude = lng
                    # session_scope commits on exit

            bar.update(len(batch))
            bar.set_postfix(matched=total_matched, failed=total_failed)

            if batch_num < len(batches):
                time.sleep(PAUSE_SECS)

    print(f"\nDone.")
    print(f"  Geocoded : {total_matched:,}")
    print(f"  No match : {total_failed:,}")
    print(f"  Success  : {total_matched/len(records)*100:.1f}%")


if __name__ == "__main__":
    main()
