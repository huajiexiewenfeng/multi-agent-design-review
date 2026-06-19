from pathlib import Path

from backend.app.services import runner_smoke_service


def test_runner_smoke_uses_configured_command(tmp_path: Path, monkeypatch) -> None:
    class SmokeRunner:
        def run(self, **kwargs):
            kwargs["inbox_dir"].mkdir(parents=True)
            kwargs["runner_log_dir"].mkdir(parents=True)
            (kwargs["inbox_dir"] / "smoke_result.md").write_text("MADR_RUNNER_SMOKE_OK", encoding="utf-8")
            (kwargs["runner_log_dir"] / "command.log").write_text("exit_code: 0", encoding="utf-8")

            class Result:
                status = "succeeded"
                exit_code = 0
                error_message = None

            return Result()

    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", lambda runner: "demo")
    monkeypatch.setattr(runner_smoke_service, "get_runner", lambda runner: SmokeRunner())

    result = runner_smoke_service.run_runner_smoke_test("codex", tmp_path, timeout_seconds=5)

    assert result["runner_id"] == "codex"
    assert result["status"] == "succeeded"
    assert result["output_content"] == "MADR_RUNNER_SMOKE_OK"
    assert "exit_code: 0" in result["log_content"]


def test_runner_smoke_uses_runner_timeout_environment(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, int] = {}

    class CapturingRunner:
        def run(self, **kwargs):
            captured["timeout_seconds"] = kwargs["timeout_seconds"]
            kwargs["inbox_dir"].mkdir(parents=True)
            kwargs["runner_log_dir"].mkdir(parents=True)
            (kwargs["inbox_dir"] / "smoke_result.md").write_text("MADR_RUNNER_SMOKE_OK", encoding="utf-8")
            (kwargs["runner_log_dir"] / "command.log").write_text("exit_code: 0", encoding="utf-8")

            class Result:
                status = "succeeded"
                exit_code = 0
                error_message = None

            return Result()

    monkeypatch.setenv("MADR_RUNNER_TIMEOUT_SECONDS", "240")
    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", lambda runner: "demo")
    monkeypatch.setattr(runner_smoke_service, "get_runner", lambda runner: CapturingRunner())

    runner_smoke_service.run_runner_smoke_test("codex", tmp_path)

    assert captured["timeout_seconds"] == 240


def test_runner_smoke_fails_when_output_marker_is_missing(tmp_path: Path, monkeypatch) -> None:
    class WrongOutputRunner:
        def run(self, **kwargs):
            kwargs["inbox_dir"].mkdir(parents=True)
            kwargs["runner_log_dir"].mkdir(parents=True)
            (kwargs["inbox_dir"] / "smoke_result.md").write_text("Reading from stdin", encoding="utf-8")
            (kwargs["runner_log_dir"] / "command.log").write_text("exit_code: 0", encoding="utf-8")

            class Result:
                status = "succeeded"
                exit_code = 0
                error_message = None

            return Result()

    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", lambda runner: "demo")
    monkeypatch.setattr(runner_smoke_service, "get_runner", lambda runner: WrongOutputRunner())

    result = runner_smoke_service.run_runner_smoke_test("antigravity", tmp_path)

    assert result["status"] == "failed"
    assert result["error_message"] == "Smoke output did not contain MADR_RUNNER_SMOKE_OK"


def test_runner_smoke_returns_non_command_log_content(tmp_path: Path, monkeypatch) -> None:
    class CustomLogRunner:
        def run(self, **kwargs):
            kwargs["inbox_dir"].mkdir(parents=True)
            kwargs["runner_log_dir"].mkdir(parents=True)
            (kwargs["inbox_dir"] / "smoke_result.md").write_text("missing marker", encoding="utf-8")
            (kwargs["runner_log_dir"] / "antigravity.log").write_text("Reading from stdin", encoding="utf-8")

            class Result:
                status = "failed"
                exit_code = 0
                error_message = "missing marker"

            return Result()

    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", lambda runner: "demo")
    monkeypatch.setattr(runner_smoke_service, "get_runner", lambda runner: CustomLogRunner())

    result = runner_smoke_service.run_runner_smoke_test("antigravity", tmp_path)

    assert "Reading from stdin" in result["log_content"]
