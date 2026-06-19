from pathlib import Path
import sys

from backend.app.runners.base import RunnerResult
from backend.app.runners.command import CommandRunner
from backend.app.runners.mock import MockRunner
from backend.app.services import runner_service


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

    result = CommandRunner(f'"{sys.executable}" "{script}" "{{prompt_file}}"').run(
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
    command_log = (logs / "command.log").read_text(encoding="utf-8")
    assert "exit_code: 0" in command_log
    assert str(prompt.resolve()) in command_log


def test_run_agent_stage_uses_configurable_timeout(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, int] = {}

    class CapturingRunner:
        def run(self, **kwargs):
            captured["timeout_seconds"] = kwargs["timeout_seconds"]
            return MockRunner().run(**kwargs)

    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\nBuild", encoding="utf-8")
    monkeypatch.setenv("MADR_RUNNER_TIMEOUT_SECONDS", "240")
    monkeypatch.setattr(runner_service, "get_runner", lambda name: CapturingRunner())

    runner_service.run_agent_stage(run_dir, "architect", runner_service.Stage.CLARIFICATION, "mock")

    assert captured["timeout_seconds"] == 240


def test_run_agent_stage_records_runner_failure_event(tmp_path: Path, monkeypatch) -> None:
    class FailingRunner:
        def run(self, **kwargs):
            kwargs["runner_log_dir"].mkdir(parents=True)
            (kwargs["runner_log_dir"] / "command.log").write_text("exit_code: 1", encoding="utf-8")
            return RunnerResult(
                status="failed",
                exit_code=1,
                produced_files=[],
                error_message="CLI did not produce output",
                started_at="2026-06-19T00:00:00+00:00",
                finished_at="2026-06-19T00:00:01+00:00",
            )

    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\nBuild", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    monkeypatch.setattr(runner_service, "get_runner", lambda name: FailingRunner())

    runner_service.run_agent_stage(run_dir, "architect", runner_service.Stage.CLARIFICATION, "codex")

    events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert "runner_failed" in events
    assert "CLI did not produce output" in events
    assert "runner_logs/architect/command.log" in events


def test_run_agent_stage_records_runner_waiting_event(tmp_path: Path, monkeypatch) -> None:
    class WaitingRunner:
        def run(self, **kwargs):
            kwargs["runner_log_dir"].mkdir(parents=True)
            (kwargs["runner_log_dir"] / "antigravity.log").write_text("waiting for output", encoding="utf-8")
            return RunnerResult(
                status="waiting_input",
                exit_code=0,
                produced_files=[],
                error_message="Antigravity launched; waiting for output file",
                started_at="2026-06-19T00:00:00+00:00",
                finished_at="2026-06-19T00:00:01+00:00",
            )

    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\nBuild", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    monkeypatch.setattr(runner_service, "get_runner", lambda name: WaitingRunner())

    runner_service.run_agent_stage(run_dir, "architect", runner_service.Stage.CLARIFICATION, "antigravity")

    events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert "runner_waiting" in events
    assert "Antigravity launched" in events
    assert "runner_logs/architect/antigravity.log" in events


def test_run_agent_stage_imports_existing_inbox_file_before_launching_runner(tmp_path: Path, monkeypatch) -> None:
    class ShouldNotRun:
        def run(self, **kwargs):
            raise AssertionError("runner should not launch when inbox output already exists")

    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\nBuild", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    inbox = run_dir / "inbox" / "architect"
    inbox.mkdir(parents=True)
    (inbox / "clarification_result.md").write_text(
        "## Clarification Questions\n\n1. [required] What is the goal?\n\n## Assumptions\n\n- Local flow.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runner_service, "get_runner", lambda name: ShouldNotRun())

    runner_service.run_agent_stage(run_dir, "architect", runner_service.Stage.CLARIFICATION, "antigravity")

    assert (run_dir / "agents" / "architect" / "clarification_questions.v1.md").is_file()
    assert "file_imported" in (run_dir / "events.jsonl").read_text(encoding="utf-8")


def test_run_agent_stage_ignores_stale_inbox_file_for_other_stage(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, bool] = {}

    class CapturingRunner:
        def run(self, **kwargs):
            captured["launched"] = True
            return MockRunner().run(**kwargs)

    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\nBuild", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    inbox = run_dir / "inbox" / "architect"
    inbox.mkdir(parents=True)
    (inbox / "clarification_result.md").write_text(
        "## Clarification Questions\n\n1. [required] Old?\n\n## Assumptions\n\n- Old.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runner_service, "get_runner", lambda name: CapturingRunner())

    runner_service.run_agent_stage(run_dir, "architect", runner_service.Stage.DRAFT_DESIGN, "mock")

    assert captured["launched"] is True
    assert (run_dir / "agents" / "architect" / "draft_response.v1.md").is_file()


def test_run_agent_stage_imports_existing_synthesis_inbox_file(tmp_path: Path, monkeypatch) -> None:
    class ShouldNotRun:
        def run(self, **kwargs):
            raise AssertionError("runner should not launch when synthesis inbox output already exists")

    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\nBuild", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    inbox = run_dir / "inbox" / "synthesizer"
    inbox.mkdir(parents=True)
    (inbox / "synthesis_result.md").write_text(
        "# Design Document\n\n## Architecture\nDesign\n\n# Execution Document\n\n## Implementation Plan\nPlan\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runner_service, "get_runner", lambda name: ShouldNotRun())

    runner_service.run_agent_stage(run_dir, "synthesizer", runner_service.Stage.SYNTHESIS, "antigravity")

    assert (run_dir / "agents" / "synthesizer" / "design_doc.v1.md").is_file()
    assert (run_dir / "agents" / "synthesizer" / "execution_doc.v1.md").is_file()


def test_command_runner_returns_when_output_file_is_stable(tmp_path: Path) -> None:
    prompt = tmp_path / "runs" / "run_001" / "agents" / "architect" / "prompt.md"
    prompt.parent.mkdir(parents=True)
    inbox = tmp_path / "runs" / "run_001" / "inbox" / "architect"
    logs = tmp_path / "runs" / "run_001" / "runner_logs" / "architect"
    prompt.write_text("## Prompt\nCreate questions", encoding="utf-8")
    script = tmp_path / "write_then_wait.py"
    script.write_text(
        "import pathlib, sys, time\n"
        "pathlib.Path(sys.argv[1]).write_text('## Clarification Questions\\n\\n1. [required] Stable?', encoding='utf-8')\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )

    result = CommandRunner(f'"{sys.executable}" "{script}" "{{output_file}}"').run(
        run_id="run_001",
        agent_id="architect",
        stage="clarification",
        prompt_file=prompt,
        inbox_dir=inbox,
        runner_log_dir=logs,
        timeout_seconds=10,
        metadata={},
    )

    assert result.status == "succeeded"
    assert result.produced_files == ["clarification_result.md"]
    assert "terminated_after_output: True" in (logs / "command.log").read_text(encoding="utf-8")


def test_command_runner_replaces_undecodable_process_output(tmp_path: Path) -> None:
    prompt = tmp_path / "runs" / "run_001" / "agents" / "architect" / "prompt.md"
    prompt.parent.mkdir(parents=True)
    inbox = tmp_path / "runs" / "run_001" / "inbox" / "architect"
    logs = tmp_path / "runs" / "run_001" / "runner_logs" / "architect"
    prompt.write_text("## Prompt\nCreate questions", encoding="utf-8")
    script = tmp_path / "emit_invalid_bytes.py"
    script.write_text(
        "import sys\n"
        "sys.stdout.write('## Clarification Questions\\n\\n1. [required] Still works?')\n"
        "sys.stderr.buffer.write(b'\\xae')\n",
        encoding="utf-8",
    )

    result = CommandRunner(f'"{sys.executable}" "{script}" "{{prompt_file}}"').run(
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
    assert "Still works" in (inbox / "clarification_result.md").read_text(encoding="utf-8")
    assert "stderr:" in (logs / "command.log").read_text(encoding="utf-8")
