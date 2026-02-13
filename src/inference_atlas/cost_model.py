"""Monthly cost calculations for different platform billing models.

This module computes total monthly costs for GPU-backed and per-token platforms,
accounting for multi-GPU scaling, billing type, idle waste, and cost per million tokens.

Billing models:
- autoscaling: Pay only for active hours (active_hours × hourly_rate × gpu_count)
- dedicated/per_second/hourly/hourly_variable: Pay for full month (720 hours × rate × gpu_count)
- per_token: Pay per token consumed (tokens/month × price_per_million_tokens)
"""

from __future__ import annotations

from dataclasses import dataclass

from inference_atlas.config import DAYS_PER_MONTH, HOURS_PER_MONTH
from inference_atlas.data_loader import get_models, get_platforms
from inference_atlas.scaling import UtilizationEstimate, calculate_utilization


@dataclass(frozen=True)
class CostBreakdown:
    """Cost details for one platform option."""

    platform: str
    option_key: str
    option_name: str
    billing_type: str
    monthly_cost_usd: float
    active_hours_per_month: float
    idle_waste_usd: float
    cost_per_million_tokens: float
    idle_waste_pct: float


def calculate_gpu_monthly_cost(
    platform_key: str,
    gpu_key: str,
    tokens_per_day: float,
    pattern: str,
    model_key: str = "llama_70b",
    utilization: UtilizationEstimate | None = None,
) -> CostBreakdown:
    """Calculate monthly cost for GPU-backed offerings.

    Cost formulas:
    - Autoscaling: active_hours × hourly_rate × gpu_count
    - Dedicated: 720 hours × hourly_rate × gpu_count
    - Idle waste: (720 - active_hours) × hourly_rate × gpu_count (dedicated only)

    Args:
        platform_key: Platform identifier (e.g., "fireworks", "runpod")
        gpu_key: GPU type key (e.g., "a100_80gb")
        tokens_per_day: Daily token volume
        pattern: Traffic pattern name
        model_key: Model identifier for memory validation
        utilization: Pre-computed utilization (optional, will calculate if None)

    Returns:
        CostBreakdown with monthly cost, idle waste, and cost per million tokens

    Raises:
        ValueError: If inputs are invalid or model doesn't fit in GPU memory
        KeyError: If platform or GPU key is not recognized
    """
    if float(tokens_per_day) <= 0:
        raise ValueError(f"tokens_per_day must be > 0, got {tokens_per_day}.")

    platforms = get_platforms()
    models = get_models()

    if platform_key not in platforms:
        valid_platforms = ", ".join(sorted(platforms))
        raise KeyError(f"Unknown platform '{platform_key}'. Valid options: {valid_platforms}")
    platform = platforms[platform_key]

    if "gpus" not in platform:
        raise KeyError(f"Platform '{platform_key}' does not define GPU options.")
    if gpu_key not in platform["gpus"]:
        valid_gpus = ", ".join(sorted(platform["gpus"]))
        raise KeyError(
            f"Unknown GPU key '{gpu_key}' for platform '{platform_key}'. Valid options: {valid_gpus}"
        )
    gpu = platform["gpus"][gpu_key]

    if not model_key:
        raise ValueError("model_key must be a non-empty string.")

    # Lookup model-specific throughput if available
    throughput_by_model = gpu.get("throughput_by_model", {})
    if model_key in throughput_by_model:
        gpu_tps = float(throughput_by_model[model_key])
    else:
        gpu_tps = float(gpu["tokens_per_second"])

    # Memory validation: ensure model fits in GPU
    if model_key in models:
        required_mem = int(models[model_key]["recommended_memory_gb"])
        gpu_mem = int(gpu["memory_gb"])
        if required_mem > gpu_mem:
            raise ValueError(
                f"Model '{model_key}' requires {required_mem}GB but "
                f"{gpu['name']} only has {gpu_mem}GB"
            )

    hourly_rate = float(gpu["hourly_rate"])
    if hourly_rate <= 0:
        raise ValueError(
            f"hourly_rate must be > 0 for {platform_key}/{gpu_key}, got {hourly_rate}."
        )

    # Calculate utilization if not provided
    if utilization is None:
        utilization = calculate_utilization(
            tokens_per_day=tokens_per_day,
            pattern=pattern,
            gpu_tokens_per_second=gpu_tps,
            model_key=model_key,
        )

    billing = platform["billing"]
    gpu_count = utilization.gpu_count if utilization.gpu_count > 0 else 1

    # Cost calculation based on billing type
    if billing == "autoscaling":
        # Pay only for active hours
        monthly_cost = utilization.active_hours_per_month * hourly_rate * gpu_count
        idle_waste = 0.0
        idle_waste_pct = 0.0
    else:
        # Dedicated: pay for full month (720 hours)
        monthly_cost = HOURS_PER_MONTH * hourly_rate * gpu_count
        idle_hours = max(0.0, HOURS_PER_MONTH - utilization.active_hours_per_month)
        idle_waste = idle_hours * hourly_rate * gpu_count
        idle_waste_pct = (idle_waste / monthly_cost * 100) if monthly_cost > 0 else 0.0

    # Cost per million tokens
    monthly_tokens = float(tokens_per_day) * DAYS_PER_MONTH
    cost_per_m_tokens = (monthly_cost / monthly_tokens) * 1_000_000 if monthly_tokens > 0 else 0.0

    return CostBreakdown(
        platform=platform_key,
        option_key=gpu_key,
        option_name=str(gpu["name"]),
        billing_type=billing,
        monthly_cost_usd=monthly_cost,
        active_hours_per_month=utilization.active_hours_per_month,
        idle_waste_usd=idle_waste,
        cost_per_million_tokens=cost_per_m_tokens,
        idle_waste_pct=idle_waste_pct,
    )


