from pathlib import Path

from backend.app.runners.mock import MockRunner


def test_mock_runner_writes_result_to_inbox(tmp_path: Path) -> None:
    prompt = tmp_path / "prompt.md"
    inbox = tmp_path / "inbox" / "architect"
    logs = tmp_path / "runner_logs" / "architect"
    prompt.write_text("## Prompt\nCreate questions", encoding="utf-8")

    result = MockRunner().run(
        run_id="run_001",
        agent_id="architect",
        stage="clarification",
        prompt_file=prompt,
        inbox_dir=inbox,
        runner_log_dir=logs,
        timeout_seconds=30,
        metadata={},
    )

    assert result.status == "succeeded"
    assert result.produced_files == ["clarification_result.md"]
    assert (inbox / "clarification_result.md").is_file()
    assert (logs / "mock.log").is_file()
