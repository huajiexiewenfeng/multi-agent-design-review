from datetime import datetime, timezone
from pathlib import Path

from backend.app.runners.base import RunnerResult


class MockRunner:
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
        output_name = f"{stage}_result.md"
        if stage == "clarification":
            output_name = "clarification_result.md"
        (inbox_dir / output_name).write_text(
            "## Clarification Questions\n\n1. Who is the target user?\n\n## Assumptions\n\n- Local-first MVP.\n",
            encoding="utf-8",
        )
        (runner_log_dir / "mock.log").write_text(f"mock runner for {run_id}:{agent_id}:{stage}\n", encoding="utf-8")
        finished = datetime.now(timezone.utc).isoformat()
        return RunnerResult(
            status="succeeded",
            exit_code=0,
            produced_files=[output_name],
            stdout_summary="mock output written",
            started_at=started,
            finished_at=finished,
        )
