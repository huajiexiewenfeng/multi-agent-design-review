from backend.app.graph.edges import build_workflow
from backend.app.models import Stage
from backend.app.services.finalize_service import finalize_run
from backend.app.services.human_input_service import save_clarification_answers, save_clarified_requirement
from backend.app.services.run_service import create_run
from backend.app.services.workflow_service import import_from_inbox


def test_graph_driven_flow_reaches_clarification_checkpoint_then_finalizes(tmp_path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    graph = build_workflow()
    run_dir = tmp_path / projection.run_id

    first = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": False})
    assert first["checkpoint"] is True

    second = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert (run_dir / "agents" / "architect" / "clarification_questions.v1.md").is_file()

    (run_dir / "input" / "clarification_questions.json").write_text(
        '{"questions":[{"id":"q_001","required":true}]}',
        encoding="utf-8",
    )
    save_clarification_answers(run_dir, {"q_001": "Local developer"})
    save_clarified_requirement(run_dir, "# Clarified Requirement\nLocal developer")

    draft = "## Summary\nA\n\n## Proposed Design\nB\n\n## Modules\nC\n\n## Data Flow\nD\n\n## Risks\nE\n\n## Open Questions\nF\n"
    for agent in ["architect", "engineer"]:
        inbox = run_dir / "inbox" / agent
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "draft.md").write_text(draft, encoding="utf-8")
        import_from_inbox(run_dir, agent, Stage.DRAFT_DESIGN)

    review = "## Review Summary\nA\n\n## Issues\nB\n\n## Conflicts\nC\n\n## Suggestions\nD\n\n## Questions For Human\nE\n"
    for agent in ["architect", "engineer", "reviewer"]:
        inbox = run_dir / "inbox" / agent
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "review.md").write_text(review, encoding="utf-8")
        import_from_inbox(run_dir, agent, Stage.CROSS_REVIEW)

    revision = "## Revised Design\nA\n\n## Changes Made\nB\n\n## Remaining Risks\nC\n\n## Implementation Notes\nD\n"
    for agent in ["architect", "engineer"]:
        inbox = run_dir / "inbox" / agent
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "revision.md").write_text(revision, encoding="utf-8")
        import_from_inbox(run_dir, agent, Stage.REVISION)

    synth = run_dir / "agents" / "synthesizer"
    synth.mkdir(parents=True, exist_ok=True)
    (synth / "design_doc.v1.md").write_text("# Design Document\n\n## Architecture\nFile-first", encoding="utf-8")
    (synth / "execution_doc.v1.md").write_text("# Execution Document\n\n## Implementation Plan\nBuild", encoding="utf-8")
    finalize_run(run_dir)

    assert (run_dir / "output" / "design_doc.md").is_file()
    assert (run_dir / "output" / "execution_doc.md").is_file()
