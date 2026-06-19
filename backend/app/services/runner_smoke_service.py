from datetime import datetime
from pathlib import Path

from backend.app.runners.command import CommandRunner
from backend.app.services.runner_registry_service import resolve_runner_command


def run_runner_smoke_test(
    runner_id: str,
    runs_root: Path,
    timeout_seconds: int = 60,
) -> dict[str, object]:
    command = resolve_runner_command(runner_id)
    if not command:
        return {
            "runner_id": runner_id,
            "status": "failed",
            "exit_code": None,
            "output_content": "",
            "log_content": "",
            "error_message": f"Runner is not configured: {runner_id}",
        }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    smoke_dir = runs_root / "_runner_smoke" / runner_id / stamp
    prompt_file = smoke_dir / "agents" / "smoke" / "smoke_prompt.md"
    inbox_dir = smoke_dir / "inbox" / "smoke"
    log_dir = smoke_dir / "runner_logs" / "smoke"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(
        "Reply exactly: MADR_RUNNER_SMOKE_OK\n"
        "Do not inspect files. Do not run tools unless required by your CLI runtime.\n",
        encoding="utf-8",
    )

    result = CommandRunner(command).run(
        run_id=smoke_dir.name,
        agent_id="smoke",
        stage="smoke",
        prompt_file=prompt_file,
        inbox_dir=inbox_dir,
        runner_log_dir=log_dir,
        timeout_seconds=timeout_seconds,
        metadata={},
    )
    output_file = inbox_dir / "smoke_result.md"
    log_file = log_dir / "command.log"
    return {
        "runner_id": runner_id,
        "status": result.status,
        "exit_code": result.exit_code,
        "output_content": output_file.read_text(encoding="utf-8", errors="replace").strip()
        if output_file.is_file()
        else "",
        "log_content": log_file.read_text(encoding="utf-8", errors="replace") if log_file.is_file() else "",
        "error_message": result.error_message,
        "smoke_dir": str(smoke_dir.relative_to(runs_root)),
    }
