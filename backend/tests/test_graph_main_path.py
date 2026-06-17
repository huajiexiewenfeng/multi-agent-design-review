from backend.app.graph.edges import build_workflow
from backend.app.services.clarification_service import merge_clarification_questions
from backend.app.services.human_input_service import save_clarification_answers, save_clarified_requirement
from backend.app.services.run_service import create_run


def test_graph_main_path_runs_each_stage_without_crossing_human_gate(tmp_path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    graph = build_workflow()
    run_dir = tmp_path / projection.run_id

    first = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": False})
    assert first["checkpoint"] is True
    assert first["stage"] == "requirement"

    clarification = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert clarification["stage"] == "clarified_requirement"
    assert (run_dir / "agents" / "architect" / "clarification_questions.v1.md").is_file()

    merge_clarification_questions(run_dir)
    save_clarification_answers(run_dir, {"q_001": "Local developer"})
    save_clarified_requirement(run_dir, "# Clarified Requirement\nLocal developer")

    draft = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert draft["stage"] == "cross_review"
    assert (run_dir / "agents" / "architect" / "draft_response.v1.md").is_file()
    assert (run_dir / "agents" / "engineer" / "draft_response.v1.md").is_file()

    review = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert review["stage"] == "revision"
    assert (run_dir / "agents" / "reviewer" / "review_response.v1.md").is_file()

    revision = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert revision["stage"] == "synthesis"
    assert (run_dir / "agents" / "architect" / "revision_response.v1.md").is_file()

    synthesis = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert synthesis["stage"] == "synthesis"
    assert (run_dir / "agents" / "synthesizer" / "design_doc.v1.md").is_file()
    assert (run_dir / "agents" / "synthesizer" / "execution_doc.v1.md").is_file()
