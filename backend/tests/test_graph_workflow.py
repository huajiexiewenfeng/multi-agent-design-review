from pathlib import Path

from backend.app.graph.edges import build_workflow
from backend.app.services.run_service import create_run


def test_workflow_can_start_requirement_stage(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild")
    graph = build_workflow()

    result = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path)})

    assert result["run_id"] == projection.run_id
    assert result["stage"] == "requirement"
