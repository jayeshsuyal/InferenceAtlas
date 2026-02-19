"""Pydantic API contracts for backend endpoints."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CopilotMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: str
    content: str


class CopilotTurnRequest(BaseModel):
    """Request payload for one IA copilot turn.

    Supports both:
    - frontend payload: {message, history, workload_type}
    - internal payload: {user_text, state}
    """

    model_config = ConfigDict(extra="ignore")

    message: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    history: list[CopilotMessage] = Field(default_factory=list)
    workload_type: Optional[str] = None

    user_text: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    state: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_input_shape(self) -> "CopilotTurnRequest":
        if self.user_text:
            return self
        if self.message:
            return self
        raise ValueError("Either 'user_text' or 'message' must be provided.")


class CopilotTurnResponse(BaseModel):
    """Structured response payload for IA copilot UI."""

    model_config = ConfigDict(extra="ignore")

    reply: str
    extracted_spec: dict[str, Any]
    missing_fields: list[str]
    follow_up_questions: list[str]
    apply_payload: Optional[dict[str, Any]]
    is_ready: bool
