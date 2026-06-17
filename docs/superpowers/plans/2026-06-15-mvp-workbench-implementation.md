# Multi-Agent Design Review Workbench MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP local-first LangGraph workbench that creates design-review runs, manages file-first state, accepts manual/file/mock runner outputs, shows workflow progress in Web UI, and finalizes traceable Design and Execution documents.

**Architecture:** FastAPI owns API boundaries, service modules own filesystem writes, LangGraph owns fixed workflow orchestration, and `events.jsonl + files` are the facts. `run.json` is a recomputed projection, runner outputs enter through `inbox/`, and all authoritative agent outputs are versioned immutable files.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, LangGraph, pytest, React, Vite, TypeScript, Vitest, React Testing Library.

---

## Scope Check

The spec covers one cohesive MVP: a local workbench with backend workflow, runner abstraction, and frontend views. It has several subsystems, but each is required to run the core workflow end-to-end, so this plan keeps them in one implementation sequence with frequent commits.

## Implementation Phases

This plan is split into two phases:

- **Phase 0: Walking Skeleton** (`Task 1` through `Task 9`) creates the project structure, basic services, runner contract, LangGraph shell, API shell, frontend shell, and finalization utility.
- **Phase 1: Real MVP Flow** (`Task 10` through `Task 17`) turns the shell into the actual workflow described by the design spec: inbox import, versioned authoritative outputs, full state projection, prompt injection, LangGraph stage nodes, API completion, frontend interaction, and a real end-to-end flow test.

The MVP is not complete after Phase 0. Completion requires Phase 1.

## Architecture Decision: Keep LangGraph, Make It Main-Path

External review v3 correctly identified that a partially wired graph is worse than no graph. This plan keeps LangGraph because the approved design selected it as the workflow engine, but it must not remain a decorative shell.

Implementation rule:

- Services remain the fact owners: file writes, event append, import, validation, and projection all stay in service modules.
- LangGraph remains the orchestrator: stage nodes call services and runners, then stop at human checkpoints.
- No graph invocation may silently cross a human checkpoint.
- Manual API actions such as `advance`, `skip`, and `save clarification answers` write facts; the next graph invocation resumes from those facts.
- `Task 22` completes the graph main path so Draft, Review, Revision, and Synthesis are not handled only by direct service calls.

## File Structure

Create these top-level files:

- `README.md`: local setup and MVP usage.
- `.gitignore`: Python, Node, local run outputs.
- `pyproject.toml`: backend dependencies and pytest config.
- `package.json`: root scripts for frontend and backend convenience.

Backend files:

- `backend/app/main.py`: FastAPI app factory and router mounting.
- `backend/app/models.py`: Pydantic domain models and enums.
- `backend/app/services/file_service.py`: safe filesystem helpers, per-run lock, JSON/Markdown IO.
- `backend/app/services/event_service.py`: append/read `events.jsonl`.
- `backend/app/services/state_service.py`: `recompute_state(run_id)` projection logic.
- `backend/app/services/run_service.py`: run creation, loading, stage actions.
- `backend/app/services/prompt_service.py`: prompt rendering.
- `backend/app/services/runner_service.py`: runner dispatch and inbox import.
- `backend/app/services/validation_service.py`: required heading and required input checks.
- `backend/app/services/finalize_service.py`: output document and transcript generation.
- `backend/app/graph/state.py`: LangGraph state type.
- `backend/app/graph/nodes.py`: graph node functions.
- `backend/app/graph/edges.py`: fixed graph construction.
- `backend/app/runners/base.py`: runner protocol and result model.
- `backend/app/runners/manual.py`: manual runner that creates a pending action.
- `backend/app/runners/file.py`: file runner that imports from inbox.
- `backend/app/runners/mock.py`: deterministic mock runner for tests and demo.
- `backend/app/templates/prompts/*.md`: prompt templates for all stages.
- `backend/tests/`: pytest suite.

Frontend files:

- `frontend/package.json`: frontend dependencies.
- `frontend/vite.config.ts`: Vite config.
- `frontend/src/api/client.ts`: typed API client.
- `frontend/src/types/run.ts`: frontend types.
- `frontend/src/pages/RunListPage.tsx`: run list and create form.
- `frontend/src/pages/RunDetailPage.tsx`: main workbench page.
- `frontend/src/components/StageBoard.tsx`: stage progress.
- `frontend/src/components/Timeline.tsx`: event timeline.
- `frontend/src/components/AgentPanel.tsx`: prompts and submissions.
- `frontend/src/components/MarkdownViewer.tsx`: Markdown rendering.
- `frontend/src/components/HumanInputPanel.tsx`: answers, comments, decisions.
- `frontend/src/components/SubmitOutputDialog.tsx`: manual runner submission.
- `frontend/src/__tests__/`: Vitest component tests.

---

## Task 1: Repository Scaffold

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `package.json`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing backend health test**

Create `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
pytest backend/tests/test_health.py -q
```

Expected: FAIL because `backend.app.main` does not exist.

- [ ] **Step 3: Add Python project config**

Create `pyproject.toml`:

```toml
[project]
name = "multi-agent-design-review"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic>=2.8.0",
  "langgraph>=0.2.0",
  "python-multipart>=0.0.9",
  "pyyaml>=6.0.2",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "httpx>=0.27.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["backend/tests"]
```

- [ ] **Step 4: Add FastAPI health endpoint**

Create `backend/app/__init__.py` as an empty file.

Create `backend/app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Multi-Agent Design Review Workbench")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Add root scripts and ignore rules**

Create `.gitignore`:

```gitignore
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
node_modules/
frontend/dist/
runs/
*.pyc
.env
.env.local
```

Create `package.json`:

```json
{
  "scripts": {
    "backend:test": "pytest -q",
    "backend:dev": "uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000",
    "frontend:dev": "npm --prefix frontend run dev",
    "frontend:test": "npm --prefix frontend test"
  }
}
```

Create `README.md`:

````markdown
# Multi-Agent Design Review

Local-first LangGraph workbench for orchestrating multi-agent design reviews with human checkpoints, event logs, and traceable final docs.

## MVP

- FastAPI backend
- React + Vite frontend
- File-first `runs/` storage
- LangGraph fixed workflow
- Manual, file, and mock runners
```

- [ ] **Step 6: Run health test to verify it passes**

Run:

```bash
pytest backend/tests/test_health.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add .gitignore README.md pyproject.toml package.json backend/app backend/tests
git commit -m "chore: scaffold backend project"
```

---

## Task 2: Domain Models and State Projection

**Files:**
- Create: `backend/app/models.py`
- Create: `backend/app/services/state_service.py`
- Test: `backend/tests/test_state_service.py`

- [ ] **Step 1: Write failing state projection tests**

Create `backend/tests/test_state_service.py`:

```python
from pathlib import Path

from backend.app.models import Stage, StageStatus
from backend.app.services.state_service import recompute_state


def test_requirement_ready_when_requirement_file_is_non_empty(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Build a workbench\n", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.REQUIREMENT
    assert projection.status == StageStatus.READY_TO_ADVANCE
    assert projection.missing_inputs == []


def test_requirement_waits_when_requirement_file_is_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "run_002"
    run_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.REQUIREMENT
    assert projection.status == StageStatus.WAITING_INPUT
    assert projection.missing_inputs == ["input/requirement.md"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_state_service.py -q
```

Expected: FAIL because `backend.app.models` and `state_service` do not exist.

- [ ] **Step 3: Define domain models**

Create `backend/app/models.py`:

```python
from enum import StrEnum
from pydantic import BaseModel, Field


class Stage(StrEnum):
    REQUIREMENT = "requirement"
    CLARIFICATION = "clarification"
    CLARIFIED_REQUIREMENT = "clarified_requirement"
    DRAFT_DESIGN = "draft_design"
    CROSS_REVIEW = "cross_review"
    REVISION = "revision"
    SYNTHESIS = "synthesis"


class StageStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    WAITING_INPUT = "waiting_input"
    READY_TO_ADVANCE = "ready_to_advance"
    COMPLETED = "completed"


class ActorType(StrEnum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


class Event(BaseModel):
    id: str
    run_id: str
    timestamp: str
    stage: Stage
    actor: str
    actor_type: ActorType
    event_type: str
    message: str
    related_file: str | None = None
    visibility: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class RunProjection(BaseModel):
    run_id: str
    stage: Stage
    status: StageStatus
    missing_inputs: list[str] = Field(default_factory=list)
    current_versions: dict[str, str] = Field(default_factory=dict)
```

- [ ] **Step 4: Implement minimal state projection**

Create `backend/app/services/state_service.py`:

```python
from pathlib import Path

from backend.app.models import RunProjection, Stage, StageStatus


def _is_non_empty_file(path: Path) -> bool:
    return path.is_file() and path.read_text(encoding="utf-8").strip() != ""


def recompute_state(run_dir: Path) -> RunProjection:
    requirement = run_dir / "input" / "requirement.md"
    run_id = run_dir.name

    if not _is_non_empty_file(requirement):
        return RunProjection(
            run_id=run_id,
            stage=Stage.REQUIREMENT,
            status=StageStatus.WAITING_INPUT,
            missing_inputs=["input/requirement.md"],
        )

    return RunProjection(
        run_id=run_id,
        stage=Stage.REQUIREMENT,
        status=StageStatus.READY_TO_ADVANCE,
        missing_inputs=[],
    )
```

- [ ] **Step 5: Run state tests**

Run:

```bash
pytest backend/tests/test_state_service.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/models.py backend/app/services/state_service.py backend/tests/test_state_service.py
git commit -m "feat: add run state projection"
```

---

## Task 3: File, Event, and Run Services

**Files:**
- Create: `backend/app/services/file_service.py`
- Create: `backend/app/services/event_service.py`
- Create: `backend/app/services/run_service.py`
- Test: `backend/tests/test_run_service.py`

- [ ] **Step 1: Write failing run creation test**

Create `backend/tests/test_run_service.py`:

```python
from pathlib import Path

from backend.app.services.run_service import create_run


def test_create_run_writes_required_files(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    run_dir = tmp_path / projection.run_id

    assert (run_dir / "run.json").is_file()
    assert (run_dir / "events.jsonl").is_file()
    assert (run_dir / "runners.yaml").is_file()
    assert (run_dir / "input" / "requirement.md").read_text(encoding="utf-8").startswith("# Requirement")
    assert (run_dir / "inbox" / "architect").is_dir()
    assert projection.status.value == "ready_to_advance"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_run_service.py -q
```

Expected: FAIL because `run_service` does not exist.

- [ ] **Step 3: Implement file service**

Create `backend/app/services/file_service.py`:

```python
from contextlib import contextmanager
from pathlib import Path
import json
import threading
from typing import Iterator

_LOCKS: dict[str, threading.Lock] = {}


@contextmanager
def run_lock(run_dir: Path) -> Iterator[None]:
    key = str(run_dir.resolve())
    lock = _LOCKS.setdefault(key, threading.Lock())
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
```

- [ ] **Step 4: Implement event service**

Create `backend/app/services/event_service.py`:

```python
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json

from backend.app.models import ActorType, Stage


def append_event(
    run_dir: Path,
    stage: Stage,
    actor: str,
    actor_type: ActorType,
    event_type: str,
    message: str,
    related_file: str | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    event = {
        "id": f"evt_{uuid4().hex[:12]}",
        "run_id": run_dir.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage.value,
        "actor": actor,
        "actor_type": actor_type.value,
        "event_type": event_type,
        "message": message,
        "related_file": related_file,
        "visibility": None,
        "metadata": metadata or {},
    }
    with (run_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
```

- [ ] **Step 5: Implement run creation**

Create `backend/app/services/run_service.py`:

