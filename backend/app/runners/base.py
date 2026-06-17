from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


class RunnerResult(BaseModel):
    status: str
    exit_code: int | None
    produced_files: list[str]
    stdout_summary: str = ""
    stderr_summary: str = ""
    error_message: str | None = None
    started_at: str
    finished_at: str


class Runner(Protocol):
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
        raise NotImplementedError
