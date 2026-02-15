from __future__ import annotations

from inference_atlas.data_loader import get_huggingface_models, validate_huggingface_catalog


def test_validate_huggingface_catalog_file() -> None:
    count = validate_huggingface_catalog(force=True)
    assert count >= 0


def test_get_huggingface_models_returns_list() -> None:
    rows = get_huggingface_models()
    assert isinstance(rows, list)
