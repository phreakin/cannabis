"""
REST API routes for the dashboard frontend (AJAX calls).
Handles CRUD for sources, schedules, and data operations.
"""
import logging
from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy import desc, func

from src.storage.database import session_scope
from src.storage.models import (
    DataSource, CollectionSchedule, CollectionRun, RawRecord, CollectionLog
)

api_bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)


# ==============================================================================
# DATA SOURCES API
# ==============================================================================

@api_bp.route("/sources", methods=["GET"])
def list_sources():
    """GET /api/sources - List all data sources."""
    state = request.args.get("state")
    category = request.args.get("category")
    enabled = request.args.get("enabled")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    with session_scope() as session:
        q = session.query(DataSource)
        if state:
            q = q.filter(DataSource.state == state.upper())
        if category:
            q = q.filter(DataSource.category == category)
        if enabled is not None:
            q = q.filter(DataSource.enabled == (enabled.lower() == "true"))

        total = q.count()
        sources = q.order_by(DataSource.state, DataSource.name)\
                   .offset((page - 1) * per_page)\
                   .limit(per_page)\
                   .all()

        return jsonify({
            "total": total,
            "page": page,
            "per_page": per_page,
            "sources": [s.to_dict() for s in sources],
        })


@api_bp.route("/sources/<int:source_id>", methods=["GET"])
def get_source(source_id: int):
    """GET /api/sources/:id - Get a single source."""
    with session_scope() as session:
        source = session.get(DataSource, source_id)
        if not source:
            return jsonify({"error": "Source not found"}), 404
        return jsonify(source.to_dict())


@api_bp.route("/sources", methods=["POST"])
def create_source():
    """POST /api/sources - Create a new data source."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["source_id", "name", "state", "category", "format", "url"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    with session_scope() as session:
        # Check for duplicate source_id
        existing = session.query(DataSource).filter_by(
            source_id=data["source_id"]
        ).first()
        if existing:
            return jsonify({"error": f"Source ID '{data['source_id']}' already exists"}), 409

        source = DataSource(
            source_id=data["source_id"],
            name=data["name"],
            description=data.get("description"),
            state=data["state"].upper(),
            agency=data.get("agency"),
            category=data["category"],
            subcategory=data.get("subcategory"),
            format=data["format"].lower(),
            url=data.get("url"),
            discovery_url=data.get("discovery_url"),
            website=data.get("website"),
            enabled=data.get("enabled", True),
            api_key_required=data.get("api_key_required", False),
            api_key_env=data.get("api_key_env"),
            params=data.get("params"),
            headers=data.get("headers"),
            pagination=data.get("pagination"),
            field_mapping=data.get("field_mapping"),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            rate_limit_rpm=data.get("rate_limit_rpm", 60),
            timeout=data.get("timeout", 60),
        )
        session.add(source)
        session.flush()
        return jsonify(source.to_dict()), 201


@api_bp.route("/sources/<int:source_id>", methods=["PUT"])
def update_source(source_id: int):
    """PUT /api/sources/:id - Update a data source."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    with session_scope() as session:
        source = session.get(DataSource, source_id)
        if not source:
            return jsonify({"error": "Source not found"}), 404

        updatable = [
            "name", "description", "state", "agency", "category", "subcategory",
            "format", "url", "discovery_url", "website", "enabled",
            "api_key_required", "api_key_env", "params", "headers",
            "pagination", "field_mapping", "tags", "notes",
            "rate_limit_rpm", "timeout",
        ]
        for field in updatable:
            if field in data:
                val = data[field]
                if field == "state" and isinstance(val, str):
                    val = val.upper()
                if field == "format" and isinstance(val, str):
                    val = val.lower()
                setattr(source, field, val)

        source.updated_at = datetime.utcnow()
        return jsonify(source.to_dict())


@api_bp.route("/sources/<int:source_id>", methods=["DELETE"])
def delete_source(source_id: int):
    """DELETE /api/sources/:id - Delete a data source."""
    with session_scope() as session:
        source = session.get(DataSource, source_id)
        if not source:
            return jsonify({"error": "Source not found"}), 404
        session.delete(source)
        return jsonify({"message": "Source deleted"}), 200


