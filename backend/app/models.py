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


class AgentProjection(BaseModel):
    id: str
    label: str
    runner: str
    model: str
    llm_name: str
    stages: list[Stage] = Field(default_factory=list)


class RunProjection(BaseModel):
    run_id: str
    title: str = ""
    stage: Stage
    status: StageStatus
    missing_inputs: list[str] = Field(default_factory=list)
    current_versions: dict[str, str] = Field(default_factory=dict)
    agents: list[AgentProjection] = Field(default_factory=list)
