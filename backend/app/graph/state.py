from typing import TypedDict


class WorkflowState(TypedDict, total=False):
    run_id: str
    runs_root: str
    stage: str
    confirmed: bool
