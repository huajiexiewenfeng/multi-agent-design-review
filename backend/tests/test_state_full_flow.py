from pathlib import Path

from backend.app.models import Stage, StageStatus
from backend.app.services.state_service import recompute_state


def test_state_moves_to_draft_after_clarified_requirement_ready(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "agents" / "architect").mkdir(parents=True)
    (run_dir / "agents" / "engineer").mkdir(parents=True)
    (run_dir / "agents" / "reviewer").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
    (run_dir / "agents" / "architect" / "clarification_questions.v1.md").write_text(
        "## Clarification Questions\n\n## Assumptions\n",
        encoding="utf-8",
    )
    (run_dir / "agents" / "engineer" / "clarification_questions.v1.md").write_text(
        "## Clarification Questions\n\n## Assumptions\n",
        encoding="utf-8",
    )
    (run_dir / "agents" / "reviewer" / "clarification_questions.v1.md").write_text(
        "## Clarification Questions\n\n## Assumptions\n",
        encoding="utf-8",
    )
    (run_dir / "input" / "clarification_questions.json").write_text(
        '{"questions":[{"id":"q_001","required":true}]}',
        encoding="utf-8",
    )
    (run_dir / "input" / "human_answers.json").write_text('{"answers":{"q_001":"Local user"}}', encoding="utf-8")
    (run_dir / "input" / "human_answers.md").write_text("# Human Answers\n\nLocal user\n", encoding="utf-8")
    (run_dir / "input" / "clarified_requirement.md").write_text("# Clarified\n", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.DRAFT_DESIGN
    assert projection.status == StageStatus.WAITING_INPUT
    assert "agents/architect/draft_response.v*.md" in projection.missing_inputs


def test_skip_event_unblocks_missing_reviewer(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_002"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "agents" / "architect").mkdir(parents=True)
    (run_dir / "agents" / "engineer").mkdir(parents=True)
    (run_dir / "agents" / "reviewer").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
    (run_dir / "agents" / "architect" / "clarification_questions.v1.md").write_text(
        "## Clarification Questions\n\n## Assumptions\n",
        encoding="utf-8",
    )
    (run_dir / "agents" / "engineer" / "clarification_questions.v1.md").write_text(
        "## Clarification Questions\n\n## Assumptions\n",
        encoding="utf-8",
    )
    (run_dir / "events.jsonl").write_text(
        '{"event_type":"agent_skipped","stage":"clarification","actor":"reviewer"}\n',
        encoding="utf-8",
    )

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.CLARIFIED_REQUIREMENT
    assert "agents/reviewer/clarification_questions.v*.md" not in projection.missing_inputs
