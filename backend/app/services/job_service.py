from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.services.graph_service import run_graph_step


class GraphJob(BaseModel):
    id: str
    run_id: str
    status: str
    message: str = ""
    projection: dict[str, object] | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


_EXECUTOR = ThreadPoolExecutor(max_workers=2)
_JOBS: dict[str, GraphJob] = {}
_LOCK = Lock()


def start_graph_step_job(runs_root: Path, run_id: str, confirmed: bool) -> GraphJob:
    job = GraphJob(id=f"job_{uuid4().hex[:12]}", run_id=run_id, status="queued", message="Graph step queued")
    with _LOCK:
        _JOBS[job.id] = job
    _EXECUTOR.submit(_run_job, runs_root, run_id, confirmed, job.id)
    return job


def get_job(job_id: str) -> GraphJob:
    with _LOCK:
        if job_id not in _JOBS:
            raise KeyError(job_id)
        return _JOBS[job_id]


def _update_job(job_id: str, **changes: object) -> None:
    with _LOCK:
        job = _JOBS[job_id]
        _JOBS[job_id] = job.model_copy(update=changes)


def _run_job(runs_root: Path, run_id: str, confirmed: bool, job_id: str) -> None:
    _update_job(
        job_id,
        status="running",
        message="Graph step running",
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    try:
        result = run_graph_step(runs_root, run_id, confirmed)
        _update_job(
            job_id,
            status="succeeded",
            message="Graph step completed",
            projection=result["projection"],
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        _update_job(
            job_id,
            status="failed",
            message="Graph step failed",
            error=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
