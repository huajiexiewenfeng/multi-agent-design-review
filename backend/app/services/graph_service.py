from pathlib import Path

from backend.app.graph.edges import build_workflow
from backend.app.models import Stage
from backend.app.services.clarification_service import merge_clarification_questions
from backend.app.services.file_service import write_json
from backend.app.services.state_service import recompute_state


def run_graph_step(runs_root: Path, run_id: str, confirmed: bool) -> dict[str, object]:
    run_dir = runs_root / run_id
    if not run_dir.is_dir():
        raise FileNotFoundError(run_id)

    projection = recompute_state(run_dir)
    graph_state = build_workflow().invoke({"run_id": run_id, "runs_root": str(runs_root), "confirmed": confirmed})
    projection = recompute_state(run_dir)
    if projection.stage == Stage.CLARIFIED_REQUIREMENT and "input/clarification_questions.json" in projection.missing_inputs:
        merge_clarification_questions(run_dir)
        projection = recompute_state(run_dir)
    write_json(run_dir / "run.json", projection.model_dump(mode="json"))
    return {
        "projection": projection.model_dump(mode="json"),
        "graph_state": graph_state,
    }
