from pathlib import Path

from backend.app.models import Stage, StageStatus
from backend.app.services.state_service import recompute_state


def test_requirement_ready_when_requirement_file_is_non_empty(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Build a workbench\n", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.REQUIREMENT
    assert projection.status == StageStatus.READY_TO_ADVANCE
    assert projection.missing_inputs == []


def test_requirement_waits_when_requirement_file_is_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "run_002"
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.REQUIREMENT
    assert projection.status == StageStatus.WAITING_INPUT
    assert projection.missing_inputs == ["input/requirement.md"]