```python
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from backend.app.models import ActorType, Stage
from backend.app.services.event_service import append_event
from backend.app.services.file_service import run_lock, write_json, write_text
from backend.app.services.state_service import recompute_state

AGENTS = ["architect", "engineer", "reviewer", "synthesizer"]


def _new_run_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{uuid4().hex[:4]}"


def _create_directories(run_dir: Path) -> None:
    for path in [
        "input",
        "human",
        "output",
        *[f"agents/{agent}" for agent in AGENTS],
        *[f"inbox/{agent}" for agent in AGENTS],
        *[f"runner_logs/{agent}" for agent in AGENTS],
    ]:
        (run_dir / path).mkdir(parents=True, exist_ok=True)


def create_run(runs_root: Path, title: str, requirement: str):
    run_id = _new_run_id()
    run_dir = runs_root / run_id
    with run_lock(run_dir):
        _create_directories(run_dir)
        write_text(run_dir / "input" / "requirement.md", requirement)
        write_text(run_dir / "events.jsonl", "")
        write_text(
            run_dir / "runners.yaml",
            "architect: mock\nengineer: mock\nreviewer: mock\nsynthesizer: mock\n",
        )
        append_event(
            run_dir,
            Stage.REQUIREMENT,
            "system",
            ActorType.SYSTEM,
            "run_created",
            f"Created run: {title}",
            "input/requirement.md",
            {"title": title},
        )
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json") | {"title": title})
        return projection
```

- [ ] **Step 6: Run run service tests**

Run:

```bash
pytest backend/tests/test_run_service.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services backend/tests/test_run_service.py
git commit -m "feat: add file event and run services"
```

---

## Task 4: Validation, Prompt Rendering, and Runner Contract

**Files:**
- Create: `backend/app/services/validation_service.py`
- Create: `backend/app/services/prompt_service.py`
- Create: `backend/app/runners/base.py`
- Create: `backend/app/runners/manual.py`
- Create: `backend/app/runners/file.py`
- Create: `backend/app/runners/mock.py`
- Create: `backend/app/services/runner_service.py`
- Test: `backend/tests/test_runner_service.py`

- [ ] **Step 1: Write failing runner test**

Create `backend/tests/test_runner_service.py`:

```python
from pathlib import Path

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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_runner_service.py -q
```

Expected: FAIL because runner modules do not exist.

- [ ] **Step 3: Add runner base contract**

Create `backend/app/runners/base.py`:

```python
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
```

- [ ] **Step 4: Add mock runner**

Create `backend/app/runners/mock.py`:

```python
from datetime import datetime, timezone
from pathlib import Path

from backend.app.runners.base import RunnerResult


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
        output_name = f"{stage}_result.md"
        if stage == "clarification":
            output_name = "clarification_result.md"
        (inbox_dir / output_name).write_text(
            "## Clarification Questions\n\n1. Who is the target user?\n\n## Assumptions\n\n- Local-first MVP.\n",
            encoding="utf-8",
        )
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
```

- [ ] **Step 5: Add manual and file runner stubs with explicit behavior**

Create `backend/app/runners/manual.py`:

```python
from datetime import datetime, timezone
from pathlib import Path

from backend.app.runners.base import RunnerResult


class ManualRunner:
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
        now = datetime.now(timezone.utc).isoformat()
        runner_log_dir.mkdir(parents=True, exist_ok=True)
        (runner_log_dir / "manual.log").write_text(f"waiting for manual submission: {prompt_file}\n", encoding="utf-8")
        return RunnerResult(
            status="cancelled",
            exit_code=None,
            produced_files=[],
            stdout_summary="manual submission required",
            started_at=now,
            finished_at=now,
        )
```

Create `backend/app/runners/file.py`:

```python
from datetime import datetime, timezone
from pathlib import Path

from backend.app.runners.base import RunnerResult


class FileRunner:
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
        files = sorted(path.name for path in inbox_dir.glob("*.md"))
        (runner_log_dir / "file.log").write_text(f"found files: {files}\n", encoding="utf-8")
        finished = datetime.now(timezone.utc).isoformat()
        return RunnerResult(
            status="succeeded" if files else "cancelled",
            exit_code=0 if files else None,
            produced_files=files,
            stdout_summary=f"{len(files)} inbox files found",
            started_at=started,
            finished_at=finished,
        )
```

- [ ] **Step 6: Add supporting services**

Create `backend/app/services/validation_service.py`:

```python
from pathlib import Path


def has_required_headings(path: Path, headings: list[str]) -> bool:
    if not path.is_file():
        return False
    content = path.read_text(encoding="utf-8")
    return all(heading in content for heading in headings)
```

Create `backend/app/services/prompt_service.py`:

```python
from pathlib import Path


def write_prompt(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")
```

Create `backend/app/services/runner_service.py`:

```python
from backend.app.runners.file import FileRunner
from backend.app.runners.manual import ManualRunner
from backend.app.runners.mock import MockRunner


def get_runner(name: str):
    runners = {
        "manual": ManualRunner(),
        "file": FileRunner(),
        "mock": MockRunner(),
    }
    if name not in runners:
        raise ValueError(f"Unsupported runner: {name}")
    return runners[name]
```

- [ ] **Step 7: Run runner tests**

Run:

```bash
pytest backend/tests/test_runner_service.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/runners backend/app/services/validation_service.py backend/app/services/prompt_service.py backend/app/services/runner_service.py backend/tests/test_runner_service.py
git commit -m "feat: add runner contract and mock runner"
```

---

## Task 5: LangGraph Workflow

**Files:**
- Create: `backend/app/graph/state.py`
- Create: `backend/app/graph/nodes.py`
- Create: `backend/app/graph/edges.py`
- Modify: `backend/app/services/run_service.py`
- Test: `backend/tests/test_graph_workflow.py`

- [ ] **Step 1: Write failing workflow test**

Create `backend/tests/test_graph_workflow.py`:

```python
from pathlib import Path

from backend.app.graph.edges import build_workflow
from backend.app.services.run_service import create_run


def test_workflow_can_start_requirement_stage(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild")
    graph = build_workflow()

    result = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path)})

    assert result["run_id"] == projection.run_id
    assert result["stage"] == "requirement"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_graph_workflow.py -q
```

Expected: FAIL because graph modules do not exist.

- [ ] **Step 3: Add LangGraph state type**

Create `backend/app/graph/state.py`:

```python
from typing import TypedDict


class WorkflowState(TypedDict):
    run_id: str
    runs_root: str
    stage: str
```

- [ ] **Step 4: Add graph nodes**

Create `backend/app/graph/nodes.py`:

```python
from pathlib import Path

from backend.app.graph.state import WorkflowState
from backend.app.services.state_service import recompute_state


def load_projection_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value}
```

- [ ] **Step 5: Add graph builder**

Create `backend/app/graph/edges.py`:

```python
from langgraph.graph import END, StateGraph

from backend.app.graph.nodes import load_projection_node
from backend.app.graph.state import WorkflowState


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("load_projection", load_projection_node)
    graph.set_entry_point("load_projection")
    graph.add_edge("load_projection", END)
    return graph.compile()
```

- [ ] **Step 6: Run workflow test**

Run:

```bash
pytest backend/tests/test_graph_workflow.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/graph backend/tests/test_graph_workflow.py
git commit -m "feat: add LangGraph workflow skeleton"
```

---

## Task 6: API Endpoints

**Files:**
- Modify: `backend/app/main.py`
- Create: `backend/app/api.py`
- Test: `backend/tests/test_api_runs.py`

- [ ] **Step 1: Write failing API test**

Create `backend/tests/test_api_runs.py`:

```python
from fastapi.testclient import TestClient

import backend.app.api as api_module
from backend.app.main import app


def test_create_run_api(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)

    response = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"})

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "requirement"
    assert body["status"] == "ready_to_advance"
```

- [ ] **Step 2: Run API test to verify it fails**

Run:

```bash
pytest backend/tests/test_api_runs.py -q
```

Expected: FAIL because `/api/runs` does not exist.

- [ ] **Step 3: Add API router**

Create `backend/app/api.py`:

```python
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.run_service import create_run

RUNS_ROOT = Path("runs")
router = APIRouter(prefix="/api")


class CreateRunRequest(BaseModel):
    title: str
    requirement: str


@router.post("/runs")
def create_run_endpoint(request: CreateRunRequest):
    projection = create_run(RUNS_ROOT, request.title, request.requirement)
    return projection.model_dump(mode="json")
```

- [ ] **Step 4: Mount API router**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI

from backend.app.api import router as api_router

app = FastAPI(title="Multi-Agent Design Review Workbench")
app.include_router(api_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Run backend tests**

Run:

```bash
pytest backend/tests -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api.py backend/app/main.py backend/tests/test_api_runs.py
git commit -m "feat: add run API endpoints"
```

---

## Task 7: Frontend Scaffold and Run Views

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/types/run.ts`
- Create: `frontend/src/pages/RunListPage.tsx`
- Create: `frontend/src/pages/RunDetailPage.tsx`
- Create: `frontend/src/components/StageBoard.tsx`
- Create: `frontend/src/components/Timeline.tsx`
- Test: `frontend/src/__tests__/StageBoard.test.tsx`

- [ ] **Step 1: Add failing StageBoard test**

Create `frontend/src/__tests__/StageBoard.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StageBoard } from "../components/StageBoard";

describe("StageBoard", () => {
  it("marks current stage", () => {
    render(<StageBoard currentStage="draft_design" />);
    expect(screen.getByText("Draft Design").getAttribute("data-current")).toBe("true");
  });
});
```

- [ ] **Step 2: Run frontend test to verify it fails**

Run:

```bash
npm --prefix frontend test -- --run
```

Expected: FAIL because frontend project files do not exist.

- [ ] **Step 3: Add frontend package and config**

Create `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1 --port 5173",
    "build": "vite build",
    "test": "vitest"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "marked": "^14.1.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.8",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0",
    "jsdom": "^24.1.0"
  }
}
```

Create `frontend/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom"
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000"
    }
  }
});
```

Create `frontend/index.html`:

```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

- [ ] **Step 4: Add StageBoard component**

Create `frontend/src/components/StageBoard.tsx`:

```tsx
const STAGES = [
  ["requirement", "Requirement"],
  ["clarification", "Clarification"],
  ["clarified_requirement", "Clarified Requirement"],
  ["draft_design", "Draft Design"],
  ["cross_review", "Cross Review"],
  ["revision", "Revision"],
  ["synthesis", "Synthesis"]
];

export function StageBoard({ currentStage }: { currentStage: string }) {
  return (
    <nav aria-label="Workflow stages">
      {STAGES.map(([id, label]) => (
        <button key={id} data-current={id === currentStage ? "true" : "false"}>
          {label}
        </button>
      ))}
    </nav>
  );
}
```

- [ ] **Step 5: Add minimal pages and main entry**

Create `frontend/src/main.tsx`:

```tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { RunListPage } from "./pages/RunListPage";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RunListPage />
  </React.StrictMode>
);
```

Create `frontend/src/pages/RunListPage.tsx`:

```tsx
import { StageBoard } from "../components/StageBoard";

export function RunListPage() {
  return (
    <main>
      <h1>Multi-Agent Design Review</h1>
      <StageBoard currentStage="requirement" />
    </main>
  );
}
```

Create `frontend/src/pages/RunDetailPage.tsx`:

```tsx
import { StageBoard } from "../components/StageBoard";

export function RunDetailPage({ stage }: { stage: string }) {
  return (
    <main>
      <StageBoard currentStage={stage} />
      <section aria-label="Current stage content" />
    </main>
  );
}
```

Create `frontend/src/components/Timeline.tsx`:

```tsx
export type TimelineEvent = {
  id: string;
  actor: string;
  event_type: string;
  message: string;
};

export function Timeline({ events }: { events: TimelineEvent[] }) {
  return (
    <aside aria-label="Timeline">
      {events.map((event) => (
        <article key={event.id}>
          <strong>{event.actor}</strong>
          <span>{event.event_type}</span>
          <p>{event.message}</p>
        </article>
      ))}
    </aside>
  );
}
```

- [ ] **Step 6: Run frontend tests**

Run:

```bash
npm --prefix frontend test -- --run
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend
git commit -m "feat: add frontend workbench scaffold"
```

---

## Task 8: Finalize and Transcript

**Files:**
- Create: `backend/app/services/finalize_service.py`
- Test: `backend/tests/test_finalize_service.py`

- [ ] **Step 1: Write failing finalize test**

