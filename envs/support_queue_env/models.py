from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SupportQueueAction(BaseModel):
    route: str
    reply: str


class SupportQueueObservation(BaseModel):
    ticket_id: str
    status: str
    subject: str = ""
    summary: str = ""


class SupportQueueReward(BaseModel):
    score: float


class SupportQueueState(BaseModel):
    step_count: int
    episode_done: bool
    current_ticket_id: str
    task_name: str


class TaskSpec(BaseModel):
    name: str
    difficulty: str
    ticket_id: str
    subject: str
    summary: str
    expected_route: str
    success_keyword: str


class StepResult(BaseModel):
    observation: SupportQueueObservation
    reward: SupportQueueReward
    done: bool
    info: dict[str, Any] = Field(default_factory=dict)
