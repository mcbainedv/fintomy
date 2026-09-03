from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fintomy_core.db import init_schema, wait_for_db

from .routers import chart, companies, favorites, meta, refresh, signals

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("fintomy.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_db()
    init_schema()
    log.info("Fintomy API ready")
    yield


app = FastAPI(title="Fintomy API", version="0.1.0", lifespan=lifespan)

_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router)
app.include_router(companies.router)
app.include_router(chart.router)
app.include_router(signals.router)
app.include_router(favorites.router)
app.include_router(refresh.router)
