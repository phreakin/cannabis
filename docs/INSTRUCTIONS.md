# Cannabis Data Aggregator – Web UI Guide

> **Dashboard URL:** `http://<host>:<port>/` (default `http://10.0.0.2:5000/`)
> **Tech stack:** PHP 8+ · MySQL 8 · Bootstrap 5 · Python 3 (Flask / APScheduler)

---

## Table of Contents

1. [Quick-Start Setup](#quick-start-setup)
2. [Dashboard Overview](#dashboard-overview)
3. [Data Sources](#data-sources)
4. [Schedules](#schedules)
5. [Browse Records](#browse-records)
6. [Map View](#map-view)
7. [Export](#export)
8. [Logs](#logs)
9. [Scripts](#scripts)
10. [Settings](#settings)
11. [REST API Reference](#rest-api-reference)
12. [Troubleshooting](#troubleshooting)

---

## Quick-Start Setup

### 1. Environment

Copy `.env.example` (or `.env`) and fill in your values:

```bash
cp .env .env.local   # keep your secrets out of git
```

Key variables:

| Variable | Purpose |
|---|---|
| `MYSQL_HOST` / `MYSQL_PORT` | MySQL server address |
| `MYSQL_DATABASE` | Database name (default `cannabis_data`) |
| `MYSQL_USER` / `MYSQL_PASSWORD` | MySQL credentials |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Dashboard login |
| `APP_HOST` / `APP_PORT` | Flask bind address |

### 2. Database

```bash
# Create schema (run once)
mysql -u root -p < schema.sql

# Or via Python setup mode
python main.py --mode setup
```

### 3. Seed Sources

```bash
python main.py --mode seed
```

This imports all data sources from `config/sources.yaml` into the `data_sources` table.

### 4. Start the Application

```bash
python main.py          # starts Flask + APScheduler together
```

Or for development:

```bash
python main.py --mode web       # web only
python main.py --mode scheduler # scheduler only
```

### 5. Web Interface (PHP)

The PHP web UI in `web/` can be served separately via Apache/Nginx/PHP built-in server:

```bash
cd web
php -S 10.0.0.2:8080
```

Make sure `web/includes/config.php` can read your `.env` file from the project root.

---

## Dashboard Overview

**URL:** `index.php`

The dashboard provides a real-time summary of the system:

| Card | Description |
|---|---|
| **Total Records** | All rows in `raw_records` |
| **Active Sources** | Enabled data sources |
| **GPS Records** | Records with latitude/longitude |
| **Collection Runs** | Total runs ever executed |

### Charts

- **Daily Runs (7 days)** – Bar chart of collection runs per day, colour-coded by status
- **Records by State** – Doughnut chart showing top states by record count
- **Records by Category** – Breakdown by data category (licenses, sales, violations, etc.)

### Recent Runs Table

Shows the last 10 collection runs with source name, start time, duration, status badge, and record counts.

---

## Data Sources

**URL:** `sources.php`

Lists every data source configured in the system.

### Columns

| Column | Description |
|---|---|
| Source ID | Unique string identifier (e.g. `wa_liquor_licenses`) |
| Name | Human-readable name |
| State | Two-letter state abbreviation |
| Category | Data category |
| Format | `soda` / `csv` / `json` / `geojson` / `xml` |
| Enabled | Green = active, Red = disabled |
| Last Run | Timestamp of last collection |
| Records | Total records stored |
| Actions | Edit / Run / Enable-Disable / Delete |

### Adding a New Source

1. Click **Add Source** (top right)
2. Fill in the form:
   - **Source ID** – unique slug, lowercase with underscores
   - **Name** – display name
   - **State** – two-letter code (or `FED` for federal)
   - **Category** – `licenses`, `sales`, `violations`, `lab_results`, `legislation`, `demographics`, `other`
   - **Format** – how the remote API delivers data
   - **URL** – API endpoint or direct download link
   - **Rate Limit (RPM)** – requests per minute (default 60)
   - **Timeout** – HTTP request timeout in seconds
3. Click **Save Source**

### Running a Collection

- Click the **▶ Run** button next to any source to trigger an immediate collection
- Status updates appear as a toast notification
- Check **Logs** or the Dashboard Recent Runs table for results

### JSON Fields

Advanced sources can use these JSON fields:

- **Params** – default query parameters (e.g. `{"$limit": 5000, "$where": "license_status='Active'"}`)
- **Headers** – custom HTTP headers
- **Pagination** – pagination config (e.g. `{"type": "offset", "page_size": 5000}`)
- **Field Mapping** – map source field names to canonical names

---

## Schedules

**URL:** `schedules.php`

Schedules control when each source's data is automatically collected.

### Schedule Types

| Type | Description |
|---|---|
| **Cron** | Standard cron expression (minute / hour / day / month / weekday) |
| **Interval** | Every N minutes / hours / days / weeks |

### Priorities

- **1 – High** – runs first when multiple jobs are queued
- **2 – Normal** – default
- **3 – Low** – runs last

### Adding a Schedule

1. Click **Add Schedule**
2. Select the **Data Source**
3. Choose **Interval** or **Cron**
4. Set the timing (e.g. every 24 hours, or `0 3 * * *` for 3 AM daily)
5. Click **Save**

### Common Cron Examples

| Cron | Meaning |
|---|---|
| `0 3 * * *` | Daily at 3:00 AM |
| `0 */6 * * *` | Every 6 hours |
| `0 2 * * 1` | Mondays at 2:00 AM |
| `0 1 1 * *` | 1st of every month at 1:00 AM |

---

## Browse Records

**URL:** `data.php`

Full-text searchable, filterable table of all collected records.

### Filters

| Filter | Description |
|---|---|
| **Search** | Searches name, license number, city, address |
| **State** | Filter by state |
| **Category** | Filter by data category |
| **Status** | Filter by license status |
| **Date From / To** | Filter by `record_date` |

### Columns

Name · License # · Type · Status · City · State · Date · Source

### Detail View

Click any row to open a modal with full record details including:
- All standard fields
- Raw JSON data (collapsible)
- GPS coordinates (if available)

### Exporting Filtered Results

Use the **Export CSV** button above the table to download the current filtered set.

---

## Map View

**URL:** `map.php`

Interactive Leaflet map showing all records with GPS coordinates.

- **Blue markers** – individual records
- **Clustering** – markers cluster at high zoom-out levels
- Click a marker to see name, license type, status, city, and coordinates

### Filters

Same state/category filters as Browse Records. Changes reload the markers.

---

## Export

**URL:** `exports.php`

Bulk-export the database in multiple formats.

### Formats

| Format | Description |
|---|---|
| **CSV** | Comma-separated, UTF-8 BOM, all standard columns |
| **JSON** | Array of record objects |
| **GeoJSON** | Feature collection for GPS-tagged records only |

### Options

- **State** – filter to one state (or all)
- **Category** – filter to one category (or all)
- **GPS Only** – include only records with coordinates
- **Max Rows** – limit row count (0 = unlimited, up to 100,000 hard cap)

### REST Export

```
GET api/records.php?action=export&fmt=csv&state=WA&category=licenses
GET api/records.php?action=geojson&state=CO
```

---

## Logs

**URL:** `logs.php`

View the collection log stream written during every run.

### Log Levels

| Level | Colour | Meaning |
|---|---|---|
| DEBUG | Grey | Verbose detail (pagination, field mapping) |
| INFO | White | Normal operation messages |
| WARNING | Yellow | Non-fatal issues (missing fields, rate limit) |
| ERROR | Red | Failed requests, parse errors, DB errors |

### Filters

- **Level** – minimum level to show
- **Source** – filter to one data source
- **Date From / To** – time range

### Purging Logs

Click **Purge Old Logs** to delete logs older than N days (configurable in Settings).

---

## Scripts

**URL:** `scripts.php`

The script manager lets you create, edit, and run Python scripts directly from the browser.

### Script Directories

Scripts are discovered from these paths (relative to project root):

- `scripts/` – general-purpose scripts
- `src/` – source modules
- `src/collectors/` – collector scripts

### Creating a Script

1. Click **New Script**
2. Choose a directory
3. Enter a filename (`.py` extension added automatically)
4. Write your code in the CodeMirror editor (Python syntax highlighting)
5. Click **Save**

### Editing a Script

Click **Edit** next to any listed script.

### Running a Script

Click **▶ Run** from the list or from inside the editor.

- Output (stdout + stderr) appears in the console panel below the editor
- Execution timeout: **120 seconds**
- Scripts run as the same user as the web server / PHP process
- Working directory is the project root

> **Security:** Only `.py` files within the allowed directories can be run. Path traversal attempts are blocked.

### Deleting a Script

Click **Delete** and confirm the dialog.

---

## Settings

**URL:** `settings.php`

Application-wide configuration stored in the `app_settings` database table.

| Setting | Default | Description |
|---|---|---|
| `collection_timeout` | 60 | HTTP request timeout (seconds) |
| `collection_rate_limit_rpm` | 60 | Requests per minute |
| `collection_max_retries` | 3 | Retry attempts on failure |
| `collection_retry_delay` | 5 | Seconds between retries |
| `storage_dedup_enabled` | true | Deduplicate records by hash |
| `storage_max_records` | 0 | Max records per source (0=unlimited) |
| `log_retention_days` | 90 | Days to keep logs |
| `log_level` | INFO | Minimum log level to store |
| `dashboard_records_per_page` | 50 | Rows per page in Browse Records |
| `scheduler_enabled` | true | Enable background scheduler |

---

## REST API Reference

All API endpoints are under `api/` relative to the web root.

### Records

| Method | Endpoint | Description |
|---|---|---|
| GET | `api/records.php` | List records (paginated, filterable) |
| GET | `api/records.php?id=N` | Get single record by ID |
| GET | `api/records.php?action=export&fmt=csv` | Export as CSV |
| GET | `api/records.php?action=export&fmt=json` | Export as JSON |
| GET | `api/records.php?action=geojson` | GeoJSON feature collection |

**Query parameters for list/export:**

| Param | Type | Description |
|---|---|---|
| `state` | string | Filter by state code |
| `category` | string | Filter by category |
| `status` | string | Filter by license status |
| `search` | string | Full-text search |
| `date_from` | YYYY-MM-DD | Record date from |
| `date_to` | YYYY-MM-DD | Record date to |
| `limit` | int | Max rows (default 50) |
| `offset` | int | Pagination offset |

### Sources

| Method | Endpoint | Description |
|---|---|---|
| GET | `api/sources.php` | List all sources |
| GET | `api/sources.php?id=N` | Get one source |
| POST | `api/sources.php` | Create source |
| PUT | `api/sources.php?id=N` | Update source |
| DELETE | `api/sources.php?id=N` | Delete source |
| POST | `api/sources.php?action=run&id=ID` | Trigger collection |
| POST | `api/sources.php?action=enable&id=ID` | Enable source |
| POST | `api/sources.php?action=disable&id=ID` | Disable source |

### Schedules

| Method | Endpoint | Description |
|---|---|---|
| GET | `api/schedules.php` | List schedules |
| POST | `api/schedules.php` | Create schedule |
| PUT | `api/schedules.php?id=N` | Update schedule |
| DELETE | `api/schedules.php?id=N` | Delete schedule |
| POST | `api/schedules.php?action=enable&id=ID` | Enable schedule |
| POST | `api/schedules.php?action=disable&id=ID` | Disable schedule |

### Runs & Logs

| Method | Endpoint | Description |
|---|---|---|
| GET | `api/runs.php` | List collection runs |
| GET | `api/runs.php?id=N` | Run detail + logs |
| POST | `api/runs.php?action=purge&days=N` | Purge old runs |
| GET | `api/logs.php` | List logs |
| POST | `api/logs.php?action=purge&days=N` | Purge old logs |

### Stats

| Method | Endpoint | Description |
|---|---|---|
| GET | `api/stats.php` | Full dashboard stats |
| GET | `api/stats.php?type=states` | Counts by state |
| GET | `api/stats.php?type=categories` | Counts by category |
| GET | `api/stats.php?type=formats` | Counts by format |
| GET | `api/stats.php?type=daily_runs` | Runs per day (30d) |

### Scripts

| Method | Endpoint | Description |
|---|---|---|
| GET | `api/scripts.php?action=list` | List available scripts |
| GET | `api/scripts.php?action=read&path=...` | Read script content |
| POST | `api/scripts.php?action=save` | Save (create/update) script |
| POST | `api/scripts.php?action=run` | Run a script |
| DELETE | `api/scripts.php?path=...` | Delete a script |

---

## Troubleshooting

### Database connection fails

1. Check `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD` in `.env`
2. Verify MySQL is running: `mysqladmin -u phreakin -p ping -h 10.0.0.2`
3. Check that `cannabis_data` database exists: `SHOW DATABASES;`
4. Verify PHP PDO MySQL extension is enabled: `php -m | grep pdo`

### "WEB_BASE" path errors (broken links/assets)

The `WEB_BASE` constant is computed automatically from `$_SERVER['SCRIPT_NAME']`. If assets return 404:

1. Check the `web/` directory is served at the right path
2. Verify `config.php` is included before any output
3. Check Apache/Nginx rewrite rules aren't stripping path prefixes

### Scheduler not running

1. Confirm `SCHEDULER_ENABLED=true` in `.env`
2. Check `python main.py` is running (not just the PHP side)
3. Inspect `logs/` directory for scheduler errors
4. Manually trigger a collection from the Sources page to verify connectivity

### Collections return no records

1. Check **Logs** for the specific source – look for HTTP errors or empty response messages
2. Verify the source URL is still valid (APIs change)
3. Test the URL directly in a browser or with `curl`
4. Check rate limits – some Socrata APIs throttle un-authenticated requests

### PHP warnings in forms

If you see PHP notices about undefined array keys:

- Ensure you're on PHP 8.0+
- The edit forms use `$src ??= [];` to handle null-safe access

### Export file is empty

- Verify records exist: go to Browse Records and check filters
- Check `MAX_EXPORT_ROWS` constant in `config.php` (default 100,000)
- For GeoJSON, confirm records have `latitude`/`longitude` populated

---

*Generated: 2026-02-22 | Cannabis Data Aggregator v1.0*
