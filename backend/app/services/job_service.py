from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.services.flow_control_service import run_until_pause
from backend.app.services.graph_service import run_graph_step


class GraphJob(BaseModel):
    id: str
    run_id: str
    status: str
    message: str = ""
    projection: dict[str, object] | None = None
    mode: str = "step"
    stop_reason: str | None = None
    steps_run: int = 0
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


def start_run_until_pause_job(runs_root: Path, run_id: str, max_steps: int = 10) -> GraphJob:
    job = GraphJob(
        id=f"job_{uuid4().hex[:12]}",
        run_id=run_id,
        status="queued",
        message="Run-until-pause queued",
        mode="until_pause",
    )
    with _LOCK:
        _JOBS[job.id] = job
    _EXECUTOR.submit(_run_until_pause_job, runs_root, run_id, max_steps, job.id)
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
            steps_run=1,
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


def _run_until_pause_job(runs_root: Path, run_id: str, max_steps: int, job_id: str) -> None:
    _update_job(
        job_id,
        status="running",
        message="Run-until-pause running",
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    try:
        result = run_until_pause(runs_root, run_id, max_steps=max_steps)
        _update_job(
            job_id,
            status="succeeded",
            message=f"Paused: {result['stop_reason']}",
            projection=result["projection"],
            stop_reason=str(result["stop_reason"]),
            steps_run=int(result["steps_run"]),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        _update_job(
            job_id,
            status="failed",
            message="Run-until-pause failed",
            error=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
