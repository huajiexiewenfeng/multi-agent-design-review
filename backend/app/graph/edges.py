from langgraph.graph import END, StateGraph

from backend.app.graph.nodes import (
    checkpoint_node,
    clarification_node,
    draft_node,
    load_projection_node,
    review_node,
    revision_node,
    synthesis_node,
)
from backend.app.graph.state import WorkflowState


def _after_checkpoint(state: WorkflowState) -> str:
    if state.get("checkpoint"):
        return END
    return {
        "requirement": "clarification",
        "clarification": "clarification",
        "clarified_requirement": "draft",
        "draft_design": "draft",
        "cross_review": "review",
        "revision": "revision",
        "synthesis": "synthesis",
    }.get(state["stage"], END)


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("load_projection", load_projection_node)
    graph.add_node("checkpoint", checkpoint_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("draft", draft_node)
    graph.add_node("review", review_node)
    graph.add_node("revision", revision_node)
    graph.add_node("synthesis", synthesis_node)
    graph.set_entry_point("load_projection")
    graph.add_edge("load_projection", "checkpoint")
    graph.add_conditional_edges(
        "checkpoint",
        _after_checkpoint,
        {
            END: END,
            "clarification": "clarification",
            "draft": "draft",
            "review": "review",
            "revision": "revision",
            "synthesis": "synthesis",
        },
    )
    graph.add_edge("clarification", END)
    graph.add_edge("draft", END)
    graph.add_edge("review", END)
    graph.add_edge("revision", END)
    graph.add_edge("synthesis", END)
    return graph.compile()
