"""Tiny in-process TTL cache for computed analyses.

Entries are additionally tagged with a *data version* token.  The API layer sets
the current token once per request (cheap query on ``scrape_runs`` / latest price
date); when a scrape lands and the token changes, every cached entry is
considered stale even if its TTL has not expired.  This keeps the dashboard fast
without ever showing data from before the last scrape.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable

_LOCK = threading.Lock()
_STORE: dict[Any, tuple[float, str, Any]] = {}
_VERSION = "0"
DEFAULT_TTL = 300.0  # seconds


def set_version(version: str) -> None:
    global _VERSION
    with _LOCK:
        _VERSION = version


def get_or_set(key: Any, producer: Callable[[], Any], ttl: float = DEFAULT_TTL) -> Any:
    now = time.monotonic()
    with _LOCK:
        version = _VERSION
        hit = _STORE.get(key)
        if hit and hit[0] > now and hit[1] == version:
            return hit[2]
    value = producer()
    with _LOCK:
        _STORE[key] = (now + ttl, version, value)
    return value


def clear() -> None:
    with _LOCK:
        _STORE.clear()
