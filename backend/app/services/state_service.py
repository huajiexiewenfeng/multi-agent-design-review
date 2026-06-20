from pathlib import Path

import json
import re
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

DEFAULT_RUNNER_MODELS = {
    "mock": "Mock runner",
    "manual": "Manual CLI",
    "file": "File drop",
    "codex": "gpt-5.5",
    "claude-code": "opus",
    "antigravity": "Gemini 3.5 Flash (High)",
}


def _is_non_empty_file(path: Path) -> bool:
    return path.is_file() and path.read_text(encoding="utf-8").strip() != ""


def _has_version(run_dir: Path, pattern: str) -> bool:
    return bool(list(run_dir.glob(pattern)))


def _latest_version(run_dir: Path, pattern: str) -> int:
    versions: list[int] = []
    version_pattern = re.compile(r"\.v(\d+)\.md$")
    for path in run_dir.glob(pattern):
        match = version_pattern.search(path.name)
        if match:
            versions.append(int(match.group(1)))
    return max(versions, default=0)


def latest_artifact_version(run_dir: Path, pattern: str) -> int:
    return _latest_version(run_dir, pattern)


def required_discussion_version(run_dir: Path) -> int:
    return _latest_discussion_required_version(read_events(run_dir))


def _latest_discussion_required_version(events: list[dict[str, object]]) -> int:
    required_version = 1
    for event in events:
        if event.get("event_type") != "discussion_reopened":
            continue
        metadata = event.get("metadata")
        if not isinstance(metadata, dict):
            continue
        value = metadata.get("required_version")
        try:
            required_version = max(required_version, int(value))
        except (TypeError, ValueError):
            continue
    return required_version


def _read_runner_config(run_dir: Path) -> dict[str, dict[str, str]]:
    runners_file = run_dir / "runners.yaml"
    if not runners_file.is_file():
        return {}

    raw = yaml.safe_load(runners_file.read_text(encoding="utf-8")) or {}
    runners: dict[str, dict[str, str]] = {}
    for agent_id, value in raw.items():
        if isinstance(value, str):
            runners[agent_id] = {"runner": value, "model": DEFAULT_RUNNER_MODELS.get(value, value)}
        elif isinstance(value, dict):
            runner = str(value.get("runner", "mock"))
            model = str(value.get("model") or value.get("llm_name") or DEFAULT_RUNNER_MODELS.get(runner, runner))
            runners[agent_id] = {"runner": runner, "model": model}
    return runners


def _run_title(run_dir: Path, events: list[dict[str, object]]) -> str:
    for event in events:
        if event.get("event_type") != "run_created":
            continue
        metadata = event.get("metadata")
        if isinstance(metadata, dict) and isinstance(metadata.get("title"), str):
            return str(metadata["title"])

    run_file = run_dir / "run.json"
    if run_file.is_file():
        try:
            raw = json.loads(run_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raw = {}
        if isinstance(raw.get("title"), str):
            return str(raw["title"])

    return run_dir.name


def _agents(run_dir: Path) -> list[AgentProjection]:
    runners = _read_runner_config(run_dir)
    agents: list[AgentProjection] = []
    for agent_id, definition in AGENT_DEFINITIONS.items():
        config = runners.get(agent_id, {"runner": "mock", "model": "Mock runner"})
        runner = config["runner"]
        model = config["model"]
        agents.append(
            AgentProjection(
                id=agent_id,
                label=str(definition["label"]),
                runner=runner,
                model=model,
                llm_name=model,
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
    min_version: int = 1,
) -> list[str]:
    missing: list[str] = []
    for agent in agents:
        if _skipped(events, stage, agent):
            continue
        pattern = f"agents/{agent}/{artifact}.v*.md"
        if _latest_version(run_dir, pattern) < min_version:
            missing.append(f"agents/{agent}/{artifact}.v{min_version}.md" if min_version > 1 else pattern)
    return missing


def _required_answers_ready(run_dir: Path) -> bool:
    questions = run_dir / "input" / "clarification_questions.json"
    answers = run_dir / "input" / "human_answers.md"
    return _is_non_empty_file(questions) and _is_non_empty_file(answers)


def _projection(run_dir: Path, title: str, stage: Stage, missing: list[str]) -> RunProjection:
    return RunProjection(
        run_id=run_dir.name,
        title=title,
        stage=stage,
        status=StageStatus.READY_TO_ADVANCE if not missing else StageStatus.WAITING_INPUT,
        missing_inputs=missing,
        agents=_agents(run_dir),
    )


def recompute_state(run_dir: Path) -> RunProjection:
    events = read_events(run_dir)
    title = _run_title(run_dir, events)
    required_discussion_version = _latest_discussion_required_version(events)
    if not _is_non_empty_file(run_dir / "input" / "requirement.md"):
        return _projection(run_dir, title, Stage.REQUIREMENT, ["input/requirement.md"])

    missing = _missing_agent_versions(
        run_dir,
        events,
        Stage.CLARIFICATION,
        ["architect", "engineer", "reviewer"],
        "clarification_questions",
    )
    if missing:
        return _projection(run_dir, title, Stage.CLARIFICATION, missing)

    clarified_missing = []
    if not _required_answers_ready(run_dir):
        clarified_missing.extend(["input/clarification_questions.json", "input/human_answers.md"])
    if not _is_non_empty_file(run_dir / "input" / "clarified_requirement.md"):
        clarified_missing.append("input/clarified_requirement.md")
    if clarified_missing:
        return _projection(run_dir, title, Stage.CLARIFIED_REQUIREMENT, clarified_missing)

    missing = _missing_agent_versions(run_dir, events, Stage.DRAFT_DESIGN, ["architect", "engineer"], "draft_response")
    if missing:
        return _projection(run_dir, title, Stage.DRAFT_DESIGN, missing)

    missing = _missing_agent_versions(
        run_dir,
        events,
        Stage.CROSS_REVIEW,
        ["architect", "engineer", "reviewer"],
        "review_response",
        required_discussion_version,
    )
    if missing:
        return _projection(run_dir, title, Stage.CROSS_REVIEW, missing)

    missing = _missing_agent_versions(
        run_dir,
        events,
        Stage.REVISION,
        ["architect", "engineer"],
        "revision_response",
        required_discussion_version,
    )
    if missing:
        return _projection(run_dir, title, Stage.REVISION, missing)

    synthesis_missing = []
    if _latest_version(run_dir, "agents/synthesizer/design_doc.v*.md") < required_discussion_version:
        synthesis_missing.append(
            f"agents/synthesizer/design_doc.v{required_discussion_version}.md"
            if required_discussion_version > 1
            else "agents/synthesizer/design_doc.v*.md"
        )
    if _latest_version(run_dir, "agents/synthesizer/execution_doc.v*.md") < required_discussion_version:
        synthesis_missing.append(
            f"agents/synthesizer/execution_doc.v{required_discussion_version}.md"
            if required_discussion_version > 1
            else "agents/synthesizer/execution_doc.v*.md"
        )
    if not synthesis_missing and not _is_non_empty_file(run_dir / "input" / "final_approval.md"):
        synthesis_missing.append("input/final_approval.md")
    return _projection(run_dir, title, Stage.SYNTHESIS, synthesis_missing)
