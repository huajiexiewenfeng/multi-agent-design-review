# Multi-Agent Design Review Workbench MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP local-first LangGraph workbench that creates design-review runs, manages file-first state, accepts manual/file/mock runner outputs, shows workflow progress in Web UI, and finalizes traceable Design and Execution documents.

**Architecture:** FastAPI owns API boundaries, service modules own filesystem writes, LangGraph owns fixed workflow orchestration, and `events.jsonl + files` are the facts. `run.json` is a recomputed projection, runner outputs enter through `inbox/`, and all authoritative agent outputs are versioned immutable files.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, LangGraph, pytest, React, Vite, TypeScript, Vitest, React Testing Library.

---

## Scope Check

The spec covers one cohesive MVP: a local workbench with backend workflow, runner abstraction, and frontend views. It has several subsystems, but each is required to run the core workflow end-to-end, so this plan keeps them in one implementation sequence with frequent commits.

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

## Task 9: End-to-End Verification and Documentation

**Files:**
- Modify: `README.md`
- Create: `backend/tests/test_mvp_flow.py`

- [ ] **Step 1: Write failing MVP flow test**

Create `backend/tests/test_mvp_flow.py`:

```python
from pathlib import Path

from backend.app.services.finalize_service import finalize_run
from backend.app.services.run_service import create_run


def test_minimal_mvp_flow_with_mock_outputs(tmp_path: Path) -> None:
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
git commit -m "test: add MVP flow verification"
```

---

## Self-Review Checklist

- Spec coverage:
  - File-first storage is covered in Tasks 2, 3, and 9.
  - LangGraph fixed workflow is covered in Task 5.
  - Manual/file/mock runner boundary is covered in Task 4.
  - Single write entrance and versioned outputs are covered in Tasks 3, 4, and 8.
  - Web UI stage board and timeline are covered in Task 7.
  - Final output generation is covered in Task 8.
- Placeholder scan:
  - This plan avoids placeholder tokens and unspecified implementation steps.
  - Every code-writing step includes concrete file content or a concrete code block.
- Type consistency:
  - `Stage`, `StageStatus`, `RunProjection`, and runner result fields are introduced before use.
  - Backend tests import modules from paths created in earlier tasks.
  - Frontend tests import `StageBoard` from the exact created component path.
