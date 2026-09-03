"""Yahoo Finance scraping via the :mod:`yfinance` client.

The public entry point is :func:`run_scrape`, which records a row in
``scrape_runs`` (with live progress + a per-ticker error log) and updates the
``companies`` and ``prices`` tables.  A single bad ticker never aborts the run.
"""
from __future__ import annotations

import logging
import math
import os
import time
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Company, Price, ScrapeRun
from .tickers import ALL_TICKERS, seed_rows

log = logging.getLogger("fintomy.scrape")

PRICE_BATCH_SIZE = int(os.environ.get("PRICE_BATCH_SIZE", "40"))
FUNDAMENTALS_SLEEP = float(os.environ.get("FUNDAMENTALS_SLEEP", "1.0"))
BACKFILL_PERIOD = os.environ.get("BACKFILL_PERIOD", "2y")
DAILY_PERIOD = os.environ.get("DAILY_PERIOD", "1mo")
MAX_STORED_ERRORS = 300


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _clean_float(value) -> float | None:
    try:
        if value is None:
            return None
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _clean_int(value) -> int | None:
    f = _clean_float(value)
    return int(f) if f is not None else None


# --------------------------------------------------------------------------- #
# Seeding
# --------------------------------------------------------------------------- #
def seed_companies(session: Session) -> int:
    """Insert any tickers from the curated list that are missing. Returns count added."""
    existing = set(session.scalars(select(Company.ticker)).all())
    added = 0
    for row in seed_rows():
        if row["ticker"] in existing:
            continue
        session.add(Company(**row))
        added += 1
    if added:
        session.commit()
        log.info("Seeded %d new companies", added)
    return added


# --------------------------------------------------------------------------- #
# Live progress on the scrape_runs row
# --------------------------------------------------------------------------- #
class Progress:
    """Mirrors progress + errors onto the ``scrape_runs`` row (DB commits throttled)."""

    def __init__(self, session: Session, run_id: int):
        self.session = session
        self.run_id = run_id
        self.errors: list[str] = []
        self.ok = 0
        self.fail = 0
        self.rows_written = 0
        self._phase_done = 0
        self._last_commit = 0.0

    def _run(self) -> ScrapeRun:
        return self.session.get(ScrapeRun, self.run_id)

    def _commit(self) -> None:
        """Commit progress; never let a bookkeeping failure abort the scrape."""
        try:
            self.session.commit()
        except Exception:  # noqa: BLE001
            log.exception("progress commit failed")
            self.session.rollback()

    def _write(self, run: ScrapeRun, *, force: bool) -> None:
        now = time.monotonic()
        if force or now - self._last_commit >= 1.0:
            self._commit()
            self._last_commit = now

    def start_phase(self, name: str, total: int) -> None:
        self._phase_done = 0
        run = self._run()
        run.phase = name
        run.total = total
        run.done = 0
        run.current = ""
        self._write(run, force=True)

    def step(self, ticker: str, *, ok: bool, rows: int = 0) -> None:
        self._phase_done += 1
        self.rows_written += rows
        if ok:
            self.ok += 1
        else:
            self.fail += 1
        run = self._run()
        run.done = self._phase_done
        run.current = ticker
        run.ok_count = self.ok
        run.fail_count = self.fail
        run.rows_written = self.rows_written
        self._write(run, force=False)

    def add_error(self, ticker: str, reason: str) -> None:
        entry = f"{ticker}: {reason}"
        self.errors.append(entry)
        log.warning("scrape issue - %s", entry)
        run = self._run()
        run.errors = "\n".join(self.errors[-MAX_STORED_ERRORS:])
        self._commit()

    def finish_phase(self) -> None:
        run = self._run()
        run.done = run.total
        run.current = ""
        self._write(run, force=True)


# --------------------------------------------------------------------------- #
# yfinance helper
# --------------------------------------------------------------------------- #
def _yf():
    """Import yfinance and point its tz cache at a writable path (quiets warnings)."""
    import yfinance as yf

    try:
        cache_dir = os.environ.get("YF_CACHE_DIR", "/tmp/py-yfinance")
        os.makedirs(cache_dir, exist_ok=True)
        yf.set_tz_cache_location(cache_dir)
    except Exception:  # noqa: BLE001 - best effort
        pass
    return yf


