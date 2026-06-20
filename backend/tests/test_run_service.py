from pathlib import Path

from backend.app.services.run_service import create_run, list_runs


def test_create_run_writes_required_files(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    run_dir = tmp_path / projection.run_id

    assert (run_dir / "run.json").is_file()
    assert (run_dir / "events.jsonl").is_file()
    assert (run_dir / "runners.yaml").is_file()
    assert (run_dir / "input" / "requirement.md").read_text(encoding="utf-8").startswith("# Requirement")
    assert (run_dir / "inbox" / "architect").is_dir()
    assert projection.status.value == "waiting_input"


def test_create_run_projects_agent_llm_names(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")

    assert projection.agents[0].id == "architect"
    assert projection.agents[0].runner == "mock"
    assert projection.agents[0].llm_name == "Mock runner"


def test_list_runs_returns_newest_first_with_titles(tmp_path: Path) -> None:
    first = create_run(tmp_path, title="First feature", requirement="# Requirement\nFirst")
    second = create_run(tmp_path, title="Second feature", requirement="# Requirement\nSecond")

    runs = list_runs(tmp_path)

    assert [run["run_id"] for run in runs] == [second.run_id, first.run_id]
    assert runs[0]["title"] == "Second feature"
    assert runs[1]["title"] == "First feature"
