from pathlib import Path

from backend.app.models import Stage, StageStatus
from backend.app.services.event_service import append_event
from backend.app.services.state_service import recompute_state
from backend.app.models import ActorType


def test_requirement_moves_to_clarification_when_requirement_file_is_non_empty(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Build a workbench\n", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.CLARIFICATION
    assert projection.status == StageStatus.WAITING_INPUT
    assert projection.missing_inputs == [
        "agents/architect/clarification_questions.v*.md",
        "agents/engineer/clarification_questions.v*.md",
        "agents/reviewer/clarification_questions.v*.md",
    ]


def test_requirement_waits_when_requirement_file_is_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "run_002"
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.REQUIREMENT
    assert projection.status == StageStatus.WAITING_INPUT
    assert projection.missing_inputs == ["input/requirement.md"]


def _write_ready_for_synthesis(run_dir: Path, version: int = 1) -> None:
    (run_dir / "input").mkdir(parents=True, exist_ok=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\nBuild", encoding="utf-8")
    (run_dir / "input" / "clarification_questions.json").write_text('{"questions":[]}', encoding="utf-8")
    (run_dir / "input" / "human_answers.json").write_text('{"answers":{"human_response":"ok"}}', encoding="utf-8")
    (run_dir / "input" / "human_answers.md").write_text("# Human Answers\n\nok\n", encoding="utf-8")
    (run_dir / "input" / "clarified_requirement.md").write_text("# Clarified\nBuild", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    for agent in ["architect", "engineer", "reviewer"]:
        (run_dir / "agents" / agent).mkdir(parents=True, exist_ok=True)
        (run_dir / "agents" / agent / "clarification_questions.v1.md").write_text(
            "## Clarification Questions\n\n1. [required] Q?",
            encoding="utf-8",
        )
        if agent != "reviewer":
            (run_dir / "agents" / agent / "draft_response.v1.md").write_text(
                "## Proposed Design\nDraft",
                encoding="utf-8",
            )
            (run_dir / "agents" / agent / f"revision_response.v{version}.md").write_text(
                "## Revised Design\nRevision",
                encoding="utf-8",
            )
        (run_dir / "agents" / agent / f"review_response.v{version}.md").write_text(
            "## Review Summary\nReview",
            encoding="utf-8",
        )
    (run_dir / "agents" / "synthesizer").mkdir(parents=True, exist_ok=True)
    (run_dir / "agents" / "synthesizer" / f"design_doc.v{version}.md").write_text(
        "# Design Document\n\n## Architecture\nDesign",
        encoding="utf-8",
    )
    (run_dir / "agents" / "synthesizer" / f"execution_doc.v{version}.md").write_text(
        "# Execution Document\n\n## Implementation Plan\nPlan",
        encoding="utf-8",
    )


def test_synthesis_waits_for_human_final_approval(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "run_003"
    _write_ready_for_synthesis(run_dir)

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.SYNTHESIS
    assert projection.status == StageStatus.WAITING_INPUT
    assert projection.missing_inputs == ["input/final_approval.md"]


def test_reopened_discussion_requires_next_review_revision_and_synthesis_versions(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "run_004"
    _write_ready_for_synthesis(run_dir)
    append_event(
        run_dir,
        Stage.SYNTHESIS,
        "human",
        ActorType.HUMAN,
        "discussion_reopened",
        "Need another round",
        "input/discussion_requests/request_changes.v2.md",
        {"required_version": 2},
    )

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.CROSS_REVIEW
    assert projection.missing_inputs == [
        "agents/architect/review_response.v2.md",
        "agents/engineer/review_response.v2.md",
        "agents/reviewer/review_response.v2.md",
    ]

    for agent in ["architect", "engineer", "reviewer"]:
        (run_dir / "agents" / agent / "review_response.v2.md").write_text("## Review Summary\nRound 2", encoding="utf-8")
    projection = recompute_state(run_dir)
    assert projection.stage == Stage.REVISION
    assert projection.missing_inputs == [
        "agents/architect/revision_response.v2.md",
        "agents/engineer/revision_response.v2.md",
    ]

    for agent in ["architect", "engineer"]:
        (run_dir / "agents" / agent / "revision_response.v2.md").write_text("## Revised Design\nRound 2", encoding="utf-8")
    projection = recompute_state(run_dir)
    assert projection.stage == Stage.SYNTHESIS
    assert projection.missing_inputs == [
        "agents/synthesizer/design_doc.v2.md",
        "agents/synthesizer/execution_doc.v2.md",
    ]