# --------------------------------------------------------------------------- #
# Fundamentals
# --------------------------------------------------------------------------- #
def fetch_fundamentals(ticker: str) -> dict | None:
    yf = _yf()
    try:
        info = yf.Ticker(ticker).get_info()
    except Exception as exc:  # noqa: BLE001 - yfinance raises many types
        raise RuntimeError(str(exc).splitlines()[0][:200] or exc.__class__.__name__) from exc
    if not info or not isinstance(info, dict):
        return None
    # yfinance sometimes returns a near-empty stub for delisted/renamed symbols.
    if not (info.get("longName") or info.get("shortName") or info.get("marketCap")):
        return None

    return {
        "name": info.get("longName") or info.get("shortName") or "",
        "sector": info.get("sector") or "",
        "industry": info.get("industry") or "",
        "exchange": info.get("fullExchangeName") or info.get("exchange") or "",
        "currency": info.get("currency") or "",
        "description": info.get("longBusinessSummary") or "",
        "market_cap": _clean_int(info.get("marketCap")),
        "beta": _clean_float(info.get("beta")),
        "trailing_pe": _clean_float(info.get("trailingPE")),
        "forward_pe": _clean_float(info.get("forwardPE")),
        "dividend_yield": _clean_float(info.get("dividendYield")),
        "week52_high": _clean_float(info.get("fiftyTwoWeekHigh")),
        "week52_low": _clean_float(info.get("fiftyTwoWeekLow")),
    }


def update_fundamentals(
    session: Session, tickers: list[str], progress: Progress | None = None
) -> tuple[int, int]:
    ok = fail = 0
    if progress:
        progress.start_phase("fundamentals", len(tickers))

    for ticker in tickers:
        got = False
        try:
            data = fetch_fundamentals(ticker)
            if data:
                company = session.get(Company, ticker)
                if company is None:
                    company = Company(ticker=ticker, region="US")
                    session.add(company)
                for key, value in data.items():
                    if value in ("", None) and getattr(company, key, None):
                        continue  # keep the curated fallback
                    setattr(company, key, value)
                company.fundamentals_updated_at = _utcnow()
                session.commit()
                got = True
            else:
                if progress:
                    progress.add_error(ticker, "fundamentals: no data returned")
        except Exception as exc:  # noqa: BLE001 - one ticker must not abort the run
            session.rollback()
            if progress:
                progress.add_error(ticker, f"fundamentals: {exc}")

        ok += got
        fail += not got
        if progress:
            progress.step(ticker, ok=got)
        time.sleep(FUNDAMENTALS_SLEEP)

    if progress:
        progress.finish_phase()
    return ok, fail


