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
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.post("/runs/{run_id}/agents/{agent_id}/submit")
def submit_agent_output_endpoint(run_id: str, agent_id: str, request: SubmitAgentOutputRequest):
    try:
        run_dir = get_run_dir(RUNS_ROOT, run_id)
        inbox_file = run_dir / "inbox" / agent_id / f"{request.stage.value}_manual.md"
        write_text(inbox_file, request.content)
        imported = import_from_inbox(run_dir, agent_id, request.stage)
        return {"related_file": str(imported.relative_to(run_dir))}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
