from pathlib import Path

import yaml

from backend.app.services.file_service import run_lock, write_json, write_text
from backend.app.services.state_service import AGENT_DEFINITIONS, recompute_state


def update_agent_config(run_dir: Path, agent_id: str, runner: str, model: str):
    if agent_id not in AGENT_DEFINITIONS:
        raise ValueError(f"Unknown agent: {agent_id}")

    with run_lock(run_dir):
        config = _read_config(run_dir)
        config[agent_id] = {"runner": runner, "model": model}
        _write_config(run_dir, config)
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json"))
        return projection


def _read_config(run_dir: Path) -> dict[str, dict[str, str]]:
    runners_file = run_dir / "runners.yaml"
    if not runners_file.is_file():
        return {}

    raw = yaml.safe_load(runners_file.read_text(encoding="utf-8")) or {}
    config: dict[str, dict[str, str]] = {}
    for agent_id, value in raw.items():
        if isinstance(value, str):
            config[agent_id] = {"runner": value, "model": ""}
        elif isinstance(value, dict):
            config[agent_id] = {
                "runner": str(value.get("runner", "mock")),
                "model": str(value.get("model") or value.get("llm_name") or ""),
            }
    return config


def _write_config(run_dir: Path, config: dict[str, dict[str, str]]) -> None:
    ordered = {agent_id: config.get(agent_id, {"runner": "mock", "model": ""}) for agent_id in AGENT_DEFINITIONS}
    write_text(run_dir / "runners.yaml", yaml.safe_dump(ordered, sort_keys=False, allow_unicode=False))
