from pathlib import Path
import re

from backend.app.models import Stage
from backend.app.services.event_service import read_events
from backend.app.services.file_service import write_json
from backend.app.services.runner_service import import_existing_stage_output
from backend.app.services.state_service import recompute_state


OUTPUT_FILE_PATTERN = re.compile(r"^OUTPUT_FILE:\s*(.+)$", re.MULTILINE)


def get_runner_handoffs(run_dir: Path) -> dict[str, object]:
    handoffs: list[dict[str, object]] = []
    for event in read_events(run_dir):
        if event.get("event_type") != "runner_waiting":
            continue
        related_file = str(event.get("related_file") or "")
        log_file = run_dir / related_file if related_file else None
        instruction_file = log_file.parent / "antigravity_instruction.md" if log_file else None
        instruction = (
            instruction_file.read_text(encoding="utf-8", errors="replace")
            if instruction_file and instruction_file.is_file()
            else ""
        ).lstrip("\ufeff")
        output_match = OUTPUT_FILE_PATTERN.search(instruction)
        handoffs.append(
            {
                "event_id": event.get("id"),
                "agent_id": event.get("actor"),
                "stage": event.get("stage"),
                "message": event.get("message"),
                "related_file": related_file,
                "instruction_file": instruction_file.relative_to(run_dir).as_posix() if instruction_file else None,
                "instruction": instruction,
                "output_file": output_match.group(1).strip() if output_match else "",
                "metadata": event.get("metadata") or {},
            }
        )
    return {"run_id": run_dir.name, "handoffs": handoffs}


def import_waiting_runner_outputs(run_dir: Path) -> dict[str, object]:
    projection = recompute_state(run_dir)
    current_stage = projection.stage
    imported: list[str] = []
    errors: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for event in read_events(run_dir):
        if event.get("event_type") != "runner_waiting" or event.get("stage") != current_stage.value:
            continue
        agent_id = str(event.get("actor"))
        key = (agent_id, current_stage.value)
        if key in seen:
            continue
        seen.add(key)
        try:
            path = import_existing_stage_output(run_dir, agent_id, Stage(current_stage))
            if path:
                imported.append(path.relative_to(run_dir).as_posix())
            else:
                imported.append(f"agents/{agent_id}/synthesis")
        except Exception as exc:
            errors.append({"agent_id": agent_id, "stage": current_stage.value, "error": str(exc)})
    projection = recompute_state(run_dir)
    write_json(run_dir / "run.json", projection.model_dump(mode="json"))
    return {"projection": projection.model_dump(mode="json"), "imported": imported, "errors": errors}
