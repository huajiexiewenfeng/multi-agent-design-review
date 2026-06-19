from pathlib import Path

from backend.app.services.event_service import read_events


REQUIRED_RUNNERS = ["codex", "claude-code", "antigravity"]
FINAL_OUTPUTS = ["output/design_doc.md", "output/execution_doc.md"]
RUNNER_EVENT_TYPES = {"runner_succeeded", "runner_waiting"}


def get_mixed_runner_verification(run_dir: Path) -> dict[str, object]:
    events = read_events(run_dir)
    final_outputs = [_output_status(run_dir, path) for path in FINAL_OUTPUTS]
    runners = [_runner_status(events, runner) for runner in REQUIRED_RUNNERS]
    final_outputs_ready = all(output["ready"] for output in final_outputs)

    return {
        "run_id": run_dir.name,
        "complete": final_outputs_ready and all(runner["satisfied"] for runner in runners),
        "final_outputs_ready": final_outputs_ready,
        "final_outputs": final_outputs,
        "runners": runners,
    }


def _output_status(run_dir: Path, path: str) -> dict[str, object]:
    output_file = run_dir / path
    exists = output_file.is_file()
    non_empty = exists and output_file.read_text(encoding="utf-8").strip() != ""
    return {"path": path, "exists": exists, "non_empty": non_empty, "ready": exists and non_empty}


def _runner_status(events: list[dict[str, object]], runner: str) -> dict[str, object]:
    evidence = [
        _runner_event_evidence(event)
        for event in events
        if event.get("event_type") in RUNNER_EVENT_TYPES and event.get("metadata", {}).get("runner") == runner
    ]
    return {"runner": runner, "satisfied": bool(evidence), "evidence": evidence}


def _runner_event_evidence(event: dict[str, object]) -> dict[str, object]:
    return {
        "event_id": event.get("id"),
        "event_type": event.get("event_type"),
        "stage": event.get("stage"),
        "agent_id": event.get("actor"),
        "message": event.get("message"),
        "related_file": event.get("related_file"),
        "metadata": event.get("metadata", {}),
    }
