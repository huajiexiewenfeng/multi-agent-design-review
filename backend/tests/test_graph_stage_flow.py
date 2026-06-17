from pathlib import Path

from backend.app.graph.edges import build_workflow
from backend.app.services.run_service import create_run


def test_graph_runs_clarification_with_mock_runner(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild")
    graph = build_workflow()

    result = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})

    run_dir = tmp_path / projection.run_id
    assert result["stage"] in {"clarification", "clarified_requirement"}
    assert (run_dir / "agents" / "architect" / "clarification_questions.v1.md").is_file()
    assert "file_imported" in (run_dir / "events.jsonl").read_text(encoding="utf-8")
