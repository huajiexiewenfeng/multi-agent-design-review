from pathlib import Path

from backend.app.services import runner_smoke_job_service


def test_runner_smoke_job_runs_in_background(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        runner_smoke_job_service,
        "run_runner_smoke_test",
        lambda runner_id, runs_root: {
            "runner_id": runner_id,
            "status": "succeeded",
            "exit_code": 0,
            "output_content": "MADR_RUNNER_SMOKE_OK",
            "log_content": "exit_code: 0",
            "error_message": None,
            "smoke_dir": "_runner_smoke/codex/demo",
        },
    )

    job = runner_smoke_job_service.start_runner_smoke_job(tmp_path, "codex")
    result = runner_smoke_job_service.get_runner_smoke_job(job.id)

    assert result.runner_id == "codex"
    assert result.status in {"queued", "running", "succeeded"}
    assert result.message
