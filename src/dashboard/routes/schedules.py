"""Schedules management page routes."""
from flask import Blueprint, render_template
from src.storage.database import session_scope
from src.storage.models import CollectionSchedule, DataSource

schedules_bp = Blueprint("schedules", __name__)


@schedules_bp.route("/")
def index():
    """Schedules list page."""
    with session_scope() as session:
        rows = (
            session.query(CollectionSchedule, DataSource.name, DataSource.source_id)
            .join(DataSource, CollectionSchedule.source_id == DataSource.id)
            .order_by(CollectionSchedule.enabled.desc(), CollectionSchedule.name)
            .all()
        )
        schedules = []
        for sched, src_name, src_slug in rows:
            d = sched.to_dict()
            d["source_name"] = src_name
            d["source_slug"] = src_slug
            schedules.append(d)

    return render_template("schedules/index.html", schedules=schedules)


@schedules_bp.route("/new")
def new():
    """New schedule form page."""
    with session_scope() as session:
        sources = session.query(DataSource).filter(
            DataSource.enabled == True
        ).order_by(DataSource.state, DataSource.name).all()
        sources_data = [s.to_dict() for s in sources]
    return render_template(
        "schedules/form.html",
        schedule=None,
        sources=sources_data,
        action="create",
    )


@schedules_bp.route("/<int:sched_id>/edit")
def edit(sched_id: int):
    """Edit schedule form page."""
    with session_scope() as session:
        sched = session.get(CollectionSchedule, sched_id)
        if not sched:
            from flask import abort
            abort(404)
        sched_data = sched.to_dict()
        sources = session.query(DataSource).order_by(
            DataSource.state, DataSource.name
        ).all()
        sources_data = [s.to_dict() for s in sources]

    return render_template(
        "schedules/form.html",
        schedule=sched_data,
        sources=sources_data,
        action="edit",
    )
