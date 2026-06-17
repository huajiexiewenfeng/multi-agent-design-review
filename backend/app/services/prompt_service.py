from pathlib import Path

from backend.app.models import Stage

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "prompts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _latest_text(run_dir: Path, pattern: str) -> str:
    files = sorted(run_dir.glob(pattern))
    return files[-1].read_text(encoding="utf-8") if files else ""


def _all_text(run_dir: Path, pattern: str) -> str:
    return "\n\n".join(path.read_text(encoding="utf-8") for path in sorted(run_dir.glob(pattern)))


def _template(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text(encoding="utf-8")


def write_prompt(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def render_prompt(stage: Stage, agent_id: str, run_dir: Path) -> str:
    requirement = _read(run_dir / "input" / "requirement.md")
    human_answers = _read(run_dir / "input" / "human_answers.md")
    clarified_requirement = _read(run_dir / "input" / "clarified_requirement.md")
    human_notes = "\n\n".join([_read(run_dir / "human" / "comments.md"), _read(run_dir / "human" / "decisions.md")])

    if stage == Stage.CLARIFICATION:
        return _template("clarification.md").format(agent_id=agent_id, requirement=requirement)
    if stage == Stage.DRAFT_DESIGN:
        return _template("draft.md").format(
            agent_id=agent_id,
            requirement=requirement,
            human_answers=human_answers,
            clarified_requirement=clarified_requirement,
        )
    if stage == Stage.CROSS_REVIEW:
        return _template("review.md").format(
            agent_id=agent_id,
            clarified_requirement=clarified_requirement,
            drafts=_all_text(run_dir, "agents/*/draft_response.v*.md"),
        )
    if stage == Stage.REVISION:
        return _template("revision.md").format(
            agent_id=agent_id,
            own_draft=_latest_text(run_dir, f"agents/{agent_id}/draft_response.v*.md"),
            reviews=_all_text(run_dir, "agents/*/review_response.v*.md"),
            human_notes=human_notes,
        )
    if stage == Stage.SYNTHESIS:
        return _template("synthesis.md").format(
            clarified_requirement=clarified_requirement,
            drafts=_all_text(run_dir, "agents/*/draft_response.v*.md"),
            reviews=_all_text(run_dir, "agents/*/review_response.v*.md"),
            revisions=_all_text(run_dir, "agents/*/revision_response.v*.md"),
            human_notes=human_notes,
        )
    raise ValueError(f"Unsupported prompt stage: {stage}")
