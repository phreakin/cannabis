# Cannabis Data Acquisition Guide

> How to find, evaluate, and onboard cannabis-related open data sources for each US state and federal agency.

---

## Table of Contents

1. [Overview & Strategy](#overview--strategy)
2. [Data Categories](#data-categories)
3. [API Formats & Connectors](#api-formats--connectors)
4. [State-by-State Status](#state-by-state-status)
5. [Federal Sources](#federal-sources)
6. [Adding a New Source](#adding-a-new-source)
7. [Field Mapping Reference](#field-mapping-reference)
8. [Authentication & API Keys](#authentication--api-keys)
9. [Rate Limits & Etiquette](#rate-limits--etiquette)
10. [Data Quality Checklist](#data-quality-checklist)

---

## Overview & Strategy

### Priority Order for Acquisition

1. **Active license registries** – who is legally operating right now
2. **Sales / tax data** – market size, revenue trends
3. **Lab test results** – product safety, potency
4. **Violations / enforcement** – compliance picture
5. **Legislation / rules** – regulatory changes
6. **Demographics / census** – market analysis overlays

### Where to Look First

| Source Type | URL Pattern |
|---|---|
| State open-data portal (Socrata) | `data.<state>.gov` |
| State regulatory agency | `<agency>.<state>.gov` |
| State legislature | `leg.<state>.gov` |
| USDA / DEA / FDA | `*.usda.gov`, `*.dea.gov` |
| Data.gov | `catalog.data.gov` |

---

## Data Categories

| Category Slug | Description | Key Fields |
|---|---|---|
| `licenses` | Cannabis business licenses | name, license_number, license_type, status, address, issued_date, expiry_date |
| `sales` | Retail sales & tax revenue | period, total_sales, tax_collected, store_count |
| `lab_results` | Product lab test reports | product_name, test_date, thc_pct, cbd_pct, contaminants_pass |
| `violations` | Enforcement actions | licensee, violation_date, violation_type, penalty |
| `legislation` | Bills, rules, regulations | bill_id, title, status, effective_date |
| `demographics` | Census, ZIP-level stats | zip_code, population, median_income |
| `hemp` | Hemp grower/processor licenses | farm_name, license_number, county, acreage |
| `other` | Anything that doesn't fit | varies |

---

## API Formats & Connectors

### Socrata (SODA)

Most state open-data portals use Socrata. The SODA API is consistent across all of them.

**Base URL pattern:** `https://data.<state>.gov/resource/<dataset-id>.json`

**Key params:**
```
$limit=5000          # rows per page
$offset=0            # pagination
$where=status='Active'   # filter
$order=:id           # sort (use for stable pagination)
$select=col1,col2    # field selection
```

**Format:** `soda`
**Pagination config:**
```json
{ "type": "offset", "page_size": 5000, "param": "$offset", "total_field": null }
```

**Getting an app token:**
Register at https://dev.socrata.com/register — free, greatly increases rate limits from ~1 req/s to ~10 req/s.

### Direct JSON API

Some state agencies host their own REST APIs.

**Format:** `json`
**Pagination config** (offset style):
```json
{ "type": "offset", "page_size": 100, "param": "page", "count_param": "per_page" }
```

### CSV Download

Static or scheduled CSV exports from agency websites.

**Format:** `csv`
**URL:** Direct link to `.csv` file
**Pagination:** None (single download)

### GeoJSON

Geographic data with embedded geometry.

**Format:** `geojson`

### XML / Other

For USDA and some legacy state systems.

**Format:** `xml`

---

## State-by-State Status

### ✅ Fully Legal (Adult-Use + Medical)

#### Alaska
- **Portal:** https://data.alaska.gov
- **Agency:** Marijuana Control Board — https://www.commerce.alaska.gov/web/amco/
- **Available data:**
  - [ ] License registry (MCB monthly PDF – no open API yet)
  - [ ] Convert PDF to structured data via script
- **Status:** 🔴 No open API – manual PDF extraction required

#### Arizona
- **Portal:** https://data.phx.gov (Phoenix only)
- **Agency:** Department of Health Services — https://www.azdhs.gov/licensing/medical-marijuana/
- **Available data:**
  - [ ] Medical dispensary list (DHS website, CSV download)
  - [ ] Adult-use licenses (AZ DHS open data pending)
- **API Token Env:** `AZ_APP_TOKEN`
- **Status:** 🟡 Partial – CSV only

#### California
- **Portal:** https://data.ca.gov
- **Agency:** DCC — https://cannabis.ca.gov
- **Available data:**
  - [x] Active license list — `https://data.ca.gov/dataset/cannabis-license-data`
  - [ ] Sales data (not public)
  - [ ] Lab results (not public – BCC holds)
- **Socrata dataset IDs:**
  - Licenses: `sty4-k3dz` (verify – IDs change on portal refresh)
- **API Token Env:** `CA_APP_TOKEN`
- **Field mapping:**
  ```yaml
  license_number: license_number
  name: business_dba_name
  license_type: license_type_name
  license_status: license_status
  address: premise_address
  city: premise_city
  zip_code: premise_zip
  county: county
  latitude: premise_latitude
  longitude: premise_longitude
  license_date: issue_date
  expiry_date: expiration_date
  ```
- **Status:** ✅ Active — seed from `config/sources.yaml`

#### Colorado
- **Portal:** https://data.colorado.gov
- **Agency:** MED — https://sbg.colorado.gov/med
- **Available data:**
  - [x] Active license list (Socrata)
  - [x] Monthly sales data by county (Socrata)
  - [ ] Lab results (not public)
- **Socrata dataset IDs:**
  - Licenses: verify at https://data.colorado.gov/browse?q=marijuana+license
  - Sales: verify at https://data.colorado.gov/browse?q=marijuana+sales
- **API Token Env:** `CO_APP_TOKEN`
- **Status:** ✅ Active

#### Illinois
- **Portal:** https://data.illinois.gov
- **Agency:** IDFPR — https://www.idfpr.com/profs/cannabis.asp
- **Available data:**
  - [x] Dispensary license list (Socrata)
  - [ ] Monthly sales/tax (IDREV reports – PDF only)
- **API Token Env:** `IL_APP_TOKEN`
- **Status:** ✅ Licenses active

#### Maine
- **Portal:** https://data.maine.gov
- **Agency:** OCP — https://www.maine.gov/dafs/ocp/adult-use-cannabis
- **Available data:**
  - [ ] Licensee list (OCP website, no Socrata yet)
- **Status:** 🔴 No open API

#### Massachusetts
- **Portal:** https://data.mass.gov
- **Agency:** CCC — https://masscannabiscontrol.com
- **Available data:**
  - [x] License list (Socrata) — `https://opendata.mass.gov/resource/<id>.json`
  - [x] Sales by municipality (Socrata)
  - [x] Market data reports
- **API Token Env:** `MA_APP_TOKEN`
- **Status:** ✅ Active — one of the best open-data states

#### Michigan
- **Portal:** https://data.michigan.gov
- **Agency:** MRA — https://www.michigan.gov/mra
- **Available data:**
  - [x] License registry (Socrata on LARA portal)
  - [ ] Sales data (not public yet)
- **Status:** ✅ Licenses active

#### Montana
- **Portal:** No dedicated Socrata portal
- **Agency:** Cannabis Control Division — https://mtrevenue.gov/cannabis/
- **Status:** 🔴 No open API – contact agency for data sharing

#### Nevada
- **Portal:** https://data.nv.gov
- **Agency:** CCB — https://ccb.nv.gov
- **Available data:**
  - [ ] License list (CCB website download – CSV)
  - [ ] Sales data (not public)
- **Status:** 🟡 CSV only

#### New Jersey
- **Portal:** https://data.nj.gov
- **Agency:** CRC — https://www.nj.gov/cannabis/
- **Available data:**
  - [x] License registry (Socrata)
- **Status:** ✅ Active

#### New Mexico
- **Portal:** https://data.nm.gov (limited)
- **Agency:** RLD Cannabis Control Division
- **Status:** 🔴 No open API

#### New York
- **Portal:** https://data.ny.gov
- **Agency:** OCM — https://cannabis.ny.gov
- **Available data:**
  - [x] Licensed dispensaries (Socrata)
  - [ ] Sales data (not yet public)
- **Status:** ✅ Active

#### Oregon
- **Portal:** https://data.oregon.gov
- **Agency:** OLCC — https://www.oregon.gov/olcc/marijuana/
- **Available data:**
  - [x] License registry (Socrata)
  - [x] Monthly sales data
  - [x] Lab results (partial)
- **API Token Env:** `OR_APP_TOKEN`
- **Status:** ✅ Active — excellent open data

#### Vermont
- **Portal:** No Socrata portal
- **Agency:** CCB — https://ccb.vermont.gov
- **Status:** 🔴 No open API

#### Virginia
- **Portal:** https://data.virginia.gov
- **Agency:** Vcannabis — https://www.vca.virginia.gov
- **Status:** 🟡 Recently launched, check for new datasets

#### Washington
- **Portal:** https://data.wa.gov | https://data.lcb.wa.gov
- **Agency:** LCB — https://lcb.wa.gov
- **Available data:**
  - [x] License list (Socrata – LCB portal)
  - [x] Monthly sales by county (Socrata)
  - [x] Violations / enforcement (Socrata)
  - [x] Lab results (Socrata – partial)
- **API Token Env:** `WA_APP_TOKEN`
- **Status:** ✅ Active — best overall open-data state

---

### 🏥 Medical Only States

#### Arkansas
- **Agency:** ABC — https://www.dfa.arkansas.gov/abc
- **Status:** 🔴 No open API

#### Florida
- **Portal:** https://data.fl.gov (limited)
- **Agency:** DOH OMMU — https://knowthefactsmmj.com
- **Available data:**
  - [ ] Dispensary locator (JSON from OMMU website)
  - [ ] Patient counts (public report, no API)
- **Status:** 🟡 Unofficial JSON scrape possible

#### Georgia
- **Status:** 🔴 Very limited – low-THC oil only, no open API

#### Louisiana
- **Status:** 🔴 No open API

#### Minnesota
- **Portal:** https://mn.gov/data
- **Agency:** MDH Office of Cannabis Management
- **Status:** 🟡 Recently transitioned to adult-use, new datasets emerging

#### Mississippi
- **Status:** 🔴 No open API

#### Missouri
- **Portal:** https://data.mo.gov
- **Agency:** DHSS Cannabis Regulation Center
- **Status:** ✅ Check Socrata for license data

#### New Hampshire
- **Status:** 🔴 No open API

#### North Dakota
- **Status:** 🔴 No open API

#### Ohio
- **Portal:** https://data.ohio.gov
- **Agency:** Division of Cannabis Control
- **Available data:**
  - [ ] License list (check data.ohio.gov)
- **Status:** 🟡 Adult-use recently passed, check for new data

#### Oklahoma
- **Portal:** https://data.ok.gov
- **Agency:** OMMA — https://omma.ok.gov
- **Available data:**
  - [x] License list (Socrata – one of the largest datasets)
  - [ ] Sales data (not public)
- **API Token Env:** `OK_APP_TOKEN`
- **Status:** ✅ Active — large dataset

#### Pennsylvania
- **Status:** 🔴 No Socrata portal, PDF reports only

#### Utah
- **Status:** 🔴 No open API

---

### 🚫 Not Yet Legal / No Data

Alabama, Idaho, Indiana, Iowa, Kansas, Kentucky, Nebraska, North Carolina, South Carolina, South Dakota, Tennessee, Texas, Wisconsin, Wyoming — **no cannabis data to collect**.

---

## Federal Sources

### USDA – Hemp Licensing

- **URL:** https://apps.fas.usda.gov/hemp-licensing/
- **API:** https://apps.fas.usda.gov/hemp-licensing/api/ (requires API key)
- **Env var:** `USDA_API_KEY`
- **Data:** Hemp grower/processor/handler licenses by state
- **Status:** ✅ API available — seed with `usda_hemp_licenses` source

### DEA – Schedule I/II

- **URL:** https://www.deadiversion.usdoj.gov/drugreg/
- **Data:** Registered researchers, Schedule I research registrations
- **Status:** 🔴 No open API – FOIA required

### FDA – Cannabis Research

- **URL:** https://www.fda.gov/news-events/public-health-focus/fda-and-cannabis
- **Status:** 🔴 Reports only

### Congress.gov – Legislation

- **URL:** https://api.congress.gov/
- **Env var:** `CONGRESS_API_KEY`
- **Data:** Bills with "cannabis" or "marijuana" keyword search
- **Source ID:** `federal_legislation`
- **Status:** ✅ API available

### Census Bureau – ACS Demographics

- **URL:** https://api.census.gov/data
- **Data:** ZIP/county population, income, demographics for market analysis
- **Status:** ✅ Free, no key required for basic queries

---

## Adding a New Source

### Step 1 – Find the dataset

1. Go to `data.<state>.gov` and search for "cannabis", "marijuana", "hemp", "dispensary", "license"
2. Note the **dataset ID** (last path segment of the URL, e.g. `abc1-2def`)
3. Test the API: `https://data.<state>.gov/resource/<dataset-id>.json?$limit=5`

### Step 2 – Inspect the fields

```bash
curl "https://data.<state>.gov/resource/<id>.json?\$limit=1" | python -m json.tool
```

Map the fields to the canonical schema using the Field Mapping Reference below.

### Step 3 – Add via the Web UI

1. Go to **Data Sources → Add Source**
2. Fill in:
   - **Source ID:** e.g. `mn_cannabis_licenses`
   - **Name:** e.g. `Minnesota Cannabis Licenses`
   - **State:** `MN`
   - **Category:** `licenses`
   - **Format:** `soda`
   - **URL:** `https://data.mn.gov/resource/<dataset-id>.json`
   - **Params:** `{"$limit": 5000, "$order": ":id"}`
   - **Field Mapping:** (JSON, see below)
   - **Rate Limit:** `30` (be conservative for new sources)

### Step 4 – Test

Click **▶ Run** and verify records appear in Browse Records.

### Step 5 – Add to YAML (optional, for persistence)

Add the source to `config/sources.yaml` so it survives database resets:

```yaml
- source_id: mn_cannabis_licenses
  name: Minnesota Cannabis Licenses
  state: MN
  category: licenses
  format: soda
  url: "https://data.mn.gov/resource/<id>.json"
  params:
    $limit: 5000
    $order: ":id"
  field_mapping:
    name: business_name
    license_number: license_id
    license_type: license_type
    city: city
    state: state
  tags: [licenses, adult-use]
```

### Step 6 – Create a Schedule

Go to **Schedules → Add Schedule** and set a daily or weekly collection.

---

## Field Mapping Reference

Canonical field → typical source field names across states:

| Canonical Field | Common Source Names |
|---|---|
| `name` | `business_name`, `licensee_name`, `dba_name`, `trade_name`, `retailer` |
| `license_number` | `license_number`, `license_id`, `license_no`, `lic_num` |
| `license_type` | `license_type`, `license_category`, `type`, `license_class` |
| `license_status` | `license_status`, `status`, `current_status`, `active` |
| `address` | `address`, `premise_address`, `street_address`, `location` |
| `city` | `city`, `premise_city`, `municipality` |
| `zip_code` | `zip`, `zip_code`, `postal_code`, `premise_zip` |
| `county` | `county`, `county_name` |
| `latitude` | `latitude`, `lat`, `geolocation.latitude` |
| `longitude` | `longitude`, `lon`, `lng`, `geolocation.longitude` |
| `phone` | `phone`, `phone_number`, `contact_phone` |
| `email` | `email`, `contact_email`, `email_address` |
| `website` | `website`, `url`, `web_site` |
| `license_date` | `issue_date`, `issued_date`, `license_date`, `effective_date` |
| `expiry_date` | `expiration_date`, `expiry_date`, `expire_date`, `renewal_date` |
| `record_date` | `date`, `as_of_date`, `report_date`, `updated_date` |

### GeoJSON / Nested Coordinates

For Socrata datasets with a `geolocation` field:

```json
{
  "latitude": "geolocation.latitude",
  "longitude": "geolocation.longitude"
}
```

For datasets with a `location` object:

```json
{
  "latitude": "location.coordinates.1",
  "longitude": "location.coordinates.0"
}
```

*(Note: GeoJSON is [longitude, latitude] order)*

---

## Authentication & API Keys

### Socrata App Token

1. Register at https://dev.socrata.com/register
2. Create an application, copy the **App Token**
3. Add to `.env`: `SOCRATA_APP_TOKEN=your-token-here`
4. The token is passed as the `X-App-Token` header automatically

### State-Specific Tokens

Some states have their own portal tokens (separate from the generic Socrata token):

```
AZ_APP_TOKEN=...    # data.phx.gov
CA_APP_TOKEN=...    # data.ca.gov
CO_APP_TOKEN=...    # data.colorado.gov
WA_APP_TOKEN=...    # data.wa.gov
OR_APP_TOKEN=...    # data.oregon.gov
OK_APP_TOKEN=...    # data.ok.gov
IL_APP_TOKEN=...    # data.illinois.gov
MA_APP_TOKEN=...    # opendata.mass.gov
```

---

## Rate Limits & Etiquette

| Scenario | Recommendation |
|---|---|
| Socrata without token | Max 1 request/second, ~1,000 rows/call |
| Socrata with token | Up to 10 req/s, 50,000 rows/call |
| State agency direct API | Start at 1 req/2 seconds, follow robots.txt |
| Large historical backfill | Run overnight, use `$offset` pagination |
| Real-time data | Prefer webhooks/notifications if offered |

**Best practices:**
- Use `$order=:id` on Socrata for stable pagination (avoids missed/duplicate rows)
- Add `User-Agent: CannabisDataAggregator/1.0 (Open Data Collector)` to all requests
- Set reasonable timeouts (60s default is usually fine)
- Respect `Retry-After` headers on 429 responses
- Cache responses locally – don't re-fetch unchanged data unnecessarily

---

## Data Quality Checklist

Before marking a source as production-ready:

### Completeness
- [ ] Records have `name` populated (>95%)
- [ ] Records have `license_number` populated (>90%)
- [ ] Records have `city` and `state` (>95%)
- [ ] Active/Inactive status is correctly mapped to `license_status`

### Geographic
- [ ] GPS coordinates populate `latitude`/`longitude` where available
- [ ] Coordinates are valid (lat: -90 to 90, lon: -180 to 180)
- [ ] Coordinates are within the expected state boundary

### Dates
- [ ] `license_date` parses correctly (ISO 8601 or MM/DD/YYYY)
- [ ] `expiry_date` is in the future for active licenses
- [ ] `record_date` reflects when the data was last updated

### Deduplication
- [ ] Source has a stable unique identifier (`source_record_id`)
- [ ] Confirm `record_hash` correctly detects changed records
- [ ] No duplicate `license_number` within a single source run

### Pagination
- [ ] Full dataset is collected (compare record count to agency website totals)
- [ ] Pagination loop terminates (no infinite loops on partial responses)

### Field Mapping
- [ ] All relevant source fields are mapped in `field_mapping`
- [ ] Unmapped fields still land in `record_data` JSON blob
- [ ] No important data is silently dropped

---

## Collection Status Summary

| State | Licenses | Sales | Labs | Violations | Notes |
|---|---|---|---|---|---|
| AK | 🔴 | 🔴 | 🔴 | 🔴 | PDF only |
| AZ | 🟡 | 🔴 | 🔴 | 🔴 | CSV download |
| CA | ✅ | 🔴 | 🔴 | 🔴 | Socrata active |
| CO | ✅ | ✅ | 🔴 | 🟡 | Socrata active |
| FL | 🟡 | 🔴 | 🔴 | 🔴 | Medical only, JSON scrape |
| IL | ✅ | 🔴 | 🔴 | 🔴 | Socrata active |
| MA | ✅ | ✅ | 🔴 | 🟡 | Best open-data state |
| MI | ✅ | 🔴 | 🔴 | 🔴 | Socrata active |
| MO | 🟡 | 🔴 | 🔴 | 🔴 | Check data.mo.gov |
| NJ | ✅ | 🔴 | 🔴 | 🔴 | Socrata active |
| NV | 🟡 | 🔴 | 🔴 | 🔴 | CSV only |
| NY | ✅ | 🔴 | 🔴 | 🔴 | Socrata active |
| OH | 🟡 | 🔴 | 🔴 | 🔴 | Adult-use new |
| OK | ✅ | 🔴 | 🔴 | 🔴 | Large dataset |
| OR | ✅ | ✅ | 🟡 | ✅ | Excellent open data |
| VA | 🟡 | 🔴 | 🔴 | 🔴 | Recently launched |
| WA | ✅ | ✅ | 🟡 | ✅ | Best overall |

**Legend:** ✅ Active collection &nbsp; 🟡 Partial/In-Progress &nbsp; 🔴 Not yet available

---

*Updated: 2026-02-22 | Cannabis Data Aggregator v1.0*
