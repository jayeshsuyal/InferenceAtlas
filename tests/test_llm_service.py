from __future__ import annotations

from typing import Any

import pytest

from inference_atlas.llm.base import LLMAdapter
from inference_atlas.llm.router import LLMRouter, RouterConfig
from inference_atlas.llm.schema import WorkloadSpec
from inference_atlas.llm.service import parse_workload_text


class _SuccessAdapter(LLMAdapter):
    def __init__(self, provider_name: str, payload: dict[str, Any]) -> None:
        self.provider_name = provider_name
        self._payload = payload

    def parse_workload(self, user_text: str) -> dict[str, Any]:
        return self._payload

    def explain(self, recommendation_summary: str, workload: WorkloadSpec) -> str:
        return "ok"


class _FailAdapter(LLMAdapter):
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    def parse_workload(self, user_text: str) -> dict[str, Any]:
        raise RuntimeError("provider unavailable")

    def explain(self, recommendation_summary: str, workload: WorkloadSpec) -> str:
        raise RuntimeError("provider unavailable")


def test_parse_workload_text_success_path() -> None:
    router = LLMRouter(
        adapters={
            "gpt_5_2": _SuccessAdapter(
                "gpt_5_2",
                {"tokens_per_day": 2_500_000, "pattern": "steady", "model_key": "llama_70b"},
            ),
            "opus_4_6": _FailAdapter("opus_4_6"),
        },
        config=RouterConfig(primary_provider="gpt_5_2", fallback_provider="opus_4_6"),
    )

    result = parse_workload_text("test", router=router)
    assert result.used_fallback is False
    assert result.provider_used == "gpt_5_2"
    assert result.workload.tokens_per_day == 2_500_000


def test_parse_workload_text_fallback_path() -> None:
    router = LLMRouter(
        adapters={
            "gpt_5_2": _FailAdapter("gpt_5_2"),
            "opus_4_6": _FailAdapter("opus_4_6"),
        },
        config=RouterConfig(primary_provider="gpt_5_2", fallback_provider="opus_4_6"),
    )
    manual = WorkloadSpec(
        tokens_per_day=1_000_000,
        pattern="steady",
        model_key="llama_8b",
        latency_requirement_ms=None,
    )

    result = parse_workload_text("test", fallback_workload=manual, router=router)
    assert result.used_fallback is True
    assert result.provider_used == "manual_fallback"
    assert result.workload == manual
    assert result.warning == "AI parser unavailable. Used manual form values."
    assert result.debug_details is not None
    assert "provider unavailable" in result.debug_details


def test_parse_workload_text_schema_rejection_raises_without_fallback() -> None:
    router = LLMRouter(
        adapters={
            "gpt_5_2": _SuccessAdapter(
                "gpt_5_2",
                {"tokens_per_day": 0, "pattern": "steady", "model_key": "llama_70b"},
            ),
            "opus_4_6": _FailAdapter("opus_4_6"),
        },
        config=RouterConfig(primary_provider="gpt_5_2", fallback_provider="opus_4_6"),
    )

    with pytest.raises(RuntimeError, match="All LLM providers failed to parse workload"):
        parse_workload_text("test", router=router)
