from __future__ import annotations

from inference_atlas.config import DAYS_PER_MONTH, HOURS_PER_MONTH
from inference_atlas.cost_model import calculate_gpu_monthly_cost
from inference_atlas.recommender import compute_penalty
from inference_atlas.scaling import (
    UtilizationEstimate,
    calculate_utilization,
    latency_risk_band,
)


def test_multi_gpu_scaling() -> None:
    utilization = calculate_utilization(
        tokens_per_day=8_640_000,  # 100 tokens/sec average
        pattern="steady",
        gpu_tokens_per_second=50,
        model_key="llama_70b",
    )
    assert utilization.gpu_count == 3
    assert 0 < utilization.utilization_after <= utilization.utilization_ratio


def test_month_consistency() -> None:
    assert HOURS_PER_MONTH == 720
    assert DAYS_PER_MONTH == 30


def test_penalty_ramp() -> None:
    p1 = compute_penalty(
        utilization_after=0.91,
        gpu_count=1,
        latency_risk="low",
        strict_latency_required=False,
    )
    p2 = compute_penalty(
        utilization_after=1.0,
        gpu_count=1,
        latency_risk="low",
        strict_latency_required=False,
    )
    assert p1 > 0
    assert p2 > p1


def test_latency_risk_levels() -> None:
    assert latency_risk_band(0.40) == "low"
    assert latency_risk_band(0.60) == "medium"
    assert latency_risk_band(0.80) == "high"


def test_dedicated_cost_scales_with_gpu_count_and_idle_waste() -> None:
    utilization = UtilizationEstimate(
        active_hours_per_month=180.0,
        avg_tokens_per_second_global=10.0,
        required_peak_tokens_per_second=10.0,
        effective_gpu_tokens_per_second=20.0,
        utilization_ratio=0.5,
        gpu_count=2,
        utilization_after=0.25,
    )
    breakdown = calculate_gpu_monthly_cost(
        platform_key="runpod",
        gpu_key="a100_80gb",
        tokens_per_day=1_000_000,
        pattern="business_hours",
        model_key="llama_70b",
        utilization=utilization,
    )

    expected_monthly = 720 * 1.89 * 2
    expected_idle = (720 - 180) * 1.89 * 2
    expected_idle_pct = expected_idle / expected_monthly * 100
    assert breakdown.monthly_cost_usd == expected_monthly
    assert breakdown.idle_waste_usd == expected_idle
    assert breakdown.idle_waste_pct == expected_idle_pct


def test_autoscaling_cost_scales_with_gpu_count_and_zero_idle_waste() -> None:
    utilization = UtilizationEstimate(
        active_hours_per_month=180.0,
        avg_tokens_per_second_global=10.0,
        required_peak_tokens_per_second=10.0,
        effective_gpu_tokens_per_second=20.0,
        utilization_ratio=0.5,
        gpu_count=2,
        utilization_after=0.25,
    )
    breakdown = calculate_gpu_monthly_cost(
        platform_key="fireworks",
        gpu_key="a100_80gb",
        tokens_per_day=1_000_000,
        pattern="business_hours",
        model_key="llama_70b",
        utilization=utilization,
    )

    expected_monthly = 180 * 2.9 * 2
    assert breakdown.monthly_cost_usd == expected_monthly
    assert breakdown.idle_waste_usd == 0
    assert breakdown.idle_waste_pct == 0


def test_penalty_has_scaling_and_strict_latency_components() -> None:
    penalty = compute_penalty(
        utilization_after=0.95,
        gpu_count=10,
        latency_risk="high",
        strict_latency_required=True,
    )
    assert penalty > 0
    assert penalty == (20000 * ((0.95 - 0.90) / 0.10)) + (50000 * 2) + 30000
