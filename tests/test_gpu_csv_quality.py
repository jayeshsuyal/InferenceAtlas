from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


GPU_DIR = Path("data/providers_csv/gpu")
REQUIRED_COLUMNS = [
    "provider",
    "gpu_type",
    "billing_mode",
    "price_per_gpu_hour_usd",
    "region",
    "workload_type",
    "throughput_value",
    "throughput_unit",
    "min_gpus",
    "max_gpus",
    "startup_latency_sec",
    "source_url",
    "confidence",
    "last_verified_at",
]
ALLOWED_BILLING = {"dedicated_hourly", "autoscale_hourly"}
ALLOWED_WORKLOADS = {
    "llm",
    "embeddings",
    "speech_to_text",
    "text_to_speech",
    "vision",
    "image_generation",
    "video_generation",
    "moderation",
}
ALLOWED_CONFIDENCE = {"official", "high", "medium", "low", "estimated"}


def test_gpu_csv_files_exist() -> None:
    files = sorted(GPU_DIR.glob("*.csv"))
    assert files, "Expected GPU CSV files under data/providers_csv/gpu/"


def test_gpu_csv_headers_and_rows_are_valid() -> None:
    files = sorted(GPU_DIR.glob("*.csv"))
    assert files
    for path in files:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == REQUIRED_COLUMNS, f"{path.name} headers mismatch"
            keys: set[tuple[str, str, str, str, str]] = set()
            row_count = 0
            for line_no, row in enumerate(reader, start=2):
                row_count += 1
                provider = (row.get("provider") or "").strip()
                gpu_type = (row.get("gpu_type") or "").strip()
                billing_mode = (row.get("billing_mode") or "").strip()
                workload_type = (row.get("workload_type") or "").strip()
                region = (row.get("region") or "").strip()
                source_url = (row.get("source_url") or "").strip()
                confidence = (row.get("confidence") or "").strip()
                verified_at = (row.get("last_verified_at") or "").strip()

                assert provider, f"{path.name}:{line_no} missing provider"
                assert gpu_type, f"{path.name}:{line_no} missing gpu_type"
                assert billing_mode in ALLOWED_BILLING, f"{path.name}:{line_no} invalid billing_mode"
                assert workload_type in ALLOWED_WORKLOADS, f"{path.name}:{line_no} invalid workload_type"
                assert region, f"{path.name}:{line_no} missing region"
                assert source_url.startswith("http"), f"{path.name}:{line_no} invalid source_url"
                assert confidence in ALLOWED_CONFIDENCE, f"{path.name}:{line_no} invalid confidence"
                datetime.strptime(verified_at, "%Y-%m-%d")

                price = float((row.get("price_per_gpu_hour_usd") or "").strip())
                assert price > 0, f"{path.name}:{line_no} non-positive price"

                min_gpus_raw = (row.get("min_gpus") or "").strip()
                max_gpus_raw = (row.get("max_gpus") or "").strip()
                assert min_gpus_raw, f"{path.name}:{line_no} missing min_gpus"
                min_gpus = int(min_gpus_raw)
                assert min_gpus >= 1, f"{path.name}:{line_no} min_gpus must be >= 1"
                if max_gpus_raw:
                    max_gpus = int(max_gpus_raw)
                    assert max_gpus >= min_gpus, f"{path.name}:{line_no} max_gpus < min_gpus"

                key = (provider, gpu_type, billing_mode, region, workload_type)
                assert key not in keys, f"{path.name}:{line_no} duplicate key {key}"
                keys.add(key)

            assert row_count >= 1, f"{path.name} has no data rows"
