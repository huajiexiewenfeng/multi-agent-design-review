from datetime import datetime, timezone
from pathlib import Path

from backend.app.runners.base import RunnerResult


class ManualRunner:
    def run(
        self,
        run_id: str,
        agent_id: str,
        stage: str,
        prompt_file: Path,
        inbox_dir: Path,
        runner_log_dir: Path,
        timeout_seconds: int,
        metadata: dict[str, object],
    ) -> RunnerResult:
        now = datetime.now(timezone.utc).isoformat()
        runner_log_dir.mkdir(parents=True, exist_ok=True)
        (runner_log_dir / "manual.log").write_text(f"waiting for manual submission: {prompt_file}\n", encoding="utf-8")
        return RunnerResult(
            status="cancelled",
            exit_code=None,
            produced_files=[],
            stdout_summary="manual submission required",
            started_at=now,
            finished_at=now,
        )
