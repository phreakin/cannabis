"""Data browser and map view routes."""
from flask import Blueprint, render_template, request
from src.storage.database import session_scope
from src.storage.models import RawRecord, DataSource
from sqlalchemy import func, distinct

data_bp = Blueprint("data", __name__)


@data_bp.route("/")
def index():
    """Data browser page."""
    with session_scope() as session:
        categories = [
            r[0] for r in
            session.query(distinct(RawRecord.category))
            .filter(RawRecord.category.isnot(None))
            .order_by(RawRecord.category).all()
        ]
        states = [
            r[0] for r in
            session.query(distinct(RawRecord.state))
            .filter(RawRecord.state.isnot(None))
            .order_by(RawRecord.state).all()
        ]
        total_records = session.query(RawRecord).count()
        geo_records = session.query(RawRecord).filter(
            RawRecord.latitude.isnot(None)
        ).count()

    with session_scope() as session:
        sources = [
            {"id": s.id, "name": s.name, "state": s.state}
            for s in session.query(DataSource).order_by(DataSource.state, DataSource.name).all()
        ]

    return render_template(
        "data/index.html",
        categories=categories,
        states=states,
        sources=sources,
        total_records=total_records,
        geo_records=geo_records,
    )


@data_bp.route("/map")
def map_view():
    """Full map view of dispensary locations."""
    with session_scope() as session:
        categories = [
            r[0] for r in
            session.query(distinct(RawRecord.category))
            .filter(RawRecord.category.isnot(None))
            .order_by(RawRecord.category).all()
        ]
        states = [
            r[0] for r in
            session.query(distinct(RawRecord.state))
            .filter(RawRecord.state.isnot(None))
            .order_by(RawRecord.state).all()
        ]
    return render_template("data/map.html", categories=categories, states=states)


@data_bp.route("/logs")
def logs():
    """Logs viewer page."""
    with session_scope() as session:
        sources = [
            {"id": s.id, "name": s.name, "state": s.state}
            for s in session.query(DataSource).order_by(DataSource.state, DataSource.name).all()
        ]
    return render_template("logs/index.html", sources=sources)


@data_bp.route("/exports")
def exports():
    """Exports page."""
    with session_scope() as session:
        categories = [
            r[0] for r in
            session.query(distinct(RawRecord.category))
            .filter(RawRecord.category.isnot(None))
            .order_by(RawRecord.category).all()
        ]
        states = [
            r[0] for r in
            session.query(distinct(RawRecord.state))
            .filter(RawRecord.state.isnot(None))
            .order_by(RawRecord.state).all()
        ]
        sources = [
            {"id": s.id, "name": s.name, "state": s.state}
            for s in session.query(DataSource).order_by(DataSource.state, DataSource.name).all()
        ]
    return render_template(
        "exports/index.html",
        categories=categories,
        states=states,
        sources=sources,
    )


@data_bp.route("/settings")
def settings():
    """Settings page."""
    return render_template("settings/index.html")
