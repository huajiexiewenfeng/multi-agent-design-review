from pathlib import Path
import sys

from backend.app.runners.command import CommandRunner
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


def test_command_runner_writes_stdout_to_inbox(tmp_path: Path) -> None:
    prompt = tmp_path / "runs" / "run_001" / "agents" / "architect" / "prompt.md"
    prompt.parent.mkdir(parents=True)
    inbox = tmp_path / "runs" / "run_001" / "inbox" / "architect"
    logs = tmp_path / "runs" / "run_001" / "runner_logs" / "architect"
    prompt.write_text("## Prompt\nCreate questions", encoding="utf-8")
    script = tmp_path / "emit_markdown.py"
    script.write_text("print('## Clarification Questions\\n\\n1. [required] Who uses it?')", encoding="utf-8")

    result = CommandRunner(f'"{sys.executable}" "{script}"').run(
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
    assert "Who uses it" in (inbox / "clarification_result.md").read_text(encoding="utf-8")
    assert "exit_code: 0" in (logs / "command.log").read_text(encoding="utf-8")
