"""Monthly cost calculations for different platform billing models."""

from __future__ import annotations

from dataclasses import dataclass

from core.utilization import UtilizationEstimate, calculate_utilization
from data.performance import MODEL_REQUIREMENTS
from data.platforms import PLATFORMS

HOURS_PER_MONTH = 730
DAYS_PER_MONTH = HOURS_PER_MONTH / 24


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

    Billing rules:
    - autoscaling: active_hours x hourly_rate
    - dedicated/per_second/hourly/hourly_variable: 730 x hourly_rate
    """
    if float(tokens_per_day) <= 0:
        raise ValueError(f"tokens_per_day must be > 0, got {tokens_per_day}.")

    if platform_key not in PLATFORMS:
        valid_platforms = ", ".join(sorted(PLATFORMS))
        raise KeyError(f"Unknown platform '{platform_key}'. Valid options: {valid_platforms}")
    platform = PLATFORMS[platform_key]
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

    throughput_by_model = gpu.get("throughput_by_model", {})
    if model_key in throughput_by_model:
        gpu_tps = float(throughput_by_model[model_key])
    else:
        gpu_tps = float(gpu["tokens_per_second"])

    if model_key in MODEL_REQUIREMENTS:
        required_mem = int(MODEL_REQUIREMENTS[model_key]["recommended_memory_gb"])
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

    if utilization is None:
        utilization = calculate_utilization(
            tokens_per_day=tokens_per_day,
            pattern=pattern,
            gpu_tokens_per_second=gpu_tps,
            model_key=model_key,
        )

    billing = platform["billing"]

    if billing == "autoscaling":
        monthly_cost = utilization.active_hours_per_month * hourly_rate
        idle_waste = 0.0
        idle_waste_pct = 0.0
    else:
        monthly_cost = HOURS_PER_MONTH * hourly_rate
        idle_waste = max(0.0, HOURS_PER_MONTH - utilization.active_hours_per_month) * hourly_rate
        idle_waste_pct = (idle_waste / monthly_cost * 100) if monthly_cost > 0 else 0.0

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
    """Calculate monthly cost for per-token offerings."""
    if float(tokens_per_day) <= 0:
        raise ValueError(f"tokens_per_day must be > 0, got {tokens_per_day}.")

    if platform_key not in PLATFORMS:
        valid_platforms = ", ".join(sorted(PLATFORMS))
        raise KeyError(f"Unknown platform '{platform_key}'. Valid options: {valid_platforms}")
    platform = PLATFORMS[platform_key]
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
