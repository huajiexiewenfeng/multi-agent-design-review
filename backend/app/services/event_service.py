from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from backend.app.models import ActorType, Stage


def append_event(
    run_dir: Path,
    stage: Stage,
    actor: str,
    actor_type: ActorType,
    event_type: str,
    message: str,
    related_file: str | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    event = {
        "id": f"evt_{uuid4().hex[:12]}",
        "run_id": run_dir.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage.value,
        "actor": actor,
        "actor_type": actor_type.value,
        "event_type": event_type,
        "message": message,
        "related_file": related_file,
        "visibility": None,
        "metadata": metadata or {},
    }
    with (run_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_events(run_dir: Path) -> list[dict[str, object]]:
    events_file = run_dir / "events.jsonl"
    if not events_file.is_file():
        return []
    events: list[dict[str, object]] = []
    for raw in events_file.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            events.append(json.loads(raw))
    return events
