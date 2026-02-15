from __future__ import annotations

import inference_atlas.data_loader as dl


def test_validate_mvp_catalogs_loads_all_three() -> None:
    counts = dl.validate_mvp_catalogs(force=True)
    assert "providers.json" in counts
    assert "models.json" in counts
    assert "capacity_table.json" in counts
    assert counts["providers.json"] > 0
    assert counts["models.json"] > 0
    assert counts["capacity_table.json"] > 0


def test_get_mvp_catalog_returns_valid_object() -> None:
    providers = dl.get_mvp_catalog("providers")
    assert "providers" in providers
    assert isinstance(providers["providers"], list)
    assert providers["providers"]


def test_get_platforms_triggers_mvp_validation() -> None:
    called = {"count": 0}
    original = dl.validate_mvp_catalogs

    def wrapped(*args: object, **kwargs: object) -> dict[str, int]:
        called["count"] += 1
        return original(*args, **kwargs)

    dl.validate_mvp_catalogs = wrapped  # type: ignore[assignment]
    try:
        platforms = dl.get_platforms()
    finally:
        dl.validate_mvp_catalogs = original  # type: ignore[assignment]

    assert called["count"] >= 1
    assert platforms
