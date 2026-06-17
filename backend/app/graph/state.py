from typing import TypedDict


class WorkflowState(TypedDict):
    run_id: str
    runs_root: str
    stage: str
