"""Database engine / session helpers.

The connection string comes from ``DATABASE_URL``.  In Docker this points at the
``db`` service, e.g.::

    mysql+pymysql://fintomy:fintomy@db:3306/fintomy?charset=utf8mb4

For local (non-Docker) experiments you can point it at SQLite::

    DATABASE_URL=sqlite:///fintomy.db
"""
from __future__ import annotations

import os
import time

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_URL = "mysql+pymysql://fintomy:fintomy@db:3306/fintomy?charset=utf8mb4"


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_URL)


def make_engine(url: str | None = None) -> Engine:
    url = url or get_database_url()
    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if url.startswith("mysql"):
        kwargs["pool_recycle"] = 3600
    return create_engine(url, **kwargs)


engine: Engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def wait_for_db(max_wait: float = 120.0, interval: float = 2.0) -> None:
    """Block until the database accepts connections (used on container start)."""
    deadline = time.monotonic() + max_wait
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return
        except OperationalError as exc:  # pragma: no cover - timing dependent
            last_err = exc
            time.sleep(interval)
    raise RuntimeError(f"Database not reachable after {max_wait}s: {last_err}")


def init_schema(retries: int = 5) -> None:
    """Create all tables that do not yet exist.

    ``backend`` and ``scraper`` boot together and both call this, so a
    concurrent ``CREATE TABLE`` / metadata-lock race is expected on a fresh
    volume — retry a few times before giving up.
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError

    from . import models  # noqa: F401  (register mappers)

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            models.Base.metadata.create_all(engine, checkfirst=True)
            return
        except (OperationalError, ProgrammingError) as exc:  # pragma: no cover - timing
            last_err = exc
            time.sleep(1.0 + attempt)
    raise RuntimeError(f"init_schema failed after {retries} attempts: {last_err}")
