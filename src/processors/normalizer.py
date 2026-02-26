"""
Data normalization: maps raw source records to the standard RawRecord schema
using field_mapping configurations from sources.yaml.
"""
import logging
import re
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


# Standard field names in the RawRecord model
STANDARD_FIELDS = {
    "name", "license_number", "license_type", "license_status",
    "address", "city", "state", "zip_code", "county",
    "latitude", "longitude", "phone", "email", "website",
    "record_date", "license_date", "expiry_date",
    "owner_name", "entity_type", "category", "subcategory",
    "district", "period_year", "period_month", "amount",
}


class RecordNormalizer:
    """
    Normalizes raw collected records into the standard schema.
    Uses the field_mapping from a DataSource configuration to
    translate source-specific field names to standard names.
    """

    def __init__(self, source):
        self.source = source
        self.source_state = getattr(source, "state", None)
        self.source_category = getattr(source, "category", None)
        self.field_mapping = self._build_field_mapping(source)

    def _build_field_mapping(self, source) -> Dict[str, str]:
        """Build field mapping: standard_name -> source_field_name."""
        mapping = getattr(source, "field_mapping", None) or {}
        # Mapping is stored as {standard_name: source_field}
        return mapping

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a raw record dict into the standard schema.
        Returns a dict ready for creating a RawRecord.
        """
        normalized = {}

        # Apply field mapping (map standard names to source values)
        for std_field, src_field in self.field_mapping.items():
            if not src_field:
                continue
            value = self._nested_get(raw, src_field)
            if value is not None:
                normalized[std_field] = self._clean_value(value)

        # For unmapped fields, try direct name matching
        for std_field in STANDARD_FIELDS:
            if std_field not in normalized:
                # Try exact match, then case-insensitive variations
                for variation in self._field_name_variations(std_field):
                    if variation in raw:
                        normalized[std_field] = self._clean_value(raw[variation])
                        break

        # Fill in source defaults
        if "state" not in normalized or not normalized["state"]:
            normalized["state"] = self.source_state
        if "category" not in normalized or not normalized["category"]:
            normalized["category"] = self.source_category

        # Parse and standardize typed fields
        normalized = self._parse_coordinates(normalized, raw)
        normalized = self._parse_dates(normalized)
        normalized = self._clean_phone(normalized)
        normalized = self._standardize_state(normalized)
        normalized = self._clean_zip(normalized)
        normalized = self._clean_website(normalized)

        return normalized

    def _nested_get(self, data: dict, key_path: str, default=None):
        """
        Get a value from a dict using dot notation for nested access.
        E.g. 'location.latitude' -> data['location']['latitude']
        """
        if not key_path or data is None:
            return default

        # Handle special Socrata location format: {latitude: ..., longitude: ...}
        keys = key_path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, (list, tuple)) and key.isdigit():
                try:
                    current = current[int(key)]
                except (IndexError, TypeError):
                    return default
            else:
                return default
            if current is None:
                return default
        return current

    def _field_name_variations(self, std_field: str) -> list:
        """Generate common field name variations for auto-detection."""
        variations = [
            std_field,
            std_field.replace("_", ""),          # no underscores
            std_field.replace("_", " "),          # spaces
            std_field.upper(),
            std_field.replace("_", " ").title(),  # Title Case
        ]
        # Special mappings
        aliases = {
            "name": ["dba", "business_name", "tradename", "license_name",
                     "dispensary_name", "facility_name", "applicant_name"],
            "license_number": ["license_no", "ubi", "license_id", "permit_number",
                               "lic_no", "license"],
            "license_type": ["type", "privilege", "category", "permit_type"],
            "license_status": ["status", "license_status"],
            "address": ["street", "street_address", "premise_address",
                        "physicaladdress", "physical_address"],
            "city": ["premise_city", "city_town", "physicalcity"],
            "zip_code": ["zip", "postal_code", "zipcode", "premise_zip",
                         "physicalzip"],
            "county": ["borough", "parish"],
            "latitude": ["lat", "y", "ylat"],
            "longitude": ["lon", "lng", "long", "x", "xlong"],
            "phone": ["telephone", "phone_number", "contact_phone"],
            "website": ["url", "web", "web_address"],
            "license_date": ["issued", "issue_date", "issueddate",
                             "effective_date", "licenseissuedate"],
            "expiry_date": ["expires", "expiration_date", "expiration",
                            "expirationdate", "licenseexpirationdate"],
        }
        if std_field in aliases:
            variations.extend(aliases[std_field])
        return variations

    def _clean_value(self, value) -> Any:
        """Basic value cleaning."""
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in ("", "n/a", "na", "null", "none", "-", "unknown"):
                return None
        return value if value != "" else None

    def _parse_coordinates(
        self, normalized: Dict, raw: Dict
    ) -> Dict:
        """Extract and validate latitude/longitude."""
        # Try various coordinate field formats
        lat = normalized.get("latitude")
        lon = normalized.get("longitude")

        # Handle Socrata nested location object: {"latitude": "...", "longitude": "..."}
        for loc_key in ("location", "geolocation", "coordinates", "point"):
            if loc_key in raw and isinstance(raw[loc_key], dict):
                loc = raw[loc_key]
                if lat is None:
                    lat = loc.get("latitude") or loc.get("lat")
                if lon is None:
                    lon = loc.get("longitude") or loc.get("lon") or loc.get("lng")
                break

        # Handle Socrata location with "human_address"
        if lat is None and "location" in raw:
            loc = raw.get("location")
            if isinstance(loc, dict):
                lat = loc.get("latitude")
                lon = loc.get("longitude")

        # Convert to float and validate
        try:
            lat_f = float(lat) if lat is not None and lat != "" else None
            lon_f = float(lon) if lon is not None and lon != "" else None

            # Basic validation of coordinate ranges
            if lat_f is not None and not (-90 <= lat_f <= 90):
                lat_f = None
            if lon_f is not None and not (-180 <= lon_f <= 180):
                lon_f = None
            # Skip null island (0,0) which often means missing data
            if lat_f == 0.0 and lon_f == 0.0:
                lat_f = lon_f = None

            normalized["latitude"] = lat_f
            normalized["longitude"] = lon_f
        except (ValueError, TypeError):
            normalized["latitude"] = None
            normalized["longitude"] = None

        return normalized

    def _parse_dates(self, normalized: Dict) -> Dict:
        """Parse date strings into date objects."""
        date_fields = ["record_date", "license_date", "expiry_date"]
        for field in date_fields:
            val = normalized.get(field)
            if val and not isinstance(val, (date, datetime)):
                parsed = self._parse_date_string(str(val))
                normalized[field] = parsed

        return normalized

    def _parse_date_string(self, date_str: str) -> Optional[date]:
        """Try various date formats."""
        if not date_str or date_str.lower() in ("n/a", "none", "null"):
            return None

        # Truncate to date part if datetime string
        date_str = date_str.split("T")[0].split(" ")[0].strip()

        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y",
            "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d",
            "%m/%d/%y", "%d-%b-%Y", "%B %d, %Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def _clean_phone(self, normalized: Dict) -> Dict:
        """Standardize phone number format."""
        phone = normalized.get("phone")
        if phone:
            digits = re.sub(r"\D", "", str(phone))
            if len(digits) == 10:
                normalized["phone"] = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == "1":
                normalized["phone"] = f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return normalized

    def _standardize_state(self, normalized: Dict) -> Dict:
        """Ensure state is a 2-letter abbreviation."""
        state = normalized.get("state")
        if state and len(state) > 2:
            # Could be full state name - map to abbreviation
            state_map = {
                "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
                "california": "CA", "colorado": "CO", "connecticut": "CT",
                "delaware": "DE", "florida": "FL", "georgia": "GA",
                "hawaii": "HI", "idaho": "ID", "illinois": "IL",
                "indiana": "IN", "iowa": "IA", "kansas": "KS",
                "kentucky": "KY", "louisiana": "LA", "maine": "ME",
                "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
                "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
                "montana": "MT", "nebraska": "NE", "nevada": "NV",
                "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
                "new york": "NY", "north carolina": "NC", "north dakota": "ND",
                "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
                "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
                "south dakota": "SD", "tennessee": "TN", "texas": "TX",
                "utah": "UT", "vermont": "VT", "virginia": "VA",
                "washington": "WA", "west virginia": "WV", "wisconsin": "WI",
                "wyoming": "WY", "district of columbia": "DC",
            }
            abbr = state_map.get(state.lower().strip())
            if abbr:
                normalized["state"] = abbr
        elif state:
            normalized["state"] = state.upper().strip()
        return normalized

    def _clean_zip(self, normalized: Dict) -> Dict:
        """Standardize ZIP code to 5-digit format."""
        zip_code = normalized.get("zip_code")
        if zip_code:
            zip_str = str(zip_code).strip()
            # Extract first 5 digits
            digits = re.sub(r"\D", "", zip_str)
            if len(digits) >= 5:
                normalized["zip_code"] = digits[:5]
            elif digits:
                normalized["zip_code"] = digits.zfill(5)
        return normalized

    def _clean_website(self, normalized: Dict) -> Dict:
        """Ensure website has http(s) prefix."""
        website = normalized.get("website")
        if website and isinstance(website, str):
            website = website.strip()
            if website and not website.startswith(("http://", "https://")):
                normalized["website"] = "https://" + website
        return normalized
