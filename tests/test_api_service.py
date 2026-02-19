from __future__ import annotations

import pytest
from pydantic import ValidationError

from inference_atlas.api_models import CopilotTurnRequest
from inference_atlas.api_service import run_copilot_turn


def test_run_copilot_turn_returns_valid_response() -> None:
    payload = CopilotTurnRequest(user_text="Need llm with 5 million tokens/day and $300 budget")
    response = run_copilot_turn(payload)
    assert response.extracted_spec["workload_type"] == "llm"
    assert response.extracted_spec["tokens_per_day"] == 5_000_000
    assert response.extracted_spec["monthly_budget_max_usd"] == 300
    assert isinstance(response.follow_up_questions, list)
    assert response.apply_payload is None or isinstance(response.apply_payload, dict)


def test_run_copilot_turn_merges_prior_state() -> None:
    first = run_copilot_turn(CopilotTurnRequest(user_text="Need speech to text under $50"))
    second = run_copilot_turn(
        CopilotTurnRequest(
            user_text="monthly usage 4000 and strict latency",
            state={
                "messages": [{"role": "user", "content": "Need speech to text under $50"}],
                "extracted_spec": first.extracted_spec,
            },
        )
    )
    assert second.extracted_spec["workload_type"] == "speech_to_text"
    assert second.extracted_spec["monthly_budget_max_usd"] == 50
    assert second.extracted_spec["monthly_usage"] == 4000
    assert second.extracted_spec["latency_priority"] == "strict"


def test_copilot_turn_request_validates_input() -> None:
    with pytest.raises(ValidationError):
        CopilotTurnRequest()


def test_run_copilot_turn_accepts_frontend_shape() -> None:
    payload = CopilotTurnRequest(
        message="Need vision with monthly usage 2000",
        history=[],
        workload_type="vision",
    )
    response = run_copilot_turn(payload)
    assert response.extracted_spec["workload_type"] == "vision"
    assert response.extracted_spec["monthly_usage"] == 2000