def calculate_per_token_monthly_cost(
    platform_key: str,
    model_key: str,
    tokens_per_day: float,
) -> CostBreakdown:
    """Calculate monthly cost for per-token offerings.

    Per-token platforms (e.g., Together AI) charge per million tokens consumed,
    with no idle waste or GPU provisioning.

    Cost formula:
    monthly_cost = (tokens_per_day × 30) / 1_000_000 × price_per_m_tokens

    Args:
        platform_key: Platform identifier (e.g., "together")
        model_key: Model identifier (e.g., "llama_70b")
        tokens_per_day: Daily token volume

    Returns:
        CostBreakdown with monthly cost and zero idle waste

    Raises:
        ValueError: If inputs are invalid
        KeyError: If platform or model key is not recognized
    """
    if float(tokens_per_day) <= 0:
        raise ValueError(f"tokens_per_day must be > 0, got {tokens_per_day}.")

    platforms = get_platforms()

    if platform_key not in platforms:
        valid_platforms = ", ".join(sorted(platforms))
        raise KeyError(f"Unknown platform '{platform_key}'. Valid options: {valid_platforms}")
    platform = platforms[platform_key]

    if "models" not in platform:
        raise KeyError(f"Platform '{platform_key}' does not define model options.")
    if model_key not in platform["models"]:
        valid_models = ", ".join(sorted(platform["models"]))
        raise KeyError(
            f"Unknown model key '{model_key}' for platform '{platform_key}'. "
            f"Valid options: {valid_models}"
        )
    model = platform["models"][model_key]

    price_per_m_tokens = float(model["price_per_m_tokens"])
    if price_per_m_tokens <= 0:
        raise ValueError(
            f"price_per_m_tokens must be > 0 for {platform_key}/{model_key}, "
            f"got {price_per_m_tokens}."
        )

    monthly_tokens = float(tokens_per_day) * DAYS_PER_MONTH
    monthly_cost = (monthly_tokens / 1_000_000) * price_per_m_tokens
    cost_per_m_tokens = (monthly_cost / monthly_tokens) * 1_000_000 if monthly_tokens > 0 else 0.0

    return CostBreakdown(
        platform=platform_key,
        option_key=model_key,
        option_name=model_key,
        billing_type=str(platform["billing"]),
        monthly_cost_usd=monthly_cost,
        active_hours_per_month=0.0,
        idle_waste_usd=0.0,
        cost_per_million_tokens=cost_per_m_tokens,
        idle_waste_pct=0.0,
    )
