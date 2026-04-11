from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

MIN_OPEN_SCORE = 0.01
MAX_OPEN_SCORE = 0.99


def clamp_open_score(value: float) -> float:
    score = float(value)
    if score <= MIN_OPEN_SCORE:
        return MIN_OPEN_SCORE
    if score >= MAX_OPEN_SCORE:
        return MAX_OPEN_SCORE
    return score


class SupportQueueAction(BaseModel):
    route: str
    reply: str


class SupportQueueObservation(BaseModel):
    ticket_id: str
    status: str
    subject: str = ""
    summary: str = ""


class SupportQueueReward(BaseModel):
    score: float = Field(gt=0.0, lt=1.0)

    @field_validator("score", mode="before")
    @classmethod
    def _sanitize_score(cls, value: float) -> float:
        # Defensive normalization: any accidental boundary value is nudged to strict open interval.
        return clamp_open_score(value)


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
    reward: float = Field(gt=0.0, lt=1.0)
    done: bool
    info: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reward", mode="before")
    @classmethod
    def _sanitize_reward(cls, value: float) -> float:
        return clamp_open_score(value)
