from pathlib import Path

from backend.app.models import Stage
from backend.app.services.prompt_service import render_prompt


def test_draft_prompt_does_not_include_other_agent_draft(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "agents" / "engineer").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("Original requirement", encoding="utf-8")
    (run_dir / "input" / "human_answers.md").write_text("Human answer", encoding="utf-8")
    (run_dir / "input" / "clarified_requirement.md").write_text("Clarified requirement", encoding="utf-8")
    (run_dir / "agents" / "engineer" / "draft_response.v1.md").write_text(
        "Engineer draft should not appear",
        encoding="utf-8",
    )

    prompt = render_prompt(Stage.DRAFT_DESIGN, "architect", run_dir)

    assert "Original requirement" in prompt
    assert "Human answer" in prompt
    assert "Clarified requirement" in prompt
    assert "Engineer draft should not appear" not in prompt


def test_review_prompt_includes_all_drafts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_002"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "agents" / "architect").mkdir(parents=True)
    (run_dir / "agents" / "engineer").mkdir(parents=True)
    (run_dir / "input" / "clarified_requirement.md").write_text("Clarified", encoding="utf-8")
    (run_dir / "agents" / "architect" / "draft_response.v1.md").write_text("Architect draft", encoding="utf-8")
    (run_dir / "agents" / "engineer" / "draft_response.v1.md").write_text("Engineer draft", encoding="utf-8")

    prompt = render_prompt(Stage.CROSS_REVIEW, "reviewer", run_dir)

    assert "Architect draft" in prompt
    assert "Engineer draft" in prompt
