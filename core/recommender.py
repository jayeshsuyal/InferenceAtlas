"""Recommendation engine for GPU/platform selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.cost_calculator import (
    CostBreakdown,
    calculate_gpu_monthly_cost,
    calculate_per_token_monthly_cost,
)
from core.utilization import calculate_utilization
from data.platforms import PLATFORMS

CAPACITY_VIOLATION_PENALTY = 1_000_000.0
LATENCY_VIOLATION_PENALTY = 100_000.0


@dataclass(frozen=True)
class Recommendation:
    """One ranked recommendation entry."""

    rank: int
    platform: str
    option: str
    monthly_cost_usd: float
    reasoning: str
    utilization_pct: float
    cost_per_million_tokens: float
    idle_waste_pct: float


def _latency_compatible(
    latency_requirement_ms: Optional[float],
    effective_tps: float,
) -> bool:
    """Return whether a simplified latency target is met.

    This heuristic assumes mostly sequential token generation and estimates latency
    for generating 1k tokens from effective throughput. It does not account for
    TTFT, dynamic batching behavior, queueing, model-specific decoding settings,
    or network overhead, so real-world latency may vary.
    """
    if latency_requirement_ms is None or latency_requirement_ms <= 0:
        return True
    if effective_tps <= 0:
        return False

    estimated_ms_for_1k_tokens = (1000.0 / effective_tps) * 1000.0
    return estimated_ms_for_1k_tokens <= latency_requirement_ms


def get_recommendations(
    tokens_per_day: float,
    pattern: str,
    model_key: str = "llama_70b",
    latency_requirement_ms: Optional[float] = None,
    top_k: int = 3,
) -> list[Recommendation]:
    """Return top ranked recommendations ordered by fit and cost."""
    candidates: list[tuple[float, str, str, CostBreakdown, str, float]] = []

    for platform_key, platform in PLATFORMS.items():
        if "gpus" in platform:
            for gpu_key, gpu in platform["gpus"].items():
                throughput_by_model = gpu.get("throughput_by_model", {})
                gpu_tps = float(throughput_by_model.get(model_key, gpu["tokens_per_second"]))

                try:
                    utilization = calculate_utilization(
                        tokens_per_day=tokens_per_day,
                        pattern=pattern,
                        gpu_tokens_per_second=gpu_tps,
                        model_key=model_key,
                    )
                    cost = calculate_gpu_monthly_cost(
                        platform_key=platform_key,
                        gpu_key=gpu_key,
                        tokens_per_day=tokens_per_day,
                        pattern=pattern,
                        model_key=model_key,
                        utilization=utilization,
                    )
                except ValueError as exc:
                    # Skip incompatible GPUs (e.g. model does not fit in memory).
                    if "requires" in str(exc):
                        continue
                    raise

                fits_capacity = utilization.utilization_ratio <= 1.0
                fits_latency = _latency_compatible(
                    latency_requirement_ms=latency_requirement_ms,
                    effective_tps=utilization.effective_gpu_tokens_per_second,
                )
                utilization_pct = utilization.utilization_ratio * 100

                penalty = 0.0
                if not fits_capacity:
                    penalty += CAPACITY_VIOLATION_PENALTY
                if not fits_latency:
                    penalty += LATENCY_VIOLATION_PENALTY

                reasoning = (
                    f"{cost.billing_type} billing; "
                    f"utilization {utilization_pct:.0f}%; "
                    f"idle waste {cost.idle_waste_pct:.0f}%"
                )

                score = cost.monthly_cost_usd + penalty
                candidates.append((score, platform_key, gpu["name"], cost, reasoning, utilization_pct))

        if "models" in platform and platform.get("billing") == "per_token":
            if model_key not in platform["models"]:
                continue
            for platform_model_key in platform["models"]:
                if platform_model_key != model_key:
                    continue
                cost = calculate_per_token_monthly_cost(
                    platform_key=platform_key,
                    model_key=platform_model_key,
                    tokens_per_day=tokens_per_day,
                )
                reasoning = "Per-token billing; no dedicated idle waste"
                score = cost.monthly_cost_usd
                candidates.append((score, platform_key, platform_model_key, cost, reasoning, 0.0))

    if not candidates:
        raise ValueError("No platforms can handle the specified workload")

    candidates.sort(key=lambda row: row[0])

    recommendations: list[Recommendation] = []
    for idx, (_, platform_key, option_name, cost, reasoning, util_pct) in enumerate(
        candidates[:top_k], start=1
    ):
        recommendations.append(
            Recommendation(
                rank=idx,
                platform=platform_key,
                option=option_name,
                monthly_cost_usd=cost.monthly_cost_usd,
                reasoning=reasoning,
                utilization_pct=util_pct,
                cost_per_million_tokens=cost.cost_per_million_tokens,
                idle_waste_pct=cost.idle_waste_pct,
            )
        )

    return recommendations
