"""Platform and GPU pricing data for the deployment optimizer."""

from __future__ import annotations

from typing import Literal, TypedDict


class GPUSpecBase(TypedDict):
    """GPU-backed option metadata."""

    name: str
    hourly_rate: float
    memory_gb: int
    tokens_per_second: int


class GPUSpec(GPUSpecBase, total=False):
    """GPU-backed option metadata with optional model-specific throughput."""

    throughput_by_model: dict[str, int]


class ModelSpec(TypedDict):
    """Model-based (per-token) option metadata."""

    price_per_m_tokens: float


PlatformType = Literal["serverless", "dedicated", "marketplace", "model_based"]
BillingType = Literal["autoscaling", "per_second", "hourly", "hourly_variable", "per_token"]


class Platform(TypedDict, total=False):
    """Platform configuration for GPU and/or model-based offerings."""

    type: PlatformType
    billing: BillingType
    gpus: dict[str, GPUSpec]
    models: dict[str, ModelSpec]


PLATFORMS: dict[str, Platform] = {
    "fireworks": {
        "type": "serverless",
        "billing": "autoscaling",
        "gpus": {
            "a100_80gb": {
                "name": "NVIDIA A100 80GB",
                "hourly_rate": 2.9,
                "memory_gb": 80,
                "tokens_per_second": 8000,
                "throughput_by_model": {
                    "llama_8b": 20000,
                    "llama_70b": 8000,
                    "llama_405b": 1500,
                    "mixtral_8x7b": 7000,
                    "mistral_7b": 22000,
                },
            },
            "h100_80gb": {
                "name": "NVIDIA H100 80GB",
                "hourly_rate": 4.0,
                "memory_gb": 80,
                "tokens_per_second": 15000,
                "throughput_by_model": {
                    "llama_8b": 35000,
                    "llama_70b": 15000,
                    "llama_405b": 2800,
                    "mixtral_8x7b": 13000,
                    "mistral_7b": 38000,
                },
            },
            "h200_141gb": {
                "name": "NVIDIA H200 141GB",
                "hourly_rate": 6.0,
                "memory_gb": 141,
                "tokens_per_second": 18000,
                "throughput_by_model": {
                    "llama_8b": 42000,
                    "llama_70b": 18000,
                    "llama_405b": 3500,
                    "mixtral_8x7b": 16000,
                    "mistral_7b": 45000,
                },
            },
            "b200_180gb": {
                "name": "NVIDIA B200 180GB",
                "hourly_rate": 9.0,
                "memory_gb": 180,
                "tokens_per_second": 25000,
                "throughput_by_model": {
                    "llama_8b": 60000,
                    "llama_70b": 25000,
                    "llama_405b": 5000,
                    "mixtral_8x7b": 22000,
                    "mistral_7b": 65000,
                },
            },
        },
    },
    "replicate": {
        "type": "dedicated",
        "billing": "per_second",
        "gpus": {
            "a100_80gb": {
                "name": "NVIDIA A100 80GB",
                "hourly_rate": 10.08,
                "memory_gb": 80,
                "tokens_per_second": 8000,
                "throughput_by_model": {
                    "llama_8b": 20000,
                    "llama_70b": 8000,
                    "llama_405b": 1500,
                    "mixtral_8x7b": 7000,
                    "mistral_7b": 22000,
                },
            }
        },
    },
    "modal": {
        "type": "dedicated",
        "billing": "hourly",
        "gpus": {
            "a100_40gb": {
                "name": "NVIDIA A100",
                "hourly_rate": 3.67,
                "memory_gb": 40,
                "tokens_per_second": 6000,
                "throughput_by_model": {
                    "llama_8b": 15000,
                    "llama_70b": 6000,
                    "mixtral_8x7b": 5500,
                    "mistral_7b": 18000,
                },
            }
        },
    },
    "runpod": {
        "type": "dedicated",
        "billing": "hourly",
        "gpus": {
            "a100_80gb": {
                "name": "NVIDIA A100 80GB",
                "hourly_rate": 1.89,
                "memory_gb": 80,
                "tokens_per_second": 8000,
                "throughput_by_model": {
                    "llama_8b": 20000,
                    "llama_70b": 8000,
                    "llama_405b": 1500,
                    "mixtral_8x7b": 7000,
                    "mistral_7b": 22000,
                },
            }
        },
    },
    "vast_ai": {
        "type": "marketplace",
        "billing": "hourly_variable",
        "gpus": {
            "a100_80gb": {
                "name": "NVIDIA A100 80GB",
                "hourly_rate": 1.75,  # Average marketplace price
                "memory_gb": 80,
                "tokens_per_second": 8000,
                "throughput_by_model": {
                    "llama_8b": 20000,
                    "llama_70b": 8000,
                    "llama_405b": 1500,
                    "mixtral_8x7b": 7000,
                    "mistral_7b": 22000,
                },
            }
        },
    },
    "together": {
        "type": "model_based",
        "billing": "per_token",
        "models": {
            "llama_70b": {
                "price_per_m_tokens": 0.88,
            }
        },
    },
}
