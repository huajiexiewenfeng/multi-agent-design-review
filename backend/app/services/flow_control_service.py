from pathlib import Path

from backend.app.models import Stage, StageStatus
from backend.app.services.graph_service import run_graph_step
from backend.app.services.runner_handoff_service import get_runner_handoffs
from backend.app.services.run_service import get_run_dir
from backend.app.services.state_service import recompute_state


def run_until_pause(runs_root: Path, run_id: str, max_steps: int = 10) -> dict[str, object]:
    steps: list[dict[str, object]] = []
    stop_reason = "max_steps"
    projection: dict[str, object] | None = None

    for _ in range(max_steps):
        before_stage = recompute_state(get_run_dir(runs_root, run_id)).stage.value
        result = run_graph_step(runs_root, run_id, confirmed=True)
        projection = result["projection"]
        steps.append(result)

        stop_reason = _stop_reason(runs_root, run_id, before_stage, projection)
        if stop_reason != "continue":
            break

    return {
        "run_id": run_id,
        "status": "paused",
        "stop_reason": stop_reason,
        "steps_run": len(steps),
        "projection": projection,
        "steps": steps,
    }


def _stop_reason(runs_root: Path, run_id: str, before_stage: str, projection: dict[str, object]) -> str:
    stage = str(projection["stage"])
    missing_inputs = projection.get("missing_inputs") or []
    status = str(projection["status"])

    if _has_current_stage_handoff(runs_root, run_id, stage, _missing_agent_ids(missing_inputs)):
        return "runner_handoff"
    if stage == Stage.CLARIFIED_REQUIREMENT.value and missing_inputs:
        return "human_input"
    if stage == Stage.SYNTHESIS.value and not missing_inputs:
        return "ready_to_finalize"
    if stage == before_stage and status == StageStatus.WAITING_INPUT.value and missing_inputs:
        return "waiting_input"
    return "continue"


def _has_current_stage_handoff(runs_root: Path, run_id: str, stage: str, missing_agents: set[str]) -> bool:
    if not missing_agents:
        return False
    run_dir = get_run_dir(runs_root, run_id)
    handoffs = get_runner_handoffs(run_dir)["handoffs"]
    return any(
        handoff["stage"] == stage and str(handoff.get("agent_id")) in missing_agents
        for handoff in handoffs
    )


def _missing_agent_ids(missing_inputs: object) -> set[str]:
    agents: set[str] = set()
    for missing in missing_inputs:
        parts = str(missing).replace("\\", "/").split("/")
        if len(parts) >= 3 and parts[0] == "agents":
            agents.add(parts[1])
    return agents
