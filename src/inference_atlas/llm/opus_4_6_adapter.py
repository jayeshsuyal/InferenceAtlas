"""Stub adapter for Opus 4.6 integration."""

from __future__ import annotations

from typing import Any

from inference_atlas.llm.base import LLMAdapter
from inference_atlas.llm.schema import WorkloadSpec


class Opus46Adapter(LLMAdapter):
    """Opus 4.6 adapter stub.

    This class defines the integration boundary only. API calls are intentionally
    not implemented in Step 1.
    """

    provider_name = "opus_4_6"

    def parse_workload(self, user_text: str) -> dict[str, Any]:
        raise NotImplementedError("Opus 4.6 adapter not configured yet.")

    def explain(self, recommendation_summary: str, workload: WorkloadSpec) -> str:
        raise NotImplementedError("Opus 4.6 adapter not configured yet.")
