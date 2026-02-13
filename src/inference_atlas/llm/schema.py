"""Schema and validation helpers for LLM-generated workload payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from inference_atlas.config import TRAFFIC_PATTERNS


@dataclass(frozen=True)
class WorkloadSpec:
    """Validated workload extracted from natural-language input."""

    tokens_per_day: float
    pattern: str
    model_key: str
    latency_requirement_ms: Optional[float] = None


def _normalize_pattern(pattern: str) -> str:
    normalized = pattern.strip().lower().replace(" ", "_")
    if normalized not in TRAFFIC_PATTERNS:
        valid_patterns = ", ".join(sorted(TRAFFIC_PATTERNS))
        raise ValueError(f"Invalid pattern '{pattern}'. Valid options: {valid_patterns}")
    return normalized


def validate_workload_payload(payload: Mapping[str, Any]) -> WorkloadSpec:
    """Validate/coerce an LLM payload into a deterministic WorkloadSpec.

    Required keys:
    - tokens_per_day: float > 0
    - pattern: one of TRAFFIC_PATTERNS
    - model_key: non-empty string

    Optional key:
    - latency_requirement_ms: float > 0 (or omitted/None)
    """
    if "tokens_per_day" not in payload:
        raise ValueError("Missing required field: tokens_per_day")
    if "pattern" not in payload:
        raise ValueError("Missing required field: pattern")
    if "model_key" not in payload:
        raise ValueError("Missing required field: model_key")

    tokens_per_day = float(payload["tokens_per_day"])
    if tokens_per_day <= 0:
        raise ValueError(f"tokens_per_day must be > 0, got {tokens_per_day}.")

    pattern = _normalize_pattern(str(payload["pattern"]))

    model_key = str(payload["model_key"]).strip()
    if not model_key:
        raise ValueError("model_key must be a non-empty string.")

    latency_raw = payload.get("latency_requirement_ms")
    latency_requirement_ms: Optional[float]
    if latency_raw in (None, "", 0, 0.0):
        latency_requirement_ms = None
    else:
        latency_requirement_ms = float(latency_raw)
        if latency_requirement_ms <= 0:
            raise ValueError(
                "latency_requirement_ms must be > 0 when provided."
            )

    return WorkloadSpec(
        tokens_per_day=tokens_per_day,
        pattern=pattern,
        model_key=model_key,
        latency_requirement_ms=latency_requirement_ms,
    )
