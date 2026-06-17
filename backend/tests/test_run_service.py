from pathlib import Path

from backend.app.services.run_service import create_run


def test_create_run_writes_required_files(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    run_dir = tmp_path / projection.run_id

    assert (run_dir / "run.json").is_file()
    assert (run_dir / "events.jsonl").is_file()
    assert (run_dir / "runners.yaml").is_file()
    assert (run_dir / "input" / "requirement.md").read_text(encoding="utf-8").startswith("# Requirement")
    assert (run_dir / "inbox" / "architect").is_dir()
    assert projection.status.value == "ready_to_advance"
