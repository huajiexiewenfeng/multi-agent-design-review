from datetime import datetime, timezone
from pathlib import Path

from backend.app.runners.base import RunnerResult


MOCK_OUTPUTS = {
    "clarification": (
        "clarification_result.md",
        "## Clarification Questions\n\n1. [required] Who is the target user?\n\n## Assumptions\n\n- Local-first MVP.\n",
    ),
    "draft_design": (
        "draft_result.md",
        "## Summary\nMock summary\n\n## Proposed Design\nMock design\n\n## Modules\nMock modules\n\n## Data Flow\nMock flow\n\n## Risks\nMock risks\n\n## Open Questions\nNone\n",
    ),
    "cross_review": (
        "review_result.md",
        "## Review Summary\nMock review\n\n## Issues\nNone\n\n## Conflicts\nNone\n\n## Suggestions\nProceed\n\n## Questions For Human\nNone\n",
    ),
    "revision": (
        "revision_result.md",
        "## Revised Design\nMock revision\n\n## Changes Made\nReviewed\n\n## Remaining Risks\nNone\n\n## Implementation Notes\nImplement incrementally\n",
    ),
    "synthesis": (
        "synthesis_result.md",
        "# Design Document\n\n## Architecture\nMock architecture\n\n# Execution Document\n\n## Implementation Plan\nMock plan\n",
    ),
}


class MockRunner:
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
        started = datetime.now(timezone.utc).isoformat()
        inbox_dir.mkdir(parents=True, exist_ok=True)
        runner_log_dir.mkdir(parents=True, exist_ok=True)
        output_name, content = MOCK_OUTPUTS[stage]
        (inbox_dir / output_name).write_text(content, encoding="utf-8")
        (runner_log_dir / "mock.log").write_text(f"mock runner for {run_id}:{agent_id}:{stage}\n", encoding="utf-8")
        finished = datetime.now(timezone.utc).isoformat()
        return RunnerResult(
            status="succeeded",
            exit_code=0,
            produced_files=[output_name],
            stdout_summary="mock output written",
            started_at=started,
            finished_at=finished,
        )
