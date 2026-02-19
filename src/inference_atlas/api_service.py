"""Service-layer handlers for API endpoints."""

from __future__ import annotations

from typing import Any

from inference_atlas.ai_copilot import next_copilot_turn
from inference_atlas.api_models import CopilotTurnRequest, CopilotTurnResponse


def _normalize_state(payload: CopilotTurnRequest) -> tuple[str, dict[str, Any]]:
    if payload.user_text:
        return payload.user_text, dict(payload.state or {})

    user_text = str(payload.message or "")
    state = dict(payload.state or {})
    if not state:
        state["messages"] = [
            {"role": message.role, "content": message.content}
            for message in payload.history
        ]
        extracted = dict(state.get("extracted_spec") or {})
        if payload.workload_type:
            extracted["workload_type"] = payload.workload_type
        state["extracted_spec"] = extracted
    return user_text, state


def _to_frontend_apply_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    values = payload.get("values")
    if isinstance(values, dict):
        return dict(values)
    if isinstance(payload, dict):
        return dict(payload)
    return None


def _build_reply(result: dict[str, Any]) -> str:
    missing_fields = list(result.get("missing_fields") or [])
    if not missing_fields:
        return "Configuration is ready. Click Apply to Config and run optimization."
    follow_ups = list(result.get("next_questions") or [])
    if follow_ups:
        return "Got it. Quick follow-ups:\n- " + "\n- ".join(follow_ups)
    return "I need a bit more detail to proceed."


def run_copilot_turn(payload: CopilotTurnRequest) -> CopilotTurnResponse:
    """Run one IA copilot turn with validated input/output contracts."""
    user_text, state = _normalize_state(payload)
    result = next_copilot_turn(user_text=user_text, state=state)
    response = {
        "reply": _build_reply(result),
        "extracted_spec": result.get("extracted_spec", {}),
        "missing_fields": result.get("missing_fields", []),
        "follow_up_questions": result.get("next_questions", []),
        "apply_payload": _to_frontend_apply_payload(result.get("apply_payload")),
        "is_ready": bool(result.get("ready_to_rank", False)),
    }
    return CopilotTurnResponse.model_validate(response)
