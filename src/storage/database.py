"""
Database connection and session management.
"""
import os
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_SessionFactory = None


def get_database_url() -> str:
    """Get database URL from environment or default to SQLite."""
    url = os.environ.get("DATABASE_URL", "sqlite:///data/cannabis_aggregator.db")
    # Ensure SQLite data directory exists
    if url.startswith("sqlite:///"):
        db_path = url.replace("sqlite:///", "")
        if not db_path.startswith("/"):  # relative path
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return url


def create_db_engine(database_url: str = None, echo: bool = False):
    """Create and configure the SQLAlchemy engine."""
    if database_url is None:
        database_url = get_database_url()

    connect_args = {}
    engine_kwargs = {}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine_kwargs["poolclass"] = StaticPool
    else:
        # MySQL / MariaDB: reconnect transparently when MySQL drops idle connections.
        # pool_pre_ping sends a lightweight SELECT 1 before each checkout; if the
        # connection is dead SQLAlchemy discards it and opens a fresh one.
        # pool_recycle forces connections to be replaced before MySQL's wait_timeout
        # (default 8 h) closes them, eliminating "Lost connection" errors.
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 3600   # recycle every 1 h
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10

    engine = create_engine(
        database_url,
        echo=echo,
        connect_args=connect_args,
        **engine_kwargs
    )

    # Enable WAL mode for SQLite (better concurrent read performance)
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    return engine


def init_db(database_url: str = None, echo: bool = False, drop_all: bool = False) -> None:
    """
    Initialize the database: create engine, session factory, and all tables.
    Call this once at application startup.
    """
    global _engine, _SessionFactory

    _engine = create_db_engine(database_url, echo=echo)

    if drop_all:
        logger.warning("Dropping all tables!")
        Base.metadata.drop_all(_engine)

    Base.metadata.create_all(_engine)
    _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)
    logger.info(f"Database initialized: {database_url or get_database_url()}")


def get_engine():
    """Get the global database engine."""
    global _engine
    if _engine is None:
        init_db()
    return _engine


def get_session_factory():
    """Get the global session factory."""
    global _SessionFactory
    if _SessionFactory is None:
        init_db()
    return _SessionFactory


def get_session() -> Session:
    """Get a new database session. Caller is responsible for closing."""
    return get_session_factory()()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager that provides a transactional session scope.
    Automatically commits on success and rolls back on exception.

    Usage:
        with session_scope() as session:
            session.add(record)
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def health_check() -> bool:
    """Check if the database connection is working."""
    try:
        with session_scope() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def get_table_counts() -> dict:
    """Get record counts for all main tables."""
    from .models import DataSource, CollectionSchedule, CollectionRun, RawRecord
    with session_scope() as session:
        return {
            "data_sources": session.query(DataSource).count(),
            "schedules": session.query(CollectionSchedule).count(),
            "collection_runs": session.query(CollectionRun).count(),
            "raw_records": session.query(RawRecord).count(),
        }