@api_bp.route("/sources/<int:source_id>/toggle", methods=["POST"])
def toggle_source(source_id: int):
    """POST /api/sources/:id/toggle - Toggle enabled/disabled."""
    with session_scope() as session:
        source = session.get(DataSource, source_id)
        if not source:
            return jsonify({"error": "Source not found"}), 404
        source.enabled = not source.enabled
        return jsonify({"enabled": source.enabled})


@api_bp.route("/sources/<int:source_id>/test", methods=["POST"])
def test_source(source_id: int):
    """POST /api/sources/:id/test - Test source connectivity."""
    with session_scope() as session:
        source = session.get(DataSource, source_id)
        if not source:
            return jsonify({"error": "Source not found"}), 404
        source_dict = source.to_dict()

    from src.collectors import get_collector
    from src.scheduler.manager import _SourceProxy
    proxy = _SourceProxy(source_dict)
    collector = get_collector(proxy)
    success, message = collector.test_connection()

    return jsonify({"success": success, "message": message})


@api_bp.route("/sources/<int:source_id>/run", methods=["POST"])
def run_source(source_id: int):
    """POST /api/sources/:id/run - Manually trigger collection."""
    from src.scheduler.manager import run_collection_job
    try:
        result = run_collection_job(source_id, triggered_by="manual_api")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# SCHEDULES API
# ==============================================================================

@api_bp.route("/schedules", methods=["GET"])
def list_schedules():
    """GET /api/schedules - List all schedules."""
    with session_scope() as session:
        schedules = (
            session.query(CollectionSchedule, DataSource.name)
            .join(DataSource, CollectionSchedule.source_id == DataSource.id)
            .order_by(CollectionSchedule.name)
            .all()
        )
        result = []
        for sched, source_name in schedules:
            d = sched.to_dict()
            d["source_name"] = source_name
            result.append(d)
        return jsonify({"schedules": result})


@api_bp.route("/schedules/<int:sched_id>", methods=["GET"])
def get_schedule(sched_id: int):
    with session_scope() as session:
        sched = session.get(CollectionSchedule, sched_id)
        if not sched:
            return jsonify({"error": "Not found"}), 404
        return jsonify(sched.to_dict())


