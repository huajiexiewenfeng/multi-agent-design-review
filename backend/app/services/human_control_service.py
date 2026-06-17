from pathlib import Path

from backend.app.models import ActorType, Stage
from backend.app.services.event_service import append_event
from backend.app.services.file_service import run_lock, write_json
from backend.app.services.state_service import recompute_state


def advance_stage(run_dir: Path):
    with run_lock(run_dir):
        projection = recompute_state(run_dir)
        append_event(
            run_dir,
            projection.stage,
            "human",
            ActorType.HUMAN,
            "stage_advanced",
            f"Advanced from {projection.stage.value}",
        )
        updated = recompute_state(run_dir)
        write_json(run_dir / "run.json", updated.model_dump(mode="json"))
        return updated


def skip_agent(run_dir: Path, agent_id: str, stage: Stage, reason: str):
    with run_lock(run_dir):
        append_event(
            run_dir,
            stage,
            agent_id,
            ActorType.AGENT,
            "agent_skipped",
            reason,
            metadata={"reason": reason},
        )
        updated = recompute_state(run_dir)
        write_json(run_dir / "run.json", updated.model_dump(mode="json"))
        return updated


def revert_stage(run_dir: Path, reason: str):
    with run_lock(run_dir):
        projection = recompute_state(run_dir)
        append_event(
            run_dir,
            projection.stage,
            "human",
            ActorType.HUMAN,
            "stage_reverted",
            reason,
            metadata={"reason": reason},
        )
        updated = recompute_state(run_dir)
        write_json(run_dir / "run.json", updated.model_dump(mode="json"))
        return updated
