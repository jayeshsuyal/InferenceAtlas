"""Bundled model performance defaults for runtime-safe imports."""

from __future__ import annotations

MODEL_REQUIREMENTS = {
    "llama_8b": {
        "display_name": "Llama 3.1 8B",
        "recommended_memory_gb": 16,
        "parameter_count": 8_000_000_000,
    },
    "llama_70b": {
        "display_name": "Llama 3.1 70B",
        "recommended_memory_gb": 80,
        "parameter_count": 70_000_000_000,
    },
    "llama_405b": {
        "display_name": "Llama 3.1 405B",
        "recommended_memory_gb": 400,
        "parameter_count": 405_000_000_000,
    },
    "mixtral_8x7b": {
        "display_name": "Mixtral 8x7B",
        "recommended_memory_gb": 90,
        "parameter_count": 47_000_000_000,
    },
    "mistral_7b": {
        "display_name": "Mistral 7B",
        "recommended_memory_gb": 16,
        "parameter_count": 7_000_000_000,
    },
}

