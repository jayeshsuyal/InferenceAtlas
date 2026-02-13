"""Stub adapter for GPT-5.2 integration."""

from __future__ import annotations

from typing import Any

from inference_atlas.llm.base import LLMAdapter
from inference_atlas.llm.schema import WorkloadSpec


class GPT52Adapter(LLMAdapter):
    """GPT-5.2 adapter stub.

    This class defines the integration boundary only. API calls are intentionally
    not implemented in Step 1.
    """

    provider_name = "gpt_5_2"

    def parse_workload(self, user_text: str) -> dict[str, Any]:
        raise NotImplementedError("GPT-5.2 adapter not configured yet.")

    def explain(self, recommendation_summary: str, workload: WorkloadSpec) -> str:
        raise NotImplementedError("GPT-5.2 adapter not configured yet.")
