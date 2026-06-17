from langgraph.graph import END, StateGraph

from backend.app.graph.nodes import checkpoint_node, clarification_node, load_projection_node
from backend.app.graph.state import WorkflowState


def _after_checkpoint(state: WorkflowState) -> str:
    return END if state.get("checkpoint") else "clarification"


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("load_projection", load_projection_node)
    graph.add_node("checkpoint", checkpoint_node)
    graph.add_node("clarification", clarification_node)
    graph.set_entry_point("load_projection")
    graph.add_edge("load_projection", "checkpoint")
    graph.add_conditional_edges("checkpoint", _after_checkpoint, {END: END, "clarification": "clarification"})
    graph.add_edge("clarification", END)
    return graph.compile()
