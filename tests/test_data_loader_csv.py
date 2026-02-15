from __future__ import annotations

from inference_atlas.data_loader import (
    get_platforms,
    get_pricing_by_workload,
    get_pricing_records,
    validate_pricing_datasets,
)
from inference_atlas.workload_types import WorkloadType


def test_pricing_datasets_validate_and_load() -> None:
    counts = validate_pricing_datasets()
    assert "master_ai_pricing_dataset_16_providers.csv" in counts
    assert "ai_pricing_final_4_providers.csv" in counts
    assert counts["master_ai_pricing_dataset_16_providers.csv"] > 0
    assert counts["ai_pricing_final_4_providers.csv"] > 0


def test_workload_type_routing_filters_records() -> None:
    llm_rows = get_pricing_records(WorkloadType.LLM)
    stt_rows = get_pricing_records(WorkloadType.SPEECH_TO_TEXT)
    tts_rows = get_pricing_records("tts")
    image_rows = get_pricing_records("image_gen")
    vision_rows = get_pricing_records("vision")

    assert llm_rows
    assert stt_rows
    assert tts_rows
    assert image_rows
    assert vision_rows
    assert all(row.workload_type == WorkloadType.LLM for row in llm_rows)


def test_pricing_grouped_by_workload() -> None:
    grouped = get_pricing_by_workload()
    assert WorkloadType.LLM in grouped
    assert WorkloadType.SPEECH_TO_TEXT in grouped
    assert WorkloadType.TEXT_TO_SPEECH in grouped


def test_get_platforms_keeps_llm_compatibility() -> None:
    platforms = get_platforms()
    assert "runpod" in platforms
    assert "fireworks" in platforms
    assert "a100_80gb" in platforms["runpod"]["gpus"]
