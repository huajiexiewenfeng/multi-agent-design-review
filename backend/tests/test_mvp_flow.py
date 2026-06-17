from pathlib import Path

from backend.app.services.finalize_service import finalize_run
from backend.app.services.run_service import create_run


def test_phase0_smoke_flow_with_manual_synthesis_files(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    run_dir = tmp_path / projection.run_id
    synth_dir = run_dir / "agents" / "synthesizer"
    synth_dir.mkdir(parents=True, exist_ok=True)
    (synth_dir / "design_doc.v1.md").write_text("# Design Document\n\n## Architecture\nFile-first", encoding="utf-8")
    (synth_dir / "execution_doc.v1.md").write_text(
        "# Execution Document\n\n## Implementation Plan\nBuild services",
        encoding="utf-8",
    )

    finalize_run(run_dir)

    assert (run_dir / "output" / "design_doc.md").is_file()
    assert (run_dir / "output" / "execution_doc.md").is_file()
    assert (run_dir / "output" / "transcript.md").is_file()
