from pathlib import Path
import json

from backend.app.services.clarification_service import merge_clarification_questions


def test_merge_clarification_questions_writes_json_and_markdown(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    for agent in ["architect", "engineer"]:
        (run_dir / "agents" / agent).mkdir(parents=True)
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "agents" / "architect" / "clarification_questions.v1.md").write_text(
        "## Clarification Questions\n\n1. [required] Who is the user?\n\n## Assumptions\n",
        encoding="utf-8",
    )
    (run_dir / "agents" / "engineer" / "clarification_questions.v1.md").write_text(
        "## Clarification Questions\n\n1. What platform must run first?\n\n## Assumptions\n",
        encoding="utf-8",
    )

    merge_clarification_questions(run_dir)

    data = json.loads((run_dir / "input" / "clarification_questions.json").read_text(encoding="utf-8"))
    assert len(data["questions"]) == 2
    assert data["questions"][0]["required"] is True
    assert "Who is the user?" in (run_dir / "input" / "clarification_questions.md").read_text(encoding="utf-8")
