# Fintomy

![CI](https://github.com/mcbainedv/fintomy/actions/workflows/ci.yml/badge.svg)

Self-hosted stock dashboard. Scrapes daily prices + fundamentals for ~100 US and
~100 European large caps from Yahoo Finance (`yfinance`), stores them in a local
**MariaDB**, computes technical indicators and buy/sell signals (SMA crossover,
RSI, MACD, Bollinger), and shows everything in a React dashboard on
**`http://localhost:6001`**. Auto-refreshes daily at 17:00 local time, or on a
button click. *Educational / informational use only — not investment advice.*

## Install (one command)

Needs **Docker** or **Podman** with the Compose plugin, plus `git`.

```bash
curl -fsSL https://raw.githubusercontent.com/mcbainedv/fintomy/main/install.sh | bash
```

This clones the repo into `./fintomy`, creates `.env`, and runs
`compose up -d --build`. Then open <http://localhost:6001> (the first backfill
takes a few minutes — watch it with `docker compose logs -f scraper`).

Or do it manually:

```bash
git clone https://github.com/mcbainedv/fintomy.git
cd fintomy
cp .env.example .env
docker compose up -d --build     # or: podman compose up -d --build
```

---

> Ostatak dokumentacije je na srpskom. / The rest of this document is in Serbian.

Skrejpuje fundamentalne i cenovne podatke za ~100 americkih i ~100 evropskih
kompanija sa Yahoo Finance (preko `yfinance`), cuva ih u lokalnu **MariaDB**,
racuna tehnicke indikatore i buy/sell signale, i prikazuje sve kroz web
dashboard na **`http://localhost:6001`**.

Ceo sistem se pokrece jednom komandom (`docker compose up`) i sam se azurira
svakog dana u 17:00 po lokalnom vremenu (ili rucno, dugmetom u UI-ju).

---

## Arhitektura

| Servis | Slika | Uloga |
|--------|-------|-------|
| `db` | `mariadb:11` | skladiste (`companies`, `prices`, `favorites`, `scrape_runs`, `refresh_queue`) |
| `scraper` | `scraper/Dockerfile` | inicijalni backfill · dnevni cron u 17:00 · obrada „refresh now" zahteva |
| `backend` | `backend/Dockerfile` | FastAPI REST API + racun indikatora/signala (interni port 8000) |
| `frontend` | `frontend/Dockerfile` | React SPA + nginx koji servira na portu **6001** i proksira `/api` → `backend` |

Zajednicki Python kod je u `core/` (paket `fintomy_core`) i instalira se i u
`backend` i u `scraper` sliku:

```
core/fintomy_core/
  db.py          engine / session iz DATABASE_URL
  models.py      SQLAlchemy ORM modeli
  tickers.py     kurirane liste US + EU tickera  <-- ovde menjas univerzum
  scrape.py      yfinance -> baza (fundamentali + cene, upsert)
  indicators.py  SMA, EMA, RSI, MACD, Bollinger, crossover
  signals.py     buy/sell pravila + agregacija (vecinsko glasanje)
  queries.py     citanje cena kao pandas DataFrame (za API)
```

---

## Pokretanje

Potreban je Docker (ili Podman) sa `compose` plugin-om.

```bash
cp .env.example .env        # po zelji izmeni lozinke / TZ / vreme skrejpovanja
docker compose up -d --build
```

Prvi start:

1. `db` se podigne, `scraper` kreira seme i pokrece **backfill** (~2 godine
   dnevnih cena za ceo univerzum — traje nekoliko minuta, zavisi od Yahoo
   rate-limita).
2. Kad backfill zavrsi, otvori **http://localhost:6001**.

Prati napredak:

```bash
docker compose logs -f scraper
```

Zaustavljanje: `docker compose down` &nbsp;·&nbsp; brisanje i podataka: `docker compose down -v`

---

## Web interfejs (port 6001)

```
┌──────────────────────────────────────────────────────────────┐
│ FINTOMY        [Osvezi podatke]         poslednje azuriranje… │
├───────────────────────────┬──────────────────────────────────┤
│ BUY signali (zeleno)      │ SELL signali (crveno)            │  <- gornji panel
├───────────────┬───────────┴──────────────────────────────────┤
│ ★ AAPL  +1.2% │  AAPL · Apple Inc.   325.13 USD  +0.4%  BUY  │
│ ☆ MSFT  -0.4% │  Moving average: [7] [14] [28]   Period: …   │
│ ☆ NVDA  +2.1% │  ┌ indikatori: SMA / RSI / MACD / Bollinger ┐│
│  … skrol …    │  │ candlestick + SMA + Bollinger + markeri  ││
│ filter US/EU  │  │ RSI(14)                                  ││
│ ★ samo fav.   │  │ MACD(12,26,9)                            ││
│ sektor ▾      │  market cap · beta · P/E · 52w · opis firme  ││
└───────────────┴──────────────────────────────────────────────┘
```

