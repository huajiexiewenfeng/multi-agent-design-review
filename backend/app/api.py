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
