from datetime import datetime, timezone
from pathlib import Path
import subprocess
import time

from backend.app.runners.base import RunnerResult


class AntigravityRunner:
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
        instruction_file = runner_log_dir / "antigravity_instruction.md"
        stdout_file = runner_log_dir / "stdout.log"
        stderr_file = runner_log_dir / "stderr.log"
        original_prompt = prompt_file.read_text(encoding="utf-8", errors="replace")
        instruction_file.write_text(
            "You are running inside an automated multi-agent design review workflow.\n"
            "Write your final answer to the exact file path below and then stop.\n"
            f"OUTPUT_FILE: {output_file.resolve()}\n\n"
            "Create parent directories if needed. Do not ask the human to copy anything.\n"
            "Do not write analysis outside the output file.\n\n"
            "Original prompt:\n"
            f"{original_prompt}\n",
            encoding="utf-8",
        )
        command = self.command_template.format(
            run_id=run_id,
            agent_id=agent_id,
            stage=stage,
            prompt_file=str(prompt_file.resolve()),
            instruction_file=str(instruction_file.resolve()),
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
                    launcher_exited_for = 0
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
                        elif process.poll() is not None:
                            launcher_exited_for += 1
                            if launcher_exited_for >= 5:
                                break
                        time.sleep(1)

                    if process.poll() is None:
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
            status = "succeeded" if produced_files else "waiting_input"
            log = (
                f"command: {command}\n"
                f"exit_code: {process.returncode}\n"
                f"output_file: {output_file.resolve()}\n\n"
                f"status: {status}\n"
                f"stdout:\n{stdout}\n\n"
                f"stderr:\n{stderr}\n"
            )
            if status == "waiting_input":
                log += "\nwaiting for Antigravity to write the output file asynchronously.\n"
            (runner_log_dir / "antigravity.log").write_text(log, encoding="utf-8")
            finished = datetime.now(timezone.utc).isoformat()
            return RunnerResult(
                status=status,
                exit_code=process.returncode,
                produced_files=produced_files,
                stdout_summary=stdout[:500],
                stderr_summary=stderr[:500],
                error_message=None
                if status == "succeeded"
                else "Antigravity launched; waiting for output file",
                started_at=started,
                finished_at=finished,
            )
        except Exception as exc:
            finished = datetime.now(timezone.utc).isoformat()
            (runner_log_dir / "antigravity.log").write_text(f"command: {command}\nerror: {exc}\n", encoding="utf-8")
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
