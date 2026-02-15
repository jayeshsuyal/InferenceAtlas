"""Workload type definitions and routing configuration.

This module defines the supported inference workload types and controls
which types are currently enabled in production.
"""

from __future__ import annotations

from enum import Enum


class WorkloadType(Enum):
    """Supported inference workload types.

    Each type has fundamentally different capacity math, cost models,
    and provider ecosystems.
    """

    LLM = "llm"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    EMBEDDINGS = "embeddings"
    IMAGE_GENERATION = "image_generation"
    VISION = "vision"

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return {
            WorkloadType.LLM: "LLM Inference",
            WorkloadType.SPEECH_TO_TEXT: "Speech-to-Text",
            WorkloadType.TEXT_TO_SPEECH: "Text-to-Speech",
            WorkloadType.EMBEDDINGS: "Embeddings",
            WorkloadType.IMAGE_GENERATION: "Image Generation",
            WorkloadType.VISION: "Vision",
        }[self]

    @property
    def unit(self) -> str:
        """Primary throughput unit for this workload type."""
        return {
            WorkloadType.LLM: "tokens/sec",
            WorkloadType.SPEECH_TO_TEXT: "audio minutes/hour",
            WorkloadType.TEXT_TO_SPEECH: "audio seconds/minute",
            WorkloadType.EMBEDDINGS: "vectors/sec",
            WorkloadType.IMAGE_GENERATION: "images/minute",
            WorkloadType.VISION: "images/minute",
        }[self]


# Production-enabled workload types
# Only these types will be available in the recommendation engine
ENABLED_WORKLOAD_TYPES = {WorkloadType.LLM}


def is_workload_type_enabled(workload_type: WorkloadType) -> bool:
    """Check if a workload type is enabled in production.

    Args:
        workload_type: The workload type to check

    Returns:
        True if the workload type is enabled, False otherwise
    """
    return workload_type in ENABLED_WORKLOAD_TYPES


def get_enabled_workload_types() -> set[WorkloadType]:
    """Get all currently enabled workload types.

    Returns:
        Set of enabled WorkloadType values
    """
    return ENABLED_WORKLOAD_TYPES.copy()
