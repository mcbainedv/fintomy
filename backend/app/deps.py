"""FastAPI dependencies."""
from __future__ import annotations

from collections.abc import Iterator

from fintomy_core.db import SessionLocal
from fintomy_core.models import Price, ScrapeRun
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .cache import set_version


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        # Tag the analysis cache with the current data version so a finished
        # scrape (possibly in the scraper process) busts stale entries.
        last_run = db.scalar(select(func.max(ScrapeRun.id)).where(ScrapeRun.status == "ok"))
        last_price = db.scalar(select(func.max(Price.date)))
        set_version(f"{last_run}:{last_price}")
        yield db
    finally:
        db.close()
