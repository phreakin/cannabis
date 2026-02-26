"""
Flask application factory for the Cannabis Data Aggregator dashboard.
"""
import logging
import os
from datetime import datetime

from flask import Flask, jsonify

from src.storage.database import init_db, get_table_counts, health_check

logger = logging.getLogger(__name__)

# Module-level scheduler reference (set by main.py when running combined mode)
scheduler_manager = None


def create_app(config: dict = None) -> Flask:
    """
    Application factory. Creates and configures the Flask app.

    Args:
        config: Optional dict of Flask config overrides.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Core config
    app.config["SECRET_KEY"] = os.environ.get(
        "FLASK_SECRET_KEY", "dev-secret-key-change-in-production"
    )
    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.config["DATABASE_URL"] = os.environ.get(
        "DATABASE_URL", "sqlite:///data/cannabis_aggregator.db"
    )
    app.config["ADMIN_USERNAME"] = os.environ.get("ADMIN_USERNAME", "admin")
    app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD", "changeme123")

    if config:
        app.config.update(config)

    # Initialize database
    init_db(app.config["DATABASE_URL"])

    # Register blueprints
    from .routes.main import main_bp
    from .routes.sources import sources_bp
    from .routes.schedules import schedules_bp
    from .routes.data import data_bp
    from .routes.api import api_bp
    from .routes.entities import entities_bp
    from .routes.api_entities import api_entities_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(sources_bp, url_prefix="/sources")
    app.register_blueprint(schedules_bp, url_prefix="/schedules")
    app.register_blueprint(data_bp, url_prefix="/data")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(entities_bp, url_prefix="/entities")
    app.register_blueprint(api_entities_bp, url_prefix="/api/entities")

    # Health check endpoint
    @app.route("/health")
    def health():
        from src.storage.database import get_table_counts
        db_ok = health_check()
        counts = {}
        try:
            counts = get_table_counts()
        except Exception:
            pass
        return jsonify({
            "status": "healthy" if db_ok else "degraded",
            "database": "ok" if db_ok else "error",
            "database_url": app.config.get("DATABASE_URL", "").split("@")[-1],  # hide credentials
            "record_count": counts.get("raw_records", 0),
            "source_count": counts.get("data_sources", 0),
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }), 200 if db_ok else 503

    # Template context processor
    @app.context_processor
    def inject_globals():
        return {
            "app_name": "Cannabis Data Aggregator",
            "app_version": "1.0.0",
            "current_year": datetime.utcnow().year,
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500

    logger.info("Flask application initialized.")
    return app
