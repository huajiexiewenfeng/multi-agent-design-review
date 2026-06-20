from pathlib import Path

from backend.app.services import runner_smoke_service


def test_runner_smoke_uses_configured_command(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, str] = {}

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

    def fake_resolve_runner_command(runner: str, model: str | None = None) -> str:
        captured["resolve_runner"] = runner
        captured["resolve_model"] = model or ""
        return "demo"

    def fake_get_runner(runner: str, model: str | None = None):
        captured["runner"] = runner
        captured["model"] = model or ""
        return SmokeRunner()

    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", fake_resolve_runner_command)
    monkeypatch.setattr(runner_smoke_service, "get_runner", fake_get_runner)

    result = runner_smoke_service.run_runner_smoke_test("codex", tmp_path, model="gpt-5.5", timeout_seconds=5)

    assert result["runner_id"] == "codex"
    assert result["model"] == "gpt-5.5"
    assert result["status"] == "succeeded"
    assert result["output_content"] == "MADR_RUNNER_SMOKE_OK"
    assert "exit_code: 0" in result["log_content"]
    assert captured == {
        "resolve_runner": "codex",
        "resolve_model": "gpt-5.5",
        "runner": "codex",
        "model": "gpt-5.5",
    }


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
    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", lambda runner, model=None: "demo")
    monkeypatch.setattr(runner_smoke_service, "get_runner", lambda runner, model=None: CapturingRunner())

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

    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", lambda runner, model=None: "demo")
    monkeypatch.setattr(runner_smoke_service, "get_runner", lambda runner, model=None: WrongOutputRunner())

    result = runner_smoke_service.run_runner_smoke_test("codex", tmp_path)

    assert result["status"] == "failed"
    assert result["error_message"] == "Smoke output did not contain MADR_RUNNER_SMOKE_OK"


def test_runner_smoke_reports_unconfigured_runner(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", lambda runner, model=None: None)

    result = runner_smoke_service.run_runner_smoke_test("claude-code", tmp_path, model="opus")

    assert result["status"] == "unconfigured"
    assert result["runner_id"] == "claude-code"
    assert result["model"] == "opus"
    assert result["error_message"] == "Runner is not configured: claude-code"


def test_runner_smoke_does_not_launch_interactive_antigravity(tmp_path: Path, monkeypatch) -> None:
    called = False

    def fake_get_runner(runner: str, model: str | None = None):
        nonlocal called
        called = True
        raise AssertionError("Antigravity should not be launched by smoke test")

    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", lambda runner, model=None: "demo")
    monkeypatch.setattr(runner_smoke_service, "get_runner", fake_get_runner)

    result = runner_smoke_service.run_runner_smoke_test(
        "antigravity",
        tmp_path,
        model="Gemini 3.5 Flash (High)",
    )

    assert called is False
    assert result["status"] == "interactive_only"
    assert result["error_message"] == "Antigravity is interactive-only in this MVP; use handoff instead of smoke test."


def test_runner_smoke_preserves_waiting_input_status(tmp_path: Path, monkeypatch) -> None:
    class WaitingRunner:
        def run(self, **kwargs):
            kwargs["inbox_dir"].mkdir(parents=True)
            kwargs["runner_log_dir"].mkdir(parents=True)
            (kwargs["runner_log_dir"] / "antigravity.log").write_text("Reading from stdin", encoding="utf-8")

            class Result:
                status = "waiting_input"
                exit_code = 0
                error_message = "Antigravity launched; waiting for output file"

            return Result()

    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", lambda runner, model=None: "demo")
    monkeypatch.setattr(runner_smoke_service, "get_runner", lambda runner, model=None: WaitingRunner())

    result = runner_smoke_service.run_runner_smoke_test("codex", tmp_path, model="gpt-5.5")

    assert result["status"] == "waiting_input"
    assert result["error_message"] == "Antigravity launched; waiting for output file"


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

    monkeypatch.setattr(runner_smoke_service, "resolve_runner_command", lambda runner, model=None: "demo")
    monkeypatch.setattr(runner_smoke_service, "get_runner", lambda runner, model=None: CustomLogRunner())

    result = runner_smoke_service.run_runner_smoke_test("codex", tmp_path)

    assert "Reading from stdin" in result["log_content"]