Create `backend/tests/test_finalize_service.py`:

```python
from pathlib import Path

from backend.app.services.finalize_service import finalize_run


def test_finalize_copies_current_synthesis_outputs(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    (run_dir / "agents" / "synthesizer").mkdir(parents=True)
    (run_dir / "events.jsonl").write_text(
        '{"id":"evt_1","actor":"system","event_type":"run_created","message":"created"}\n',
        encoding="utf-8",
    )
    (run_dir / "agents" / "synthesizer" / "design_doc.v1.md").write_text("# Design Document\n\n## Architecture\nA", encoding="utf-8")
    (run_dir / "agents" / "synthesizer" / "execution_doc.v1.md").write_text("# Execution Document\n\n## Implementation Plan\nB", encoding="utf-8")

    finalize_run(run_dir)

    assert (run_dir / "output" / "design_doc.md").read_text(encoding="utf-8").startswith("# Design Document")
    assert (run_dir / "output" / "execution_doc.md").read_text(encoding="utf-8").startswith("# Execution Document")
    assert "run_created" in (run_dir / "output" / "transcript.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_finalize_service.py -q
```

Expected: FAIL because `finalize_service` does not exist.

- [ ] **Step 3: Implement finalize service**

Create `backend/app/services/finalize_service.py`:

```python
from pathlib import Path
import json
import shutil


def _latest_version(path: Path, pattern: str) -> Path:
    candidates = sorted(path.glob(pattern))
    if not candidates:
        raise FileNotFoundError(f"Missing synthesis output matching {pattern}")
    return candidates[-1]


def _render_transcript(events_jsonl: Path) -> str:
    lines = ["# Transcript", ""]
    for raw in events_jsonl.read_text(encoding="utf-8").splitlines():
        if raw.strip() == "":
            continue
        event = json.loads(raw)
        lines.append(f"- **{event.get('actor', 'unknown')}** `{event.get('event_type', 'event')}`: {event.get('message', '')}")
    lines.append("")
    return "\n".join(lines)


def finalize_run(run_dir: Path) -> None:
    synthesizer_dir = run_dir / "agents" / "synthesizer"
    output_dir = run_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    design_source = _latest_version(synthesizer_dir, "design_doc.v*.md")
    execution_source = _latest_version(synthesizer_dir, "execution_doc.v*.md")

    shutil.copyfile(design_source, output_dir / "design_doc.md")
    shutil.copyfile(execution_source, output_dir / "execution_doc.md")
    (output_dir / "transcript.md").write_text(_render_transcript(run_dir / "events.jsonl"), encoding="utf-8")
```

- [ ] **Step 4: Run finalize test**

Run:

```bash
pytest backend/tests/test_finalize_service.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/finalize_service.py backend/tests/test_finalize_service.py
git commit -m "feat: add finalization outputs"
```

---

## Task 9: Phase 0 Smoke Verification and Documentation

**Files:**
- Modify: `README.md`
- Create: `backend/tests/test_mvp_flow.py`

- [ ] **Step 1: Write failing MVP flow test**

Create `backend/tests/test_mvp_flow.py`:

```python
from pathlib import Path

from backend.app.services.finalize_service import finalize_run
from backend.app.services.run_service import create_run


def test_phase0_smoke_flow_with_manual_synthesis_files(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    run_dir = tmp_path / projection.run_id
    synth_dir = run_dir / "agents" / "synthesizer"
    synth_dir.mkdir(parents=True, exist_ok=True)
    (synth_dir / "design_doc.v1.md").write_text("# Design Document\n\n## Architecture\nFile-first", encoding="utf-8")
    (synth_dir / "execution_doc.v1.md").write_text("# Execution Document\n\n## Implementation Plan\nBuild services", encoding="utf-8")

    finalize_run(run_dir)

    assert (run_dir / "output" / "design_doc.md").is_file()
    assert (run_dir / "output" / "execution_doc.md").is_file()
    assert (run_dir / "output" / "transcript.md").is_file()
```

- [ ] **Step 2: Run MVP flow test**

Run:

```bash
pytest backend/tests/test_mvp_flow.py -q
```

Expected: PASS after earlier tasks are complete.

- [ ] **Step 3: Update README with local commands**

Modify `README.md`:

```markdown
# Multi-Agent Design Review

Local-first LangGraph workbench for orchestrating multi-agent design reviews with human checkpoints, event logs, and traceable final docs.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
npm --prefix frontend install
```

## Run Backend

```bash
npm run backend:dev
```

## Run Frontend

```bash
npm run frontend:dev
```

## Test

```bash
npm run backend:test
npm --prefix frontend test -- --run
```

## MVP Storage

Runs are stored under `runs/<run_id>/`. The facts are `events.jsonl` and files. `run.json` is a recomputed projection.
````

- [ ] **Step 4: Run all backend tests**

Run:

```bash
pytest -q
```

Expected: PASS.

- [ ] **Step 5: Run frontend tests**

Run:

```bash
npm --prefix frontend test -- --run
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add README.md backend/tests/test_mvp_flow.py
git commit -m "test: add phase 0 smoke verification"
```

---

## Task 10: Inbox Import Pipeline and Versioned Submissions

**Files:**
- Create: `backend/app/services/workflow_service.py`
- Modify: `backend/app/services/validation_service.py`
- Modify: `backend/app/services/state_service.py`
- Test: `backend/tests/test_workflow_import.py`

- [ ] **Step 1: Write failing import tests**

Create `backend/tests/test_workflow_import.py`:

```python
from pathlib import Path

from backend.app.models import Stage
from backend.app.services.workflow_service import import_from_inbox


def _make_run(run_dir: Path) -> None:
    (run_dir / "agents" / "architect").mkdir(parents=True)
    (run_dir / "inbox" / "architect").mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (run_dir / "run.json").write_text("{}", encoding="utf-8")


def test_import_from_inbox_creates_versioned_authoritative_file(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    _make_run(run_dir)
    (run_dir / "inbox" / "architect" / "draft.md").write_text(
        "## Summary\nA\n\n## Proposed Design\nB\n\n## Modules\nC\n\n## Data Flow\nD\n\n## Risks\nE\n\n## Open Questions\nF\n",
        encoding="utf-8",
    )

    imported = import_from_inbox(run_dir, "architect", Stage.DRAFT_DESIGN)

    assert imported == run_dir / "agents" / "architect" / "draft_response.v1.md"
    assert imported.read_text(encoding="utf-8").startswith("## Summary")
    assert "file_imported" in (run_dir / "events.jsonl").read_text(encoding="utf-8")


def test_second_import_creates_new_version_and_superseded_event(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_002"
    _make_run(run_dir)
    inbox_file = run_dir / "inbox" / "architect" / "draft.md"
    inbox_file.write_text(
        "## Summary\nA\n\n## Proposed Design\nB\n\n## Modules\nC\n\n## Data Flow\nD\n\n## Risks\nE\n\n## Open Questions\nF\n",
        encoding="utf-8",
    )
    import_from_inbox(run_dir, "architect", Stage.DRAFT_DESIGN)
    inbox_file.write_text(
        "## Summary\nA2\n\n## Proposed Design\nB2\n\n## Modules\nC2\n\n## Data Flow\nD2\n\n## Risks\nE2\n\n## Open Questions\nF2\n",
        encoding="utf-8",
    )

    imported = import_from_inbox(run_dir, "architect", Stage.DRAFT_DESIGN)

    assert imported.name == "draft_response.v2.md"
    events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert "submission_superseded" in events
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_workflow_import.py -q
```

Expected: FAIL because `workflow_service.import_from_inbox` does not exist.

- [ ] **Step 3: Extend validation service**

Modify `backend/app/services/validation_service.py`:

```python
from pathlib import Path

from backend.app.models import Stage


REQUIRED_HEADINGS: dict[Stage, list[str]] = {
    Stage.CLARIFICATION: ["## Clarification Questions", "## Assumptions"],
    Stage.DRAFT_DESIGN: ["## Summary", "## Proposed Design", "## Modules", "## Data Flow", "## Risks", "## Open Questions"],
    Stage.CROSS_REVIEW: ["## Review Summary", "## Issues", "## Conflicts", "## Suggestions", "## Questions For Human"],
    Stage.REVISION: ["## Revised Design", "## Changes Made", "## Remaining Risks", "## Implementation Notes"],
}


def has_required_headings(path: Path, headings: list[str]) -> bool:
    if not path.is_file():
        return False
    content = path.read_text(encoding="utf-8")
    return all(heading in content for heading in headings)


def validate_stage_output(path: Path, stage: Stage) -> list[str]:
    if not path.is_file():
        return [f"Missing file: {path.name}"]
    if path.read_text(encoding="utf-8").strip() == "":
        return [f"Empty file: {path.name}"]
    missing = [heading for heading in REQUIRED_HEADINGS.get(stage, []) if heading not in path.read_text(encoding="utf-8")]
    return [f"Missing heading: {heading}" for heading in missing]
```

- [ ] **Step 4: Implement workflow import service**

Create `backend/app/services/workflow_service.py`:

```python
from pathlib import Path
import re

from backend.app.models import ActorType, Stage
from backend.app.services.event_service import append_event
from backend.app.services.file_service import run_lock, write_json
from backend.app.services.state_service import recompute_state
from backend.app.services.validation_service import validate_stage_output

ARTIFACT_BY_STAGE: dict[Stage, str] = {
    Stage.CLARIFICATION: "clarification_questions",
    Stage.DRAFT_DESIGN: "draft_response",
    Stage.CROSS_REVIEW: "review_response",
    Stage.REVISION: "revision_response",
}


def _next_version(agent_dir: Path, artifact: str) -> int:
    versions: list[int] = []
    pattern = re.compile(rf"^{re.escape(artifact)}\.v(\d+)\.md$")
    for path in agent_dir.glob(f"{artifact}.v*.md"):
        match = pattern.match(path.name)
        if match:
            versions.append(int(match.group(1)))
    return max(versions, default=0) + 1


def _first_inbox_markdown(run_dir: Path, agent_id: str) -> Path:
    inbox_dir = run_dir / "inbox" / agent_id
    files = sorted(inbox_dir.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No markdown files found in {inbox_dir}")
    return files[0]


def import_from_inbox(run_dir: Path, agent_id: str, stage: Stage) -> Path:
    artifact = ARTIFACT_BY_STAGE[stage]
    with run_lock(run_dir):
        source = _first_inbox_markdown(run_dir, agent_id)
        errors = validate_stage_output(source, stage)
        if errors:
            append_event(run_dir, stage, agent_id, ActorType.AGENT, "validation_failed", "; ".join(errors), str(source.relative_to(run_dir)))
            raise ValueError("; ".join(errors))

        agent_dir = run_dir / "agents" / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        version = _next_version(agent_dir, artifact)
        target = agent_dir / f"{artifact}.v{version}.md"
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        if version > 1:
            append_event(
                run_dir,
                stage,
                agent_id,
                ActorType.AGENT,
                "submission_superseded",
                f"{artifact}.v{version - 1}.md superseded by {target.name}",
                str(target.relative_to(run_dir)),
            )
        append_event(run_dir, stage, agent_id, ActorType.AGENT, "file_imported", f"Imported {target.name}", str(target.relative_to(run_dir)))
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json"))
        return target
```

- [ ] **Step 5: Run import tests**

Run:

```bash
pytest backend/tests/test_workflow_import.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/workflow_service.py backend/app/services/validation_service.py backend/tests/test_workflow_import.py
git commit -m "feat: add inbox import pipeline"
```

---

## Task 11: Full-Stage State Projection

**Files:**
- Modify: `backend/app/services/event_service.py`
- Modify: `backend/app/services/state_service.py`
- Test: `backend/tests/test_state_full_flow.py`

- [ ] **Step 1: Write failing full-state tests**

Create `backend/tests/test_state_full_flow.py`:

