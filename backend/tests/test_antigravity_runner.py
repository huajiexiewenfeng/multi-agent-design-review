from pathlib import Path
import sys

from backend.app.runners.antigravity import AntigravityRunner


def test_antigravity_runner_waits_for_output_file(tmp_path: Path) -> None:
    prompt = tmp_path / "runs" / "run_001" / "agents" / "architect" / "prompt.md"
    prompt.parent.mkdir(parents=True)
    inbox = tmp_path / "runs" / "run_001" / "inbox" / "architect"
    logs = tmp_path / "runs" / "run_001" / "runner_logs" / "architect"
    prompt.write_text("Reply exactly: MADR_RUNNER_SMOKE_OK", encoding="utf-8")
    script = tmp_path / "fake_antigravity.py"
    script.write_text(
        "import pathlib, re, sys\n"
        "instruction = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')\n"
        "output = re.search(r'OUTPUT_FILE: (.+)', instruction).group(1).strip()\n"
        "pathlib.Path(output).write_text('MADR_RUNNER_SMOKE_OK', encoding='utf-8')\n",
        encoding="utf-8",
    )

    result = AntigravityRunner(f'"{sys.executable}" "{script}" "{{instruction_file}}"').run(
        run_id="run_001",
        agent_id="architect",
        stage="smoke",
        prompt_file=prompt,
        inbox_dir=inbox,
        runner_log_dir=logs,
        timeout_seconds=5,
        metadata={},
    )

    assert result.status == "succeeded"
    assert result.produced_files == ["smoke_result.md"]
    assert "MADR_RUNNER_SMOKE_OK" in (inbox / "smoke_result.md").read_text(encoding="utf-8")
    assert "OUTPUT_FILE:" in (logs / "antigravity_instruction.md").read_text(encoding="utf-8")


def test_antigravity_runner_returns_waiting_when_launcher_exits_without_output(tmp_path: Path) -> None:
    prompt = tmp_path / "runs" / "run_001" / "agents" / "architect" / "prompt.md"
    prompt.parent.mkdir(parents=True)
    inbox = tmp_path / "runs" / "run_001" / "inbox" / "architect"
    logs = tmp_path / "runs" / "run_001" / "runner_logs" / "architect"
    prompt.write_text("Reply exactly: MADR_RUNNER_SMOKE_OK", encoding="utf-8")
    script = tmp_path / "fake_launcher.py"
    script.write_text("print('Reading from stdin via: temp')\n", encoding="utf-8")

    result = AntigravityRunner(f'"{sys.executable}" "{script}" "{{instruction_file}}"').run(
        run_id="run_001",
        agent_id="architect",
        stage="smoke",
        prompt_file=prompt,
        inbox_dir=inbox,
        runner_log_dir=logs,
        timeout_seconds=30,
        metadata={},
    )

    assert result.status == "waiting_input"
    assert result.produced_files == []
    assert "waiting for Antigravity" in (logs / "antigravity.log").read_text(encoding="utf-8")
