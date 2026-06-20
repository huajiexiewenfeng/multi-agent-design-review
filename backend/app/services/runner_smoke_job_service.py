from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.services.runner_smoke_service import run_runner_smoke_test


class RunnerSmokeJob(BaseModel):
    id: str
    runner_id: str
    model: str | None = None
    status: str
    message: str = ""
    result: dict[str, object] | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


_EXECUTOR = ThreadPoolExecutor(max_workers=2)
_JOBS: dict[str, RunnerSmokeJob] = {}
_LOCK = Lock()


def start_runner_smoke_job(runs_root: Path, runner_id: str, model: str | None = None) -> RunnerSmokeJob:
    job = RunnerSmokeJob(
        id=f"smoke_job_{uuid4().hex[:12]}",
        runner_id=runner_id,
        model=model,
        status="queued",
        message="Runner smoke test queued",
    )
    with _LOCK:
        _JOBS[job.id] = job
    _EXECUTOR.submit(_run_job, runs_root, runner_id, model, job.id)
    return job


def get_runner_smoke_job(job_id: str) -> RunnerSmokeJob:
    with _LOCK:
        if job_id not in _JOBS:
            raise KeyError(job_id)
        return _JOBS[job_id]


def _update_job(job_id: str, **changes: object) -> None:
    with _LOCK:
        job = _JOBS[job_id]
        _JOBS[job_id] = job.model_copy(update=changes)


def _run_job(runs_root: Path, runner_id: str, model: str | None, job_id: str) -> None:
    _update_job(
        job_id,
        status="running",
        message="Runner smoke test running",
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    try:
        result = run_runner_smoke_test(runner_id, runs_root, model=model)
        result_status = str(result.get("status"))
        _update_job(
            job_id,
            status=result_status
            if result_status in {"succeeded", "failed", "waiting_input", "unconfigured", "interactive_only"}
            else "failed",
            message=f"Runner smoke test {result_status}",
            result=result,
            error=result.get("error_message") if result_status != "succeeded" else None,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        _update_job(
            job_id,
            status="failed",
            message="Runner smoke test failed",
            error=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
