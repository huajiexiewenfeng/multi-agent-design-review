from pathlib import Path

from backend.app.graph.state import WorkflowState
from backend.app.services.state_service import recompute_state


def load_projection_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value}
