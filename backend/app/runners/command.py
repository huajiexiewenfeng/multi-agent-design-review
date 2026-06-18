from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess

from backend.app.runners.base import RunnerResult


class CommandRunner:
    def __init__(self, command_template: str) -> None:
        self.command_template = command_template

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
        output_file = inbox_dir / f"{stage}_result.md"
        command = self.command_template.format(
            run_id=run_id,
            agent_id=agent_id,
            stage=stage,
            prompt_file=str(prompt_file),
            output_file=str(output_file),
        )
        try:
            completed = subprocess.run(
                command,
                cwd=prompt_file.parents[2],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                shell=True,
            )
            if completed.stdout.strip():
                output_file.write_text(completed.stdout, encoding="utf-8")
            produced_files = [output_file.name] if output_file.is_file() else []
            status = "succeeded" if completed.returncode == 0 and produced_files else "failed"
            log = (
                f"command: {command}\n"
                f"exit_code: {completed.returncode}\n\n"
                f"stdout:\n{completed.stdout}\n\n"
                f"stderr:\n{completed.stderr}\n"
            )
            (runner_log_dir / "command.log").write_text(log, encoding="utf-8")
            finished = datetime.now(timezone.utc).isoformat()
            return RunnerResult(
                status=status,
                exit_code=completed.returncode,
                produced_files=produced_files,
                stdout_summary=completed.stdout[:500],
                stderr_summary=completed.stderr[:500],
                error_message=None if status == "succeeded" else "Command runner did not produce markdown output",
                started_at=started,
                finished_at=finished,
            )
        except Exception as exc:
            finished = datetime.now(timezone.utc).isoformat()
            (runner_log_dir / "command.log").write_text(f"command: {command}\nerror: {exc}\n", encoding="utf-8")
            return RunnerResult(
                status="failed",
                exit_code=None,
                produced_files=[],
                error_message=str(exc),
                started_at=started,
                finished_at=finished,
            )
