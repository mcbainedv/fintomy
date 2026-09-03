from __future__ import annotations

from fastapi import APIRouter, Depends
from fintomy_core.models import RefreshRequest, ScrapeRun
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..cache import clear as clear_cache
from ..deps import get_db

router = APIRouter(prefix="/api/refresh", tags=["refresh"])


def _run_dict(run: ScrapeRun | None) -> dict | None:
    if run is None:
        return None
    total = run.total or 0
    done = run.done or 0
    errors = [e for e in (run.errors or "").split("\n") if e]
    return {
        "id": run.id,
        "kind": run.kind,
        "status": run.status,
        "phase": run.phase,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "ok_count": run.ok_count,
        "fail_count": run.fail_count,
        "rows_written": run.rows_written,
        "total": total,
        "done": done,
        "current": run.current,
        "percent": round(done / total * 100) if total else 0,
        "error_count": len(errors),
        "errors": errors[-50:],
        "message": run.message,
    }


@router.post("")
def request_refresh(db: Session = Depends(get_db)):
    """Queue a manual scrape; the scraper container picks it up within ~20s."""
    pending = db.scalar(
        select(RefreshRequest).where(RefreshRequest.picked_at.is_(None)).limit(1)
    )
    if pending is None:
        pending = RefreshRequest()
        db.add(pending)
        db.commit()
    clear_cache()
    return {"queued": True, "request_id": pending.id}


@router.get("/status")
def refresh_status(db: Session = Depends(get_db)):
    last = db.scalar(select(ScrapeRun).order_by(ScrapeRun.id.desc()).limit(1))
    last_ok = db.scalar(
        select(ScrapeRun).where(ScrapeRun.status == "ok").order_by(ScrapeRun.id.desc()).limit(1)
    )
    pending = db.scalar(
        select(RefreshRequest).where(RefreshRequest.picked_at.is_(None)).limit(1)
    )
    running = last is not None and last.status == "running"
    return {
        "running": running or pending is not None,
        "last_run": _run_dict(last),
        "last_success": _run_dict(last_ok),
    }
