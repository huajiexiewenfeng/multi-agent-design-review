from datetime import datetime
import json
from pathlib import Path
from uuid import uuid4

from backend.app.models import ActorType, Stage
from backend.app.services.event_service import append_event
from backend.app.services.event_service import read_events
from backend.app.services.file_service import run_lock, write_json, write_text
from backend.app.services.state_service import recompute_state

AGENTS = ["architect", "engineer", "reviewer", "synthesizer"]


def _new_run_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{uuid4().hex[:4]}"


def _create_directories(run_dir: Path) -> None:
    for path in [
        "input",
        "human",
        "output",
        *[f"agents/{agent}" for agent in AGENTS],
        *[f"inbox/{agent}" for agent in AGENTS],
        *[f"runner_logs/{agent}" for agent in AGENTS],
    ]:
        (run_dir / path).mkdir(parents=True, exist_ok=True)


def create_run(runs_root: Path, title: str, requirement: str):
    run_id = _new_run_id()
    run_dir = runs_root / run_id
    with run_lock(run_dir):
        _create_directories(run_dir)
        write_text(run_dir / "input" / "requirement.md", requirement)
        write_text(run_dir / "events.jsonl", "")
        write_text(
            run_dir / "runners.yaml",
            "architect: mock\nengineer: mock\nreviewer: mock\nsynthesizer: mock\n",
        )
        append_event(
            run_dir,
            Stage.REQUIREMENT,
            "system",
            ActorType.SYSTEM,
            "run_created",
            f"Created run: {title}",
            "input/requirement.md",
            {"title": title},
        )
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json"))
        return projection


def _title_from_events(run_dir: Path) -> str:
    for event in read_events(run_dir):
        if event.get("event_type") != "run_created":
            continue
        metadata = event.get("metadata")
        if isinstance(metadata, dict) and isinstance(metadata.get("title"), str):
            return str(metadata["title"])
    return run_dir.name


def list_runs(runs_root: Path) -> list[dict[str, object]]:
    if not runs_root.exists():
        return []
    runs = []
    for run_json in sorted(runs_root.glob("*/run.json"), key=lambda path: path.stat().st_mtime_ns, reverse=True):
        run = json.loads(run_json.read_text(encoding="utf-8"))
        if not isinstance(run.get("title"), str) or not str(run["title"]).strip():
            run["title"] = _title_from_events(run_json.parent)
        runs.append(run)
    return runs


def get_run_dir(runs_root: Path, run_id: str) -> Path:
    run_dir = runs_root / run_id
    if not run_dir.is_dir():
        raise FileNotFoundError(run_id)
    return run_dir
