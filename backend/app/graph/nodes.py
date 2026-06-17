from pathlib import Path

from backend.app.graph.state import WorkflowState
from backend.app.models import Stage
from backend.app.services.runner_service import run_agent_stage
from backend.app.services.state_service import recompute_state


def load_projection_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value}


def checkpoint_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    projection = recompute_state(run_dir)
    if not state.get("confirmed", False):
        return {**state, "stage": Stage.REQUIREMENT.value, "checkpoint": True}
    return {**state, "stage": projection.stage.value, "checkpoint": False}


def clarification_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    for agent in ["architect", "engineer", "reviewer"]:
        if not list((run_dir / "agents" / agent).glob("clarification_questions.v*.md")):
            run_agent_stage(run_dir, agent, Stage.CLARIFICATION)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value}


def draft_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    for agent in ["architect", "engineer"]:
        if not list((run_dir / "agents" / agent).glob("draft_response.v*.md")):
            run_agent_stage(run_dir, agent, Stage.DRAFT_DESIGN)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value, "checkpoint": False}


def review_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    for agent in ["architect", "engineer", "reviewer"]:
        if not list((run_dir / "agents" / agent).glob("review_response.v*.md")):
            run_agent_stage(run_dir, agent, Stage.CROSS_REVIEW)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value, "checkpoint": False}


def revision_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    for agent in ["architect", "engineer"]:
        if not list((run_dir / "agents" / agent).glob("revision_response.v*.md")):
            run_agent_stage(run_dir, agent, Stage.REVISION)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value, "checkpoint": False}


def synthesis_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    if not list((run_dir / "agents" / "synthesizer").glob("design_doc.v*.md")):
        run_agent_stage(run_dir, "synthesizer", Stage.SYNTHESIS)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value, "checkpoint": False}
