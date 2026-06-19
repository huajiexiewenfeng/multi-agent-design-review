from pathlib import Path
import os

import yaml

from backend.app.runners.antigravity import AntigravityRunner
from backend.app.models import ActorType, Stage
from backend.app.runners.file import FileRunner
from backend.app.runners.manual import ManualRunner
from backend.app.runners.mock import MockRunner
from backend.app.services.event_service import append_event
from backend.app.services.prompt_service import render_prompt
from backend.app.services.runner_registry_service import resolve_runner_command
from backend.app.services.workflow_service import import_from_inbox
from backend.app.runners.command import CommandRunner


def get_runner(name: str):
    command = resolve_runner_command(name)
    if name == "antigravity" and command:
        return AntigravityRunner(command)
    if command:
        return CommandRunner(command)

    runners = {
        "manual": ManualRunner(),
        "file": FileRunner(),
        "mock": MockRunner(),
        "codex": ManualRunner(),
        "claude-code": ManualRunner(),
        "antigravity": ManualRunner(),
    }
    if name not in runners:
        raise ValueError(f"Unsupported runner: {name}")
    return runners[name]


def _runner_name_for_agent(run_dir: Path, agent_id: str) -> str:
    runners_file = run_dir / "runners.yaml"
    if not runners_file.is_file():
        return "mock"

    raw = yaml.safe_load(runners_file.read_text(encoding="utf-8")) or {}
    value = raw.get(agent_id, "mock")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("runner", "mock"))
    return "mock"


def _import_synthesis(run_dir: Path) -> None:
    inbox_file = sorted((run_dir / "inbox" / "synthesizer").glob("*.md"))[0]
    content = inbox_file.read_text(encoding="utf-8")
    design_marker = "# Design Document"
    execution_marker = "# Execution Document"
    if design_marker not in content or execution_marker not in content:
        raise ValueError("Synthesis output must contain Design and Execution document markers")
    design_start = content.index(design_marker)
    execution_start = content.index(execution_marker)
    synthesizer_dir = run_dir / "agents" / "synthesizer"
    synthesizer_dir.mkdir(parents=True, exist_ok=True)
    (synthesizer_dir / "design_doc.v1.md").write_text(
        content[design_start:execution_start].strip() + "\n",
        encoding="utf-8",
    )
    (synthesizer_dir / "execution_doc.v1.md").write_text(content[execution_start:].strip() + "\n", encoding="utf-8")


def run_agent_stage(run_dir: Path, agent_id: str, stage: Stage, runner_name: str | None = None) -> None:
    runner_name = runner_name or _runner_name_for_agent(run_dir, agent_id)
    prompt_name = {
        Stage.CLARIFICATION: "clarification_prompt.md",
        Stage.DRAFT_DESIGN: "draft_prompt.md",
        Stage.CROSS_REVIEW: "review_prompt.md",
        Stage.REVISION: "revision_prompt.md",
        Stage.SYNTHESIS: "synthesis_prompt.md",
    }[stage]
    prompt_file = run_dir / "agents" / agent_id / prompt_name
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(render_prompt(stage, agent_id, run_dir), encoding="utf-8")
    if _has_stage_inbox_markdown(run_dir, agent_id, stage):
        import_existing_stage_output(run_dir, agent_id, stage)
        return
    runner = get_runner(runner_name)
    result = runner.run(
        run_id=run_dir.name,
        agent_id=agent_id,
        stage=stage.value,
        prompt_file=prompt_file,
        inbox_dir=run_dir / "inbox" / agent_id,
        runner_log_dir=run_dir / "runner_logs" / agent_id,
        timeout_seconds=int(os.environ.get("MADR_RUNNER_TIMEOUT_SECONDS", "180")),
        metadata={},
    )
    if result.status != "succeeded":
        event_type = "runner_waiting" if result.status == "waiting_input" else "runner_failed"
        append_event(
            run_dir,
            stage,
            agent_id,
            ActorType.AGENT,
            event_type,
            result.error_message or f"{runner_name} runner failed",
            _first_runner_log(run_dir, agent_id),
            {
                "runner": runner_name,
                "status": result.status,
                "exit_code": result.exit_code,
                "produced_files": result.produced_files,
            },
        )
        return
    append_event(
        run_dir,
        stage,
        agent_id,
        ActorType.AGENT,
        "runner_succeeded",
        f"{runner_name} runner completed {stage.value}",
        _first_runner_log(run_dir, agent_id),
        {
            "runner": runner_name,
            "status": result.status,
            "exit_code": result.exit_code,
            "produced_files": result.produced_files,
        },
    )
    if result.status == "succeeded" and stage == Stage.SYNTHESIS:
        _import_synthesis(run_dir)
    elif result.status == "succeeded":
        import_from_inbox(run_dir, agent_id, stage)


def _first_runner_log(run_dir: Path, agent_id: str) -> str | None:
    log_dir = run_dir / "runner_logs" / agent_id
    for path in sorted(log_dir.glob("*.log")):
        return path.relative_to(run_dir).as_posix()
    return None


def _has_stage_inbox_markdown(run_dir: Path, agent_id: str, stage: Stage) -> bool:
    stage_hints = {
        Stage.CLARIFICATION: ["clarification"],
        Stage.DRAFT_DESIGN: ["draft"],
        Stage.CROSS_REVIEW: ["review"],
        Stage.REVISION: ["revision"],
        Stage.SYNTHESIS: ["synthesis"],
    }[stage]
    return any(
        any(hint in path.stem for hint in stage_hints) or path.stem.endswith("_manual")
        for path in (run_dir / "inbox" / agent_id).glob("*.md")
    )


def import_existing_stage_output(run_dir: Path, agent_id: str, stage: Stage) -> Path | None:
    if stage == Stage.SYNTHESIS:
        _import_synthesis(run_dir)
        return None
    return import_from_inbox(run_dir, agent_id, stage)
