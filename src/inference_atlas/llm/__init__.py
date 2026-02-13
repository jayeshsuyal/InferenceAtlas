"""LLM adapter layer for workload parsing and recommendation explanations."""

from inference_atlas.llm.base import LLMAdapter
from inference_atlas.llm.opus_4_6_adapter import Opus46Adapter
from inference_atlas.llm.gpt_5_2_adapter import GPT52Adapter
from inference_atlas.llm.router import LLMRouter, RouterConfig
from inference_atlas.llm.service import ParseWorkloadResult, parse_workload_text
from inference_atlas.llm.schema import WorkloadSpec, validate_workload_payload

__all__ = [
    "LLMAdapter",
    "GPT52Adapter",
    "Opus46Adapter",
    "LLMRouter",
    "RouterConfig",
    "ParseWorkloadResult",
    "parse_workload_text",
    "WorkloadSpec",
    "validate_workload_payload",
]
