from __future__ import annotations

import json

from inference_atlas.huggingface_catalog import (
    _extract_context_len,
    _extract_license,
    _infer_size_bucket,
    fetch_huggingface_models,
)


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def test_infer_size_bucket_from_model_id() -> None:
    assert _infer_size_bucket("meta-llama/Llama-2-7b-hf", []) == "7b"
    assert _infer_size_bucket("meta-llama/Llama-3.1-70B-Instruct", []) == "70b"
    assert _infer_size_bucket("foo/bar", ["34b"]) == "34b"


def test_extract_license_and_context_len() -> None:
    tags = ["license:apache-2.0", "context_length:32768"]
    assert _extract_license(tags) == "apache-2.0"
    assert _extract_context_len(tags) == 32768


def test_fetch_huggingface_models_parses_api_payload(monkeypatch: object) -> None:
    payload = [
        {
            "id": "meta-llama/Llama-2-7b-hf",
            "pipeline_tag": "text-generation",
            "downloads": 123456,
            "likes": 7890,
            "tags": ["license:apache-2.0", "context_length:4096", "llama"],
            "private": False,
            "gated": False,
            "lastModified": "2026-01-01T00:00:00.000Z",
        }
    ]

    def fake_urlopen(*_args: object, **_kwargs: object) -> _FakeResponse:
        return _FakeResponse(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("inference_atlas.huggingface_catalog.urlopen", fake_urlopen)
    models = fetch_huggingface_models(limit=1)
    assert len(models) == 1
    row = models[0]
    assert row["model_id"] == "meta-llama/Llama-2-7b-hf"
    assert row["downloads"] == 123456
    assert row["size_bucket"] == "7b"
    assert row["license"] == "apache-2.0"
