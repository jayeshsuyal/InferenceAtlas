"""Performance reference data used by the recommendation engine."""

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

TRAFFIC_PATTERNS = {
    "steady": {
        "active_ratio": 1.0,
        "efficiency": 0.80,
        "burst_factor": 1.0,
    },
    "business_hours": {
        "active_ratio": 0.238,  # 40 hrs / 168 hrs
        "efficiency": 0.75,
        "burst_factor": 1.0,
    },
    "bursty": {
        "active_ratio": 0.40,
        "efficiency": 0.60,
        "burst_factor": 3.0,
    },
}
