from pathlib import Path

import yaml

from backend.app.models import AgentProjection, RunProjection, Stage, StageStatus
from backend.app.services.event_service import read_events


AGENT_DEFINITIONS = {
    "architect": {
        "label": "Architect",
        "stages": [Stage.CLARIFICATION, Stage.DRAFT_DESIGN, Stage.CROSS_REVIEW, Stage.REVISION],
    },
    "engineer": {
        "label": "Engineer",
        "stages": [Stage.CLARIFICATION, Stage.DRAFT_DESIGN, Stage.CROSS_REVIEW, Stage.REVISION],
    },
    "reviewer": {
        "label": "Reviewer",
        "stages": [Stage.CLARIFICATION, Stage.CROSS_REVIEW],
    },
    "synthesizer": {
        "label": "Synthesizer",
        "stages": [Stage.SYNTHESIS],
    },
}

RUNNER_LLM_NAMES = {
    "mock": "Mock runner",
    "manual": "Manual CLI",
    "file": "File drop",
    "codex": "Codex CLI",
    "claude-code": "Claude Code",
    "antigravity": "Antigravity",
}


def _is_non_empty_file(path: Path) -> bool:
    return path.is_file() and path.read_text(encoding="utf-8").strip() != ""


def _has_version(run_dir: Path, pattern: str) -> bool:
    return bool(list(run_dir.glob(pattern)))


def _read_runner_config(run_dir: Path) -> dict[str, dict[str, str]]:
    runners_file = run_dir / "runners.yaml"
    if not runners_file.is_file():
        return {}

    raw = yaml.safe_load(runners_file.read_text(encoding="utf-8")) or {}
    runners: dict[str, dict[str, str]] = {}
    for agent_id, value in raw.items():
        if isinstance(value, str):
            runners[agent_id] = {"runner": value, "llm_name": RUNNER_LLM_NAMES.get(value, value)}
        elif isinstance(value, dict):
            runner = str(value.get("runner", "mock"))
            llm_name = str(value.get("llm_name") or RUNNER_LLM_NAMES.get(runner, runner))
            runners[agent_id] = {"runner": runner, "llm_name": llm_name}
    return runners


def _agents(run_dir: Path) -> list[AgentProjection]:
    runners = _read_runner_config(run_dir)
    agents: list[AgentProjection] = []
    for agent_id, definition in AGENT_DEFINITIONS.items():
        config = runners.get(agent_id, {"runner": "mock", "llm_name": "Mock runner"})
        runner = config["runner"]
        agents.append(
            AgentProjection(
                id=agent_id,
                label=str(definition["label"]),
                runner=runner,
                llm_name=config["llm_name"],
                stages=list(definition["stages"]),
            )
        )
    return agents


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
        agents=_agents(run_dir),
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
