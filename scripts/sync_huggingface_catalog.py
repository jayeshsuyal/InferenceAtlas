#!/usr/bin/env python3
"""Fetch and persist Hugging Face model catalog for open-source lane."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from inference_atlas.huggingface_catalog import (  # noqa: E402
    fetch_huggingface_models,
    write_huggingface_catalog,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Hugging Face model catalog")
    parser.add_argument("--limit", type=int, default=100, help="Number of models to fetch")
    parser.add_argument(
        "--task-filter",
        type=str,
        default="text-generation",
        help="Hugging Face filter param (e.g., text-generation)",
    )
    args = parser.parse_args()

    token = os.getenv("HUGGINGFACE_TOKEN")
    models = fetch_huggingface_models(
        limit=args.limit,
        task_filter=args.task_filter,
        token=token,
    )
    payload = write_huggingface_catalog(models)
    print(
        f"Saved {payload['model_count']} models to "
        f"{project_root / 'data' / 'huggingface_models.json'}"
    )


if __name__ == "__main__":
    main()
