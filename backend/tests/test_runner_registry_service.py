from pathlib import Path

from backend.app.services import runner_registry_service


def test_resolve_runner_command_prefers_environment(monkeypatch) -> None:
    monkeypatch.setenv("MADR_CODEX_COMMAND", "codex-test {prompt_file}")

    assert runner_registry_service.resolve_runner_command("codex") == "codex-test {prompt_file}"


def test_runner_health_reports_configured_env(monkeypatch) -> None:
    monkeypatch.setenv("MADR_CLAUDE_CODE_COMMAND", "claude-test {prompt_file}")
    monkeypatch.setattr(runner_registry_service, "_first_existing", lambda candidates: Path("C:/fake/claude.cmd"))
    monkeypatch.setattr(runner_registry_service, "_read_version", lambda executable, args: ("test-version", None))

    health = runner_registry_service.get_runner_health()
    claude = next(item for item in health if item["id"] == "claude-code")

    assert claude["available"] is True
    assert claude["configured"] is True
    assert claude["command_template"] == "claude-test {prompt_file}"


def test_read_version_replaces_undecodable_output(monkeypatch) -> None:
    captured = {}

    class Completed:
        returncode = 0
        stdout = "codex-cli 0.141.0\nwarning �"
        stderr = ""

    def fake_run(*args, **kwargs):
        captured.update(kwargs)
        return Completed()

    monkeypatch.setattr(runner_registry_service.subprocess, "run", fake_run)

    version, error = runner_registry_service._read_version(Path("C:/fake/codex.cmd"), ["--version"])

    assert version == "codex-cli 0.141.0"
    assert error is None
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"


def test_first_existing_keeps_permission_denied_candidate(monkeypatch) -> None:
    candidate = Path("C:/Users/admin/AppData/Roaming/npm/codex.cmd")

    def blocked_is_file(self):
        raise PermissionError("sandbox denied")

    monkeypatch.setattr(Path, "is_file", blocked_is_file)

    assert runner_registry_service._first_existing([candidate]) == candidate
