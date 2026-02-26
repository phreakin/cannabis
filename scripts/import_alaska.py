"""
Import Alaska marijuana license CSV files into the cannabis_licenses table.

Usage:
    python scripts/import_alaska.py

Expects the 6 CSV files to be present at the paths defined in FILES below.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import get_session
from src.storage.models import CannabisLicense

# ---------------------------------------------------------------------------
# File → license_type mapping
# ---------------------------------------------------------------------------
FILES = [
    (
        r"C:/Users/jason/Downloads/alaska_standard_marijuana_cultivation_facility.csv",
        "Standard Cultivation Facility",
    ),
    (
        r"C:/Users/jason/Downloads/alaska_marijuana_testing_facility.csv",
        "Testing Facility",
    ),
    (
        r"C:/Users/jason/Downloads/alaska_marijuana_product_manufacturing_facility.csv",
        "Product Manufacturing Facility",
    ),
    (
        r"C:/Users/jason/Downloads/alaska_marijuana_concentrate_manufacturing_facility.csv",
        "Concentrate Manufacturing Facility",
    ),
    (
        r"C:/Users/jason/Downloads/alaska_limited_cultivation_facility.csv",
        "Limited Cultivation Facility",
    ),
    (
        r"C:/Users/jason/Downloads/alaska_retail_marijuana_stores.csv",
        "Retail Store",
    ),
]


# ---------------------------------------------------------------------------
# Address parser
# ---------------------------------------------------------------------------

def _parse_address(raw: str):
    """
    Parse the lineBreaks multi-line address field.

    Expected format:
        32500 South Talkeetna Spur Road
        Talkeetna, AK 99676

    Returns (street, city, state, zipcode) — all may be None on parse failure.
    """
    if not raw or not raw.strip():
        return None, None, None, None

    lines = [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]

    street = lines[0] if len(lines) >= 1 else None

    city = state = zipcode = None
    if len(lines) >= 2:
        # "Talkeetna, AK 99676"
        second = lines[1]
        if ", " in second:
            city_part, rest = second.split(", ", 1)
            city = city_part.strip()
            parts = rest.strip().split()
            if len(parts) >= 1:
                state = parts[0]
            if len(parts) >= 2:
                zipcode = parts[1]
        else:
            # Fallback: just store the whole second line as city
            city = second

    return street, city, state, zipcode


# ---------------------------------------------------------------------------
# Main import logic
# ---------------------------------------------------------------------------

def import_file(session, filepath: str, license_type: str):
    filename = Path(filepath).name

    try:
        fh = open(filepath, newline="", encoding="utf-8-sig", errors="replace")
    except FileNotFoundError:
        print(f"  [SKIP] File not found: {filepath}")
        return 0, 0

    inserted = 0
    skipped = 0

    with fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        print(f"Processing {filename}: {len(rows)} records...")

        for row in rows:
            license_number = (row.get("deptGridViewActionCell") or "").strip() or None
            license_url = (row.get("deptGridViewActionCell href") or "").strip() or None
            business_license_number = (row.get("deptGridViewActionCell 2") or "").strip() or None
            business_license_url = (row.get("deptGridViewActionCell href 2") or "").strip() or None
            business_name = (row.get("tablescraper-selected-row") or "").strip()
            license_status = (row.get("LicenseStatus") or "").strip() or None
            raw_address = row.get("lineBreaks") or ""

            # Skip rows with no business name
            if not business_name:
                skipped += 1
                continue

            # Skip duplicate license_numbers
            if license_number:
                existing = (
                    session.query(CannabisLicense)
                    .filter(CannabisLicense.license_number == license_number)
                    .first()
                )
                if existing:
                    skipped += 1
                    continue

            street, city, state_code, zipcode = _parse_address(raw_address)

            record = CannabisLicense(
                license_number=license_number,
                license_url=license_url,
                business_license_number=business_license_number,
                business_license_url=business_license_url,
                license_type=license_type,
                license_status=license_status,
                business_name=business_name,
                street=street,
                city=city,
                state=state_code,
                zipcode=zipcode,
                country="US",
                source_state="AK",
                source_file=filename,
            )
            session.add(record)
            inserted += 1

        session.commit()

    return inserted, skipped


def main():
    session = get_session()
    total_inserted = 0
    total_skipped = 0

    try:
        for filepath, license_type in FILES:
            ins, skp = import_file(session, filepath, license_type)
            total_inserted += ins
            total_skipped += skp
    finally:
        session.close()

    print()
    print("=" * 50)
    print(f"Done. Inserted: {total_inserted}  Skipped: {total_skipped}")
    print("=" * 50)


if __name__ == "__main__":
    main()
