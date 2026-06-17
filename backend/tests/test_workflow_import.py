from pathlib import Path

from backend.app.models import Stage
from backend.app.services.workflow_service import import_from_inbox


def _make_run(run_dir: Path) -> None:
    (run_dir / "agents" / "architect").mkdir(parents=True)
    (run_dir / "inbox" / "architect").mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "run.json").write_text("{}", encoding="utf-8")


def test_import_from_inbox_creates_versioned_authoritative_file(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    _make_run(run_dir)
    (run_dir / "inbox" / "architect" / "draft.md").write_text(
        "## Summary\nA\n\n## Proposed Design\nB\n\n## Modules\nC\n\n## Data Flow\nD\n\n## Risks\nE\n\n## Open Questions\nF\n",
        encoding="utf-8",
    )

    imported = import_from_inbox(run_dir, "architect", Stage.DRAFT_DESIGN)

    assert imported == run_dir / "agents" / "architect" / "draft_response.v1.md"
    assert imported.read_text(encoding="utf-8").startswith("## Summary")
    assert "file_imported" in (run_dir / "events.jsonl").read_text(encoding="utf-8")


def test_second_import_creates_new_version_and_superseded_event(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_002"
    _make_run(run_dir)
    inbox_file = run_dir / "inbox" / "architect" / "draft.md"
    inbox_file.write_text(
        "## Summary\nA\n\n## Proposed Design\nB\n\n## Modules\nC\n\n## Data Flow\nD\n\n## Risks\nE\n\n## Open Questions\nF\n",
        encoding="utf-8",
    )
    import_from_inbox(run_dir, "architect", Stage.DRAFT_DESIGN)
    inbox_file.write_text(
        "## Summary\nA2\n\n## Proposed Design\nB2\n\n## Modules\nC2\n\n## Data Flow\nD2\n\n## Risks\nE2\n\n## Open Questions\nF2\n",
        encoding="utf-8",
    )

    imported = import_from_inbox(run_dir, "architect", Stage.DRAFT_DESIGN)

    assert imported.name == "draft_response.v2.md"
    events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert "submission_superseded" in events
