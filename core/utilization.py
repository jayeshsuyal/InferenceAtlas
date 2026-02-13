"""Utilities to model utilization from traffic volume and pattern.

Example:
    estimate = calculate_utilization(
        tokens_per_day=5_000_000,
        pattern="steady",
        gpu_tokens_per_second=8_000,
    )
"""

from __future__ import annotations

from dataclasses import dataclass

from data.performance import TRAFFIC_PATTERNS

HOURS_PER_MONTH = 730
SECONDS_PER_DAY = 24 * 60 * 60


@dataclass(frozen=True)
class TrafficProfile:
    """Traffic pattern parameters used in utilization modeling."""

    name: str
    active_ratio: float
    efficiency: float
    burst_factor: float


@dataclass(frozen=True)
class UtilizationEstimate:
    """Computed utilization metrics for a GPU under a given workload."""

    active_hours_per_month: float
    avg_tokens_per_second_global: float
    required_peak_tokens_per_second: float
    effective_gpu_tokens_per_second: float
    utilization_ratio: float


def get_traffic_profile(pattern: str) -> TrafficProfile:
    """Return normalized traffic profile for a pattern label."""
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
    )
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
    return profile


def calculate_utilization(
    tokens_per_day: float,
    pattern: str,
    gpu_tokens_per_second: float,
    model_key: str = "llama_70b",
) -> UtilizationEstimate:
    """Estimate active hours and utilization ratio for one GPU.

    The required peak throughput is modeled as:
    average_tps_global / active_ratio * burst_factor

    The effective GPU throughput is:
    gpu_tokens_per_second * efficiency
    """
    if float(tokens_per_day) <= 0:
        raise ValueError(
            f"tokens_per_day must be > 0, got {tokens_per_day}."
        )
    if float(gpu_tokens_per_second) <= 0:
        raise ValueError(
            f"gpu_tokens_per_second must be > 0, got {gpu_tokens_per_second}."
        )
    if not model_key:
        raise ValueError("model_key must be a non-empty string.")

    profile = get_traffic_profile(pattern)

    avg_tps_global = float(tokens_per_day) / SECONDS_PER_DAY
    required_peak_tps = avg_tps_global / profile.active_ratio * profile.burst_factor
    effective_gpu_tps = float(gpu_tokens_per_second) * profile.efficiency
    utilization_ratio = required_peak_tps / effective_gpu_tps

    return UtilizationEstimate(
        active_hours_per_month=HOURS_PER_MONTH * profile.active_ratio,
        avg_tokens_per_second_global=avg_tps_global,
        required_peak_tokens_per_second=required_peak_tps,
        effective_gpu_tokens_per_second=effective_gpu_tps,
        utilization_ratio=utilization_ratio,
    )
