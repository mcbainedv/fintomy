"""Fintomy scraper daemon.

Responsibilities:
  1. wait for the database, create schema, seed the company universe;
  2. if there is no price history yet, run a one-off backfill;
  3. run a scheduled scrape every day at ``SCRAPE_HOUR``:``SCRAPE_MINUTE`` local time;
  4. poll ``refresh_queue`` so the UI's "refresh now" button triggers a scrape.
"""
from __future__ import annotations

import logging
import os
import signal
import time
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fintomy_core.db import SessionLocal, init_schema, wait_for_db
from fintomy_core.models import RefreshRequest
from fintomy_core.scrape import prices_table_empty, run_scrape, seed_companies
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("fintomy.scraper")

TZ = os.environ.get("TZ", "UTC")
SCRAPE_HOUR = int(os.environ.get("SCRAPE_HOUR", "17"))
SCRAPE_MINUTE = int(os.environ.get("SCRAPE_MINUTE", "0"))
QUEUE_POLL_SECONDS = int(os.environ.get("QUEUE_POLL_SECONDS", "20"))

_running = True


def _stop(*_):
    global _running
    _running = False


def _scheduled_job():
    log.info("scheduled scrape firing")
    run_scrape("scheduled")


def _drain_refresh_queue() -> None:
    session = SessionLocal()
    try:
        pending = session.scalars(
            select(RefreshRequest).where(RefreshRequest.picked_at.is_(None)).order_by(RefreshRequest.id)
        ).all()
        if not pending:
            return
        # Collapse multiple queued requests into a single scrape.
        now = datetime.now(timezone.utc)
        for req in pending:
            req.picked_at = now
        session.commit()
        ids = [r.id for r in pending]
    finally:
        session.close()

    log.info("manual refresh requested (ids=%s)", ids)
    run = run_scrape("manual")

    session = SessionLocal()
    try:
        for req in session.scalars(
            select(RefreshRequest).where(RefreshRequest.id.in_(ids))
        ).all():
            req.run_id = run.id
        session.commit()
    finally:
        session.close()


def main() -> None:
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    wait_for_db()
    init_schema()

    session = SessionLocal()
    try:
        seed_companies(session)
        needs_backfill = prices_table_empty(session)
    finally:
        session.close()

    if needs_backfill:
        log.info("no price history found - running initial backfill")
        run_scrape("backfill")
    elif os.environ.get("SCRAPE_ON_START", "0") == "1":
        run_scrape("scheduled")

    scheduler = BackgroundScheduler(timezone=TZ)
    scheduler.add_job(
        _scheduled_job,
        CronTrigger(hour=SCRAPE_HOUR, minute=SCRAPE_MINUTE, timezone=TZ),
        id="daily_scrape",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    log.info("scheduler started - daily scrape at %02d:%02d %s", SCRAPE_HOUR, SCRAPE_MINUTE, TZ)

    try:
        while _running:
            try:
                _drain_refresh_queue()
            except Exception:  # noqa: BLE001
                log.exception("refresh queue poll failed")
            for _ in range(QUEUE_POLL_SECONDS):
                if not _running:
                    break
                time.sleep(1)
    finally:
        scheduler.shutdown(wait=False)
        log.info("scraper stopped")


if __name__ == "__main__":
    main()