```python
from pathlib import Path

from backend.app.models import Stage, StageStatus
from backend.app.services.state_service import recompute_state


def test_state_moves_to_draft_after_clarified_requirement_ready(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "agents" / "architect").mkdir(parents=True)
    (run_dir / "agents" / "engineer").mkdir(parents=True)
    (run_dir / "agents" / "reviewer").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
    (run_dir / "agents" / "architect" / "clarification_questions.v1.md").write_text("## Clarification Questions\n\n## Assumptions\n", encoding="utf-8")
    (run_dir / "agents" / "engineer" / "clarification_questions.v1.md").write_text("## Clarification Questions\n\n## Assumptions\n", encoding="utf-8")
    (run_dir / "agents" / "reviewer" / "clarification_questions.v1.md").write_text("## Clarification Questions\n\n## Assumptions\n", encoding="utf-8")
    (run_dir / "input" / "clarification_questions.json").write_text('{"questions":[{"id":"q_001","required":true}]}', encoding="utf-8")
    (run_dir / "input" / "human_answers.json").write_text('{"answers":{"q_001":"Local user"}}', encoding="utf-8")
    (run_dir / "input" / "clarified_requirement.md").write_text("# Clarified\n", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.DRAFT_DESIGN
    assert projection.status == StageStatus.WAITING_INPUT
    assert "agents/architect/draft_response.v*.md" in projection.missing_inputs


def test_skip_event_unblocks_missing_reviewer(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_002"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "agents" / "architect").mkdir(parents=True)
    (run_dir / "agents" / "engineer").mkdir(parents=True)
    (run_dir / "agents" / "reviewer").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
    (run_dir / "agents" / "architect" / "clarification_questions.v1.md").write_text("## Clarification Questions\n\n## Assumptions\n", encoding="utf-8")
    (run_dir / "agents" / "engineer" / "clarification_questions.v1.md").write_text("## Clarification Questions\n\n## Assumptions\n", encoding="utf-8")
    (run_dir / "events.jsonl").write_text(
        '{"event_type":"agent_skipped","stage":"clarification","actor":"reviewer"}\n',
        encoding="utf-8",
    )

    projection = recompute_state(run_dir)

    assert projection.stage == Stage.CLARIFIED_REQUIREMENT
    assert "agents/reviewer/clarification_questions.v*.md" not in projection.missing_inputs
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_state_full_flow.py -q
```

Expected: FAIL because `recompute_state` only handles Requirement.

- [ ] **Step 3: Add event reading helper**

Modify `backend/app/services/event_service.py`:

```python
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json

from backend.app.models import ActorType, Stage


def append_event(
    run_dir: Path,
    stage: Stage,
    actor: str,
    actor_type: ActorType,
    event_type: str,
    message: str,
    related_file: str | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    event = {
        "id": f"evt_{uuid4().hex[:12]}",
        "run_id": run_dir.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage.value,
        "actor": actor,
        "actor_type": actor_type.value,
        "event_type": event_type,
        "message": message,
        "related_file": related_file,
        "visibility": None,
        "metadata": metadata or {},
    }
    with (run_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_events(run_dir: Path) -> list[dict[str, object]]:
    events_file = run_dir / "events.jsonl"
    if not events_file.is_file():
        return []
    events: list[dict[str, object]] = []
    for raw in events_file.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            events.append(json.loads(raw))
    return events
```

- [ ] **Step 4: Implement full-stage recompute**

Modify `backend/app/services/state_service.py`:

```python
from pathlib import Path

from backend.app.models import RunProjection, Stage, StageStatus
from backend.app.services.event_service import read_events


def _is_non_empty_file(path: Path) -> bool:
    return path.is_file() and path.read_text(encoding="utf-8").strip() != ""


def _has_version(run_dir: Path, pattern: str) -> bool:
    return bool(list(run_dir.glob(pattern)))


def _skipped(events: list[dict[str, object]], stage: Stage, agent: str) -> bool:
    return any(event.get("event_type") == "agent_skipped" and event.get("stage") == stage.value and event.get("actor") == agent for event in events)


def _missing_agent_versions(run_dir: Path, events: list[dict[str, object]], stage: Stage, agents: list[str], artifact: str) -> list[str]:
    missing: list[str] = []
    for agent in agents:
        if _skipped(events, stage, agent):
            continue
        pattern = f"agents/{agent}/{artifact}.v*.md"
        if not _has_version(run_dir, pattern):
            missing.append(pattern)
    return missing


def _required_answers_ready(run_dir: Path) -> bool:
    questions = run_dir / "input" / "clarification_questions.json"
    answers = run_dir / "input" / "human_answers.json"
    return _is_non_empty_file(questions) and _is_non_empty_file(answers)


def _projection(run_dir: Path, stage: Stage, missing: list[str]) -> RunProjection:
    return RunProjection(
        run_id=run_dir.name,
        stage=stage,
        status=StageStatus.READY_TO_ADVANCE if not missing else StageStatus.WAITING_INPUT,
        missing_inputs=missing,
    )


def recompute_state(run_dir: Path) -> RunProjection:
    events = read_events(run_dir)
    if not _is_non_empty_file(run_dir / "input" / "requirement.md"):
        return _projection(run_dir, Stage.REQUIREMENT, ["input/requirement.md"])

    missing = _missing_agent_versions(run_dir, events, Stage.CLARIFICATION, ["architect", "engineer", "reviewer"], "clarification_questions")
    if missing:
        return _projection(run_dir, Stage.CLARIFICATION, missing)

    clarified_missing = []
    if not _required_answers_ready(run_dir):
        clarified_missing.extend(["input/clarification_questions.json", "input/human_answers.json"])
    if not _is_non_empty_file(run_dir / "input" / "clarified_requirement.md"):
        clarified_missing.append("input/clarified_requirement.md")
    if clarified_missing:
        return _projection(run_dir, Stage.CLARIFIED_REQUIREMENT, clarified_missing)

    missing = _missing_agent_versions(run_dir, events, Stage.DRAFT_DESIGN, ["architect", "engineer"], "draft_response")
    if missing:
        return _projection(run_dir, Stage.DRAFT_DESIGN, missing)

    missing = _missing_agent_versions(run_dir, events, Stage.CROSS_REVIEW, ["architect", "engineer", "reviewer"], "review_response")
    if missing:
        return _projection(run_dir, Stage.CROSS_REVIEW, missing)

    missing = _missing_agent_versions(run_dir, events, Stage.REVISION, ["architect", "engineer"], "revision_response")
    if missing:
        return _projection(run_dir, Stage.REVISION, missing)

    synthesis_missing = []
    if not _has_version(run_dir, "agents/synthesizer/design_doc.v*.md"):
        synthesis_missing.append("agents/synthesizer/design_doc.v*.md")
    if not _has_version(run_dir, "agents/synthesizer/execution_doc.v*.md"):
        synthesis_missing.append("agents/synthesizer/execution_doc.v*.md")
    return _projection(run_dir, Stage.SYNTHESIS, synthesis_missing)
```

- [ ] **Step 5: Run full state tests**

Run:

```bash
pytest backend/tests/test_state_full_flow.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/event_service.py backend/app/services/state_service.py backend/tests/test_state_full_flow.py
git commit -m "feat: add full workflow state projection"
```

---

## Task 12: Prompt Templates and Stage Injection

**Files:**
- Modify: `backend/app/services/prompt_service.py`
- Create: `backend/app/templates/prompts/clarification.md`
- Create: `backend/app/templates/prompts/draft.md`
- Create: `backend/app/templates/prompts/review.md`
- Create: `backend/app/templates/prompts/revision.md`
- Create: `backend/app/templates/prompts/synthesis.md`
- Test: `backend/tests/test_prompt_service.py`

- [ ] **Step 1: Write failing prompt injection tests**

Create `backend/tests/test_prompt_service.py`:

```python
from pathlib import Path

from backend.app.models import Stage
from backend.app.services.prompt_service import render_prompt


def test_draft_prompt_does_not_include_other_agent_draft(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "agents" / "engineer").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("Original requirement", encoding="utf-8")
    (run_dir / "input" / "human_answers.md").write_text("Human answer", encoding="utf-8")
    (run_dir / "input" / "clarified_requirement.md").write_text("Clarified requirement", encoding="utf-8")
    (run_dir / "agents" / "engineer" / "draft_response.v1.md").write_text("Engineer draft should not appear", encoding="utf-8")

    prompt = render_prompt(Stage.DRAFT_DESIGN, "architect", run_dir)

    assert "Original requirement" in prompt
    assert "Human answer" in prompt
    assert "Clarified requirement" in prompt
    assert "Engineer draft should not appear" not in prompt


def test_review_prompt_includes_all_drafts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_002"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "agents" / "architect").mkdir(parents=True)
    (run_dir / "agents" / "engineer").mkdir(parents=True)
    (run_dir / "input" / "clarified_requirement.md").write_text("Clarified", encoding="utf-8")
    (run_dir / "agents" / "architect" / "draft_response.v1.md").write_text("Architect draft", encoding="utf-8")
    (run_dir / "agents" / "engineer" / "draft_response.v1.md").write_text("Engineer draft", encoding="utf-8")

    prompt = render_prompt(Stage.CROSS_REVIEW, "reviewer", run_dir)

    assert "Architect draft" in prompt
    assert "Engineer draft" in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_prompt_service.py -q
```

Expected: FAIL because `render_prompt` is not implemented.

- [ ] **Step 3: Create prompt templates**

Create `backend/app/templates/prompts/clarification.md`:

```markdown
# Clarification Prompt

Role: {agent_id}

## Requirement

{requirement}

Return:

## Clarification Questions

## Assumptions
```

Create `backend/app/templates/prompts/draft.md`:

```markdown
# Draft Prompt

Role: {agent_id}

## Original Requirement

{requirement}

## Human Answers

{human_answers}

## Clarified Requirement

{clarified_requirement}

Return:

## Summary
## Proposed Design
## Modules
## Data Flow
## Risks
## Open Questions
```

Create `backend/app/templates/prompts/review.md`:

```markdown
# Review Prompt

Role: {agent_id}

## Clarified Requirement

{clarified_requirement}

## Drafts

{drafts}

Return:

## Review Summary
## Issues
## Conflicts
## Suggestions
## Questions For Human
```

Create `backend/app/templates/prompts/revision.md`:

```markdown
# Revision Prompt

Role: {agent_id}

## Own Draft

{own_draft}

## Reviews

{reviews}

## Human Notes

{human_notes}

Return:

## Revised Design
## Changes Made
## Remaining Risks
## Implementation Notes
```

Create `backend/app/templates/prompts/synthesis.md`:

```markdown
# Synthesis Prompt

## Clarified Requirement

{clarified_requirement}

## Drafts

{drafts}

## Reviews

{reviews}

## Revisions

{revisions}

## Human Notes

{human_notes}

Produce two documents: Design Document and Execution Document.
```

- [ ] **Step 4: Implement prompt rendering**

Modify `backend/app/services/prompt_service.py`:

```python
from pathlib import Path

from backend.app.models import Stage

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "prompts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _latest_text(run_dir: Path, pattern: str) -> str:
    files = sorted(run_dir.glob(pattern))
    return files[-1].read_text(encoding="utf-8") if files else ""


def _all_text(run_dir: Path, pattern: str) -> str:
    return "\n\n".join(path.read_text(encoding="utf-8") for path in sorted(run_dir.glob(pattern)))


def _template(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text(encoding="utf-8")


def write_prompt(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def render_prompt(stage: Stage, agent_id: str, run_dir: Path) -> str:
    requirement = _read(run_dir / "input" / "requirement.md")
    human_answers = _read(run_dir / "input" / "human_answers.md")
    clarified_requirement = _read(run_dir / "input" / "clarified_requirement.md")
    human_notes = "\n\n".join([_read(run_dir / "human" / "comments.md"), _read(run_dir / "human" / "decisions.md")])

    if stage == Stage.CLARIFICATION:
        return _template("clarification.md").format(agent_id=agent_id, requirement=requirement)
    if stage == Stage.DRAFT_DESIGN:
        return _template("draft.md").format(
            agent_id=agent_id,
            requirement=requirement,
            human_answers=human_answers,
            clarified_requirement=clarified_requirement,
        )
    if stage == Stage.CROSS_REVIEW:
        return _template("review.md").format(
            agent_id=agent_id,
            clarified_requirement=clarified_requirement,
            drafts=_all_text(run_dir, "agents/*/draft_response.v*.md"),
        )
    if stage == Stage.REVISION:
        return _template("revision.md").format(
            agent_id=agent_id,
            own_draft=_latest_text(run_dir, f"agents/{agent_id}/draft_response.v*.md"),
            reviews=_all_text(run_dir, "agents/*/review_response.v*.md"),
            human_notes=human_notes,
        )
    if stage == Stage.SYNTHESIS:
        return _template("synthesis.md").format(
            clarified_requirement=clarified_requirement,
            drafts=_all_text(run_dir, "agents/*/draft_response.v*.md"),
            reviews=_all_text(run_dir, "agents/*/review_response.v*.md"),
            revisions=_all_text(run_dir, "agents/*/revision_response.v*.md"),
            human_notes=human_notes,
        )
    raise ValueError(f"Unsupported prompt stage: {stage}")
```

