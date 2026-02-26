"""
Main dashboard routes (home, overview, settings).
"""
import logging
from datetime import datetime, timedelta

from flask import Blueprint, render_template, jsonify

from src.storage.database import session_scope, get_table_counts
from src.storage.models import (
    DataSource, CollectionSchedule, CollectionRun, RawRecord, CollectionLog
)
from sqlalchemy import func, desc

main_bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@main_bp.route("/")
def index():
    """Main dashboard overview page."""
    stats = _get_dashboard_stats()
    recent_runs = _get_recent_runs(limit=10)
    category_breakdown = _get_category_breakdown()
    state_breakdown = _get_state_breakdown()
    recent_logs = _get_recent_logs(limit=20)

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_runs=recent_runs,
        category_breakdown=category_breakdown,
        state_breakdown=state_breakdown,
        recent_logs=recent_logs,
    )


@main_bp.route("/api/dashboard/stats")
def dashboard_stats():
    """JSON endpoint for dashboard stats (for live refresh)."""
    return jsonify(_get_dashboard_stats())


def _get_dashboard_stats() -> dict:
    """Aggregate dashboard statistics."""
    with session_scope() as session:
        total_sources = session.query(DataSource).count()
        enabled_sources = session.query(DataSource).filter(
            DataSource.enabled == True
        ).count()
        total_schedules = session.query(CollectionSchedule).count()
        active_schedules = session.query(CollectionSchedule).filter(
            CollectionSchedule.enabled == True
        ).count()
        total_records = session.query(RawRecord).count()

        # Records with coordinates
        geo_records = session.query(RawRecord).filter(
            RawRecord.latitude.isnot(None),
            RawRecord.longitude.isnot(None)
        ).count()

        # Recent run stats
        last_run = session.query(CollectionRun).order_by(
            desc(CollectionRun.started_at)
        ).first()

        # Runs in last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_success = session.query(CollectionRun).filter(
            CollectionRun.started_at >= seven_days_ago,
            CollectionRun.status == "success"
        ).count()
        recent_failed = session.query(CollectionRun).filter(
            CollectionRun.started_at >= seven_days_ago,
            CollectionRun.status == "failed"
        ).count()

        # States covered
        states_count = session.query(
            func.count(func.distinct(RawRecord.state))
        ).scalar() or 0

        return {
            "total_sources": total_sources,
            "enabled_sources": enabled_sources,
            "total_schedules": total_schedules,
            "active_schedules": active_schedules,
            "total_records": total_records,
            "geo_records": geo_records,
            "states_covered": states_count,
            "last_run": last_run.started_at.isoformat() if last_run else None,
            "last_run_status": last_run.status if last_run else None,
            "recent_success": recent_success,
            "recent_failed": recent_failed,
        }


def _get_recent_runs(limit: int = 10) -> list:
    """Get recent collection runs with source name."""
    with session_scope() as session:
        runs = (
            session.query(CollectionRun, DataSource.name, DataSource.source_id)
            .join(DataSource, CollectionRun.source_id == DataSource.id)
            .order_by(desc(CollectionRun.started_at))
            .limit(limit)
            .all()
        )
        return [
            {
                **run.to_dict(),
                "source_name": name,
                "source_slug": slug,
            }
            for run, name, slug in runs
        ]


def _get_category_breakdown() -> list:
    """Records per category."""
    with session_scope() as session:
        rows = (
            session.query(RawRecord.category, func.count(RawRecord.id))
            .filter(RawRecord.category.isnot(None))
            .group_by(RawRecord.category)
            .order_by(desc(func.count(RawRecord.id)))
            .all()
        )
        return [{"category": cat, "count": cnt} for cat, cnt in rows]


def _get_state_breakdown() -> list:
    """Records per state."""
    with session_scope() as session:
        rows = (
            session.query(RawRecord.state, func.count(RawRecord.id))
            .filter(RawRecord.state.isnot(None))
            .group_by(RawRecord.state)
            .order_by(desc(func.count(RawRecord.id)))
            .limit(20)
            .all()
        )
        return [{"state": state, "count": cnt} for state, cnt in rows]


def _get_recent_logs(limit: int = 20) -> list:
    """Get recent log entries."""
    with session_scope() as session:
        logs = (
            session.query(CollectionLog)
            .order_by(desc(CollectionLog.timestamp))
            .limit(limit)
            .all()
        )
        return [log.to_dict() for log in logs]
