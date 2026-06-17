from pathlib import Path

from backend.app.models import Stage
from backend.app.runners.file import FileRunner
from backend.app.runners.manual import ManualRunner
from backend.app.runners.mock import MockRunner
from backend.app.services.prompt_service import render_prompt
from backend.app.services.workflow_service import import_from_inbox


def get_runner(name: str):
    runners = {
        "manual": ManualRunner(),
        "file": FileRunner(),
        "mock": MockRunner(),
    }
    if name not in runners:
        raise ValueError(f"Unsupported runner: {name}")
    return runners[name]


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


def run_agent_stage(run_dir: Path, agent_id: str, stage: Stage, runner_name: str = "mock") -> None:
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
    runner = get_runner(runner_name)
    result = runner.run(
        run_id=run_dir.name,
        agent_id=agent_id,
        stage=stage.value,
        prompt_file=prompt_file,
        inbox_dir=run_dir / "inbox" / agent_id,
        runner_log_dir=run_dir / "runner_logs" / agent_id,
        timeout_seconds=30,
        metadata={},
    )
    if result.status == "succeeded" and stage == Stage.SYNTHESIS:
        _import_synthesis(run_dir)
    elif result.status == "succeeded":
        import_from_inbox(run_dir, agent_id, stage)
