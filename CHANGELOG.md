# Changelog — Cannabis Data Aggregator

All notable changes are documented here.
Format: `[Version] YYYY-MM-DD — Summary`

---

## [Unreleased] — 2026-02-25

### Added
- **Geocoding script** (`scripts/geocode_records.py`) — batch geocodes raw records with address data but no lat/lng using the free US Census Geocoder API (no API key required). Supports `--state`, `--limit`, and `--dry-run` flags.
- **Polished dark tech theme** for PHP web dashboard — redesigned CSS with deep dark backgrounds, vibrant colored stat cards (green/blue/teal/purple/orange/red) with glow effects, Inter font, glass-morphism surfaces, and refined sidebar.
- **`TODO.md`** and **`CHANGELOG.md`** added to project root.
- **`.gitignore`** and **`.gitattributes`** added for clean version control.

### Fixed
- **PHP map heredoc bug** — JavaScript template literals like `${variable}` inside a PHP heredoc were being executed as PHP function calls, causing a fatal runtime error that silently truncated the page response. Fixed by escaping all `${` as `\${` in `web/map.php`.
- **SQLAlchemy "Lost connection to MySQL"** — added `pool_pre_ping=True`, `pool_recycle=3600`, `pool_size=5`, and `max_overflow=10` to the SQLAlchemy engine for MySQL/MariaDB connections to survive idle connection drops.
- **Census Geocoder CSV format** — the `build_csv()` function was wrapping fields in double-quotes; the Census batch API requires unquoted plain CSV. Removed quotes from all CSV fields.
- **Census Geocoder response parser** — used naive `line.split(",")` which broke when address fields (echoed back in the API response) contained commas. Replaced with `csv.reader` for correct quoted-field parsing.
- **Duplicate CSS links** — `header.php` had 5 identical `<link>` tags for `custom.css`. Cleaned up to a single canonical reference.
- **Sidebar nav link classes** — removed redundant `link-light` classes that conflicted with the new theme's custom active/hover state styling.

### Changed
- **Dashboard stat cards** — updated from all-green single-color to a mixed palette: green (Total Records), blue (Active Sources), teal (GPS Records), purple (Runs Today), red (Failed 24h), orange (Active Schedules).
- **Sidebar** — refreshed with Inter font, branded icon badge, section separators, and active link left-border indicator.
- **`header.php`** — pinned Bootstrap to 5.3.3, Font Awesome to 6.5.2, Bootstrap Icons to 1.11.3 (was `@latest` which can break on CDN updates).

### Removed
- **`.venv/`** — Python virtual environment directory removed from project root (should never be committed).

---

## [1.0.0] — Initial Release

### Added
- Core collection engine with Socrata SODA, JSON REST, CSV, and GeoJSON collectors
- 50+ pre-configured US state/federal cannabis data sources (`config/sources.yaml`)
- APScheduler background job runner with cron and interval support
- PHP web dashboard: sources management, schedules, data browser, map view, exports, logs, scripts runner, settings
- Flask entity hub: companies, licenses, products, brands, retailers, tests, strains, lab results
- Hash-based deduplication to prevent duplicate records across runs
- Leaflet.js interactive map with MarkerCluster for GPS-tagged records
- Export formats: CSV, JSON, GeoJSON, Excel (multi-sheet by category)
- REST API endpoints for programmatic data access
- SQLite (default) and MySQL/MariaDB support via `DATABASE_URL`
- Docker Compose configuration for containerized deployment
- Makefile with common tasks (`make run`, `make setup`, `make seed`, `make export`)
