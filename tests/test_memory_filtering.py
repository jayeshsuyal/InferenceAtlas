"""Tests for model memory requirements and GPU memory filtering."""

from __future__ import annotations

import pytest

from inference_atlas import get_recommendations
from inference_atlas.cost_model import calculate_gpu_monthly_cost


def test_model_fits_in_gpu_memory() -> None:
    """Test that Llama 70B (80GB) fits in A100 80GB."""
    # Should not raise - model fits
    breakdown = calculate_gpu_monthly_cost(
        platform_key="fireworks",
        gpu_key="a100_80gb",
        tokens_per_day=1_000_000,
        pattern="steady",
        model_key="llama_70b",
    )
    assert breakdown.monthly_cost_usd > 0


def test_model_does_not_fit_raises_error() -> None:
    """Test that Llama 70B (80GB) does not fit in A100 40GB."""
    with pytest.raises(ValueError, match="requires 80GB but.*only has 40GB"):
        calculate_gpu_monthly_cost(
            platform_key="modal",
            gpu_key="a100_40gb",
            tokens_per_day=1_000_000,
            pattern="steady",
            model_key="llama_70b",  # Needs 80GB
        )


def test_405b_model_requires_high_memory_gpu() -> None:
    """Test that 405B model (400GB) cannot fit on single GPUs.

    Note: 405B requires tensor parallelism across multiple GPUs.
    Current model doesn't support this, so should raise ValueError.
    """
    with pytest.raises(ValueError, match="No platforms can handle"):
        recommendations = get_recommendations(
            tokens_per_day=5_000_000,
            pattern="steady",
            model_key="llama_405b",
            top_k=3,
        )


def test_small_model_has_more_gpu_options() -> None:
    """Test that Llama 8B (16GB) can run on all GPU types."""
    recommendations = get_recommendations(
        tokens_per_day=5_000_000,
        pattern="steady",
        model_key="llama_8b",
        top_k=10,  # Request many options
    )

    # Should have at least 5 options (not all filtered by memory)
    assert len(recommendations) >= 5


def test_memory_check_skips_incompatible_gpus_gracefully() -> None:
    """Test that recommendations handle memory-incompatible GPUs gracefully.

    For models that don't fit on any single GPU (e.g., 405B), the system
    should raise a clear error rather than crashing.
    """
    # 405B doesn't fit on any single GPU - should raise clear error
    with pytest.raises(ValueError, match="No platforms can handle"):
        recommendations = get_recommendations(
            tokens_per_day=10_000_000,
            pattern="steady",
            model_key="llama_405b",
            top_k=3,
        )
