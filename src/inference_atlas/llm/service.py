"""Service helpers for safe LLM parsing with deterministic fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from inference_atlas.llm.router import LLMRouter
from inference_atlas.llm.schema import WorkloadSpec


@dataclass(frozen=True)
class ParseWorkloadResult:
    """Structured result for natural-language workload parsing."""

    workload: WorkloadSpec
    provider_used: str
    raw_payload: dict[str, object]
    used_fallback: bool = False
    warning: Optional[str] = None


def parse_workload_text(
    user_text: str,
    fallback_workload: Optional[WorkloadSpec] = None,
    router: Optional[LLMRouter] = None,
) -> ParseWorkloadResult:
    """Parse text with LLM providers, optionally falling back to manual input.

    If all providers fail and `fallback_workload` is supplied, this function
    returns fallback data explicitly marked with `used_fallback=True`.
    """
    effective_router = router or LLMRouter()
    try:
        workload, provider_name, raw_payload = effective_router.parse_workload_with_meta(user_text)
        return ParseWorkloadResult(
            workload=workload,
            provider_used=provider_name,
            raw_payload=raw_payload,
            used_fallback=False,
            warning=None,
        )
    except RuntimeError as exc:
        if fallback_workload is None:
            raise
        return ParseWorkloadResult(
            workload=fallback_workload,
            provider_used="manual_fallback",
            raw_payload={},
            used_fallback=True,
            warning=str(exc),
        )
