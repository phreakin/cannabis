# Cannabis Data Aggregator

Automated collection and management of US cannabis open data from state and federal APIs.
Aggregates dispensary locations, license data, sales figures, grower/processor records, and more
into a unified database — with a web dashboard for management and export.

---

## Features

- **50+ pre-configured data sources** across ~20 states + federal agencies
- **Multiple formats**: Socrata SODA, JSON REST API, CSV, GeoJSON
- **Automated scheduling** with cron and interval-based jobs (APScheduler)
- **Web dashboard** for monitoring, managing sources/schedules, and browsing data
- **Map view** of GPS-tagged records (Leaflet.js)
- **Export**: CSV, JSON, GeoJSON, Excel (multi-sheet by category)
- **REST API** for programmatic access to all collected data
- **Admin-configurable**: add/remove sources, change schedules, toggle sources
- **Hash-based deduplication** to avoid storing duplicate records
- **SQLite** by default, PostgreSQL supported via `DATABASE_URL`

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env .env
# Edit .env — at minimum set your Socrata app tokens for better rate limits
```

### 3. Initialize database

```bash
python main.py --mode setup
```

### 4. Seed sources and schedules from YAML config

```bash
python main.py --mode seed
```

### 5. Run

```bash
# Dashboard + background scheduler (recommended)
python main.py

# Or with make:
make run
```

Open http://localhost:5000 in your browser.

---

## Usage

### Run modes

```bash
python main.py                          # Dashboard + Scheduler (default)
python main.py --mode dashboard         # Web dashboard only
python main.py --mode scheduler         # Background scheduler only
python main.py --mode setup             # Initialize database
python main.py --mode seed              # Load sources/schedules from YAML
python main.py --mode seed --force      # Re-seed, overwriting existing

# Trigger collection manually
python main.py --mode collect --source co_med_licensees
python main.py --mode collect --all
python main.py --mode collect --all --state CO
python main.py --mode collect --all --category dispensary
```

### Scripts

```bash
# Direct script access
python scripts/setup_db.py --check                    # DB health check
python scripts/seed_sources.py --dry-run              # Preview seed
python scripts/seed_sources.py --sources-only --force # Re-seed sources only
python scripts/run_collector.py --list                # List enabled sources
python scripts/run_collector.py --source co_med_licensees
python scripts/run_collector.py --all --state WA

# Export data
python scripts/export_data.py --format csv
python scripts/export_data.py --format geojson --state CO
python scripts/export_data.py --format xlsx --category dispensary
python scripts/export_data.py --format json --output my_export.json --limit 50000
```

### Make targets

```bash
make install       # pip install -r requirements.txt
make setup         # Initialize database
make seed          # Seed sources and schedules
make run           # Start dashboard + scheduler
make dashboard     # Dashboard only
make scheduler     # Scheduler only
make collect       # Collect all enabled sources
make collect SOURCE=co_med_licensees   # Collect specific source
make export        # Export to CSV
make clean         # Remove cached files
```

---

## Configuration

### Environment variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///data/cannabis_aggregator.db` | Database connection |
| `FLASK_HOST` | `0.0.0.0` | Dashboard host |
| `FLASK_PORT` | `5000` | Dashboard port |
| `FLASK_SECRET_KEY` | `dev-secret-key-...` | Session secret |
| `FLASK_DEBUG` | `false` | Debug mode |
| `SCHEDULER_TIMEZONE` | `America/Chicago` | Cron timezone |
| `SCHEDULER_MAX_WORKERS` | `5` | Concurrent collection threads |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CO_APP_TOKEN` | — | Colorado Socrata app token |
| `WA_APP_TOKEN` | — | Washington Socrata app token |
| *(see .env.example for all)* | | |

### `config/sources.yaml`

Defines all data sources. Key fields per source:

```yaml
- id: co_med_licensees            # Unique identifier
  name: "Colorado MED Licensees"
  state: CO
  agency: Colorado MED
  category: licensee
  format: soda                    # soda | json | csv | geojson
  url: https://data.colorado.gov/resource/sqs8-2una.json
  enabled: true
  api_key_env: CO_APP_TOKEN       # Optional env var for auth
  pagination:
    type: offset                  # offset | page | cursor | link
    page_size: 1000
  field_mapping:                  # Maps source fields → standard schema
    name: licensee_name
    license_number: license_no
    address: street_address
    city: city
    state: state
    zip_code: zip
    latitude: latitude
    longitude: longitude
```

### `config/schedules.yaml`

```yaml
- id: sched_co_med_weekly
  name: "Colorado MED Licensees - Weekly"
  source_id: co_med_licensees
  enabled: true
  schedule_type: cron
  cron:
    minute: 0
    hour: 2
    day_of_week: sun    # Every Sunday at 2:00 AM
  priority: 2