- [ ] **Step 5: Run prompt tests**

Run:

```bash
pytest backend/tests/test_prompt_service.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/prompt_service.py backend/app/templates/prompts backend/tests/test_prompt_service.py
git commit -m "feat: add stage prompt rendering"
```

---

## Task 13: LangGraph Stage Nodes and Checkpoint Flow

**Files:**
- Modify: `backend/app/graph/state.py`
- Modify: `backend/app/graph/nodes.py`
- Modify: `backend/app/graph/edges.py`
- Modify: `backend/app/services/runner_service.py`
- Test: `backend/tests/test_graph_stage_flow.py`

- [ ] **Step 1: Write failing graph stage test**

Create `backend/tests/test_graph_stage_flow.py`:

```python
from pathlib import Path

from backend.app.graph.edges import build_workflow
from backend.app.services.run_service import create_run


def test_graph_runs_clarification_with_mock_runner(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild")
    graph = build_workflow()

    result = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})

    run_dir = tmp_path / projection.run_id
    assert result["stage"] in {"clarification", "clarified_requirement"}
    assert (run_dir / "agents" / "architect" / "clarification_questions.v1.md").is_file()
    assert "file_imported" in (run_dir / "events.jsonl").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_graph_stage_flow.py -q
```

Expected: FAIL because graph nodes do not call runners or import inbox.

- [ ] **Step 3: Extend graph state**

Modify `backend/app/graph/state.py`:

```python
from typing import TypedDict


class WorkflowState(TypedDict, total=False):
    run_id: str
    runs_root: str
    stage: str
    confirmed: bool
```

- [ ] **Step 4: Add runner invocation helper**

Modify `backend/app/services/runner_service.py`:

```python
from pathlib import Path

from backend.app.models import Stage
from backend.app.runners.file import FileRunner
from backend.app.runners.manual import ManualRunner
from backend.app.runners.mock import MockRunner
from backend.app.services.prompt_service import render_prompt
from backend.app.services.workflow_service import import_from_inbox


def get_runner(name: str):
    runners = {
        "manual": ManualRunner(),
        "file": FileRunner(),
        "mock": MockRunner(),
    }
    if name not in runners:
        raise ValueError(f"Unsupported runner: {name}")
    return runners[name]


def run_agent_stage(run_dir: Path, agent_id: str, stage: Stage, runner_name: str = "mock") -> None:
    prompt_name = {
        Stage.CLARIFICATION: "clarification_prompt.md",
        Stage.DRAFT_DESIGN: "draft_prompt.md",
        Stage.CROSS_REVIEW: "review_prompt.md",
        Stage.REVISION: "revision_prompt.md",
        Stage.SYNTHESIS: "synthesis_prompt.md",
    }[stage]
    prompt_file = run_dir / "agents" / agent_id / prompt_name
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(render_prompt(stage, agent_id, run_dir), encoding="utf-8")
    runner = get_runner(runner_name)
    result = runner.run(
        run_id=run_dir.name,
        agent_id=agent_id,
        stage=stage.value,
        prompt_file=prompt_file,
        inbox_dir=run_dir / "inbox" / agent_id,
        runner_log_dir=run_dir / "runner_logs" / agent_id,
        timeout_seconds=30,
        metadata={},
    )
    if result.status == "succeeded":
        import_from_inbox(run_dir, agent_id, stage)
```

- [ ] **Step 5: Implement clarification graph node**

Modify `backend/app/graph/nodes.py`:

```python
from pathlib import Path

from backend.app.graph.state import WorkflowState
from backend.app.models import Stage
from backend.app.services.runner_service import run_agent_stage
from backend.app.services.state_service import recompute_state


def load_projection_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value}


def clarification_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    for agent in ["architect", "engineer", "reviewer"]:
        if not list((run_dir / "agents" / agent).glob("clarification_questions.v*.md")):
            run_agent_stage(run_dir, agent, Stage.CLARIFICATION)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value}
```

- [ ] **Step 6: Wire graph through clarification**

Modify `backend/app/graph/edges.py`:

```python
from langgraph.graph import END, StateGraph

from backend.app.graph.nodes import clarification_node, load_projection_node
from backend.app.graph.state import WorkflowState


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("load_projection", load_projection_node)
    graph.add_node("clarification", clarification_node)
    graph.set_entry_point("load_projection")
    graph.add_edge("load_projection", "clarification")
    graph.add_edge("clarification", END)
    return graph.compile()
```

- [ ] **Step 7: Run graph stage test**

Run:

```bash
pytest backend/tests/test_graph_stage_flow.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/graph backend/app/services/runner_service.py backend/tests/test_graph_stage_flow.py
git commit -m "feat: connect LangGraph to runner import flow"
```

---

## Task 14: Clarification Question Merge

**Files:**
- Create: `backend/app/services/clarification_service.py`
- Test: `backend/tests/test_clarification_service.py`

- [ ] **Step 1: Write failing merge test**

Create `backend/tests/test_clarification_service.py`:

```python
from pathlib import Path
import json

from backend.app.services.clarification_service import merge_clarification_questions


def test_merge_clarification_questions_writes_json_and_markdown(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    for agent in ["architect", "engineer"]:
        (run_dir / "agents" / agent).mkdir(parents=True)
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "agents" / "architect" / "clarification_questions.v1.md").write_text(
        "## Clarification Questions\n\n1. [required] Who is the user?\n\n## Assumptions\n",
        encoding="utf-8",
    )
    (run_dir / "agents" / "engineer" / "clarification_questions.v1.md").write_text(
        "## Clarification Questions\n\n1. What platform must run first?\n\n## Assumptions\n",
        encoding="utf-8",
    )

    merge_clarification_questions(run_dir)

    data = json.loads((run_dir / "input" / "clarification_questions.json").read_text(encoding="utf-8"))
    assert len(data["questions"]) == 2
    assert data["questions"][0]["required"] is True
    assert "Who is the user?" in (run_dir / "input" / "clarification_questions.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_clarification_service.py -q
```

Expected: FAIL because `clarification_service` does not exist.

- [ ] **Step 3: Implement simple merge**

Create `backend/app/services/clarification_service.py`:

```python
from pathlib import Path
import json
import re


def _extract_questions(content: str) -> list[str]:
    questions: list[str] = []
    for line in content.splitlines():
        match = re.match(r"^\s*\d+\.\s*(.+)$", line)
        if match:
            questions.append(match.group(1).strip())
    return questions


def merge_clarification_questions(run_dir: Path) -> None:
    merged: list[dict[str, object]] = []
    counter = 1
    for path in sorted(run_dir.glob("agents/*/clarification_questions.v*.md")):
        agent = path.parts[-2]
        for question in _extract_questions(path.read_text(encoding="utf-8")):
            required = "[required]" in question.lower()
            clean = question.replace("[required]", "").strip()
            merged.append(
                {
                    "id": f"q_{counter:03d}",
                    "text": clean,
                    "source_agents": [agent],
                    "required": required,
                    "merged_from": [f"{agent}:q{counter}"],
                }
            )
            counter += 1
    input_dir = run_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "clarification_questions.json").write_text(json.dumps({"questions": merged}, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = ["# Clarification Questions", ""]
    for item in merged:
        marker = "required" if item["required"] else "optional"
        markdown.append(f"- `{item['id']}` ({marker}) {item['text']}")
    markdown.append("")
    (input_dir / "clarification_questions.md").write_text("\n".join(markdown), encoding="utf-8")
```

- [ ] **Step 4: Run merge test**

Run:

```bash
pytest backend/tests/test_clarification_service.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/clarification_service.py backend/tests/test_clarification_service.py
git commit -m "feat: add clarification question merge"
```

---

## Task 15: Complete Run API

**Files:**
- Modify: `backend/app/api.py`
- Modify: `backend/app/services/run_service.py`
- Test: `backend/tests/test_api_workflow.py`

- [ ] **Step 1: Write failing workflow API tests**

Create `backend/tests/test_api_workflow.py`:

```python
from fastapi.testclient import TestClient

import backend.app.api as api_module
from backend.app.main import app


def test_submit_agent_output_imports_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(
        f"/api/runs/{created['run_id']}/agents/architect/submit",
        json={"stage": "draft_design", "content": "## Summary\nA\n\n## Proposed Design\nB\n\n## Modules\nC\n\n## Data Flow\nD\n\n## Risks\nE\n\n## Open Questions\nF\n"},
    )

    assert response.status_code == 200
    assert "draft_response.v1.md" in response.json()["related_file"]


def test_get_events_returns_event_list(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.get(f"/api/runs/{created['run_id']}/events")

    assert response.status_code == 200
    assert response.json()[0]["event_type"] == "run_created"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_api_workflow.py -q
```

Expected: FAIL because workflow endpoints do not exist.

- [ ] **Step 3: Add run helpers**

Modify `backend/app/services/run_service.py` by adding:

```python
import json


def list_runs(runs_root: Path) -> list[dict[str, object]]:
    if not runs_root.exists():
        return []
    runs = []
    for run_json in sorted(runs_root.glob("*/run.json")):
        runs.append(json.loads(run_json.read_text(encoding="utf-8")))
    return runs


def get_run_dir(runs_root: Path, run_id: str) -> Path:
    run_dir = runs_root / run_id
    if not run_dir.is_dir():
        raise FileNotFoundError(run_id)
    return run_dir
```

- [ ] **Step 4: Add API endpoints**

Modify `backend/app/api.py`:

```python
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.models import Stage
from backend.app.services.event_service import read_events
from backend.app.services.file_service import write_text
from backend.app.services.run_service import create_run, get_run_dir, list_runs
from backend.app.services.workflow_service import import_from_inbox

RUNS_ROOT = Path("runs")
router = APIRouter(prefix="/api")


class CreateRunRequest(BaseModel):
    title: str
    requirement: str


class SubmitAgentOutputRequest(BaseModel):
    stage: Stage
    content: str


@router.get("/runs")
def list_runs_endpoint():
    return list_runs(RUNS_ROOT)


@router.post("/runs")
def create_run_endpoint(request: CreateRunRequest):
    projection = create_run(RUNS_ROOT, request.title, request.requirement)
    return projection.model_dump(mode="json")


@router.get("/runs/{run_id}/events")
def get_events_endpoint(run_id: str):
    try:
        return read_events(get_run_dir(RUNS_ROOT, run_id))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")


@router.post("/runs/{run_id}/agents/{agent_id}/submit")
def submit_agent_output_endpoint(run_id: str, agent_id: str, request: SubmitAgentOutputRequest):
    try:
        run_dir = get_run_dir(RUNS_ROOT, run_id)
        inbox_file = run_dir / "inbox" / agent_id / f"{request.stage.value}_manual.md"
        write_text(inbox_file, request.content)
        imported = import_from_inbox(run_dir, agent_id, request.stage)
        return {"related_file": str(imported.relative_to(run_dir))}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
```

- [ ] **Step 5: Run workflow API tests**

Run:

```bash
pytest backend/tests/test_api_workflow.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api.py backend/app/services/run_service.py backend/tests/test_api_workflow.py
git commit -m "feat: add workflow API endpoints"
```

---

