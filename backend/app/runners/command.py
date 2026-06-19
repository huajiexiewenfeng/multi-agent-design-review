from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import time

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
        stdout_file = runner_log_dir / "stdout.log"
        stderr_file = runner_log_dir / "stderr.log"
        command = self.command_template.format(
            run_id=run_id,
            agent_id=agent_id,
            stage=stage,
            prompt_file=str(prompt_file.resolve()),
            output_file=str(output_file.resolve()),
        )
        try:
            with stdout_file.open("w", encoding="utf-8", errors="replace") as stdout_handle:
                with stderr_file.open("w", encoding="utf-8", errors="replace") as stderr_handle:
                    process = subprocess.Popen(
                        command,
                        cwd=prompt_file.parents[2],
                        stdout=stdout_handle,
                        stderr=stderr_handle,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        shell=True,
                    )
                    output_stable_for = 0
                    last_size = -1
                    for _ in range(timeout_seconds):
                        if output_file.is_file() and output_file.stat().st_size > 0:
                            current_size = output_file.stat().st_size
                            if current_size == last_size:
                                output_stable_for += 1
                            else:
                                output_stable_for = 0
                                last_size = current_size
                            if output_stable_for >= 2:
                                break
                        if process.poll() is not None:
                            break
                        time.sleep(1)
                    timed_out = process.poll() is None
                    if timed_out:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                    else:
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
            stdout = stdout_file.read_text(encoding="utf-8", errors="replace")
            stderr = stderr_file.read_text(encoding="utf-8", errors="replace")
            produced_files = [output_file.name] if _is_non_empty_file(output_file) else []
            exit_code = process.returncode
            if stdout.strip() and not _is_non_empty_file(output_file):
                output_file.write_text(stdout, encoding="utf-8")
                produced_files = [output_file.name]
            status = "succeeded" if produced_files and (exit_code in (0, None) or timed_out) else "failed"
            log = (
                f"command: {command}\n"
                f"exit_code: {exit_code}\n"
                f"terminated_after_output: {timed_out and bool(produced_files)}\n\n"
                f"stdout:\n{stdout}\n\n"
                f"stderr:\n{stderr}\n"
            )
            (runner_log_dir / "command.log").write_text(log, encoding="utf-8")
            finished = datetime.now(timezone.utc).isoformat()
            return RunnerResult(
                status=status,
                exit_code=exit_code,
                produced_files=produced_files,
                stdout_summary=stdout[:500],
                stderr_summary=stderr[:500],
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


def _is_non_empty_file(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0
