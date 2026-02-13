"""Multi-GPU scaling and utilization estimation.

This module models GPU utilization under various traffic patterns and calculates
the number of GPUs needed to meet demand while maintaining target utilization.

The scaling model:
1. Converts daily token volume to average tokens/second
2. Applies traffic pattern (active_ratio, burst_factor) to estimate peak load
3. Accounts for GPU efficiency (batching, scheduling overhead)
4. Scales to multiple GPUs if single-GPU utilization exceeds target threshold
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from inference_atlas.config import (
    HOURS_PER_MONTH,
    SECONDS_PER_DAY,
    TRAFFIC_PATTERNS,
    U_TARGET,
)


@dataclass(frozen=True)
class TrafficProfile:
    """Traffic pattern parameters used in utilization modeling."""

    name: str
    active_ratio: float  # Fraction of time with active traffic
    efficiency: float  # GPU batching/scheduling efficiency (0-1)
    burst_factor: float  # Peak-to-average traffic multiplier
    batch_mult: float  # Batching throughput gain under load


@dataclass(frozen=True)
class UtilizationEstimate:
    """Computed utilization metrics for a GPU cluster under a given workload."""

    active_hours_per_month: float
    avg_tokens_per_second_global: float
    required_peak_tokens_per_second: float
    effective_gpu_tokens_per_second: float
    utilization_ratio: float  # Required capacity / available capacity (per GPU)
    gpu_count: int = 1  # Number of GPUs needed
    utilization_after: float = 0.0  # Utilization after multi-GPU scaling


def get_traffic_profile(pattern: str) -> TrafficProfile:
    """Return normalized traffic profile for a pattern label.

    Args:
        pattern: Traffic pattern name (case-insensitive, spaces allowed)

    Returns:
        TrafficProfile with validated parameters

    Raises:
        ValueError: If pattern is unknown or has invalid parameters
    """
    normalized = pattern.strip().lower().replace(" ", "_")
    if normalized not in TRAFFIC_PATTERNS:
        valid = ", ".join(sorted(TRAFFIC_PATTERNS))
        raise ValueError(f"Unknown pattern '{pattern}'. Valid options: {valid}")

    config = TRAFFIC_PATTERNS[normalized]
    profile = TrafficProfile(
        name=normalized,
        active_ratio=float(config["active_ratio"]),
        efficiency=float(config["efficiency"]),
        burst_factor=float(config["burst_factor"]),
        batch_mult=float(config["batch_mult"]),
    )

    # Validate parameters
    if profile.active_ratio <= 0:
        raise ValueError(
            f"Traffic pattern '{pattern}' has invalid active_ratio={profile.active_ratio}. "
            "active_ratio must be > 0."
        )
    if profile.efficiency <= 0:
        raise ValueError(
            f"Traffic pattern '{pattern}' has invalid efficiency={profile.efficiency}. "
            "efficiency must be > 0."
        )
    if profile.burst_factor <= 0:
        raise ValueError(
            f"Traffic pattern '{pattern}' has invalid burst_factor={profile.burst_factor}. "
            "burst_factor must be > 0."
        )
    if profile.batch_mult <= 0:
        raise ValueError(
            f"Traffic pattern '{pattern}' has invalid batch_mult={profile.batch_mult}. "
            "batch_mult must be > 0."
        )
    return profile


def calculate_utilization(
    tokens_per_day: float,
    pattern: str,
    gpu_tokens_per_second: float,
    model_key: str = "llama_70b",
) -> UtilizationEstimate:
    """Estimate GPU count and utilization for a given workload.

    The scaling algorithm:
    1. Calculate average tokens/second over 24 hours
    2. Adjust for traffic pattern:
       - Divide by active_ratio (concentrates load into active periods)
       - Multiply by burst_factor (accounts for peak traffic spikes)
    3. Calculate effective GPU throughput:
       - Apply efficiency factor (batching/scheduling overhead)
       - Apply batch_mult (throughput gains from batching)
    4. Scale to multiple GPUs if utilization exceeds U_TARGET (75%)

    Args:
        tokens_per_day: Total tokens generated/processed per day
        pattern: Traffic pattern name ("steady", "business_hours", "bursty")
        gpu_tokens_per_second: Raw GPU throughput (tokens/sec)
        model_key: Model identifier (used for validation)

    Returns:
        UtilizationEstimate with GPU count and utilization metrics

    Raises:
        ValueError: If inputs are invalid or pattern is unknown
    """
    if float(tokens_per_day) <= 0:
        raise ValueError(f"tokens_per_day must be > 0, got {tokens_per_day}.")
    if float(gpu_tokens_per_second) <= 0:
        raise ValueError(f"gpu_tokens_per_second must be > 0, got {gpu_tokens_per_second}.")
    if not model_key:
        raise ValueError("model_key must be a non-empty string.")

    profile = get_traffic_profile(pattern)

    # Step 1: Average global throughput over 24 hours
    avg_tps_global = float(tokens_per_day) / SECONDS_PER_DAY

    # Step 2: Peak throughput during active periods
    required_peak_tps = avg_tps_global / profile.active_ratio * profile.burst_factor

    # Step 3: Effective GPU throughput (accounting for efficiency and batching)
    effective_gpu_tps = float(gpu_tokens_per_second) * profile.efficiency * profile.batch_mult

    # Step 4: Utilization ratio (before multi-GPU scaling)
    utilization_ratio = required_peak_tps / effective_gpu_tps

    # Step 5: Scale to multiple GPUs if utilization exceeds target
    gpu_count = max(1, math.ceil(utilization_ratio / U_TARGET))

    # Step 6: Utilization after scaling
    utilization_after = utilization_ratio / gpu_count

    return UtilizationEstimate(
        active_hours_per_month=HOURS_PER_MONTH * profile.active_ratio,
        avg_tokens_per_second_global=avg_tps_global,
        required_peak_tokens_per_second=required_peak_tps,
        effective_gpu_tokens_per_second=effective_gpu_tps,
        utilization_ratio=utilization_ratio,
        gpu_count=gpu_count,
        utilization_after=utilization_after,
    )


def latency_risk_band(utilization_after: float) -> str:
    """Return latency risk category based on post-scaling utilization.

    Risk bands:
    - low:    utilization ≤ 50% (ample headroom)
    - medium: utilization ≤ 75% (target threshold)
    - high:   utilization > 75% (approaching saturation)

    Args:
        utilization_after: Utilization ratio after multi-GPU scaling

    Returns:
        Risk level: "low", "medium", or "high"
    """
    if utilization_after <= 0.50:
        return "low"
    if utilization_after <= 0.75:
        return "medium"
    return "high"
