"""Data loading utilities for platform catalog and model specifications.

This module provides access to GPU platform pricing data and LLM model requirements.
Data is loaded from the data/ directory at the project root.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Add project root to path to allow importing from data/
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

if TYPE_CHECKING:
    from data.platforms import Platform
    from typing import TypedDict

    class ModelRequirement(TypedDict):
        """Model memory and parameter specifications."""

        display_name: str
        recommended_memory_gb: int
        parameter_count: int


def get_platforms() -> dict[str, Platform]:
    """Load GPU platform catalog with pricing and specs.

    Returns:
        Dictionary mapping platform keys to platform configurations.
        Each platform includes GPU specs, billing type, and pricing.
    """
    from data.platforms import PLATFORMS

    return PLATFORMS


def get_models() -> dict[str, ModelRequirement]:
    """Load LLM model memory requirements and specifications.

    Returns:
        Dictionary mapping model keys to model requirements.
        Includes recommended memory, display name, and parameter count.
    """
    from data.performance import MODEL_REQUIREMENTS

    return MODEL_REQUIREMENTS


def get_model_display_name(model_key: str) -> str:
    """Get human-readable display name for a model key.

    Args:
        model_key: Internal model identifier (e.g., "llama_70b")

    Returns:
        Display name (e.g., "Llama 3.1 70B")

    Raises:
        KeyError: If model_key is not recognized
    """
    models = get_models()
    if model_key not in models:
        valid_keys = ", ".join(sorted(models.keys()))
        raise KeyError(f"Unknown model '{model_key}'. Valid options: {valid_keys}")
    return models[model_key]["display_name"]
