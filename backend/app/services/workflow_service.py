from pathlib import Path
import re

from backend.app.models import ActorType, Stage
from backend.app.services.event_service import append_event
from backend.app.services.file_service import run_lock, write_json
from backend.app.services.state_service import recompute_state
from backend.app.services.validation_service import validate_stage_output

ARTIFACT_BY_STAGE: dict[Stage, str] = {
    Stage.CLARIFICATION: "clarification_questions",
    Stage.DRAFT_DESIGN: "draft_response",
    Stage.CROSS_REVIEW: "review_response",
    Stage.REVISION: "revision_response",
}


def _next_version(agent_dir: Path, artifact: str) -> int:
    versions: list[int] = []
    pattern = re.compile(rf"^{re.escape(artifact)}\.v(\d+)\.md$")
    for path in agent_dir.glob(f"{artifact}.v*.md"):
        match = pattern.match(path.name)
        if match:
            versions.append(int(match.group(1)))
    return max(versions, default=0) + 1


def _first_inbox_markdown(run_dir: Path, agent_id: str) -> Path:
    inbox_dir = run_dir / "inbox" / agent_id
    files = sorted(inbox_dir.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No markdown files found in {inbox_dir}")
    return files[0]


def import_from_inbox(run_dir: Path, agent_id: str, stage: Stage) -> Path:
    artifact = ARTIFACT_BY_STAGE[stage]
    with run_lock(run_dir):
        source = _first_inbox_markdown(run_dir, agent_id)
        errors = validate_stage_output(source, stage)
        if errors:
            append_event(
                run_dir,
                stage,
                agent_id,
                ActorType.AGENT,
                "validation_failed",
                "; ".join(errors),
                str(source.relative_to(run_dir)),
            )
            raise ValueError("; ".join(errors))

        agent_dir = run_dir / "agents" / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        version = _next_version(agent_dir, artifact)
        target = agent_dir / f"{artifact}.v{version}.md"
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        if version > 1:
            append_event(
                run_dir,
                stage,
                agent_id,
                ActorType.AGENT,
                "submission_superseded",
                f"{artifact}.v{version - 1}.md superseded by {target.name}",
                str(target.relative_to(run_dir)),
            )
        append_event(
            run_dir,
            stage,
            agent_id,
            ActorType.AGENT,
            "file_imported",
            f"Imported {target.name}",
            str(target.relative_to(run_dir)),
        )
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json"))
        return target