# --------------------------------------------------------------------------- #
# Prices
# --------------------------------------------------------------------------- #
def _iter_batches(seq: list[str], size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def _rows_from_frame(ticker: str, frame: pd.DataFrame | None, now: datetime) -> list[dict]:
    rows: list[dict] = []
    if frame is None or frame.empty:
        return rows
    frame = frame.dropna(how="all")
    for idx, rec in frame.iterrows():
        d = idx.date() if hasattr(idx, "date") else idx
        close = _clean_float(rec.get("Close"))
        if close is None:
            continue
        rows.append(
            {
                "ticker": ticker,
                "date": d,
                "open": _clean_float(rec.get("Open")),
                "high": _clean_float(rec.get("High")),
                "low": _clean_float(rec.get("Low")),
                "close": close,
                "adj_close": _clean_float(rec.get("Adj Close")) or close,
                "volume": _clean_int(rec.get("Volume")),
                "scraped_at": now,
            }
        )
    return rows


def _upsert_prices(session: Session, rows: list[dict]) -> int:
    if not rows:
        return 0
    dialect = session.bind.dialect.name if session.bind else ""
    if dialect == "mysql":
        stmt = mysql_insert(Price.__table__).values(rows)
        update_cols = {
            c: stmt.inserted[c]
            for c in ("open", "high", "low", "close", "adj_close", "volume", "scraped_at")
        }
        stmt = stmt.on_duplicate_key_update(**update_cols)
        session.execute(stmt)
    else:
        for row in rows:
            session.query(Price).filter_by(ticker=row["ticker"], date=row["date"]).delete()
            session.add(Price(**row))
    session.commit()
    return len(rows)


def _extract_ticker_frame(data: pd.DataFrame, ticker: str, single: bool) -> pd.DataFrame | None:
    if single:
        return data
    try:
        if ticker in data.columns.get_level_values(0):
            return data[ticker]
    except Exception:  # noqa: BLE001
        return None
    return None


def _download(yf, tickers: list[str], period: str) -> pd.DataFrame:
    return yf.download(
        tickers=tickers,
        period=period,
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )


def fetch_prices(
    session: Session, tickers: list[str], period: str, progress: Progress | None = None
) -> tuple[int, int]:
    yf = _yf()
    ok = fail = 0
    now = _utcnow()
    if progress:
        progress.start_phase("prices", len(tickers))

    for batch in _iter_batches(tickers, PRICE_BATCH_SIZE):
        try:
            data = _download(yf, batch, period)
        except Exception as exc:  # noqa: BLE001 - retry the batch one ticker at a time
            log.warning("price batch failed (%s...): %s", batch[:2], exc)
            data = None

        for ticker in batch:
            rows: list[dict] = []
            reason = ""
            try:
                frame = _extract_ticker_frame(data, ticker, len(batch) == 1) if data is not None else None
                if frame is None or frame.empty:
                    # Per-ticker fallback download so a bad symbol can't poison the batch.
                    single = _download(yf, [ticker], period)
                    frame = single
                rows = _rows_from_frame(ticker, frame, now)
                if not rows:
                    reason = "no price data (symbol may be delisted or renamed)"
            except Exception as exc:  # noqa: BLE001
                reason = f"prices: {str(exc).splitlines()[0][:200]}"

            if rows:
                try:
                    written = _upsert_prices(session, rows)
                except Exception as exc:  # noqa: BLE001
                    session.rollback()
                    reason = f"db write failed: {exc}"
                    written = 0
                if written:
                    ok += 1
                    if progress:
                        progress.step(ticker, ok=True, rows=written)
                    continue

            fail += 1
            if progress:
                if reason:
                    progress.add_error(ticker, reason)
                progress.step(ticker, ok=False)

        time.sleep(1.0)

    if progress:
        progress.finish_phase()
    return ok, fail


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def prices_table_empty(session: Session) -> bool:
    return session.scalar(select(func.count(Price.id))) == 0


def run_scrape(kind: str = "manual", period: str | None = None) -> ScrapeRun:
    """Run a full scrape. ``kind`` is one of scheduled | manual | backfill."""
    session = SessionLocal()
    run = ScrapeRun(kind=kind, status="running", phase="starting", started_at=_utcnow())
    session.add(run)
    session.commit()
    run_id = run.id

    tickers = [t[0] for t in ALL_TICKERS]
    if period is None:
        period = BACKFILL_PERIOD if kind == "backfill" else DAILY_PERIOD

    log.info("scrape run #%s (%s) started, %d tickers, period=%s", run_id, kind, len(tickers), period)
    progress = Progress(session, run_id)
    messages: list[str] = []
    p_ok = 0

    try:
        seed_companies(session)

        try:
            p_ok, p_fail = fetch_prices(session, tickers, period, progress)
            messages.append(f"prices ok={p_ok} fail={p_fail} rows={progress.rows_written}")
        except Exception as exc:  # noqa: BLE001
            log.exception("prices phase crashed")
            messages.append(f"prices phase crashed: {exc}")

        try:
            f_ok, f_fail = update_fundamentals(session, tickers, progress)
            messages.append(f"fundamentals ok={f_ok} fail={f_fail}")
        except Exception as exc:  # noqa: BLE001
            log.exception("fundamentals phase crashed")
            messages.append(f"fundamentals phase crashed: {exc}")

        run = session.get(ScrapeRun, run_id)
        run.status = "ok" if p_ok > 0 else "error"
        run.phase = "done"
        run.current = ""
        run.message = "; ".join(messages)
        run.finished_at = _utcnow()
        session.commit()
        log.info("scrape run #%s finished: %s", run_id, run.message)
    except Exception as exc:  # noqa: BLE001
        log.exception("scrape run #%s crashed", run_id)
        run = session.get(ScrapeRun, run_id)
        run.status = "error"
        run.phase = "error"
        run.message = f"{'; '.join(messages)}; crashed: {exc}"
        run.finished_at = _utcnow()
        session.commit()
    finally:
        result = session.get(ScrapeRun, run_id)
        session.expunge(result)
        session.close()
    return result
