"""
Import Kushy Cannabis Dataset CSVs into the database.

Imports:
  - brands-kushy_api.2017-11-14.csv   → CannabisBrand
  - products-kushy_api.2017-11-14.csv → CannabisProduct
  - shops-kushy_api.2017-11-14.csv    → CannabisShop
  - strains-kushy_api.2017-11-14.csv  → CannabisStrain

Usage:
    python scripts/import_kushy.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import get_session
from src.storage.models import CannabisBrand, CannabisProduct, CannabisShop, CannabisStrain

KUSHY_DIR = r"C:/Users/jason/Downloads/Kushy Cannabis Dataset"

BRANDS_FILE   = f"{KUSHY_DIR}/brands-kushy_api.2017-11-14.csv"
PRODUCTS_FILE = f"{KUSHY_DIR}/products-kushy_api.2017-11-14.csv"
SHOPS_FILE    = f"{KUSHY_DIR}/shops-kushy_api.2017-11-14.csv"
STRAINS_FILE  = f"{KUSHY_DIR}/strains-kushy_api.2017-11-14.csv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val, skip_zero=False):
    """Convert value to float. Returns None for empty/NULL/invalid values.
    If skip_zero=True, also returns None for "0" (used for cannabinoid columns)."""
    if val is None:
        return None
    s = str(val).strip()
    if s in ("", "NULL", "null", "None", "none"):
        return None
    if skip_zero and s == "0":
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _safe_int(val):
    """Convert value to int. Returns None for empty/NULL/invalid values."""
    if val is None:
        return None
    s = str(val).strip()
    if s in ("", "NULL", "null", "None", "none"):
        return None
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return None


def _clean_str(val):
    """Strip and return None if empty."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s.lower() not in ("null", "none") else None


def _open_csv(filepath):
    """Open a CSV file and return (header_list, row_iterator) or None on missing."""
    try:
        fh = open(filepath, newline="", encoding="utf-8-sig", errors="replace")
    except FileNotFoundError:
        print(f"  [SKIP] File not found: {filepath}")
        return None, None
    reader = csv.DictReader(fh)
    rows = list(reader)
    fh.close()
    return rows


# ---------------------------------------------------------------------------
# Brands import
# ---------------------------------------------------------------------------

def import_brands(session):
    filepath = BRANDS_FILE
    filename = Path(filepath).name
    rows = _open_csv(filepath)
    if rows is None:
        return 0, 0

    print(f"Processing {filename}: {len(rows)} records...")
    inserted = skipped = 0

    for row in rows:
        name = _clean_str(row.get("name"))
        if not name:
            skipped += 1
            continue

        # Deduplicate by name
        existing = session.query(CannabisBrand).filter(CannabisBrand.name == name).first()
        if existing:
            skipped += 1
            continue

        obj = CannabisBrand(
            name=name,
            slug=_clean_str(row.get("slug")),
            category=_clean_str(row.get("category")),
            instagram=_clean_str(row.get("instagram")),
            state=_clean_str(row.get("location")),
        )
        session.add(obj)
        inserted += 1

    session.commit()
    return inserted, skipped


# ---------------------------------------------------------------------------
# Products import
# ---------------------------------------------------------------------------

def import_products(session):
    filepath = PRODUCTS_FILE
    filename = Path(filepath).name
    rows = _open_csv(filepath)
    if rows is None:
        return 0, 0

    print(f"Processing {filename}: {len(rows)} records...")
    inserted = skipped = 0

    # Build a set of existing names for fast dedup (products table may be large)
    existing_names = {r[0] for r in session.query(CannabisProduct.name).all()}

    for row in rows:
        name = _clean_str(row.get("name"))
        if not name:
            skipped += 1
            continue

        # Deduplicate by name
        if name in existing_names:
            skipped += 1
            continue

        obj = CannabisProduct(
            name=name,
            category=_clean_str(row.get("category")),
            strain_name=_clean_str(row.get("strain")),
            thc_percentage=_safe_float(row.get("thc")),
            cbd_percentage=_safe_float(row.get("cbd")),
        )
        session.add(obj)
        existing_names.add(name)
        inserted += 1

        # Commit in batches to avoid huge transactions
        if inserted % 1000 == 0:
            session.commit()
            print(f"  ... {inserted} products inserted so far")

    session.commit()
    return inserted, skipped


# ---------------------------------------------------------------------------
# Shops import
# ---------------------------------------------------------------------------