@api_bp.route("/schedules", methods=["POST"])
def create_schedule():
    """POST /api/schedules - Create a new schedule."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    with session_scope() as session:
        sched = CollectionSchedule(
            schedule_id=data.get("schedule_id") or f"sched_{int(datetime.utcnow().timestamp())}",
            source_id=data["source_id"],
            name=data["name"],
            schedule_type=data.get("schedule_type", "cron"),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 2),
            cron_minute=data.get("cron_minute", "0"),
            cron_hour=data.get("cron_hour", "0"),
            cron_day_of_month=data.get("cron_day_of_month", "*"),
            cron_month=data.get("cron_month", "*"),
            cron_day_of_week=data.get("cron_day_of_week", "*"),
            interval_value=data.get("interval_value"),
            interval_unit=data.get("interval_unit", "hours"),
            notes=data.get("notes"),
        )
        session.add(sched)
        session.flush()
        return jsonify(sched.to_dict()), 201


@api_bp.route("/schedules/<int:sched_id>", methods=["PUT"])
def update_schedule(sched_id: int):
    data = request.get_json()
    with session_scope() as session:
        sched = session.get(CollectionSchedule, sched_id)
        if not sched:
            return jsonify({"error": "Not found"}), 404
        fields = [
            "name", "enabled", "priority", "schedule_type",
            "cron_minute", "cron_hour", "cron_day_of_month",
            "cron_month", "cron_day_of_week",
            "interval_value", "interval_unit", "notes",
        ]
        for f in fields:
            if f in data:
                setattr(sched, f, data[f])
        return jsonify(sched.to_dict())


@api_bp.route("/schedules/<int:sched_id>", methods=["DELETE"])
def delete_schedule(sched_id: int):
    with session_scope() as session:
        sched = session.get(CollectionSchedule, sched_id)
        if not sched:
            return jsonify({"error": "Not found"}), 404
        session.delete(sched)
        return jsonify({"message": "Schedule deleted"})


@api_bp.route("/schedules/<int:sched_id>/toggle", methods=["POST"])
def toggle_schedule(sched_id: int):
    with session_scope() as session:
        sched = session.get(CollectionSchedule, sched_id)
        if not sched:
            return jsonify({"error": "Not found"}), 404
        sched.enabled = not sched.enabled
        return jsonify({"enabled": sched.enabled})


# ==============================================================================
# DATA / RECORDS API
# ==============================================================================

@api_bp.route("/records", methods=["GET"])
def list_records():
    """GET /api/records - Browse collected records with filters."""
    state     = request.args.get("state")
    category  = request.args.get("category")
    source_id = request.args.get("source_id")
    city      = request.args.get("city")
    license_type = request.args.get("license_type")
    # Accept both "search" (frontend) and "q" (legacy)
    search  = request.args.get("search") or request.args.get("q")
    # Accept both "has_gps" (frontend) and "has_geo" (legacy)
    has_gps = request.args.get("has_gps") or request.args.get("has_geo")
    page     = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 500)

    with session_scope() as session:
        q = session.query(RawRecord)
        if state:
            q = q.filter(RawRecord.state == state.upper())
        if category:
            q = q.filter(RawRecord.category == category)
        if source_id:
            try:
                q = q.filter(RawRecord.source_id == int(source_id))
            except (ValueError, TypeError):
                pass
        if city:
            q = q.filter(RawRecord.city.ilike(f"%{city}%"))
        if license_type:
            q = q.filter(RawRecord.license_type.ilike(f"%{license_type}%"))
        if search:
            q = q.filter(RawRecord.name.ilike(f"%{search}%"))
        if has_gps in ("1", "true"):
            q = q.filter(
                RawRecord.latitude.isnot(None),
                RawRecord.longitude.isnot(None),
            )
        elif has_gps in ("0", "false"):
            from sqlalchemy import or_
            q = q.filter(
                or_(RawRecord.latitude.is_(None), RawRecord.longitude.is_(None))
            )

        total = q.count()
        pages = max(1, (total + per_page - 1) // per_page)
        records = (
            q.order_by(desc(RawRecord.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        records_data = []
        for r in records:
            d = r.to_dict(include_raw=False)
            # Alias created_at → collected_at for the frontend table
            d["collected_at"] = d.get("created_at")
            records_data.append(d)

        return jsonify({
            "total": total,
            "page": page,
            "pages": pages,
            "per_page": per_page,
            "records": records_data,
        })


@api_bp.route("/records/<int:record_id>", methods=["GET"])
def get_record(record_id: int):
    """GET /api/records/<id> - Get a single raw record by ID."""
    with session_scope() as session:
        record = session.get(RawRecord, record_id)
        if not record:
            return jsonify({"error": "Record not found"}), 404
        return jsonify(record.to_dict(include_raw=True))


@api_bp.route("/records/geojson", methods=["GET"])
def records_geojson():
    """GET /api/records/geojson - Records as GeoJSON FeatureCollection."""
    state = request.args.get("state")
    category = request.args.get("category")
    limit = min(int(request.args.get("limit", 5000)), 50000)

    with session_scope() as session:
        q = session.query(RawRecord).filter(
            RawRecord.latitude.isnot(None),
            RawRecord.longitude.isnot(None)
        )
        if state:
            q = q.filter(RawRecord.state == state.upper())
        if category:
            q = q.filter(RawRecord.category == category)

        records = q.limit(limit).all()

    features = [r.to_geojson_feature() for r in records]
    features = [f for f in features if f]

    return jsonify({
        "type": "FeatureCollection",
        "features": features,
        "count": len(features),
    })


@api_bp.route("/records/export", methods=["GET"])
def export_records():
    """GET /api/records/export - Export records as CSV or JSON."""
    import csv
    import io
    from flask import Response

    fmt = request.args.get("format", "json")
    state = request.args.get("state")
    category = request.args.get("category")
    limit = min(int(request.args.get("limit", 10000)), 100000)

    with session_scope() as session:
        q = session.query(RawRecord)
        if state:
            q = q.filter(RawRecord.state == state.upper())
        if category:
            q = q.filter(RawRecord.category == category)
        records = q.limit(limit).all()
        data = [r.to_dict(include_raw=False) for r in records]

    if fmt == "csv":
        if not data:
            return Response("", mimetype="text/csv")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=cannabis_data.csv"},
        )
    else:
        import json
        return Response(
            json.dumps(data, indent=2, default=str),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=cannabis_data.json"},
        )


# ==============================================================================
# COLLECTION RUNS API
# ==============================================================================

@api_bp.route("/runs", methods=["GET"])
def list_runs():
    """GET /api/runs - List collection runs."""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))
    source_id = request.args.get("source_id")
    status = request.args.get("status")

    with session_scope() as session:
        q = (
            session.query(CollectionRun, DataSource.name)
            .join(DataSource, CollectionRun.source_id == DataSource.id)
        )
        if source_id:
            q = q.filter(CollectionRun.source_id == int(source_id))
        if status:
            q = q.filter(CollectionRun.status == status)

        total = q.count()
        runs = q.order_by(desc(CollectionRun.started_at))\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()

        result = []
        for run, src_name in runs:
            d = run.to_dict()
            d["source_name"] = src_name
            result.append(d)

        return jsonify({"total": total, "runs": result})


# ==============================================================================
# LOGS API
# ==============================================================================

@api_bp.route("/logs", methods=["GET"])
def list_logs():
    """GET /api/logs - List recent log entries."""
    level     = request.args.get("level")
    source_id = request.args.get("source_id")
    run_id    = request.args.get("run_id")
    since     = request.args.get("since")       # YYYY-MM-DD
    search    = request.args.get("search")
    page      = int(request.args.get("page", 1))
    per_page  = int(request.args.get("per_page", 50))

    with session_scope() as session:
        q = (
            session.query(CollectionLog, DataSource.name.label("source_name"))
            .outerjoin(DataSource, CollectionLog.source_id == DataSource.id)
        )
        if level:
            q = q.filter(CollectionLog.level == level.upper())
        if source_id:
            q = q.filter(CollectionLog.source_id == int(source_id))
        if run_id:
            q = q.filter(CollectionLog.run_id == int(run_id))
        if since:
            try:
                from datetime import datetime as _dt
                cutoff = _dt.strptime(since, "%Y-%m-%d")
                q = q.filter(CollectionLog.timestamp >= cutoff)
            except ValueError:
                pass
        if search:
            q = q.filter(CollectionLog.message.ilike(f"%{search}%"))

        total  = q.count()
        pages  = max(1, (total + per_page - 1) // per_page)
        result = q.order_by(desc(CollectionLog.timestamp))\
                  .offset((page - 1) * per_page)\
                  .limit(per_page)\
                  .all()

        logs_out = []
        for log, src_name in result:
            d = log.to_dict()
            d["source_name"] = src_name
            logs_out.append(d)

        return jsonify({
            "total": total,
            "page": page,
            "pages": pages,
            "logs": logs_out,
        })


# ==============================================================================
# STATS API
# ==============================================================================

@api_bp.route("/stats/categories", methods=["GET"])
def stats_categories():
    with session_scope() as session:
        rows = (
            session.query(RawRecord.category, func.count(RawRecord.id))
            .filter(RawRecord.category.isnot(None))
            .group_by(RawRecord.category)
            .order_by(desc(func.count(RawRecord.id)))
            .all()
        )
        return jsonify([{"label": cat, "value": cnt} for cat, cnt in rows])


@api_bp.route("/stats/states", methods=["GET"])
def stats_states():
    with session_scope() as session:
        rows = (
            session.query(RawRecord.state, func.count(RawRecord.id))
            .filter(RawRecord.state.isnot(None))
            .group_by(RawRecord.state)
            .order_by(desc(func.count(RawRecord.id)))
            .all()
        )
        return jsonify([{"state": state, "count": cnt} for state, cnt in rows])


# ==============================================================================
# SCHEDULER / ADMIN API
# ==============================================================================

@api_bp.route("/jobs", methods=["GET"])
def list_jobs():
    """GET /api/jobs - Get APScheduler job status."""
    try:
        from src.dashboard.app import scheduler_manager
        if scheduler_manager:
            return jsonify(scheduler_manager.get_job_status())
    except Exception:
        pass
    return jsonify([])


@api_bp.route("/scheduler/sync", methods=["POST"])
def scheduler_sync():
    """POST /api/scheduler/sync - Sync DB schedules to APScheduler."""
    try:
        from src.dashboard.app import scheduler_manager
        if scheduler_manager:
            scheduler_manager.sync_schedules()
            return jsonify({"message": "Scheduler synced successfully"})
        return jsonify({"error": "Scheduler not running"}), 503
    except Exception as e:
        logger.error(f"Scheduler sync failed: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/logs/purge", methods=["POST"])
def purge_logs():
    """POST /api/logs/purge - Delete old log entries."""
    data = request.get_json() or {}
    days = int(data.get("days", 30))
    cutoff = datetime.utcnow() - __import__("datetime").timedelta(days=days)
    with session_scope() as session:
        deleted = session.query(CollectionLog)\
            .filter(CollectionLog.timestamp < cutoff)\
            .delete()
    return jsonify({"message": f"Deleted {deleted} log entries older than {days} days"})


@api_bp.route("/seed", methods=["POST"])
def seed_from_yaml():
    """POST /api/seed - Seed sources and schedules from YAML config files."""
    try:
        import yaml, os
        from src.storage.models import DataSource, CollectionSchedule

        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        sources_path   = os.path.join(project_root, "config", "sources.yaml")
        schedules_path = os.path.join(project_root, "config", "schedules.yaml")

        created_s = updated_s = created_sch = updated_sch = 0

        if os.path.exists(sources_path):
            with open(sources_path) as f:
                cfg = yaml.safe_load(f)
            with session_scope() as session:
                for src_cfg in cfg.get("sources", []):
                    existing = session.query(DataSource).filter_by(
                        source_id=src_cfg["id"]
                    ).first()
                    if existing:
                        for field in ["name","state","agency","category","subcategory",
                                      "format","url","enabled","tags","notes"]:
                            if field in src_cfg:
                                setattr(existing, field, src_cfg[field])
                        updated_s += 1
                    else:
                        session.add(DataSource(
                            source_id=src_cfg["id"],
                            name=src_cfg.get("name",""),
                            state=src_cfg.get("state",""),
                            agency=src_cfg.get("agency",""),
                            category=src_cfg.get("category",""),
                            subcategory=src_cfg.get("subcategory",""),
                            format=src_cfg.get("format","json"),
                            url=src_cfg.get("url",""),
                            enabled=src_cfg.get("enabled", True),
                            tags=src_cfg.get("tags",[]),
                            notes=src_cfg.get("notes",""),
                        ))
                        created_s += 1

        if os.path.exists(schedules_path):
            with open(schedules_path) as f:
                cfg = yaml.safe_load(f)
            with session_scope() as session:
                for sch_cfg in cfg.get("schedules", []):
                    src = session.query(DataSource).filter_by(
                        source_id=sch_cfg["source_id"]
                    ).first()
                    if not src:
                        continue
                    existing = session.query(CollectionSchedule).filter_by(
                        schedule_id=sch_cfg["id"]
                    ).first()
                    cron = sch_cfg.get("cron", {})
                    intv = sch_cfg.get("interval", {})
                    kwargs = dict(
                        source_id=src.id,
                        name=sch_cfg.get("name",""),
                        schedule_type=sch_cfg.get("schedule_type","cron"),
                        enabled=sch_cfg.get("enabled", True),
                        priority=sch_cfg.get("priority", 2),
                        notes=sch_cfg.get("notes",""),
                        cron_minute=str(cron.get("minute","0")),
                        cron_hour=str(cron.get("hour","2")),
                        cron_day_of_month=str(cron.get("day_of_month","*")),
                        cron_month=str(cron.get("month","*")),
                        cron_day_of_week=str(cron.get("day_of_week","*")),
                        interval_value=intv.get("value", 7),
                        interval_unit=intv.get("unit", "days"),
                    )
                    if existing:
                        for k, v in kwargs.items():
                            setattr(existing, k, v)
                        updated_sch += 1
                    else:
                        session.add(CollectionSchedule(schedule_id=sch_cfg["id"], **kwargs))
                        created_sch += 1

        msg = (f"Sources: {created_s} created, {updated_s} updated. "
               f"Schedules: {created_sch} created, {updated_sch} updated.")
        return jsonify({"message": msg})

    except Exception as e:
        logger.error(f"Seed from YAML failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
