from pathlib import Path

from backend.app.models import Stage
from backend.app.runners.base import RunnerResult
from backend.app.runners.mock import MockRunner, MOCK_OUTPUTS
from backend.app.services import runner_service
from backend.app.services.agent_config_service import update_agent_config
from backend.app.services.clarification_service import merge_clarification_questions
from backend.app.services.finalize_service import finalize_run
from backend.app.services.flow_control_service import run_until_pause
from backend.app.services.flow_verification_service import get_mixed_runner_verification
from backend.app.services.human_input_service import save_clarification_answers, save_clarified_requirement
from backend.app.services.run_service import create_run
from backend.app.services.runner_handoff_service import import_waiting_runner_outputs


class WaitingAntigravityRunner:
    def run(
        self,
        run_id: str,
        agent_id: str,
        stage: str,
        prompt_file: Path,
        inbox_dir: Path,
        runner_log_dir: Path,
        timeout_seconds: int,
        metadata: dict[str, object],
    ) -> RunnerResult:
        runner_log_dir.mkdir(parents=True, exist_ok=True)
        (runner_log_dir / "antigravity.log").write_text("waiting for external Antigravity output", encoding="utf-8")
        (runner_log_dir / "antigravity_instruction.md").write_text(
            f"OUTPUT_FILE: {inbox_dir / (stage + '_result.md')}\n",
            encoding="utf-8",
        )
        return RunnerResult(
            status="waiting_input",
            exit_code=0,
            produced_files=[],
            stdout_summary="waiting",
            error_message="Antigravity launched; waiting for output file",
            started_at="2026-06-19T00:00:00+00:00",
            finished_at="2026-06-19T00:00:01+00:00",
        )


def test_mixed_runner_flow_reaches_final_outputs_and_verifies_evidence(tmp_path, monkeypatch) -> None:
    projection = create_run(tmp_path, title="Mixed", requirement="# Requirement\nBuild mixed runner flow")
    run_dir = tmp_path / projection.run_id
    update_agent_config(run_dir, "architect", "codex", "Codex CLI")
    update_agent_config(run_dir, "engineer", "claude-code", "Claude Code")
    update_agent_config(run_dir, "reviewer", "antigravity", "Antigravity")
    update_agent_config(run_dir, "synthesizer", "codex", "Codex CLI")
    monkeypatch.setattr(
        runner_service,
        "get_runner",
        lambda name: WaitingAntigravityRunner() if name == "antigravity" else MockRunner(),
    )

    first = run_until_pause(tmp_path, projection.run_id)
    assert first["stop_reason"] == "runner_handoff"
    _write_handoff_output(run_dir, "reviewer", Stage.CLARIFICATION)
    import_waiting_runner_outputs(run_dir)
    merge_clarification_questions(run_dir)
    save_clarification_answers(run_dir, {"q_001": "Local developer"})
    save_clarified_requirement(run_dir, "# Clarified Requirement\nLocal developer")

    second = run_until_pause(tmp_path, projection.run_id)
    assert second["stop_reason"] == "runner_handoff"
    _write_handoff_output(run_dir, "reviewer", Stage.CROSS_REVIEW)
    import_waiting_runner_outputs(run_dir)

    third = run_until_pause(tmp_path, projection.run_id)
    assert third["stop_reason"] == "ready_to_finalize"
    finalize_run(run_dir)

    verification = get_mixed_runner_verification(run_dir)

    assert verification["complete"] is True
    assert (run_dir / "output" / "design_doc.md").is_file()
    assert (run_dir / "output" / "execution_doc.md").is_file()
    assert {runner["runner"]: runner["satisfied"] for runner in verification["runners"]} == {
        "codex": True,
        "claude-code": True,
        "antigravity": True,
    }


def _write_handoff_output(run_dir: Path, agent_id: str, stage: Stage) -> None:
    output_name, content = MOCK_OUTPUTS[stage.value]
    inbox = run_dir / "inbox" / agent_id
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / output_name).write_text(content, encoding="utf-8")
