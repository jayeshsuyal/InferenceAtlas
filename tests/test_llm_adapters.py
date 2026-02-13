from __future__ import annotations

import pytest

from inference_atlas.llm.gpt_5_2_adapter import GPT52Adapter
from inference_atlas.llm.opus_4_6_adapter import Opus46Adapter
from inference_atlas.llm.schema import WorkloadSpec


def test_gpt_parse_workload_extracts_json_from_text_wrapper() -> None:
    adapter = GPT52Adapter(api_key="test-key")
    adapter._generate_text = lambda _s, _u: (  # type: ignore[attr-defined]
        "Here is data:\n"
        '{"tokens_per_day": 5000000, "pattern": "steady", "model_key": "llama_70b", "latency_requirement_ms": null}'
    )
    payload = adapter.parse_workload("test")
    assert payload["tokens_per_day"] == 5_000_000
    assert payload["pattern"] == "steady"


def test_opus_parse_workload_extracts_json_from_text_wrapper() -> None:
    adapter = Opus46Adapter(api_key="test-key")
    adapter._generate_text = lambda _s, _u: (  # type: ignore[attr-defined]
        '{"tokens_per_day": 2500000, "pattern": "business_hours", "model_key": "llama_8b"}'
    )
    payload = adapter.parse_workload("test")
    assert payload["tokens_per_day"] == 2_500_000
    assert payload["pattern"] == "business_hours"


def test_gpt_explain_returns_text() -> None:
    adapter = GPT52Adapter(api_key="test-key")
    adapter._generate_text = lambda _s, _u: "grounded explanation"  # type: ignore[attr-defined]
    workload = WorkloadSpec(tokens_per_day=1_000_000, pattern="steady", model_key="llama_8b")
    explanation = adapter.explain("summary", workload)
    assert explanation == "grounded explanation"


def test_opus_explain_returns_text() -> None:
    adapter = Opus46Adapter(api_key="test-key")
    adapter._generate_text = lambda _s, _u: "ops-grade explanation"  # type: ignore[attr-defined]
    workload = WorkloadSpec(tokens_per_day=1_000_000, pattern="steady", model_key="llama_8b")
    explanation = adapter.explain("summary", workload)
    assert explanation == "ops-grade explanation"


def test_gpt_missing_key_raises() -> None:
    adapter = GPT52Adapter(api_key="")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not configured"):
        adapter._ensure_api_key()  # type: ignore[attr-defined]


def test_opus_missing_key_raises() -> None:
    adapter = Opus46Adapter(api_key="")
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY is not configured"):
        adapter._ensure_api_key()  # type: ignore[attr-defined]


def test_gpt_constructor_validates_timeouts_and_retries() -> None:
    with pytest.raises(ValueError, match="timeout_sec must be > 0"):
        GPT52Adapter(api_key="x", timeout_sec=0)
    with pytest.raises(ValueError, match="max_retries must be >= 0"):
        GPT52Adapter(api_key="x", max_retries=-1)
    with pytest.raises(ValueError, match="backoff_base_sec must be >= 0"):
        GPT52Adapter(api_key="x", backoff_base_sec=-0.1)


def test_opus_constructor_validates_timeouts_and_retries() -> None:
    with pytest.raises(ValueError, match="timeout_sec must be > 0"):
        Opus46Adapter(api_key="x", timeout_sec=0)
    with pytest.raises(ValueError, match="max_retries must be >= 0"):
        Opus46Adapter(api_key="x", max_retries=-1)
    with pytest.raises(ValueError, match="backoff_base_sec must be >= 0"):
        Opus46Adapter(api_key="x", backoff_base_sec=-0.1)
