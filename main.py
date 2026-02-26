#!/usr/bin/env python3
"""
Cannabis Data Aggregator — Main Entry Point

Modes:
    dashboard   Run only the Flask dashboard (no background scheduler)
    scheduler   Run only the background scheduler (no web server)
    all         Run both dashboard and scheduler together (default)
    collect     Run a one-time collection for one or all sources
    setup       Initialize/verify the database
    seed        Seed sources and schedules from YAML config

Usage:
    python main.py                                # run dashboard + scheduler
    python main.py --mode dashboard               # dashboard only
    python main.py --mode scheduler               # scheduler only
    python main.py --mode collect --source co_med_licensees
    python main.py --mode collect --all           # run all enabled sources
    python main.py --mode setup
    python main.py --mode seed
    python main.py --mode seed --force            # overwrite existing records
"""
import argparse
import logging
import os
import sys
import signal
import threading

# ── Environment ─────────────────────────────────────────────────────────────
# Load .env from the project root (same dir as this file), regardless of CWD.
try:
    from pathlib import Path as _Path
    from dotenv import load_dotenv
    load_dotenv(_Path(__file__).resolve().parent / ".env", override=False)
except ImportError:
    pass

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FILE  = os.environ.get("LOG_FILE", os.path.join("logs", "app.log"))

os.makedirs("logs", exist_ok=True)
os.makedirs(os.path.join("data", "raw"), exist_ok=True)
os.makedirs(os.path.join("data", "processed"), exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE),
    ],
)
logger = logging.getLogger(__name__)


def get_db_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///data/cannabis_aggregator.db")


def ensure_db_dir(db_url: str):
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)


# ── Mode: setup ──────────────────────────────────────────────────────────────
def run_setup():
    db_url = get_db_url()
    ensure_db_dir(db_url)
    from src.storage.database import init_db, health_check, get_table_counts
    logger.info(f"Setting up database: {db_url}")
    init_db(db_url)
    ok = health_check()
    if ok:
        counts = get_table_counts()
        logger.info("Database setup complete. Table counts: %s", counts)
        for t, c in counts.items():
            print(f"  {t}: {c:,} rows")
    else:
        logger.error("Database health check failed after setup")
        sys.exit(1)


# ── Mode: seed ───────────────────────────────────────────────────────────────
def run_seed(force: bool = False):
    import subprocess
    cmd = [sys.executable, "scripts/seed_sources.py"]
    if force:
        cmd.append("--force")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


# ── Mode: collect ─────────────────────────────────────────────────────────────
def run_collect(source_ids: list = None, run_all: bool = False,
                state: str = None, category: str = None):
    import subprocess
    cmd = [sys.executable, "scripts/run_collector.py"]
    if run_all:
        cmd.append("--all")
        if state:    cmd += ["--state", state]
        if category: cmd += ["--category", category]
    elif source_ids:
        cmd += ["--source"] + source_ids
    else:
        print("Error: specify --source SOURCE_ID or --all")
        sys.exit(1)
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


# ── Mode: scheduler ───────────────────────────────────────────────────────────
def run_scheduler_only():
    db_url = get_db_url()
    ensure_db_dir(db_url)
    from src.storage.database import init_db
    from src.scheduler.manager import SchedulerManager

    init_db(db_url)
    manager = SchedulerManager()
    manager.start()
    logger.info("Scheduler running. Press Ctrl+C to stop.")

    stop_event = threading.Event()

    def _shutdown(signum, frame):
        logger.info("Shutdown signal received, stopping scheduler...")
        manager.stop()
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    stop_event.wait()
    logger.info("Scheduler stopped.")


# ── Mode: dashboard ───────────────────────────────────────────────────────────
def run_dashboard_only():
    db_url = get_db_url()
    ensure_db_dir(db_url)
    from src.storage.database import init_db
    from src.dashboard.app import create_app

    init_db(db_url)
    app = create_app()

    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    logger.info(f"Dashboard starting on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False)


# ── Mode: all (default) ───────────────────────────────────────────────────────
def run_all():
    """Run both Flask dashboard and APScheduler in combined mode."""
    db_url = get_db_url()
    ensure_db_dir(db_url)

    from src.storage.database import init_db
    from src.scheduler.manager import SchedulerManager
    from src.dashboard import app as dashboard_module
    from src.dashboard.app import create_app

    init_db(db_url)

    # Start scheduler
    manager = SchedulerManager()
    manager.start()
    logger.info("Scheduler started.")

    # Expose scheduler to dashboard API routes
    dashboard_module.scheduler_manager = manager

    # Create and run Flask app
    app = create_app()

    host  = os.environ.get("FLASK_HOST", "0.0.0.0")
    port  = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    def _shutdown(signum, frame):
        logger.info("Shutdown signal received...")
        manager.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(f"Dashboard + Scheduler starting on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False)


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Cannabis Data Aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["all", "dashboard", "scheduler", "collect", "setup", "seed"],
        default="all",
        help="Run mode (default: all)",
    )
    parser.add_argument("--source", nargs="+", metavar="SOURCE_ID",
                        help="Source ID(s) for collect mode")
    parser.add_argument("--all", dest="run_all", action="store_true",
                        help="Collect all enabled sources (collect mode)")
    parser.add_argument("--state", help="Filter by state (collect mode)")
    parser.add_argument("--category", help="Filter by category (collect mode)")
    parser.add_argument("--force", action="store_true",
                        help="Force overwrite existing records (seed mode)")
    parser.add_argument("--host", default=None,
                        help="Dashboard host (overrides FLASK_HOST env)")
    parser.add_argument("--port", type=int, default=None,
                        help="Dashboard port (overrides FLASK_PORT env)")
    args = parser.parse_args()

    if args.host:
        os.environ["FLASK_HOST"] = args.host
    if args.port:
        os.environ["FLASK_PORT"] = str(args.port)

    mode = args.mode
    logger.info(f"Starting Cannabis Data Aggregator — mode: {mode}")

    if mode == "setup":
        run_setup()
    elif mode == "seed":
        run_seed(force=args.force)
    elif mode == "collect":
        run_collect(
            source_ids=args.source,
            run_all=args.run_all,
            state=args.state,
            category=args.category,
        )
    elif mode == "scheduler":
        run_scheduler_only()
    elif mode == "dashboard":
        run_dashboard_only()
    else:  # all
        run_all()


if __name__ == "__main__":
    main()
