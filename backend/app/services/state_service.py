from pathlib import Path

from backend.app.models import RunProjection, Stage, StageStatus


def _is_non_empty_file(path: Path) -> bool:
    return path.is_file() and path.read_text(encoding="utf-8").strip() != ""


def recompute_state(run_dir: Path) -> RunProjection:
    requirement = run_dir / "input" / "requirement.md"
    run_id = run_dir.name

    if not _is_non_empty_file(requirement):
        return RunProjection(
            run_id=run_id,
            stage=Stage.REQUIREMENT,
            status=StageStatus.WAITING_INPUT,
            missing_inputs=["input/requirement.md"],
        )

    return RunProjection(
        run_id=run_id,
        stage=Stage.REQUIREMENT,
        status=StageStatus.READY_TO_ADVANCE,
        missing_inputs=[],
    )
