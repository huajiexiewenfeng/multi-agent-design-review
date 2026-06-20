from pathlib import Path
import pytest

from backend.app.services.finalize_service import finalize_run


def test_finalize_copies_current_synthesis_outputs(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    (run_dir / "agents" / "synthesizer").mkdir(parents=True)
    (run_dir / "events.jsonl").write_text(
        '{"id":"evt_1","actor":"system","event_type":"run_created","message":"created"}\n',
        encoding="utf-8",
    )
    (run_dir / "agents" / "synthesizer" / "design_doc.v1.md").write_text(
        "# Design Document\n\n## Architecture\nA",
        encoding="utf-8",
    )
    (run_dir / "agents" / "synthesizer" / "execution_doc.v1.md").write_text(
        "# Execution Document\n\n## Implementation Plan\nB",
        encoding="utf-8",
    )
    (run_dir / "input").mkdir()
    (run_dir / "input" / "final_approval.md").write_text("Approved", encoding="utf-8")

    finalize_run(run_dir)

    assert (run_dir / "output" / "design_doc.md").read_text(encoding="utf-8").startswith("# Design Document")
    assert (run_dir / "output" / "execution_doc.md").read_text(encoding="utf-8").startswith("# Execution Document")
    assert "run_created" in (run_dir / "output" / "transcript.md").read_text(encoding="utf-8")


def test_finalize_requires_human_final_approval(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_002"
    (run_dir / "agents" / "synthesizer").mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "agents" / "synthesizer" / "design_doc.v1.md").write_text(
        "# Design Document\n\n## Architecture\nA",
        encoding="utf-8",
    )
    (run_dir / "agents" / "synthesizer" / "execution_doc.v1.md").write_text(
        "# Execution Document\n\n## Implementation Plan\nB",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Final output requires human approval"):
        finalize_run(run_dir)
