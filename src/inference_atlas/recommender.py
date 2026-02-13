"""Main recommendation engine for LLM deployment optimization.

This module ranks platform options by cost-efficiency, applying smooth penalties
for overload conditions, excessive scaling, and latency risk.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from inference_atlas.config import MAX_GPUS
from inference_atlas.cost_model import (
    CostBreakdown,
    calculate_gpu_monthly_cost,
    calculate_per_token_monthly_cost,
)
from inference_atlas.data_loader import get_platforms
from inference_atlas.scaling import calculate_utilization, latency_risk_band


def compute_penalty(
    utilization_after: float,
    gpu_count: int,
    latency_risk: str,
    strict_latency_required: bool,
) -> float:
    """Compute smooth penalties for overload, scaling limits, and strict latency.

    Penalty components:
    1. Overload penalty: Linear ramp above 90% utilization
       - Starts at 90% utilization
       - Reaches $20k at 100% utilization
       - Formula: $20k × ((util - 0.90) / 0.10)

    2. Scaling penalty: Linear penalty for excessive GPU count
       - Triggers above MAX_GPUS (8 GPUs)
       - $50k per GPU beyond limit
       - Formula: $50k × (gpu_count - MAX_GPUS)

    3. Strict latency penalty: Fixed penalty for high latency risk
       - Applies only if latency_requirement < 300ms
       - $30k penalty if latency_risk is "high"

    Args:
        utilization_after: Post-scaling utilization ratio (0-1)
        gpu_count: Number of GPUs in the configuration
        latency_risk: Risk level ("low", "medium", "high")
        strict_latency_required: True if latency requirement < 300ms

    Returns:
        Total penalty amount in USD (0 if no violations)
    """
    penalty = 0.0

    # Overload penalty: penalize utilization above 90%
    if utilization_after > 0.90:
        penalty += 20000 * ((utilization_after - 0.90) / 0.10)

    # Scaling penalty: penalize configurations requiring > MAX_GPUS
    if gpu_count > MAX_GPUS:
        penalty += 50000 * (gpu_count - MAX_GPUS)

    # Strict latency penalty: penalize high latency risk for strict requirements
    if latency_risk == "high" and strict_latency_required:
        penalty += 30000

    return penalty


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


def get_recommendations(
    tokens_per_day: float,
    pattern: str,
    model_key: str = "llama_70b",
    latency_requirement_ms: Optional[float] = None,
    top_k: int = 3,
) -> list[Recommendation]:
    """Return top-k ranked recommendations ordered by cost + penalties.

    The recommendation algorithm:
    1. Enumerate all platform/GPU combinations
    2. Filter out GPUs with insufficient memory
    3. Calculate utilization and multi-GPU scaling
    4. Calculate monthly cost (accounting for billing type)
    5. Compute penalties for overload, scaling, and latency violations
    6. Rank by: base_cost + penalties
    7. Return top-k results

    Args:
        tokens_per_day: Daily token volume
        pattern: Traffic pattern ("steady", "business_hours", "bursty")
        model_key: Model identifier (e.g., "llama_70b")
        latency_requirement_ms: Optional latency constraint (ms)
        top_k: Number of recommendations to return

    Returns:
        List of Recommendation objects, ranked by cost-effectiveness

    Raises:
        ValueError: If no platforms can handle the workload
    """
    platforms = get_platforms()
    candidates: list[tuple[float, str, str, CostBreakdown, str, float]] = []
    strict_latency_required = (
        latency_requirement_ms is not None and latency_requirement_ms < 300
    )

    # Enumerate GPU-backed platforms
    for platform_key, platform in platforms.items():
        if "gpus" in platform:
            for gpu_key, gpu in platform["gpus"].items():
                # Use model-specific throughput if available
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
                    # Skip incompatible GPUs (e.g., model doesn't fit in memory)
                    if "requires" in str(exc):
                        continue
                    raise

                utilization_after = utilization.utilization_after
                utilization_pct = utilization_after * 100
                latency_risk = latency_risk_band(utilization_after)

                # Compute penalties for violations
                penalty = compute_penalty(
                    utilization_after=utilization_after,
                    gpu_count=utilization.gpu_count,
                    latency_risk=latency_risk,
                    strict_latency_required=strict_latency_required,
                )

                reasoning = (
                    f"{cost.billing_type} billing; "
                    f"{utilization.gpu_count} GPU(s); "
                    f"utilization {utilization_pct:.0f}%; "
                    f"latency risk {latency_risk}; "
                    f"idle waste {cost.idle_waste_pct:.0f}%"
                )

                score = cost.monthly_cost_usd + penalty
                candidates.append((score, platform_key, gpu["name"], cost, reasoning, utilization_pct))

    # Enumerate per-token platforms
    for platform_key, platform in platforms.items():
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

    # Sort by score (cost + penalties) and take top-k
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
