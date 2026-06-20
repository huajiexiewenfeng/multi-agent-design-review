from datetime import datetime
import os
from pathlib import Path

from backend.app.services.runner_registry_service import resolve_runner_command
from backend.app.services.runner_service import get_runner


def _read_log_content(log_dir: Path) -> str:
    command_log = log_dir / "command.log"
    if command_log.is_file():
        return command_log.read_text(encoding="utf-8", errors="replace")
    log_parts = []
    for path in sorted(log_dir.glob("*.log")):
        log_parts.append(f"## {path.name}\n{path.read_text(encoding='utf-8', errors='replace')}")
    return "\n\n".join(log_parts)


def run_runner_smoke_test(
    runner_id: str,
    runs_root: Path,
    model: str | None = None,
    timeout_seconds: int | None = None,
) -> dict[str, object]:
    if runner_id == "antigravity":
        return {
            "runner_id": runner_id,
            "model": model,
            "status": "interactive_only",
            "exit_code": None,
            "output_content": "",
            "log_content": "",
            "error_message": "Antigravity is interactive-only in this MVP; use handoff instead of smoke test.",
            "smoke_dir": "",
        }

    command = resolve_runner_command(runner_id, model)
    if not command:
        return {
            "runner_id": runner_id,
            "model": model,
            "status": "unconfigured",
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

    runner = get_runner(runner_id, model)
    result = runner.run(
        run_id=smoke_dir.name,
        agent_id="smoke",
        stage="smoke",
        prompt_file=prompt_file,
        inbox_dir=inbox_dir,
        runner_log_dir=log_dir,
        timeout_seconds=timeout_seconds or int(os.environ.get("MADR_RUNNER_TIMEOUT_SECONDS", "180")),
        metadata={},
    )
    output_file = inbox_dir / "smoke_result.md"
    output_content = (
        output_file.read_text(encoding="utf-8", errors="replace").strip() if output_file.is_file() else ""
    )
    status = result.status
    error_message = result.error_message
    if result.status == "waiting_input":
        status = "waiting_input"
    elif "MADR_RUNNER_SMOKE_OK" not in output_content:
        status = "failed"
        error_message = "Smoke output did not contain MADR_RUNNER_SMOKE_OK"
    return {
        "runner_id": runner_id,
        "model": model,
        "status": status,
        "exit_code": result.exit_code,
        "output_content": output_content,
        "log_content": _read_log_content(log_dir),
        "error_message": error_message,
        "smoke_dir": str(smoke_dir.relative_to(runs_root)),
    }