- **Gornji panel** — tickeri sa aktivnim agregatnim signalom: levo BUY (zeleno),
  desno SELL (crveno). Klik na cip otvara firmu. Hover pokazuje razloge.
- **Leva lista** — sve firme, skrol, `★` zvezdica za favorite, filter po regionu
  / sektoru / „samo favoriti". Tacka pored simbola = trenutni signal.
- **Desni panel** — grafikoni (TradingView `lightweight-charts`), osnovne
  informacije o firmi i izbor **MA perioda 7 / 14 / 28** + duzine istorije.
- **„Osveži podatke"** — upisuje zahtev u `refresh_queue`; `scraper` ga pokupi
  za ~20 s. Dok radi, u zaglavlju stoji **progress bar**: faza (cene /
  fundamentali), `obradjeno / ukupno`, procenat, tekući ticker, broj upisanih
  redova i broj grešaka. Klik na **⚠ N** otvara listu grešaka po tickeru
  (npr. „RO.SW: no price data"). Kad završi, UI se sam osveži.

Skrejper ne pada zbog jednog lošeg simbola — greška se zabeleži i nastavlja dalje.

---

## Signali

Racunaju se na poslednjoj svecici; crossover se smatra „svezim" ako se desio u
poslednja 3 trgovacka dana (`SIGNAL_LOOKBACK`).

| Indikator | BUY | SELL |
|-----------|-----|------|
| **SMA crossover** (7/14/28) | cena presece SMA navise | cena presece SMA nanize |
| **RSI (14)** | ≤ 30 (preprodato) | ≥ 70 (prekupljeno) |
| **MACD (12, 26, 9)** — „oscilating moving average" | MACD linija presece signalnu navise | presece nanize |
| **Bollinger (20, 2σ)** | cena na/ispod donje trake | cena na/iznad gornje trake |

**Agregatni signal** = vecinsko glasanje (≥ 2 glasa i vise od suprotnih) →
`BUY` / `SELL` / `HOLD`. To je ono sto se prikazuje u gornjem panelu i kao tacka
u listi.

> Napomena: ovo je tehnicka analiza za informativne svrhe, ne investicioni savet.

---

## Konfiguracija (`.env`)

| Promenljiva | Default | Opis |
|-------------|---------|------|
| `TZ` | `Europe/Belgrade` | zona za cron i prikaz vremena |
| `SCRAPE_HOUR` / `SCRAPE_MINUTE` | `17` / `0` | vreme dnevnog skrejpovanja |
| `BACKFILL_PERIOD` | `2y` | koliko istorije povlaci prvi backfill |
| `DAILY_PERIOD` | `1mo` | prozor koji se povlaci pri svakom osvezavanju |
| `SCRAPE_ON_START` | `0` | `1` = skrejpuj odmah pri svakom startu kontejnera |
| `WEB_PORT` | `6001` | host port za UI |
| `MARIADB_*` / `DATABASE_URL` | — | kredencijali baze |

Izmena univerzuma firmi: `core/fintomy_core/tickers.py` (liste `US_TICKERS` i
`EU_TICKERS`), pa `docker compose up -d --build scraper backend`.

---

## Razvoj bez Docker-a

```bash
# core + testovi indikatora/signala
python -m venv .venv && source .venv/bin/activate
pip install -e "core[test]"
pytest core

# backend (SQLite umesto MariaDB)
pip install -r backend/requirements.txt
DATABASE_URL="sqlite:///dev.db" uvicorn app.main:app --app-dir backend --reload --port 8000

# scraper, jednokratno
DATABASE_URL="sqlite:///dev.db" python -c "from fintomy_core.scrape import run_scrape; run_scrape('backfill')"

# frontend
cd frontend && npm install && npm run dev   # http://localhost:5173, proksira /api na :8000
```

---

## Provera (nakon `docker compose up`)

```bash
docker compose logs -f scraper                     # prati backfill
curl -s localhost:6001/api/refresh/status | jq     # phase, done/total, percent, errors[]
curl -s localhost:6001/api/meta | jq               # company_count ~206, price_count raste
curl -s "localhost:6001/api/signals?ma_period=14" | jq '.buy[0], .sell[0]'
docker compose exec db mariadb -ufintomy -pfintomy fintomy \
  -e "SELECT region, COUNT(*) FROM companies GROUP BY region; SELECT COUNT(*) FROM prices;"
```

Test cron-a: u `.env` postavi `SCRAPE_MINUTE` na par minuta u buducnost,
`docker compose up -d scraper`, pa proveri novi red u `scrape_runs`.
