"""Sources management page routes."""
from flask import Blueprint, render_template
from src.storage.database import session_scope
from src.storage.models import DataSource
from sqlalchemy import func

sources_bp = Blueprint("sources", __name__)


@sources_bp.route("/")
def index():
    """Sources list page."""
    with session_scope() as session:
        sources = session.query(DataSource).order_by(
            DataSource.state, DataSource.category, DataSource.name
        ).all()
        sources_data = [s.to_dict() for s in sources]

        # Category counts
        categories = (
            session.query(DataSource.category, func.count(DataSource.id))
            .group_by(DataSource.category)
            .order_by(DataSource.category)
            .all()
        )
        # State counts
        states = (
            session.query(DataSource.state, func.count(DataSource.id))
            .group_by(DataSource.state)
            .order_by(DataSource.state)
            .all()
        )

    return render_template(
        "sources/index.html",
        sources=sources_data,
        categories=[{"name": c, "count": n} for c, n in categories],
        states=[{"name": s, "count": n} for s, n in states],
    )


@sources_bp.route("/new")
def new():
    """New source form page."""
    return render_template("sources/form.html", source=None, action="create")


@sources_bp.route("/<int:source_id>/edit")
def edit(source_id: int):
    """Edit source form page."""
    with session_scope() as session:
        source = session.get(DataSource, source_id)
        if not source:
            from flask import abort
            abort(404)
        source_data = source.to_dict()
    return render_template("sources/form.html", source=source_data, action="edit")