## Task 16: Frontend API Integration

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/types/run.ts`
- Create: `frontend/src/components/SubmitOutputDialog.tsx`
- Create: `frontend/src/components/HumanInputPanel.tsx`
- Modify: `frontend/src/pages/RunListPage.tsx`
- Modify: `frontend/src/pages/RunDetailPage.tsx`
- Test: `frontend/src/__tests__/SubmitOutputDialog.test.tsx`

- [ ] **Step 1: Write failing submit dialog test**

Create `frontend/src/__tests__/SubmitOutputDialog.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SubmitOutputDialog } from "../components/SubmitOutputDialog";

describe("SubmitOutputDialog", () => {
  it("submits pasted output", () => {
    const onSubmit = vi.fn();
    render(<SubmitOutputDialog agentId="architect" stage="draft_design" onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText("Agent output"), { target: { value: "## Summary\nA" } });
    fireEvent.click(screen.getByText("Submit"));
    expect(onSubmit).toHaveBeenCalledWith("architect", "draft_design", "## Summary\nA");
  });
});
```

- [ ] **Step 2: Run frontend test to verify it fails**

Run:

```bash
npm --prefix frontend test -- --run
```

Expected: FAIL because `SubmitOutputDialog` does not exist.

- [ ] **Step 3: Add frontend types and API client**

Create `frontend/src/types/run.ts`:

```ts
export type RunProjection = {
  run_id: string;
  stage: string;
  status: string;
  missing_inputs: string[];
};

export type TimelineEvent = {
  id: string;
  actor: string;
  event_type: string;
  message: string;
};
```

Create `frontend/src/api/client.ts`:

```ts
import type { RunProjection, TimelineEvent } from "../types/run";

export async function listRuns(): Promise<RunProjection[]> {
  const response = await fetch("/api/runs");
  return response.json();
}

export async function createRun(title: string, requirement: string): Promise<RunProjection> {
  const response = await fetch("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, requirement })
  });
  return response.json();
}

export async function getEvents(runId: string): Promise<TimelineEvent[]> {
  const response = await fetch(`/api/runs/${runId}/events`);
  return response.json();
}

export async function submitAgentOutput(runId: string, agentId: string, stage: string, content: string): Promise<{ related_file: string }> {
  const response = await fetch(`/api/runs/${runId}/agents/${agentId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stage, content })
  });
  return response.json();
}
```

- [ ] **Step 4: Add submit dialog**

Create `frontend/src/components/SubmitOutputDialog.tsx`:

```tsx
import { useState } from "react";

export function SubmitOutputDialog({
  agentId,
  stage,
  onSubmit
}: {
  agentId: string;
  stage: string;
  onSubmit: (agentId: string, stage: string, content: string) => void;
}) {
  const [content, setContent] = useState("");
  return (
    <section>
      <h2>Submit {agentId}</h2>
      <label>
        Agent output
        <textarea value={content} onChange={(event) => setContent(event.target.value)} />
      </label>
      <button onClick={() => onSubmit(agentId, stage, content)}>Submit</button>
    </section>
  );
}
```

Create `frontend/src/components/HumanInputPanel.tsx`:

```tsx
export function HumanInputPanel() {
  return (
    <section aria-label="Human input">
      <h2>Human Input</h2>
      <textarea aria-label="Human notes" />
    </section>
  );
}
```

- [ ] **Step 5: Run frontend tests**

Run:

```bash
npm --prefix frontend test -- --run
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api frontend/src/types frontend/src/components frontend/src/pages frontend/src/__tests__/SubmitOutputDialog.test.tsx
git commit -m "feat: connect frontend submission components"
```

---

## Task 17: Real MVP End-to-End Flow

**Files:**
- Replace: `backend/tests/test_mvp_flow.py`

- [ ] **Step 1: Replace smoke test with real MVP flow test**

Replace `backend/tests/test_mvp_flow.py`:

```python
from pathlib import Path

from backend.app.models import Stage
from backend.app.services.finalize_service import finalize_run
from backend.app.services.run_service import create_run
from backend.app.services.workflow_service import import_from_inbox


def _write_stage_output(run_dir: Path, agent: str, stage: Stage, content: str) -> None:
    inbox = run_dir / "inbox" / agent
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / f"{stage.value}.md").write_text(content, encoding="utf-8")
    import_from_inbox(run_dir, agent, stage)


def test_real_mvp_flow_through_all_authoritative_outputs(tmp_path: Path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    run_dir = tmp_path / projection.run_id

    clarification = "## Clarification Questions\n\n1. [required] Who is the user?\n\n## Assumptions\n\n- Local-first.\n"
    for agent in ["architect", "engineer", "reviewer"]:
        _write_stage_output(run_dir, agent, Stage.CLARIFICATION, clarification)

    (run_dir / "input" / "clarification_questions.json").write_text('{"questions":[{"id":"q_001","required":true}]}', encoding="utf-8")
    (run_dir / "input" / "human_answers.json").write_text('{"answers":{"q_001":"Local developer"}}', encoding="utf-8")
    (run_dir / "input" / "human_answers.md").write_text("q_001: Local developer", encoding="utf-8")
    (run_dir / "input" / "clarified_requirement.md").write_text("# Clarified Requirement\nLocal developer MVP.", encoding="utf-8")

    draft = "## Summary\nA\n\n## Proposed Design\nB\n\n## Modules\nC\n\n## Data Flow\nD\n\n## Risks\nE\n\n## Open Questions\nF\n"
    for agent in ["architect", "engineer"]:
        _write_stage_output(run_dir, agent, Stage.DRAFT_DESIGN, draft)

    review = "## Review Summary\nA\n\n## Issues\nB\n\n## Conflicts\nC\n\n## Suggestions\nD\n\n## Questions For Human\nE\n"
    for agent in ["architect", "engineer", "reviewer"]:
        _write_stage_output(run_dir, agent, Stage.CROSS_REVIEW, review)

    revision = "## Revised Design\nA\n\n## Changes Made\nB\n\n## Remaining Risks\nC\n\n## Implementation Notes\nD\n"
    for agent in ["architect", "engineer"]:
        _write_stage_output(run_dir, agent, Stage.REVISION, revision)

    synth = run_dir / "agents" / "synthesizer"
    synth.mkdir(parents=True, exist_ok=True)
    (synth / "design_doc.v1.md").write_text("# Design Document\n\n## Architecture\nFile-first", encoding="utf-8")
    (synth / "execution_doc.v1.md").write_text("# Execution Document\n\n## Implementation Plan\nBuild", encoding="utf-8")

    finalize_run(run_dir)

    assert (run_dir / "output" / "design_doc.md").is_file()
    assert (run_dir / "output" / "execution_doc.md").is_file()
    assert (run_dir / "output" / "transcript.md").is_file()
    assert (run_dir / "agents" / "architect" / "draft_response.v1.md").is_file()
    assert (run_dir / "agents" / "reviewer" / "review_response.v1.md").is_file()
```

- [ ] **Step 2: Run real MVP flow test**

Run:

```bash
pytest backend/tests/test_mvp_flow.py -q
```

Expected: PASS after Tasks 10 through 16 are complete.

- [ ] **Step 3: Run all verification**

Run:

```bash
pytest -q
npm --prefix frontend test -- --run
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_mvp_flow.py
git commit -m "test: add real MVP flow coverage"
```

---

## Task 18: Human Control API, Run Detail, Skip, and Revert

**Files:**
- Modify: `backend/app/api.py`
- Modify: `backend/app/services/run_service.py`
- Create: `backend/app/services/human_control_service.py`
- Test: `backend/tests/test_human_control_api.py`

- [ ] **Step 1: Write failing human control API tests**

Create `backend/tests/test_human_control_api.py`:

```python
from fastapi.testclient import TestClient

import backend.app.api as api_module
from backend.app.main import app


def test_get_run_detail_returns_projection(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.get(f"/api/runs/{created['run_id']}")

    assert response.status_code == 200
    assert response.json()["run_id"] == created["run_id"]


def test_skip_agent_writes_event_and_recomputes(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(
        f"/api/runs/{created['run_id']}/agents/reviewer/skip",
        json={"stage": "clarification", "reason": "Not needed for this run"},
    )

    assert response.status_code == 200
    events = client.get(f"/api/runs/{created['run_id']}/events").json()
    assert any(event["event_type"] == "agent_skipped" for event in events)


def test_advance_writes_stage_advanced_event(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(f"/api/runs/{created['run_id']}/advance")

    assert response.status_code == 200
    events = client.get(f"/api/runs/{created['run_id']}/events").json()
    assert any(event["event_type"] == "stage_advanced" for event in events)


def test_revert_writes_stage_reverted_event(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(f"/api/runs/{created['run_id']}/revert", json={"reason": "Need to revise"})

    assert response.status_code == 200
    events = client.get(f"/api/runs/{created['run_id']}/events").json()
    assert any(event["event_type"] == "stage_reverted" for event in events)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_human_control_api.py -q
```

Expected: FAIL because the endpoints and service do not exist.

- [ ] **Step 3: Add human control service**

Create `backend/app/services/human_control_service.py`:

```python
from pathlib import Path

from backend.app.models import ActorType, Stage, StageStatus
from backend.app.services.event_service import append_event
from backend.app.services.file_service import run_lock, write_json
from backend.app.services.state_service import recompute_state


def advance_stage(run_dir: Path):
    with run_lock(run_dir):
        projection = recompute_state(run_dir)
        if projection.status != StageStatus.READY_TO_ADVANCE:
            raise ValueError("Current stage is not ready to advance")
        append_event(
            run_dir,
            projection.stage,
            "human",
            ActorType.HUMAN,
            "stage_advanced",
            f"Advanced from {projection.stage.value}",
        )
        updated = recompute_state(run_dir)
        write_json(run_dir / "run.json", updated.model_dump(mode="json"))
        return updated


def skip_agent(run_dir: Path, agent_id: str, stage: Stage, reason: str):
    with run_lock(run_dir):
        append_event(
            run_dir,
            stage,
            agent_id,
            ActorType.AGENT,
            "agent_skipped",
            reason,
            metadata={"reason": reason},
        )
        updated = recompute_state(run_dir)
        write_json(run_dir / "run.json", updated.model_dump(mode="json"))
        return updated


def revert_stage(run_dir: Path, reason: str):
    with run_lock(run_dir):
        projection = recompute_state(run_dir)
        append_event(
            run_dir,
            projection.stage,
            "human",
            ActorType.HUMAN,
            "stage_reverted",
            reason,
            metadata={"reason": reason},
        )
        updated = recompute_state(run_dir)
        write_json(run_dir / "run.json", updated.model_dump(mode="json"))
        return updated
```

- [ ] **Step 4: Add API request models and endpoints**

Modify `backend/app/api.py` to include:

```python
from backend.app.services.human_control_service import advance_stage, revert_stage, skip_agent
from backend.app.services.state_service import recompute_state


class SkipAgentRequest(BaseModel):
    stage: Stage
    reason: str


class RevertStageRequest(BaseModel):
    reason: str


@router.get("/runs/{run_id}")
def get_run_endpoint(run_id: str):
    try:
        run_dir = get_run_dir(RUNS_ROOT, run_id)
        return recompute_state(run_dir).model_dump(mode="json")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")


@router.post("/runs/{run_id}/advance")
def advance_run_endpoint(run_id: str):
    try:
        return advance_stage(get_run_dir(RUNS_ROOT, run_id)).model_dump(mode="json")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/runs/{run_id}/agents/{agent_id}/skip")
def skip_agent_endpoint(run_id: str, agent_id: str, request: SkipAgentRequest):
    try:
        return skip_agent(get_run_dir(RUNS_ROOT, run_id), agent_id, request.stage, request.reason).model_dump(mode="json")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")


@router.post("/runs/{run_id}/revert")
def revert_run_endpoint(run_id: str, request: RevertStageRequest):
    try:
        return revert_stage(get_run_dir(RUNS_ROOT, run_id), request.reason).model_dump(mode="json")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
```

- [ ] **Step 5: Run human control API tests**

Run:

```bash
pytest backend/tests/test_human_control_api.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api.py backend/app/services/human_control_service.py backend/tests/test_human_control_api.py
git commit -m "feat: add human control API"
```

---

## Task 19: LangGraph Checkpoint Stop and Resume Semantics

**Files:**
- Modify: `backend/app/graph/state.py`
- Modify: `backend/app/graph/nodes.py`
- Modify: `backend/app/graph/edges.py`
- Test: `backend/tests/test_graph_checkpoint.py`

- [ ] **Step 1: Write failing checkpoint tests**

Create `backend/tests/test_graph_checkpoint.py`:

```python
from backend.app.graph.edges import build_workflow
from backend.app.services.run_service import create_run


def test_graph_stops_at_checkpoint_without_confirmation(tmp_path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild")
    graph = build_workflow()

    result = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": False})

    assert result["checkpoint"] is True
    assert result["stage"] == "requirement"


def test_graph_continues_after_confirmation(tmp_path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild")
    graph = build_workflow()

    result = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})

    assert result["checkpoint"] is False
    assert result["stage"] in {"clarification", "clarified_requirement"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest backend/tests/test_graph_checkpoint.py -q
```

Expected: FAIL because graph state does not expose checkpoint behavior.

- [ ] **Step 3: Extend workflow state with checkpoint flag**

Modify `backend/app/graph/state.py`:

```python
from typing import TypedDict


class WorkflowState(TypedDict, total=False):
    run_id: str
    runs_root: str
    stage: str
    confirmed: bool
    checkpoint: bool
```

- [ ] **Step 4: Add checkpoint node**

Modify `backend/app/graph/nodes.py` to include:

```python
from backend.app.models import StageStatus


def checkpoint_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    projection = recompute_state(run_dir)
    if projection.status == StageStatus.READY_TO_ADVANCE and not state.get("confirmed", False):
        return {**state, "stage": projection.stage.value, "checkpoint": True}
    return {**state, "stage": projection.stage.value, "checkpoint": False}
```

- [ ] **Step 5: Route based on checkpoint**

Modify `backend/app/graph/edges.py`:

```python
from langgraph.graph import END, StateGraph

from backend.app.graph.nodes import checkpoint_node, clarification_node, load_projection_node
from backend.app.graph.state import WorkflowState


def _after_checkpoint(state: WorkflowState) -> str:
    return END if state.get("checkpoint") else "clarification"


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("load_projection", load_projection_node)
    graph.add_node("checkpoint", checkpoint_node)
    graph.add_node("clarification", clarification_node)
    graph.set_entry_point("load_projection")
    graph.add_edge("load_projection", "checkpoint")
    graph.add_conditional_edges("checkpoint", _after_checkpoint, {END: END, "clarification": "clarification"})
    graph.add_edge("clarification", END)
    return graph.compile()
```

- [ ] **Step 6: Run checkpoint tests**

Run:

```bash
pytest backend/tests/test_graph_checkpoint.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/graph backend/tests/test_graph_checkpoint.py
git commit -m "feat: add LangGraph checkpoint gating"
```

---

## Task 20: Clarification Answers and Clarified Requirement Inputs

**Files:**
- Create: `backend/app/services/human_input_service.py`
- Modify: `backend/app/api.py`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/components/HumanInputPanel.tsx`
- Test: `backend/tests/test_human_input_api.py`
- Test: `frontend/src/__tests__/HumanInputPanel.test.tsx`

- [ ] **Step 1: Write failing backend human input tests**

Create `backend/tests/test_human_input_api.py`:

```python
from fastapi.testclient import TestClient

import backend.app.api as api_module
from backend.app.main import app


def test_save_clarification_answers(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(
        f"/api/runs/{created['run_id']}/clarification/answers",
        json={"answers": {"q_001": "Local developer"}},
    )

    assert response.status_code == 200
    run_dir = tmp_path / created["run_id"]
    assert "q_001" in (run_dir / "input" / "human_answers.json").read_text(encoding="utf-8")
    assert "Local developer" in (run_dir / "input" / "human_answers.md").read_text(encoding="utf-8")


def test_save_clarified_requirement(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(
        f"/api/runs/{created['run_id']}/clarified-requirement",
        json={"content": "# Clarified Requirement\nUse local files."},
    )

    assert response.status_code == 200
    run_dir = tmp_path / created["run_id"]
    assert "local files" in (run_dir / "input" / "clarified_requirement.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run backend tests to verify they fail**

Run:

```bash
pytest backend/tests/test_human_input_api.py -q
```

Expected: FAIL because human input endpoints do not exist.

- [ ] **Step 3: Add human input service**

Create `backend/app/services/human_input_service.py`:

```python
from pathlib import Path
import json

from backend.app.models import ActorType, Stage
from backend.app.services.event_service import append_event
from backend.app.services.file_service import run_lock, write_json, write_text
from backend.app.services.state_service import recompute_state


def save_clarification_answers(run_dir: Path, answers: dict[str, str]):
    with run_lock(run_dir):
        write_json(run_dir / "input" / "human_answers.json", {"answers": answers})
        markdown = ["# Human Answers", ""]
        for question_id, answer in answers.items():
            markdown.append(f"- `{question_id}`: {answer}")
        markdown.append("")
        write_text(run_dir / "input" / "human_answers.md", "\n".join(markdown))
        append_event(run_dir, Stage.CLARIFIED_REQUIREMENT, "human", ActorType.HUMAN, "human_answer_submitted", "Submitted clarification answers", "input/human_answers.json")
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json"))
        return projection


def save_clarified_requirement(run_dir: Path, content: str):
    with run_lock(run_dir):
        write_text(run_dir / "input" / "clarified_requirement.md", content)
        append_event(run_dir, Stage.CLARIFIED_REQUIREMENT, "human", ActorType.HUMAN, "clarified_requirement_saved", "Saved clarified requirement", "input/clarified_requirement.md")
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json"))
        return projection
```

- [ ] **Step 4: Add human input API endpoints**

Modify `backend/app/api.py` to include:

```python
from backend.app.services.human_input_service import save_clarification_answers, save_clarified_requirement


class ClarificationAnswersRequest(BaseModel):
    answers: dict[str, str]


class ClarifiedRequirementRequest(BaseModel):
    content: str


@router.post("/runs/{run_id}/clarification/answers")
def save_clarification_answers_endpoint(run_id: str, request: ClarificationAnswersRequest):
    try:
        return save_clarification_answers(get_run_dir(RUNS_ROOT, run_id), request.answers).model_dump(mode="json")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")


@router.post("/runs/{run_id}/clarified-requirement")
def save_clarified_requirement_endpoint(run_id: str, request: ClarifiedRequirementRequest):
    try:
        return save_clarified_requirement(get_run_dir(RUNS_ROOT, run_id), request.content).model_dump(mode="json")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
```

- [ ] **Step 5: Write failing frontend human input test**

Create `frontend/src/__tests__/HumanInputPanel.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HumanInputPanel } from "../components/HumanInputPanel";

describe("HumanInputPanel", () => {
  it("submits clarification answers and clarified requirement", () => {
    const onSaveAnswers = vi.fn();
    const onSaveRequirement = vi.fn();
    render(<HumanInputPanel onSaveAnswers={onSaveAnswers} onSaveRequirement={onSaveRequirement} />);

    fireEvent.change(screen.getByLabelText("Human answers JSON"), { target: { value: '{"q_001":"Local developer"}' } });
    fireEvent.click(screen.getByText("Save Answers"));
    fireEvent.change(screen.getByLabelText("Clarified requirement"), { target: { value: "# Clarified" } });
    fireEvent.click(screen.getByText("Save Clarified Requirement"));

    expect(onSaveAnswers).toHaveBeenCalledWith({ q_001: "Local developer" });
    expect(onSaveRequirement).toHaveBeenCalledWith("# Clarified");
  });
});
```

- [ ] **Step 6: Implement frontend human input panel and client methods**

Modify `frontend/src/api/client.ts` to include:

```ts
export async function saveClarificationAnswers(runId: string, answers: Record<string, string>): Promise<RunProjection> {
  const response = await fetch(`/api/runs/${runId}/clarification/answers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers })
  });
  return response.json();
}

