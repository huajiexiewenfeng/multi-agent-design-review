from datetime import datetime, timezone
from pathlib import Path

from backend.app.runners.base import RunnerResult


class FileRunner:
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
        started = datetime.now(timezone.utc).isoformat()
        inbox_dir.mkdir(parents=True, exist_ok=True)
        runner_log_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(path.name for path in inbox_dir.glob("*.md"))
        (runner_log_dir / "file.log").write_text(f"found files: {files}\n", encoding="utf-8")
        finished = datetime.now(timezone.utc).isoformat()
        return RunnerResult(
            status="succeeded" if files else "cancelled",
            exit_code=0 if files else None,
            produced_files=files,
            stdout_summary=f"{len(files)} inbox files found",
            started_at=started,
            finished_at=finished,
        )
