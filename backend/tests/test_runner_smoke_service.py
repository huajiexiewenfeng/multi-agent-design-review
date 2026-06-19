from pathlib import Path
import sys

from backend.app.services import runner_smoke_service


def test_runner_smoke_uses_configured_command(tmp_path: Path, monkeypatch) -> None:
    script = tmp_path / "smoke_runner.py"
    script.write_text(
        "import pathlib, sys\n"
        "pathlib.Path(sys.argv[1]).write_text('MADR_RUNNER_SMOKE_OK', encoding='utf-8')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runner_smoke_service,
        "resolve_runner_command",
        lambda runner: f'"{sys.executable}" "{script}" "{{output_file}}"',
    )

    result = runner_smoke_service.run_runner_smoke_test("codex", tmp_path, timeout_seconds=5)

    assert result["runner_id"] == "codex"
    assert result["status"] == "succeeded"
    assert result["output_content"] == "MADR_RUNNER_SMOKE_OK"
    assert "exit_code: 0" in result["log_content"]
