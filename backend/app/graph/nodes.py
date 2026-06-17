from pathlib import Path

from backend.app.graph.state import WorkflowState
from backend.app.models import Stage
from backend.app.services.runner_service import run_agent_stage
from backend.app.services.state_service import recompute_state


def load_projection_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value}


def clarification_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    for agent in ["architect", "engineer", "reviewer"]:
        if not list((run_dir / "agents" / agent).glob("clarification_questions.v*.md")):
            run_agent_stage(run_dir, agent, Stage.CLARIFICATION)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value}
