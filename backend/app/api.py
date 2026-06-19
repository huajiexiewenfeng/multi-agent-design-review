from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.models import Stage
from backend.app.services.agent_config_service import update_agent_config
from backend.app.services.artifact_service import get_stage_artifacts
from backend.app.services.event_service import read_events
from backend.app.services.file_service import write_text
from backend.app.services.finalize_service import finalize_run
from backend.app.services.flow_verification_service import get_mixed_runner_verification
from backend.app.services.graph_service import run_graph_step
from backend.app.services.human_control_service import advance_stage, revert_stage, skip_agent
from backend.app.services.human_input_service import save_clarification_answers, save_clarified_requirement
from backend.app.services.job_service import get_job, start_graph_step_job, start_run_until_pause_job
from backend.app.services.run_service import create_run, get_run_dir, list_runs
from backend.app.services.runner_handoff_service import get_runner_handoffs, import_waiting_runner_outputs
from backend.app.services.runner_log_service import get_runner_logs
from backend.app.services.runner_registry_service import get_runner_health
from backend.app.services.runner_smoke_job_service import get_runner_smoke_job, start_runner_smoke_job
from backend.app.services.runner_smoke_service import run_runner_smoke_test
from backend.app.services.state_service import recompute_state
from backend.app.services.workflow_service import import_from_inbox

RUNS_ROOT = Path("runs")
router = APIRouter(prefix="/api")


class CreateRunRequest(BaseModel):
    title: str
    requirement: str


class SubmitAgentOutputRequest(BaseModel):
    stage: Stage
    content: str


class SkipAgentRequest(BaseModel):
    stage: Stage
    reason: str


class RevertStageRequest(BaseModel):
    reason: str


class ClarificationAnswersRequest(BaseModel):
    answers: dict[str, str]


class ClarifiedRequirementRequest(BaseModel):
    content: str


class AgentConfigRequest(BaseModel):
    runner: str
    llm_name: str


class GraphStepRequest(BaseModel):
    confirmed: bool = True


class RunUntilPauseRequest(BaseModel):
    max_steps: int = 10


@router.get("/runs")
def list_runs_endpoint():
    return list_runs(RUNS_ROOT)


@router.get("/runners")
def get_runners_endpoint():
    return get_runner_health()


@router.post("/runners/{runner_id}/smoke-test")
def run_runner_smoke_test_endpoint(runner_id: str):
    return run_runner_smoke_test(runner_id, RUNS_ROOT)


@router.post("/runners/{runner_id}/smoke-test/jobs")
def start_runner_smoke_job_endpoint(runner_id: str):
    return start_runner_smoke_job(RUNS_ROOT, runner_id).model_dump(mode="json")


@router.get("/runners/{runner_id}/smoke-test/jobs/{job_id}")
def get_runner_smoke_job_endpoint(runner_id: str, job_id: str):
    try:
        job = get_runner_smoke_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    if job.runner_id != runner_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.model_dump(mode="json")


@router.post("/runs")
def create_run_endpoint(request: CreateRunRequest):
    projection = create_run(RUNS_ROOT, request.title, request.requirement)
    return projection.model_dump(mode="json")


@router.get("/runs/{run_id}")
def get_run_endpoint(run_id: str):
    try:
        run_dir = get_run_dir(RUNS_ROOT, run_id)
        return recompute_state(run_dir).model_dump(mode="json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.get("/runs/{run_id}/events")
def get_events_endpoint(run_id: str):
    try:
        return read_events(get_run_dir(RUNS_ROOT, run_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.get("/runs/{run_id}/stages/{stage}/artifacts")
def get_stage_artifacts_endpoint(run_id: str, stage: Stage):
    try:
        return get_stage_artifacts(get_run_dir(RUNS_ROOT, run_id), stage)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.get("/runs/{run_id}/runner-logs")
def get_runner_logs_endpoint(run_id: str):
    try:
        return get_runner_logs(get_run_dir(RUNS_ROOT, run_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.get("/runs/{run_id}/runner-handoffs")
def get_runner_handoffs_endpoint(run_id: str):
    try:
        return get_runner_handoffs(get_run_dir(RUNS_ROOT, run_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.post("/runs/{run_id}/runner-handoffs/import")
def import_runner_handoffs_endpoint(run_id: str):
    try:
        return import_waiting_runner_outputs(get_run_dir(RUNS_ROOT, run_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.get("/runs/{run_id}/verification/mixed-runners")
def get_mixed_runner_verification_endpoint(run_id: str):
    try:
        return get_mixed_runner_verification(get_run_dir(RUNS_ROOT, run_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.post("/runs/{run_id}/advance")
def advance_run_endpoint(run_id: str):
    try:
        return advance_stage(get_run_dir(RUNS_ROOT, run_id)).model_dump(mode="json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/runs/{run_id}/agents/{agent_id}/skip")
def skip_agent_endpoint(run_id: str, agent_id: str, request: SkipAgentRequest):
    try:
        return skip_agent(get_run_dir(RUNS_ROOT, run_id), agent_id, request.stage, request.reason).model_dump(mode="json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.post("/runs/{run_id}/revert")
def revert_run_endpoint(run_id: str, request: RevertStageRequest):
    try:
        return revert_stage(get_run_dir(RUNS_ROOT, run_id), request.reason).model_dump(mode="json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.post("/runs/{run_id}/clarification/answers")
def save_clarification_answers_endpoint(run_id: str, request: ClarificationAnswersRequest):
    try:
        return save_clarification_answers(get_run_dir(RUNS_ROOT, run_id), request.answers).model_dump(mode="json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.post("/runs/{run_id}/clarified-requirement")
def save_clarified_requirement_endpoint(run_id: str, request: ClarifiedRequirementRequest):
    try:
        return save_clarified_requirement(get_run_dir(RUNS_ROOT, run_id), request.content).model_dump(mode="json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.put("/runs/{run_id}/agents/{agent_id}/config")
def update_agent_config_endpoint(run_id: str, agent_id: str, request: AgentConfigRequest):
    try:
        return update_agent_config(get_run_dir(RUNS_ROOT, run_id), agent_id, request.runner, request.llm_name).model_dump(
            mode="json"
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runs/{run_id}/graph/step")
def run_graph_step_endpoint(run_id: str, request: GraphStepRequest):
    try:
        return run_graph_step(RUNS_ROOT, run_id, request.confirmed)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/runs/{run_id}/graph/step/jobs")
def start_graph_step_job_endpoint(run_id: str, request: GraphStepRequest):
    try:
        get_run_dir(RUNS_ROOT, run_id)
        return start_graph_step_job(RUNS_ROOT, run_id, request.confirmed).model_dump(mode="json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.post("/runs/{run_id}/graph/until-pause/jobs")
def start_run_until_pause_job_endpoint(run_id: str, request: RunUntilPauseRequest):
    try:
        get_run_dir(RUNS_ROOT, run_id)
        return start_run_until_pause_job(RUNS_ROOT, run_id, request.max_steps).model_dump(mode="json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc


@router.get("/runs/{run_id}/jobs/{job_id}")
def get_job_endpoint(run_id: str, job_id: str):
    try:
        job = get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    if job.run_id != run_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.model_dump(mode="json")


@router.post("/runs/{run_id}/finalize")
def finalize_run_endpoint(run_id: str):
    try:
        run_dir = get_run_dir(RUNS_ROOT, run_id)
        finalize_run(run_dir)
        return recompute_state(run_dir).model_dump(mode="json")
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
