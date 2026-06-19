from pathlib import Path


def get_runner_logs(run_dir: Path) -> dict[str, object]:
    logs: list[dict[str, str]] = []
    logs_root = run_dir / "runner_logs"
    if logs_root.is_dir():
        for path in sorted(logs_root.glob("*/*.log")):
            logs.append(
                {
                    "agent_id": path.parent.name,
                    "path": str(path.relative_to(run_dir)),
                    "content": path.read_text(encoding="utf-8", errors="replace"),
                }
            )
    return {"run_id": run_dir.name, "logs": logs}
