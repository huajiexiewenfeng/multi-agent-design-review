from pathlib import Path

from backend.app.models import RunProjection, Stage, StageStatus
from backend.app.services.event_service import read_events


def _is_non_empty_file(path: Path) -> bool:
    return path.is_file() and path.read_text(encoding="utf-8").strip() != ""


def _has_version(run_dir: Path, pattern: str) -> bool:
    return bool(list(run_dir.glob(pattern)))


def _skipped(events: list[dict[str, object]], stage: Stage, agent: str) -> bool:
    return any(
        event.get("event_type") == "agent_skipped" and event.get("stage") == stage.value and event.get("actor") == agent
        for event in events
    )


def _missing_agent_versions(
    run_dir: Path,
    events: list[dict[str, object]],
    stage: Stage,
    agents: list[str],
    artifact: str,
) -> list[str]:
    missing: list[str] = []
    for agent in agents:
        if _skipped(events, stage, agent):
            continue
        pattern = f"agents/{agent}/{artifact}.v*.md"
        if not _has_version(run_dir, pattern):
            missing.append(pattern)
    return missing


def _required_answers_ready(run_dir: Path) -> bool:
    questions = run_dir / "input" / "clarification_questions.json"
    answers = run_dir / "input" / "human_answers.json"
    return _is_non_empty_file(questions) and _is_non_empty_file(answers)


def _projection(run_dir: Path, stage: Stage, missing: list[str]) -> RunProjection:
    return RunProjection(
        run_id=run_dir.name,
        stage=stage,
        status=StageStatus.READY_TO_ADVANCE if not missing else StageStatus.WAITING_INPUT,
        missing_inputs=missing,
    )


def recompute_state(run_dir: Path) -> RunProjection:
    events = read_events(run_dir)
    if not _is_non_empty_file(run_dir / "input" / "requirement.md"):
        return _projection(run_dir, Stage.REQUIREMENT, ["input/requirement.md"])

    missing = _missing_agent_versions(
        run_dir,
        events,
        Stage.CLARIFICATION,
        ["architect", "engineer", "reviewer"],
        "clarification_questions",
    )
    if missing:
        return _projection(run_dir, Stage.CLARIFICATION, missing)

    clarified_missing = []
    if not _required_answers_ready(run_dir):
        clarified_missing.extend(["input/clarification_questions.json", "input/human_answers.json"])
    if not _is_non_empty_file(run_dir / "input" / "clarified_requirement.md"):
        clarified_missing.append("input/clarified_requirement.md")
    if clarified_missing:
        return _projection(run_dir, Stage.CLARIFIED_REQUIREMENT, clarified_missing)

    missing = _missing_agent_versions(run_dir, events, Stage.DRAFT_DESIGN, ["architect", "engineer"], "draft_response")
    if missing:
        return _projection(run_dir, Stage.DRAFT_DESIGN, missing)

    missing = _missing_agent_versions(
        run_dir,
        events,
        Stage.CROSS_REVIEW,
        ["architect", "engineer", "reviewer"],
        "review_response",
    )
    if missing:
        return _projection(run_dir, Stage.CROSS_REVIEW, missing)

    missing = _missing_agent_versions(run_dir, events, Stage.REVISION, ["architect", "engineer"], "revision_response")
    if missing:
        return _projection(run_dir, Stage.REVISION, missing)

    synthesis_missing = []
    if not _has_version(run_dir, "agents/synthesizer/design_doc.v*.md"):
        synthesis_missing.append("agents/synthesizer/design_doc.v*.md")
    if not _has_version(run_dir, "agents/synthesizer/execution_doc.v*.md"):
        synthesis_missing.append("agents/synthesizer/execution_doc.v*.md")
    return _projection(run_dir, Stage.SYNTHESIS, synthesis_missing)
