# TODO — Cannabis Data Aggregator

> Last updated: 02-25-2026

---

## 🔴 High Priority

- [ ] **State data acquisition fixes** — audit each configured state source; ensure endpoints are live, authentication tokens are valid, and pagination is working
  - MA (Socrata) — ✅ Working, 1,693 records with GPS coords
  - NY (Socrata) — ✅ Working, 5,420 records; geocoding in progress
  - CT (Socrata) — ⚠️  Working, 112 records; no address fields for geocoding
  - All other configured states — need full validation pass
- [ ] **Auto-geocode after collection** — hook `geocode_records.py` into the NY (and other) collector pipeline so new records get geocoded automatically after each run
- [ ] **CT address data** — CT source may not include address fields; investigate alternative CT endpoints that provide location data
- [ ] **Acquire More Data Sources** — research and add more state and federal sources to `config/sources.yaml` to expand coverage beyond the initial few states
- [ ] **Data quality review** — manually review a sample of collected records for each source to identify common issues (missing fields, inconsistent formatting) and adjust collectors/deduplication logic accordingly
- [ ] **PHP dashboard bug fixes** — address any critical bugs in the web dashboard that hinder usability (e.g. map loading issues, export errors)
- [ ] **Documentation** — update the README with clear setup instructions, usage examples, and troubleshooting tips to make it easier for new users to get started

---

## 🟡 Medium Priority

- [ ] **CSV import for Entity Hub** — add ability to upload a CSV file and map columns to entity fields in the web dashboard
- [ ] **Flask entity pages theming** — apply the polished dark tech theme to the Flask-based entity hub at port 5000 to match the PHP dashboard
- [ ] **Increase geocode coverage** — run geocoder for all states missing lat/lng, not just NY; add `--state ALL` batch job to Makefile
- [ ] **Map clustering performance** — test map with 5,000+ markers; consider server-side GeoJSON simplification for large datasets
- [ ] **Export improvements** — add date-range filter to exports; support GeoJSON export with only geocoded records
- [ ] **Source health checks** — add a "Test Connection" button per source in the dashboard that runs a dry-collect and reports back status/record count
- [ ] **Deduplication tuning** — review the hash key fields used per source; some sources may have changed their record format
- [ ] **Dark Color Theme/Palette** - add a dark color theme to the PHP dashboard and Python entity hub
- [ ] **Add Fira fon family to site** - add Fira Sans and Fira Mono fonts to the site as defaults for the PHP dashboard and Python entity hub

---

## 🟢 Lower Priority / Nice to Have

- [ ] **Release packaging** — clean directory structure, finalize `.gitignore`, create proper versioned release archive
- [ ] **Docker polish** — verify `docker-compose.yml` fully works end-to-end including web and PHP dashboard
- [ ] **API rate limiting** — add per-source configurable rate limits and retry backoff for flaky endpoints
- [ ] **Notification system** — email/webhook alerts when collection runs fail or record counts drop unexpectedly
- [ ] **Historical data trends** — store per-run record counts over time to chart data growth per state/source
- [ ] **Data quality scoring** — flag records missing key fields (address, license number, category) for review
- [ ] **Multi-user auth** — add simple HTTP Basic or token auth to the PHP dashboard for production deployments
- [ ] **README updates** — add screenshots, expand setup docs for MySQL setup, document the geocoding script
- [ ] **Git Update Scripts** - add a `git-update.sh` script to automate the process of pulling the latest code from GitHub
- [ ] **Directory clean-up** - Clean up directory structure and remove unnecessary files
- [ ] **Add CI/CD pipeline** - Add a CI/CD pipeline to automate the deployment process
- [ ] **Add unit tests** - Add unit tests to improve code quality and maintainability
- [ ] **Add documentation** - Add documentation to the project to help users understand how to use the tool effectively
- [ ] **Add support for other data formats** - Add support for other data formats (e.g. XML, JSONL)
- [ ] **Add support for other data sources** - Add support for other data sources (e.g. 3rd party APIs)
- [ ] **Add support for other geocoding services** - Add support for other geocoding services (e.g. Nominatim)
- [ ] **Add support for other data collection methods** - Add support for other data collection methods (e.g. scraping, API calls, etc.)

---

## ✅ Completed

- [x] Core collection engine (Socrata SODA, JSON, CSV, GeoJSON collectors)
- [x] 50+ pre-configured state/federal sources in `config/sources.yaml`
- [x] PHP web dashboard (sources, schedules, data browser, map, exports, logs)
- [x] Flask entity hub (companies, licenses, products, etc.)
- [x] Hash-based deduplication
- [x] APScheduler background job runner
- [x] Leaflet.js map view with MarkerCluster
- [x] CSV/JSON/GeoJSON/Excel export
- [x] SQLite + MySQL/MariaDB support
- [x] Geocoding script using US Census Geocoder batch API (`scripts/geocode_records.py`)
- [x] Fixed PHP map heredoc template literal escape bug
- [x] Fixed SQLAlchemy MySQL connection pool settings (pool_pre_ping, pool_recycle)
- [x] Polished dark tech theme for PHP dashboard
- [x] Removed `.venv` from project directory
- [x] Added `Makefile` for common commands (e.g. `make collect`, `make geocode`, `make run-web`, etc.)
- [x] Added `requirements.txt` for Python dependencies
- [x] Added `docker-compose.yml` for easy local deployment of web and PHP dashboard
- [x] Added `config/sources.yaml` for easy configuration of data sources without code changes
- [x] Added logging to collection and geocoding processes for better visibility into operations
- [x] Added error handling and retry logic to collectors for improved robustness against transient API issues
- [x] Added deduplication logic to geocoding script to avoid re-geocoding records that have already been processed
- [x] Added support for geocoding multiple states in a single batch job via command-line argument
- [x] Added export filters to allow users to export only geocoded records or records from specific states/sources
- [x] Added various git related files to the project
- [x] Removed unnecessary files from the project directory
- [x] Updated LICENSE file with correct year and author information
- [x] Updated README with installation instructions and usage examples
- [x] Updated `Makefile` with new commands and improved error handling
- [x] Added a .env.example file to the project directory with default environment variables
- [x] Added a .gitignore file to ignore unnecessary files and directories
- [x] Added a .dockerignore file to ignore unnecessary files and directories when building Docker images
- [x] Added a .editorconfig file to enforce consistent coding styles across the project
- [x] Added a .flake8 file to configure flake8 for Python linting
- [x] Added a .pylintrc file to configure pylint for Python linting
- [x] Added a .pyproject.toml file to configure Python project settings
- [x] Added a .prettierrc file to configure prettier for JavaScript linting
- [x] Added a .stylelintrc file to configure stylelint for CSS linting
- [x] Added a .vscode/settings.json file to configure VS Code settings
