# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Fintomy scrapes ~200 US/EU large caps from Yahoo Finance (via `yfinance`), stores
them in MariaDB, computes technical indicators + buy/sell signals, and serves a
React dashboard on port **6001**. Runs as four Docker services.

## Commands

```bash
# --- full stack ---
cp .env.example .env
docker compose up -d --build          # first run does a ~2y backfill (minutes)
docker compose logs -f scraper        # watch scrape progress
docker compose down                   # stop   (add -v to wipe the db volume)

# --- core package: indicator/signal unit tests (no DB, no network) ---
pip install -e "core[test]"
pytest core                           # all tests
pytest core/tests/test_signals.py::test_rsi_overbought_marks_sell   # single test

# --- backend against SQLite (no MariaDB needed) ---
pip install -r backend/requirements.txt
DATABASE_URL="sqlite:///dev.db" uvicorn app.main:app --app-dir backend --reload --port 8000

# --- one-off scrape into that SQLite db ---
DATABASE_URL="sqlite:///dev.db" python -c "from fintomy_core.scrape import run_scrape; run_scrape('backfill')"

# --- frontend ---
cd frontend && npm install
npm run dev        # :5173, proxies /api -> localhost:8000 (VITE_API_TARGET to override)
npm run build      # -> frontend/dist
```

There is no linter configured.

## Architecture

### Shared core package (`core/fintomy_core/`)
Installed into **both** the `backend` and `scraper` images (`pip install /core`).
Single source of truth for the DB schema and all computation. Backend/scraper
Docker build context is the **repo root** (not their own dir) so `core/` is
copyable — keep it that way when editing Dockerfiles.

- `models.py` — SQLAlchemy ORM; schema is created at runtime via
  `db.init_schema()` (`Base.metadata.create_all`), never migrations.
- `tickers.py` — the curated universe as `(ticker, name, region, sector)` tuples.
  **This is the file to edit to change which companies are tracked.** The scraper
  re-seeds the `companies` table from it on every start (missing rows only).
- `scrape.py` — `run_scrape(kind)` is the entry point; records a `scrape_runs`
  row, then `fetch_prices` (bulk `yf.download`, batched, per-ticker fallback
  download if a symbol is missing from the batch) + `update_fundamentals`
  (per-ticker `yf.Ticker.get_info()`, throttled). `_upsert_prices` branches:
  MySQL `INSERT ... ON DUPLICATE KEY UPDATE`, else delete+insert (SQLite/tests).
  The `Progress` class mirrors live phase/done/total/rows_written/current +
  a capped per-ticker error log onto the `scrape_runs` row (~1 commit/s). Every
  per-ticker failure is caught and logged as an error string — one bad ticker
  never aborts a phase or the run.
- `indicators.py` — pure pandas functions (SMA/EMA/RSI/MACD/Bollinger/crossover).
  Keep them side-effect free.
- `signals.py` — `compute_analysis(ticker, prices_df, ma_period)` runs the four
  indicator rules and does majority-vote aggregation. A crossover counts as an
  active signal only within `SIGNAL_LOOKBACK` (3) bars of the latest one, so the
  dashboard shows "fresh" signals rather than every historical cross.
- `queries.py` — `load_prices()` returns a date-indexed OHLCV DataFrame for the API.

### Services (`docker-compose.yml`)
- `db` — mariadb:11, named volume `db_data`, healthcheck gates the others.
- `scraper` — `scraper/run.py` daemon: backfill-if-empty → APScheduler cron at
  `SCRAPE_HOUR:SCRAPE_MINUTE` in `TZ` → 20s poll loop draining `refresh_queue`.
  The UI's "refresh now" button and the scraper are **decoupled through the
  `refresh_queue` table** — backend never scrapes.
- `backend` — FastAPI, routers under `backend/app/routers/`. All heavy responses
  go through `app/services.py` which caches via `app/cache.py`.
- `frontend` — multi-stage (node build → nginx). `nginx.conf` → static
  `proxy_pass http://backend:8000` for `/api/`, SPA fallback to `index.html`,
  listens on 6001. `depends_on: backend condition: service_healthy` so the name
  resolves at nginx start. If only the backend is rebuilt and a 502 appears,
  `podman compose restart frontend` re-resolves it.

### Cache invalidation (non-obvious)
`app/cache.py` entries carry a *data-version* token. `app/deps.get_db` runs two
cheap aggregates (`max(scrape_runs.id where ok)`, `max(prices.date)`) per request
and calls `cache.set_version(...)`. When the scraper (a **separate process**)
finishes, the token changes and every cached analysis is treated as stale
regardless of TTL. Any new router must depend on `get_db` for this to work.

### Frontend data flow (`frontend/src/`)
`App.jsx` owns all state (selected ticker, `maPeriod` 7/14/28, `range`, filters).
It polls `/api/refresh/status` every 15s; when `running` flips true→false it
reloads companies/signals/detail. `api.js` is the only place that talks to the
backend. Charts use `lightweight-charts` v4 (three stacked single-pane charts:
price, RSI, MACD — v4 has no native multi-pane).

## Conventions

- UI strings are Serbian (latin). Code identifiers/comments are English.
- Timestamps stored UTC, formatted to local time in the frontend.
- `ma_period` is always validated against `ALLOWED_MA_PERIODS` (7/14/28) server-side.
- Not investment advice — keep that framing in any user-facing copy.