def import_shops(session):
    filepath = SHOPS_FILE
    filename = Path(filepath).name
    rows = _open_csv(filepath)
    if rows is None:
        return 0, 0

    print(f"Processing {filename}: {len(rows)} records...")
    inserted = skipped = 0

    for row in rows:
        name = _clean_str(row.get("name"))
        if not name:
            skipped += 1
            continue

        source_id = _safe_int(row.get("id"))

        # Deduplicate by source_id
        if source_id is not None:
            existing = session.query(CannabisShop).filter(CannabisShop.source_id == source_id).first()
            if existing:
                skipped += 1
                continue

        obj = CannabisShop(
            source_id=source_id,
            name=name,
            slug=_clean_str(row.get("slug")),
            status=_safe_int(row.get("status")),
            featured_image=_clean_str(row.get("featured_image")),
            avatar_url=_clean_str(row.get("avatar")),
            description=_clean_str(row.get("description")),
            latitude=_safe_float(row.get("lat")),
            longitude=_safe_float(row.get("lng")),
            street=_clean_str(row.get("address")),
            city=_clean_str(row.get("city")),
            state=_clean_str(row.get("state")),
            zipcode=_clean_str(row.get("postcode")),
            country=_clean_str(row.get("country")),
            instagram=_clean_str(row.get("instagram")),
            twitter=_clean_str(row.get("twitter")),
            facebook=_clean_str(row.get("facebook")),
            rating=_safe_float(row.get("rating")),
            tags=_clean_str(row.get("tags")),
            hours=_clean_str(row.get("hours")),
            shop_type=_clean_str(row.get("type")),
        )
        session.add(obj)
        inserted += 1

    session.commit()
    return inserted, skipped


# ---------------------------------------------------------------------------
# Strains import
# ---------------------------------------------------------------------------

CANNABINOID_COLS = [
    "thc", "thca", "thcv", "cbd", "cbda", "cbdv",
    "cbn", "cbg", "cbgm", "cbgv", "cbc", "cbcv",
]


def import_strains(session):
    filepath = STRAINS_FILE
    filename = Path(filepath).name
    rows = _open_csv(filepath)
    if rows is None:
        return 0, 0

    print(f"Processing {filename}: {len(rows)} records...")
    inserted = skipped = 0

    for row in rows:
        name = _clean_str(row.get("name"))
        if not name:
            skipped += 1
            continue

        source_id = _safe_int(row.get("id"))

        # Deduplicate by source_id
        if source_id is not None:
            existing = session.query(CannabisStrain).filter(CannabisStrain.source_id == source_id).first()
            if existing:
                skipped += 1
                continue

        obj = CannabisStrain(
            source_id=source_id,
            name=name,
            slug=_clean_str(row.get("slug")),
            status=_safe_int(row.get("status")),
            image_url=_clean_str(row.get("image")),
            description=_clean_str(row.get("description")),
            strain_type=_clean_str(row.get("type")),
            crosses=_clean_str(row.get("crosses")),
            breeder=_clean_str(row.get("breeder")),
            effects=_clean_str(row.get("effects")),
            ailments=_clean_str(row.get("ailment")),
            flavors=_clean_str(row.get("flavor")),
            terpenes=_clean_str(row.get("terpenes")),
            # Cannabinoids: skip "0" values
            thc=_safe_float(row.get("thc"), skip_zero=True),
            thca=_safe_float(row.get("thca"), skip_zero=True),
            thcv=_safe_float(row.get("thcv"), skip_zero=True),
            cbd=_safe_float(row.get("cbd"), skip_zero=True),
            cbda=_safe_float(row.get("cbda"), skip_zero=True),
            cbdv=_safe_float(row.get("cbdv"), skip_zero=True),
            cbn=_safe_float(row.get("cbn"), skip_zero=True),
            cbg=_safe_float(row.get("cbg"), skip_zero=True),
            cbgm=_safe_float(row.get("cbgm"), skip_zero=True),
            cbgv=_safe_float(row.get("cbgv"), skip_zero=True),
            cbc=_safe_float(row.get("cbc"), skip_zero=True),
            cbcv=_safe_float(row.get("cbcv"), skip_zero=True),
        )
        session.add(obj)
        inserted += 1

    session.commit()
    return inserted, skipped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    session = get_session()
    results = {}

    try:
        results["brands"]   = import_brands(session)
        results["products"] = import_products(session)
        results["shops"]    = import_shops(session)
        results["strains"]  = import_strains(session)
    finally:
        session.close()

    print()
    print("=" * 60)
    print(f"{'Table':<12}  {'Inserted':>10}  {'Skipped':>10}")
    print("-" * 36)
    for table, (ins, skp) in results.items():
        print(f"{table:<12}  {ins:>10}  {skp:>10}")
    print("=" * 60)


if __name__ == "__main__":
    main()
