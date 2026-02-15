from __future__ import annotations

import warnings

from inference_atlas import get_recommendations, rank_configs


def test_legacy_and_mvp_engines_both_return_valid_outputs() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        legacy = get_recommendations(
            tokens_per_day=5_000_000,
            pattern="steady",
            model_key="llama_70b",
            top_k=3,
        )

    mvp = rank_configs(
        tokens_per_day=5_000_000,
        model_bucket="70b",
        peak_to_avg=1.5,
        top_k=3,
    )

    assert legacy
    assert mvp
    assert len(legacy) <= 3
    assert len(mvp) <= 3
    assert all(row.monthly_cost_usd > 0 for row in legacy)
    assert all(row.monthly_cost_usd > 0 for row in mvp)

    legacy_top = legacy[0].monthly_cost_usd
    mvp_top = mvp[0].monthly_cost_usd
    ratio = max(legacy_top, mvp_top) / min(legacy_top, mvp_top)
    assert ratio < 50.0
