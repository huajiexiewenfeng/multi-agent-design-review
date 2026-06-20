from pathlib import Path

from backend.app.models import Stage


PROMPT_BY_STAGE = {
    Stage.CLARIFICATION: "clarification_prompt.md",
    Stage.DRAFT_DESIGN: "draft_prompt.md",
    Stage.CROSS_REVIEW: "review_prompt.md",
    Stage.REVISION: "revision_prompt.md",
    Stage.SYNTHESIS: "synthesis_prompt.md",
}

OUTPUT_PATTERNS_BY_STAGE = {
    Stage.REQUIREMENT: ["input/requirement.md"],
    Stage.CLARIFICATION: ["agents/*/clarification_questions.v*.md"],
    Stage.CLARIFIED_REQUIREMENT: ["input/clarified_requirement.md", "input/human_answers.md"],
    Stage.DRAFT_DESIGN: ["agents/*/draft_response.v*.md"],
    Stage.CROSS_REVIEW: ["agents/*/review_response.v*.md"],
    Stage.REVISION: ["agents/*/revision_response.v*.md"],
    Stage.SYNTHESIS: [
        "agents/synthesizer/design_doc.v*.md",
        "agents/synthesizer/execution_doc.v*.md",
        "output/design_doc.md",
        "output/execution_doc.md",
        "output/transcript.md",
    ],
}


def get_stage_artifacts(run_dir: Path, stage: Stage) -> dict[str, object]:
    artifacts: list[dict[str, str | None]] = []
    prompt_name = PROMPT_BY_STAGE.get(stage)
    if prompt_name:
        for path in sorted(run_dir.glob(f"agents/*/{prompt_name}")):
            artifacts.append(_artifact(run_dir, path, "prompt"))

    for pattern in OUTPUT_PATTERNS_BY_STAGE.get(stage, []):
        for path in sorted(run_dir.glob(pattern)):
            artifacts.append(_artifact(run_dir, path, "output"))

    return {"stage": stage.value, "artifacts": artifacts}


def _artifact(run_dir: Path, path: Path, kind: str) -> dict[str, str | None]:
    relative = path.relative_to(run_dir).as_posix()
    agent_id = path.parts[-2] if "agents" in path.parts else None
    return {
        "path": relative,
        "kind": kind,
        "agent_id": agent_id,
        "content": path.read_text(encoding="utf-8"),
    }
