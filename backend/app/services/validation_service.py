from pathlib import Path

from backend.app.models import Stage


REQUIRED_HEADINGS: dict[Stage, list[str]] = {
    Stage.CLARIFICATION: ["## Clarification Questions", "## Assumptions"],
    Stage.DRAFT_DESIGN: ["## Summary", "## Proposed Design", "## Modules", "## Data Flow", "## Risks", "## Open Questions"],
    Stage.CROSS_REVIEW: ["## Review Summary", "## Issues", "## Conflicts", "## Suggestions", "## Questions For Human"],
    Stage.REVISION: ["## Revised Design", "## Changes Made", "## Remaining Risks", "## Implementation Notes"],
}


def has_required_headings(path: Path, headings: list[str]) -> bool:
    if not path.is_file():
        return False
    content = path.read_text(encoding="utf-8")
    return all(heading in content for heading in headings)


def validate_stage_output(path: Path, stage: Stage) -> list[str]:
    if not path.is_file():
        return [f"Missing file: {path.name}"]
    content = path.read_text(encoding="utf-8")
    if content.strip() == "":
        return [f"Empty file: {path.name}"]
    missing = [heading for heading in REQUIRED_HEADINGS.get(stage, []) if heading not in content]
    return [f"Missing heading: {heading}" for heading in missing]