export async function saveClarifiedRequirement(runId: string, content: string): Promise<RunProjection> {
  const response = await fetch(`/api/runs/${runId}/clarified-requirement`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content })
  });
  return response.json();
}
```

Modify `frontend/src/components/HumanInputPanel.tsx`:

```tsx
import { useState } from "react";

export function HumanInputPanel({
  onSaveAnswers,
  onSaveRequirement
}: {
  onSaveAnswers: (answers: Record<string, string>) => void;
  onSaveRequirement: (content: string) => void;
}) {
  const [answersJson, setAnswersJson] = useState("{}");
  const [clarifiedRequirement, setClarifiedRequirement] = useState("");
  return (
    <section aria-label="Human input">
      <h2>Human Input</h2>
      <label>
        Human answers JSON
        <textarea value={answersJson} onChange={(event) => setAnswersJson(event.target.value)} />
      </label>
      <button onClick={() => onSaveAnswers(JSON.parse(answersJson))}>Save Answers</button>
      <label>
        Clarified requirement
        <textarea value={clarifiedRequirement} onChange={(event) => setClarifiedRequirement(event.target.value)} />
      </label>
      <button onClick={() => onSaveRequirement(clarifiedRequirement)}>Save Clarified Requirement</button>
    </section>
  );
}
```

- [ ] **Step 7: Run human input tests**

Run:

```bash
pytest backend/tests/test_human_input_api.py -q
npm --prefix frontend test -- --run
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/api.py backend/app/services/human_input_service.py backend/tests/test_human_input_api.py frontend/src/api/client.ts frontend/src/components/HumanInputPanel.tsx frontend/src/__tests__/HumanInputPanel.test.tsx
git commit -m "feat: add human clarification inputs"
```

---

## Task 21: Graph-Driven End-to-End Flow

**Files:**
- Create: `backend/tests/test_graph_driven_e2e.py`
- Modify: `backend/app/graph/nodes.py`
- Modify: `backend/app/graph/edges.py`

- [ ] **Step 1: Write failing graph-driven E2E test**

Create `backend/tests/test_graph_driven_e2e.py`:

```python
from backend.app.graph.edges import build_workflow
from backend.app.models import Stage
from backend.app.services.finalize_service import finalize_run
from backend.app.services.human_input_service import save_clarification_answers, save_clarified_requirement
from backend.app.services.run_service import create_run
from backend.app.services.workflow_service import import_from_inbox


def test_graph_driven_flow_reaches_clarification_checkpoint_then_finalizes(tmp_path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    graph = build_workflow()
    run_dir = tmp_path / projection.run_id

    first = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": False})
    assert first["checkpoint"] is True

    second = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert (run_dir / "agents" / "architect" / "clarification_questions.v1.md").is_file()

    (run_dir / "input" / "clarification_questions.json").write_text('{"questions":[{"id":"q_001","required":true}]}', encoding="utf-8")
    save_clarification_answers(run_dir, {"q_001": "Local developer"})
    save_clarified_requirement(run_dir, "# Clarified Requirement\nLocal developer")

    draft = "## Summary\nA\n\n## Proposed Design\nB\n\n## Modules\nC\n\n## Data Flow\nD\n\n## Risks\nE\n\n## Open Questions\nF\n"
    for agent in ["architect", "engineer"]:
        inbox = run_dir / "inbox" / agent
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "draft.md").write_text(draft, encoding="utf-8")
        import_from_inbox(run_dir, agent, Stage.DRAFT_DESIGN)

    review = "## Review Summary\nA\n\n## Issues\nB\n\n## Conflicts\nC\n\n## Suggestions\nD\n\n## Questions For Human\nE\n"
    for agent in ["architect", "engineer", "reviewer"]:
        inbox = run_dir / "inbox" / agent
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "review.md").write_text(review, encoding="utf-8")
        import_from_inbox(run_dir, agent, Stage.CROSS_REVIEW)

    revision = "## Revised Design\nA\n\n## Changes Made\nB\n\n## Remaining Risks\nC\n\n## Implementation Notes\nD\n"
    for agent in ["architect", "engineer"]:
        inbox = run_dir / "inbox" / agent
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "revision.md").write_text(revision, encoding="utf-8")
        import_from_inbox(run_dir, agent, Stage.REVISION)

    synth = run_dir / "agents" / "synthesizer"
    synth.mkdir(parents=True, exist_ok=True)
    (synth / "design_doc.v1.md").write_text("# Design Document\n\n## Architecture\nFile-first", encoding="utf-8")
    (synth / "execution_doc.v1.md").write_text("# Execution Document\n\n## Implementation Plan\nBuild", encoding="utf-8")
    finalize_run(run_dir)

    assert (run_dir / "output" / "design_doc.md").is_file()
    assert (run_dir / "output" / "execution_doc.md").is_file()
