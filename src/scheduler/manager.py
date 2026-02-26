"""
Scheduler manager: manages APScheduler jobs for collection tasks.
Loads schedules from the database and creates/updates APScheduler jobs.
"""
import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Optional, List

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from pytz import timezone

from src.storage.database import session_scope, get_database_url
from src.storage.models import (
    DataSource, CollectionSchedule, CollectionRun, CollectionLog, RawRecord
)
from src.collectors import get_collector
from src.processors.normalizer import RecordNormalizer

logger = logging.getLogger(__name__)


class SchedulerManager:
    """
    Manages the APScheduler instance and collection job lifecycle.
    """

    def __init__(self):
        tz_name = os.environ.get("SCHEDULER_TIMEZONE", "America/Chicago")
        self.tz = timezone(tz_name)
        self.scheduler: Optional[BackgroundScheduler] = None
        self._build_scheduler()

    def _build_scheduler(self):
        """Initialize APScheduler with SQLAlchemy job store."""
        db_url = get_database_url()

        job_stores = {
            "default": SQLAlchemyJobStore(url=db_url)
        }
        executors = {
            "default": ThreadPoolExecutor(
                max_workers=int(os.environ.get("SCHEDULER_MAX_WORKERS", 5))
            )
        }
        job_defaults = {
            "coalesce": True,
            "max_instances": 2,
            "misfire_grace_time": int(
                os.environ.get("SCHEDULER_MISFIRE_GRACE_SECS", 3600)
            ),
        }

        self.scheduler = BackgroundScheduler(
            jobstores=job_stores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=self.tz,
        )

        # Event listeners for logging
        self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._on_job_missed, EVENT_JOB_MISSED)

    def start(self):
        """Start the scheduler and load all enabled schedules."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started.")

        self.sync_schedules()

    def stop(self):
        """Stop the scheduler gracefully."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped.")

    def sync_schedules(self):
        """
        Load all enabled schedules from the database and
        add/update/remove APScheduler jobs accordingly.
        """
        with session_scope() as session:
            schedules = (
                session.query(CollectionSchedule)
                .filter(CollectionSchedule.enabled == True)
                .all()
            )

        logger.info(f"Syncing {len(schedules)} active schedules...")

        active_job_ids = set()
        for sched in schedules:
            job_id = f"collect_{sched.schedule_id}"
            active_job_ids.add(job_id)
            self._upsert_job(sched, job_id)

        # Remove jobs for disabled/deleted schedules
        for job in self.scheduler.get_jobs():
            if job.id not in active_job_ids and job.id.startswith("collect_"):
                self.scheduler.remove_job(job.id)
                logger.info(f"Removed stale job: {job.id}")

    def _upsert_job(self, schedule: CollectionSchedule, job_id: str):
        """Add or update an APScheduler job for a collection schedule."""
        source_db_id = schedule.source_id
        schedule_db_id = schedule.id

        trigger_kwargs = self._build_trigger(schedule)
        if not trigger_kwargs:
            logger.warning(f"Skipping schedule {schedule.schedule_id}: invalid trigger config")
            return

        trigger_type = trigger_kwargs.pop("type")

        try:
            existing = self.scheduler.get_job(job_id)
            if existing:
                self.scheduler.reschedule_job(
                    job_id,
                    trigger=trigger_type,
                    **trigger_kwargs
                )
                logger.debug(f"Updated job: {job_id}")
            else:
                self.scheduler.add_job(
                    func=run_collection_job,
                    trigger=trigger_type,
                    kwargs={
                        "source_db_id": source_db_id,
                        "schedule_db_id": schedule_db_id,
                    },
                    id=job_id,
                    name=schedule.name,
                    replace_existing=True,
                    **trigger_kwargs
                )
                logger.info(f"Added job: {job_id} ({schedule.name})")
        except Exception as e:
            logger.error(f"Failed to upsert job {job_id}: {e}")

    def _build_trigger(self, schedule: CollectionSchedule) -> Optional[dict]:
        """Build APScheduler trigger kwargs from schedule config."""
        if schedule.schedule_type == "cron":
            return {
                "type": "cron",
                "minute": schedule.cron_minute or "0",
                "hour": schedule.cron_hour or "0",
                "day": schedule.cron_day_of_month or "*",
                "month": schedule.cron_month or "*",
                "day_of_week": schedule.cron_day_of_week or "*",
                "timezone": self.tz,
            }
        elif schedule.schedule_type == "interval":
            unit = schedule.interval_unit or "hours"
            value = schedule.interval_value or 24
            return {
                "type": "interval",
                **{unit: value},
            }
        else:
            logger.warning(f"Unknown schedule type: {schedule.schedule_type}")
            return None

    def trigger_now(self, source_id: int, triggered_by: str = "manual"):
        """Manually trigger collection for a source immediately."""
        logger.info(f"Manually triggering collection for source_id={source_id}")
        try:
            run_collection_job(source_id, triggered_by=triggered_by)
            return True, "Collection triggered successfully"
        except Exception as e:
            logger.error(f"Manual trigger failed: {e}")
            return False, str(e)

    def get_job_status(self) -> List[dict]:
        """Get status of all scheduler jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs

    def remove_schedule(self, schedule_id: str):
        """Remove a schedule from the scheduler."""
        job_id = f"collect_{schedule_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_job_executed(self, event):
        logger.debug(f"Job executed: {event.job_id}")

    def _on_job_error(self, event):
        logger.error(f"Job failed: {event.job_id} - {event.exception}")

    def _on_job_missed(self, event):
        logger.warning(f"Job missed: {event.job_id} scheduled for {event.scheduled_run_time}")


# ==============================================================================
# Collection job function (runs outside the class in a thread)
# ==============================================================================

def run_collection_job(
    source_db_id: int,
    schedule_db_id: Optional[int] = None,
    triggered_by: str = "scheduler",
) -> dict:
    """
    The main collection function executed by APScheduler.
    Fetches data from a source, normalizes it, and stores it in the database.
    Returns a summary dict.
    """
    run_logger = logging.getLogger("collector.job")

    # Load source from DB
    with session_scope() as session:
        source = session.get(DataSource, source_db_id)
        if not source:
            raise ValueError(f"DataSource {source_db_id} not found")
        if not source.enabled:
            run_logger.info(f"Source {source.source_id} is disabled, skipping")
            return {"status": "skipped"}

        # Create run record
        run = CollectionRun(
            source_id=source_db_id,
            schedule_id=schedule_db_id,
            started_at=datetime.utcnow(),
            status="running",
            triggered_by=triggered_by,
        )
        session.add(run)
        session.flush()
        run_id = run.id
        source_snapshot = source.to_dict()  # Avoid DetachedInstanceError

    run_logger.info(
        f"[Run {run_id}] Starting collection: {source_snapshot['source_id']} "
        f"({source_snapshot['state']}/{source_snapshot['category']})"
    )

    records_fetched = 0
    records_stored = 0
    records_skipped = 0
    error_message = None
    status = "running"

    try:
        # Create source proxy object for collector
        source_proxy = _SourceProxy(source_snapshot)
        collector = get_collector(source_proxy)
        normalizer = RecordNormalizer(source_proxy)

        batch = []
        batch_size = 500

        for raw_record in collector.collect():
            records_fetched += 1

            # Normalize the record
            normalized = normalizer.normalize(raw_record)

            # Compute hash for deduplication
            record_hash = RawRecord.compute_hash(raw_record)

            # Build RawRecord
            record = RawRecord(
                source_id=source_db_id,
                run_id=run_id,
                state=normalized.get("state"),
                category=normalized.get("category") or source_snapshot.get("category"),
                subcategory=normalized.get("subcategory") or source_snapshot.get("subcategory"),
                name=normalized.get("name"),
                license_number=normalized.get("license_number"),
                license_type=normalized.get("license_type"),
                license_status=normalized.get("license_status"),
                address=normalized.get("address"),
                city=normalized.get("city"),
                zip_code=normalized.get("zip_code"),
                county=normalized.get("county"),
                latitude=normalized.get("latitude"),
                longitude=normalized.get("longitude"),
                phone=normalized.get("phone"),
                email=normalized.get("email"),
                website=normalized.get("website"),
                record_date=normalized.get("record_date"),
                license_date=normalized.get("license_date"),
                expiry_date=normalized.get("expiry_date"),
                record_data=raw_record,
                record_hash=record_hash,
            )
            batch.append(record)

            # Flush in batches
            if len(batch) >= batch_size:
                stored = _flush_batch(batch, run_id, source_db_id, run_logger)
                records_stored += stored
                records_skipped += len(batch) - stored
                batch = []

        # Flush remaining
        if batch:
            stored = _flush_batch(batch, run_id, source_db_id, run_logger)
            records_stored += stored
            records_skipped += len(batch) - stored

        status = "success"
        run_logger.info(
            f"[Run {run_id}] Completed: fetched={records_fetched} "
            f"stored={records_stored} skipped={records_skipped}"
        )

    except Exception as e:
        status = "failed"
        error_message = str(e)
        run_logger.error(f"[Run {run_id}] Collection failed: {e}", exc_info=True)

    # Update run record
    with session_scope() as session:
        run = session.get(CollectionRun, run_id)
        if run:
            run.completed_at = datetime.utcnow()
            run.status = status
            run.records_fetched = records_fetched
            run.records_stored = records_stored
            run.records_skipped = records_skipped
            run.error_message = error_message
            run.duration_seconds = (
                datetime.utcnow() - run.started_at
            ).total_seconds()

        # Update schedule last_run
        if schedule_db_id:
            sched = session.get(CollectionSchedule, schedule_db_id)
            if sched:
                sched.last_run = datetime.utcnow()

        # Log summary
        log = CollectionLog(
            run_id=run_id,
            source_id=source_db_id,
            level="INFO" if status == "success" else "ERROR",
            message=f"Collection {status}: {records_stored}/{records_fetched} records stored",
            details={
                "status": status,
                "records_fetched": records_fetched,
                "records_stored": records_stored,
                "error": error_message,
            },
        )
        session.add(log)

    return {
        "status": status,
        "run_id": run_id,
        "records_fetched": records_fetched,
        "records_stored": records_stored,
        "error": error_message,
    }


def _flush_batch(
    batch: List[RawRecord],
    run_id: int,
    source_id: int,
    log: logging.Logger,
) -> int:
    """Persist a batch of records. Returns count of stored records."""
    if not batch:
        return 0

    stored = 0
    with session_scope() as session:
        for record in batch:
            # Optional: skip duplicates by hash
            # existing = session.query(RawRecord).filter_by(
            #     record_hash=record.record_hash
            # ).first()
            # if existing:
            #     continue
            session.add(record)
            stored += 1

    log.debug(f"Flushed batch: {stored} records")
    return stored


class _SourceProxy:
    """
    Simple proxy object that exposes DataSource fields as attributes.
    Used to pass source config to collectors without an open DB session.
    """
    def __init__(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)
