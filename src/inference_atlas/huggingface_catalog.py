"""Hugging Face model catalog ingestion via official API."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HUGGINGFACE_MODELS_API = "https://huggingface.co/api/models"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parents[2] / "data" / "huggingface_models.json"


def _infer_size_bucket(model_id: str, tags: list[str]) -> str:
    candidates = [model_id, *tags]
    text = " ".join(candidates).lower()
    if "405b" in text:
        return "405b"
    if any(token in text for token in ("70b", "72b", "65b")):
        return "70b"
    if any(token in text for token in ("34b", "32b", "30b")):
        return "34b"
    if any(token in text for token in ("13b", "14b", "15b")):
        return "13b"
    if any(token in text for token in ("7b", "8b", "9b")):
        return "7b"
    return "other"


def _extract_license(tags: list[str]) -> str | None:
    for tag in tags:
        if tag.startswith("license:"):
            return tag.split(":", 1)[1].strip() or None
    return None


def _extract_context_len(tags: list[str]) -> int | None:
    prefixes = ("context_length:", "context-length:")
    for tag in tags:
        lowered = tag.lower()
        if lowered.startswith(prefixes):
            _, value = lowered.split(":", 1)
            value = value.strip().replace("_", "")
            if value.isdigit():
                return int(value)
    return None


def fetch_huggingface_models(
    limit: int = 100,
    task_filter: str = "text-generation",
    timeout_sec: float = 20.0,
    token: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch model metadata from Hugging Face models API."""
    if limit < 1:
        raise ValueError("limit must be >= 1")
    if timeout_sec <= 0:
        raise ValueError("timeout_sec must be > 0")

    query = urlencode(
        {
            "filter": task_filter,
            "sort": "downloads",
            "direction": "-1",
            "limit": str(limit),
            "full": "true",
            "cardData": "true",
        }
    )
    url = f"{HUGGINGFACE_MODELS_API}?{query}"
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url=url, headers=headers)
    with urlopen(request, timeout=timeout_sec) as response:  # noqa: S310 - fixed trusted host
        payload = json.loads(response.read().decode("utf-8"))

    if not isinstance(payload, list):
        raise ValueError("Unexpected Hugging Face API response: expected a list")

    models: list[dict[str, Any]] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        model_id = str(row.get("id", "")).strip()
        if not model_id:
            continue
        tags = [str(tag) for tag in row.get("tags", []) if isinstance(tag, str)]

        model = {
            "model_id": model_id,
            "pipeline_tag": str(row.get("pipeline_tag", "")).strip() or None,
            "downloads": int(row.get("downloads") or 0),
            "likes": int(row.get("likes") or 0),
            "license": _extract_license(tags),
            "context_length": _extract_context_len(tags),
            "size_bucket": _infer_size_bucket(model_id=model_id, tags=tags),
            "private": bool(row.get("private", False)),
            "gated": bool(row.get("gated", False)),
            "tags": tags[:30],
            "last_modified": str(row.get("lastModified", "")).strip() or None,
            "source_url": f"https://huggingface.co/{model_id}",
            "confidence": "vendor_listed",
        }
        models.append(model)

    return models


def write_huggingface_catalog(
    models: list[dict[str, Any]],
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict[str, Any]:
    """Write Hugging Face model catalog to disk."""
    payload = {
        "schema_version": "1.0.0",
        "source": "huggingface_api",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_count": len(models),
        "models": models,
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