```

- [ ] **Step 2: Run graph-driven E2E test**

Run:

```bash
pytest backend/tests/test_graph_driven_e2e.py -q
```

Expected: PASS after Tasks 18 through 20 are complete.

- [ ] **Step 3: Run full verification**

Run:

```bash
pytest -q
npm --prefix frontend test -- --run
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_graph_driven_e2e.py backend/app/graph/nodes.py backend/app/graph/edges.py
git commit -m "test: add graph-driven MVP flow"
```

---

## Task 22: Complete LangGraph Main Path for All Stages

**Files:**
- Modify: `backend/app/graph/nodes.py`
- Modify: `backend/app/graph/edges.py`
- Modify: `backend/app/services/runner_service.py`
- Modify: `backend/app/runners/mock.py`
- Test: `backend/tests/test_graph_main_path.py`

- [ ] **Step 1: Write failing main-path graph test**

Create `backend/tests/test_graph_main_path.py`:

```python
from backend.app.graph.edges import build_workflow
from backend.app.services.clarification_service import merge_clarification_questions
from backend.app.services.human_input_service import save_clarification_answers, save_clarified_requirement
from backend.app.services.run_service import create_run


def test_graph_main_path_runs_each_stage_without_crossing_human_gate(tmp_path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    graph = build_workflow()
    run_dir = tmp_path / projection.run_id

    first = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": False})
    assert first["checkpoint"] is True
    assert first["stage"] == "requirement"

    clarification = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert clarification["stage"] == "clarified_requirement"
    assert (run_dir / "agents" / "architect" / "clarification_questions.v1.md").is_file()

    merge_clarification_questions(run_dir)
    save_clarification_answers(run_dir, {"q_001": "Local developer"})
    save_clarified_requirement(run_dir, "# Clarified Requirement\nLocal developer")

    draft = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert draft["stage"] == "cross_review"
    assert (run_dir / "agents" / "architect" / "draft_response.v1.md").is_file()
    assert (run_dir / "agents" / "engineer" / "draft_response.v1.md").is_file()

    review = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert review["stage"] == "revision"
    assert (run_dir / "agents" / "reviewer" / "review_response.v1.md").is_file()

    revision = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert revision["stage"] == "synthesis"
    assert (run_dir / "agents" / "architect" / "revision_response.v1.md").is_file()

    synthesis = graph.invoke({"run_id": projection.run_id, "runs_root": str(tmp_path), "confirmed": True})
    assert synthesis["stage"] == "synthesis"
    assert (run_dir / "agents" / "synthesizer" / "design_doc.v1.md").is_file()
    assert (run_dir / "agents" / "synthesizer" / "execution_doc.v1.md").is_file()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest backend/tests/test_graph_main_path.py -q
```

Expected: FAIL because the graph only runs clarification.

- [ ] **Step 3: Make mock runner stage-aware**

Modify `backend/app/runners/mock.py` so `MockRunner.run()` writes stage-specific outputs:

```python
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
```

- [ ] **Step 4: Teach runner service to import synthesis output**

Modify `backend/app/services/runner_service.py` so `run_agent_stage()` handles synthesis specially:

```python
from pathlib import Path

from backend.app.models import Stage
from backend.app.runners.file import FileRunner
from backend.app.runners.manual import ManualRunner
from backend.app.runners.mock import MockRunner
from backend.app.services.prompt_service import render_prompt
from backend.app.services.workflow_service import import_from_inbox


def get_runner(name: str):
    runners = {
        "manual": ManualRunner(),
        "file": FileRunner(),
        "mock": MockRunner(),
    }
    if name not in runners:
        raise ValueError(f"Unsupported runner: {name}")
    return runners[name]


def _import_synthesis(run_dir: Path) -> None:
    inbox_file = sorted((run_dir / "inbox" / "synthesizer").glob("*.md"))[0]
    content = inbox_file.read_text(encoding="utf-8")
    design_marker = "# Design Document"
    execution_marker = "# Execution Document"
    if design_marker not in content or execution_marker not in content:
        raise ValueError("Synthesis output must contain Design and Execution document markers")
    design_start = content.index(design_marker)
    execution_start = content.index(execution_marker)
    synthesizer_dir = run_dir / "agents" / "synthesizer"
    synthesizer_dir.mkdir(parents=True, exist_ok=True)
    (synthesizer_dir / "design_doc.v1.md").write_text(content[design_start:execution_start].strip() + "\n", encoding="utf-8")
    (synthesizer_dir / "execution_doc.v1.md").write_text(content[execution_start:].strip() + "\n", encoding="utf-8")


def run_agent_stage(run_dir: Path, agent_id: str, stage: Stage, runner_name: str = "mock") -> None:
    prompt_name = {
        Stage.CLARIFICATION: "clarification_prompt.md",
        Stage.DRAFT_DESIGN: "draft_prompt.md",
        Stage.CROSS_REVIEW: "review_prompt.md",
        Stage.REVISION: "revision_prompt.md",
        Stage.SYNTHESIS: "synthesis_prompt.md",
    }[stage]
    prompt_file = run_dir / "agents" / agent_id / prompt_name
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(render_prompt(stage, agent_id, run_dir), encoding="utf-8")
    runner = get_runner(runner_name)
    result = runner.run(
        run_id=run_dir.name,
        agent_id=agent_id,
        stage=stage.value,
        prompt_file=prompt_file,
        inbox_dir=run_dir / "inbox" / agent_id,
        runner_log_dir=run_dir / "runner_logs" / agent_id,
        timeout_seconds=30,
        metadata={},
    )
    if result.status == "succeeded" and stage == Stage.SYNTHESIS:
        _import_synthesis(run_dir)
    elif result.status == "succeeded":
        import_from_inbox(run_dir, agent_id, stage)
```

- [ ] **Step 5: Add graph nodes for all remaining stages**

Modify `backend/app/graph/nodes.py`:

```python
from pathlib import Path

from backend.app.graph.state import WorkflowState
from backend.app.models import Stage, StageStatus
from backend.app.services.runner_service import run_agent_stage
from backend.app.services.state_service import recompute_state


def load_projection_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value}


def checkpoint_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    projection = recompute_state(run_dir)
    if projection.status == StageStatus.READY_TO_ADVANCE and not state.get("confirmed", False):
        return {**state, "stage": projection.stage.value, "checkpoint": True}
    return {**state, "stage": projection.stage.value, "checkpoint": False}


def clarification_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    for agent in ["architect", "engineer", "reviewer"]:
        if not list((run_dir / "agents" / agent).glob("clarification_questions.v*.md")):
            run_agent_stage(run_dir, agent, Stage.CLARIFICATION)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value, "checkpoint": False}


def draft_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    for agent in ["architect", "engineer"]:
        if not list((run_dir / "agents" / agent).glob("draft_response.v*.md")):
            run_agent_stage(run_dir, agent, Stage.DRAFT_DESIGN)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value, "checkpoint": False}


def review_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    for agent in ["architect", "engineer", "reviewer"]:
        if not list((run_dir / "agents" / agent).glob("review_response.v*.md")):
            run_agent_stage(run_dir, agent, Stage.CROSS_REVIEW)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value, "checkpoint": False}


def revision_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    for agent in ["architect", "engineer"]:
        if not list((run_dir / "agents" / agent).glob("revision_response.v*.md")):
            run_agent_stage(run_dir, agent, Stage.REVISION)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value, "checkpoint": False}


def synthesis_node(state: WorkflowState) -> WorkflowState:
    run_dir = Path(state["runs_root"]) / state["run_id"]
    if not list((run_dir / "agents" / "synthesizer").glob("design_doc.v*.md")):
        run_agent_stage(run_dir, "synthesizer", Stage.SYNTHESIS)
    projection = recompute_state(run_dir)
    return {**state, "stage": projection.stage.value, "checkpoint": False}
```

- [ ] **Step 6: Route graph to exactly one runnable stage per invocation**

Modify `backend/app/graph/edges.py`:

```python
from langgraph.graph import END, StateGraph

from backend.app.graph.nodes import (
    checkpoint_node,
    clarification_node,
    draft_node,
    load_projection_node,
    review_node,
    revision_node,
    synthesis_node,
)
from backend.app.graph.state import WorkflowState


def _after_checkpoint(state: WorkflowState) -> str:
    if state.get("checkpoint"):
        return END
    return {
        "requirement": "clarification",
        "clarification": "clarification",
        "clarified_requirement": "draft",
        "draft_design": "draft",
        "cross_review": "review",
        "revision": "revision",
        "synthesis": "synthesis",
    }.get(state["stage"], END)


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("load_projection", load_projection_node)
    graph.add_node("checkpoint", checkpoint_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("draft", draft_node)
    graph.add_node("review", review_node)
    graph.add_node("revision", revision_node)
    graph.add_node("synthesis", synthesis_node)
    graph.set_entry_point("load_projection")
    graph.add_edge("load_projection", "checkpoint")
    graph.add_conditional_edges(
        "checkpoint",
        _after_checkpoint,
        {
            END: END,
            "clarification": "clarification",
            "draft": "draft",
            "review": "review",
            "revision": "revision",
            "synthesis": "synthesis",
        },
    )
    graph.add_edge("clarification", END)
    graph.add_edge("draft", END)
    graph.add_edge("review", END)
    graph.add_edge("revision", END)
    graph.add_edge("synthesis", END)
    return graph.compile()
```

- [ ] **Step 7: Run graph main-path test**

Run:

```bash
pytest backend/tests/test_graph_main_path.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/graph backend/app/services/runner_service.py backend/app/runners/mock.py backend/tests/test_graph_main_path.py
git commit -m "feat: complete LangGraph main path"
```

---

## Self-Review Checklist

- Spec coverage:
  - File-first storage starts in Tasks 2, 3, and 9, then becomes authoritative through Task 10.
  - LangGraph fixed workflow starts in Task 5 and becomes connected to runner/import flow in Task 13.
  - Manual/file/mock runner boundary is covered in Task 4 and exercised through Task 13.
  - Single write entrance and versioned outputs are implemented in Task 10.
  - Full-stage state projection is implemented in Task 11.
  - Prompt template injection is implemented in Task 12.
  - Clarification merge is implemented in Task 14.
  - API completion is implemented in Task 15.
  - Web UI stage board, timeline, and submission flow are covered in Tasks 7 and 16.
  - Final output generation is covered in Task 8 and exercised in Task 17.
  - Real MVP flow coverage is provided by Task 17.
  - Human advance, skip, revert, and run detail are implemented in Task 18.
  - LangGraph checkpoint gating is implemented in Task 19.
  - Per-question clarification answers and clarified requirement inputs are implemented in Task 20.
  - Graph-driven end-to-end coverage is implemented in Task 21.
  - LangGraph main-path orchestration for Draft, Review, Revision, and Synthesis is implemented in Task 22.
  - External review v3 is addressed by keeping LangGraph and making it the stage orchestrator, instead of leaving it as a partial wrapper.
- Placeholder scan:
  - This plan avoids placeholder tokens and unspecified implementation steps.
  - Every code-writing step includes concrete file content or a concrete code block.
- Type consistency:
  - `Stage`, `StageStatus`, `RunProjection`, and runner result fields are introduced before use.
  - Backend tests import modules from paths created in earlier tasks.
  - Frontend tests import `StageBoard` from the exact created component path.
