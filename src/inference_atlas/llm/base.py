"""Provider-agnostic interface for LLM adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from inference_atlas.llm.schema import WorkloadSpec


class LLMAdapter(ABC):
    """Contract for any LLM backend integrated with InferenceAtlas."""

    provider_name: str

    @abstractmethod
    def parse_workload(self, user_text: str) -> dict[str, Any]:
        """Return structured payload extracted from free-form user text."""

    @abstractmethod
    def explain(self, recommendation_summary: str, workload: WorkloadSpec) -> str:
        """Return plain-language explanation for deterministic recommendation outputs."""
