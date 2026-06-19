from pathlib import Path

from backend.app.models import ActorType, Stage
from backend.app.services.event_service import append_event
from backend.app.services.flow_verification_service import get_mixed_runner_verification


def test_mixed_runner_verification_requires_outputs_and_all_runner_evidence(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    (run_dir / "output").mkdir(parents=True)
    (run_dir / "output" / "design_doc.md").write_text("# Design Document\n\nDone", encoding="utf-8")
    (run_dir / "output" / "execution_doc.md").write_text("# Execution Document\n\nDone", encoding="utf-8")

    append_event(
        run_dir,
        Stage.DRAFT_DESIGN,
        "architect",
        ActorType.AGENT,
        "runner_succeeded",
        "codex completed",
        "runner_logs/architect/command.log",
        {"runner": "codex", "status": "succeeded", "produced_files": ["draft_result.md"]},
    )
    append_event(
        run_dir,
        Stage.CROSS_REVIEW,
        "engineer",
        ActorType.AGENT,
        "runner_succeeded",
        "claude completed",
        "runner_logs/engineer/command.log",
        {"runner": "claude-code", "status": "succeeded", "produced_files": ["review_result.md"]},
    )
    append_event(
        run_dir,
        Stage.REVISION,
        "reviewer",
        ActorType.AGENT,
        "runner_waiting",
        "Antigravity launched",
        "runner_logs/reviewer/antigravity.log",
        {"runner": "antigravity", "status": "waiting_input"},
    )

    result = get_mixed_runner_verification(run_dir)

    assert result["complete"] is True
    assert result["final_outputs_ready"] is True
    assert {item["runner"]: item["satisfied"] for item in result["runners"]} == {
        "codex": True,
        "claude-code": True,
        "antigravity": True,
    }
    antigravity = next(item for item in result["runners"] if item["runner"] == "antigravity")
    assert antigravity["evidence"][0]["event_type"] == "runner_waiting"


def test_mixed_runner_verification_reports_missing_runner_and_output(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    (run_dir / "output").mkdir(parents=True)
    (run_dir / "output" / "design_doc.md").write_text("# Design Document\n\nDone", encoding="utf-8")
    append_event(
        run_dir,
        Stage.DRAFT_DESIGN,
        "architect",
        ActorType.AGENT,
        "runner_succeeded",
        "codex completed",
        "runner_logs/architect/command.log",
        {"runner": "codex", "status": "succeeded"},
    )

    result = get_mixed_runner_verification(run_dir)

    assert result["complete"] is False
    assert result["final_outputs_ready"] is False
    assert result["final_outputs"][1]["path"] == "output/execution_doc.md"
    assert result["final_outputs"][1]["exists"] is False
    missing = [item["runner"] for item in result["runners"] if not item["satisfied"]]
    assert missing == ["claude-code", "antigravity"]