```

---

## Data Sources Included

### Federal
| Source | Format | Category |
|---|---|---|
| USDA AMS Hemp Producers | CSV | Hemp |
| DEA Registrant Locations | JSON | Pharmacy |
| ProPublica Congress API | JSON | Legislation |
| FDA NDC Drug Products | JSON | Pharmacy |

### States (sample)
| State | Agency | Data |
|---|---|---|
| Colorado | MED | Licensees, Sales, Market Rates |
| Washington | WSLCB | Licensees, Sales, Violations |
| Oregon | OLCC | Licensees, GeoJSON Dispensaries |
| California | DCC | Licensees |
| Oklahoma | OMMA | Dispensaries, Growers, Processors, Transporters |
| Illinois | IDFPR | Cannabis Licenses, Monthly Sales |
| Massachusetts | CCC | Licensees, Weekly Sales |
| Michigan | CRA | Licenses, Sales |
| New York | OCM | All Licenses, Dispensaries |
| New Jersey | CRC | Licenses |
| Alaska | AMCO | License Database |
| Connecticut | DCP | Cannabis Licenses |
| DC | ABCA | Cannabis Licenses |
| New Mexico | RLD | Cannabis Licenses |
| *(+ 10 more states)* | | |

### Multi-state
| Source | Format | Notes |
|---|---|---|
| OpenStreetMap/Overpass | GeoJSON | Free dispensary POI data |
| NCSL Cannabis Laws | JSON | State law tracker |

---

## Dashboard Pages

| URL | Description |
|---|---|
| `/` | Dashboard overview with stats and charts |
| `/sources` | Manage data sources (add, edit, toggle, run) |
| `/schedules` | Manage collection schedules |
| `/data` | Browse collected records with filters |
| `/data/map` | Leaflet map of GPS-tagged locations |
| `/data/logs` | Collection run logs |
| `/data/exports` | Export data + API documentation |
| `/data/settings` | App settings |

---

## REST API

Base URL: `http://localhost:5000/api`

```
GET  /api/records                    Paginated records (filters: state, category, source_id, has_gps, search)
GET  /api/records/{id}               Single record
GET  /api/records/geojson            GeoJSON FeatureCollection of GPS records
GET  /api/records/export             File download (format=csv|json|geojson)
GET  /api/sources                    List sources
POST /api/sources                    Create source
PUT  /api/sources/{id}               Update source
POST /api/sources/{id}/toggle        Enable/disable
POST /api/sources/{id}/run           Trigger collection now
GET  /api/schedules                  List schedules
POST /api/schedules                  Create schedule
PUT  /api/schedules/{id}             Update schedule
POST /api/schedules/{id}/toggle      Enable/disable
GET  /api/runs                       Collection run history
GET  /api/logs                       Log entries
GET  /api/stats/categories           Record counts by category
GET  /api/stats/states               Record counts by state
POST /api/scheduler/sync             Sync scheduler jobs from DB
POST /api/seed                       Seed from YAML config
```

---

## Adding a New Data Source

1. **Add to `config/sources.yaml`**:
   ```yaml
   - id: my_state_licenses
     name: "My State Cannabis Licenses"
     state: XX
     agency: My State Agency
     category: licensee
     format: soda        # or csv, json, geojson
     url: https://data.mystate.gov/resource/xxxx-xxxx.json
     enabled: true
     pagination:
       type: offset
       page_size: 1000
     field_mapping:
       name: business_name
       license_number: license_id
       city: city
       state: state_code
   ```

2. **Add a schedule to `config/schedules.yaml`**:
   ```yaml
   - id: sched_my_state_weekly
     name: "My State Licenses - Weekly"
     source_id: my_state_licenses
     enabled: true
     schedule_type: cron
     cron:
       minute: 0
       hour: 3
       day_of_week: sun
   ```

3. **Seed the database**:
   ```bash
   python main.py --mode seed
   # or in the dashboard: Settings → Seed Sources from YAML
   ```

4. **Test with a manual collection**:
   ```bash
   python scripts/run_collector.py --source my_state_licenses
   ```

---

## Project Structure

```
cannabis-data-aggregator/
├── main.py                    Entry point
├── requirements.txt
├── .env.example               Environment template
├── docker-compose.yml
├── Makefile
├── config/
│   ├── sources.yaml           Data source definitions (50+ sources)
│   ├── schedules.yaml         Collection schedules
│   └── settings.yaml          Global settings
├── src/
│   ├── collectors/
│   │   ├── base.py            BaseCollector (HTTP, rate limiting, retries)
│   │   ├── api_collector.py   JSON REST + Socrata SODA
│   │   ├── csv_collector.py   CSV/TSV with auto-encoding detection
│   │   └── geojson_collector.py  GeoJSON + Overpass API
│   ├── processors/
│   │   └── normalizer.py      Field mapping, standardization
│   ├── scheduler/
│   │   └── manager.py         APScheduler + collection job runner
│   ├── storage/
│   │   ├── models.py          SQLAlchemy models
│   │   └── database.py        DB init, session management
│   └── dashboard/
│       ├── app.py             Flask app factory
│       ├── routes/            Blueprint routes
│       ├── templates/         Jinja2 HTML templates
│       └── static/            CSS, JavaScript
├── scripts/
│   ├── setup_db.py            Database initialization
│   ├── seed_sources.py        Seed from YAML
│   ├── run_collector.py       CLI collection runner
│   └── export_data.py         CLI data exporter
├── data/
│   ├── raw/                   Temporary raw files
│   └── processed/             Exported data files
└── logs/                      Application logs
```

---

## Docker

```bash
# SQLite (default)
docker compose up

# PostgreSQL
docker compose --profile postgres up

# See pgAdmin at http://localhost:5050
```

---

## License

MIT
