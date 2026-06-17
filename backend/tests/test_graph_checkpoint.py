from backend.app.graph.edges import build_workflow
from backend.app.services.run_service import create_run


def test_graph_stops_at_checkpoint_without_confirmation(tmp_path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild")
    graph = build_workflow()

    result = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": False})

    assert result["checkpoint"] is True
    assert result["stage"] == "requirement"


def test_graph_continues_after_confirmation(tmp_path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild")
    graph = build_workflow()

    result = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})

    assert result["checkpoint"] is False
    assert result["stage"] in {"clarification", "clarified_requirement"}
