# Data Freshness

This document covers the sync schedule, freshness SLA, and behavior when the catalog is stale.

---

## Sync Schedule

The catalog is synced automatically by a GitHub Actions workflow.

**Schedule:** Daily at **07:00 UTC**

**Workflow file:** `.github/workflows/daily-catalog-sync.yml`

**What runs:**
```bash
python scripts/sync_catalog_v2.py --providers all --fail-on-empty
```

If any data is retrieved (at least 1 row), the result is committed to `data/catalog_v2/pricing_catalog.json` and pushed to main. If the result is empty (all connectors failed), the workflow fails and the existing catalog is preserved.

---

## Manual Sync

To sync locally:

```bash
# Sync all providers
python scripts/sync_catalog_v2.py --providers all

# Sync with API secrets (for live pricing)
FAL_KEY=your-key python scripts/sync_catalog_v2.py --providers all
```

---

## Freshness Tiers

| Age | Behavior |
|---|---|
| 0–3 days | Normal — catalog freshness shown as caption |
| 4+ days | Warning banner: "Catalog is stale (N days old). Run daily sync." |
| Unknown | Warning banner: "Catalog freshness unknown. Run sync to ensure data is current." |

The freshness check runs at every page load and reads the `generated_at_utc` field from `data/catalog_v2/pricing_catalog.json`.

---

## Staleness Impact

When the catalog is stale:
- **UI still works** — all pricing data is served from the bundled snapshot
- **Recommendations still function** — no degradation in optimizer behavior
- **Prices may be outdated** — provider pricing changes are not reflected until the next sync
- **No automatic expiry** — the app never blocks on stale data

There is no automated alerting for sync failures. Monitor the GitHub Actions workflow run history for failures.

---

## Per-Provider Freshness

Each row in the catalog has a `source_date` field (ISO date string, e.g., `2026-02-16`). The catalog browser ("Browse Pricing Catalog" view) shows `latest_source_date` per provider in the provider summary table.

`source_kind` tells you how each row was populated:

| `source_kind` | Meaning | Freshness |
|---|---|---|
| `provider_api` | Fetched live from provider API during sync | Most current |
| `provider_csv` | Loaded from `data/providers_csv/` CSV file | Current as of last CSV update |
| `normalized_catalog` | From bundled normalized catalog fallback | Matches snapshot source dates |

---

## Confidence vs Freshness

`confidence` and `source_date` are separate concerns:

- **`confidence`**: Reliability of the pricing value (official docs vs estimated)
- **`source_date`**: When the data was last collected

A row can be `confidence: high` but have a stale `source_date` if it hasn't been synced recently.

---

## Freshness SLA

**Target:** Catalog age ≤ 1 day (daily sync at 07:00 UTC)

**Degraded mode:** If sync fails, the bundled snapshot is served unchanged. This is expected behavior for short outages. If sync fails for multiple consecutive days, investigate:
1. Check GitHub Actions logs for the `Daily Catalog Sync` workflow
2. Verify required secrets are configured (see [README.md](../README.md#daily-catalog-sync))
3. Run manual sync locally to identify connector-specific failures

---

## Updating CSV Files Manually

If you need to update pricing between syncs:

1. Edit the relevant file in `data/providers_csv/` (e.g., `anthropic.csv`)
2. Run `python scripts/sync_catalog_v2.py --providers all` locally
3. Commit `data/catalog_v2/pricing_catalog.json`

The sync script reads CSV files as Tier 2 fallback. If an API connector is configured and succeeds for a provider, it takes precedence over the CSV for that provider.
