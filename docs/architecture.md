# Architecture

InferenceAtlas has two parallel processing pipelines: one for LLM workloads (capacity-aware) and one for non-LLM workloads (catalog price-based). Both share the same catalog_v2 data layer and Streamlit UI.

---

## Component Map

```
┌──────────────────────────────────────────────────────────────────┐
│  Streamlit UI  (app/streamlit_app.py)                            │
│                                                                  │
│  1. Workload selector       ← ordered_workloads from catalog     │
│  2. View selector           ← Optimize / Browse / Invoice        │
│  3. Provider multi-select   ← workload_provider_ids from catalog │
│  4. Catalog freshness badge ← get_catalog_v2_metadata()          │
└────────┬──────────────┬──────────────┬───────────────────────────┘
         │              │              │
         ▼              ▼              ▼
 ┌───────────────┐ ┌────────────┐ ┌──────────────────┐
 │ LLM Optimizer │ │  Catalog   │ │ Invoice Analyzer  │
 │  (prod)       │ │  Browser   │ │  (beta)           │
 │               │ │  (prod)    │ │                   │
 │ rank_configs()│ │ filter +   │ │ _analyze_invoice()│
 │ mvp_planner   │ │ export CSV │ │ savings vs catalog│
 └───────┬───────┘ └─────┬──────┘ └────────┬──────────┘
         │               │                  │
         └───────────────┼──────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │    Data Layer                 │
         │    data_loader.py             │
         │                               │
         │  get_catalog_v2_rows(wtype)   │
         │  get_catalog_v2_metadata()    │
         │  get_provider_compatibility() │
         └───────────────┬───────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │    catalog_v2 Pipeline        │
         │    catalog_v2/sync.py         │
         │                               │
         │  Tier 1: API connectors       │
         │    └─ fal.ai, AWS, GCP APIs   │
         │  Tier 2: Provider CSV files   │
         │    └─ data/providers_csv/     │
         │  Tier 3: Bundled snapshot     │
         │    └─ pricing_catalog.json    │
         └───────────────────────────────┘
```

---

## LLM Optimizer Pipeline (Production)

Full capacity-aware planning using `rank_configs()` in `mvp_planner.py`.

```
User inputs (tokens/day, model, traffic pattern, providers)
  │
  ▼
normalize_workload()
  ├─ avg_tok_s = tokens_per_day / 86400
  ├─ peak_tok_s = avg_tok_s × peak_to_avg
  └─ required_capacity = peak_tok_s / util_target
  │
  ▼
enumerate_configs_for_providers(model_bucket, provider_ids)
  ├─ Loads providers.json → per-billing-mode PlannerConfig objects
  ├─ Pairs *_input / *_output SKUs → blended price via output_token_ratio
  └─ Filters to requested providers
  │
  ▼
For each PlannerConfig:
  ├─ _is_feasible()           → check capacity vs required
  ├─ capacity()               → lookup tok_s from capacity_table.json
  ├─ compute_monthly_cost()   → per_token / dedicated / autoscale billing
  └─ risk_score()             → overload risk + complexity risk
  │
  ▼
Sort by score = monthly_cost × (1 + alpha × risk)
Return top_k as list[RankedPlan]
  │
  ▼
UI: ranked cards with cost, utilization, risk, assumptions
```

**Data sources used:**
- `data/providers.json` — provider offerings and pricing
- `data/capacity_table.json` — GPU throughput benchmarks
- `data/models.json` — model → size bucket mapping

---

## Non-LLM Optimizer Pipeline (Beta)

Catalog price-based ranking. No capacity modeling.

```
User inputs (workload type, providers, unit filter, usage estimate)
  │
  ▼
get_catalog_v2_rows(workload_type)
  └─ Returns CanonicalPricingRow objects for the workload
  │
  ▼
_rank_catalog_offers()
  ├─ Filter by allowed_providers
  ├─ Filter by unit_name (if selected)
  ├─ Filter by monthly_budget_max (if set)
  └─ Sort by unit_price_usd ascending
  │
  ▼
UI: table of ranked offers with optional monthly cost estimate
```

**Limitation:** This pipeline does not model throughput capacity, SLA, or latency. It is explicitly labeled beta in the UI.

---

## Invoice Analyzer Pipeline (Beta)

```
User uploads invoice CSV
  │
  ▼
_analyze_invoice(csv_bytes, all_rows)
  ├─ Parse CSV, validate required columns
  ├─ For each invoice line:
  │   ├─ Normalize workload_type alias
  │   ├─ Compute effective unit price = amount_usd / usage_qty
  │   ├─ Find catalog rows matching workload_type + unit_name
  │   ├─ Get best = min(unit_price_usd) from matching pool
  │   └─ If savings > 0: record suggestion
  └─ Sort suggestions by estimated_savings_usd desc
  │
  ▼
UI: total spend, potential savings, downloadable CSV of suggestions
```

---

## Catalog v2 Data Layer

The catalog_v2 pipeline normalizes all pricing data into a single schema.

```
scripts/sync_catalog_v2.py
  │
  ├── For each provider connector in catalog_v2/connectors/:
  │   ├─ Tier 1: fetch_rows_from_api() [if secrets present]
  │   ├─ Tier 2: fetch_rows_from_csv() [fallback]
  │   └─ Normalize to CanonicalPricingRow
  │
  ├── Merge all rows → validate schema
  └── Write → data/catalog_v2/pricing_catalog.json

CanonicalPricingRow fields:
  provider, workload_type, sku_key, sku_name, billing_mode,
  model_key, unit_price_usd, unit_name, region, source_date,
  confidence, source_kind, source_url
```

**source_kind values:**
- `provider_api` — fetched live from provider API
- `provider_csv` — loaded from provider CSV file in `data/providers_csv/`
- `normalized_catalog` — from bundled normalized catalog fallback

---

## AI Assistant Pipeline (Optional)

```
User submits question (button or chat input)
  │
  ▼
_build_catalog_context(workload, providers, rows)
  └─ Selects up to 40 catalog rows matching filters
     Formats as compact text block with provider/sku/price
  │
  ▼
LLMRouter.explain(prompt, workload_spec)
  ├─ Primary: Opus46Adapter (claude-opus-4-6)
  └─ Fallback: GPT52Adapter (gpt-5.2)
  │
  ▼
Response displayed in Streamlit
  └─ Grounded to catalog context only
```

---

## Key Files

| File | Purpose |
|---|---|
| `app/streamlit_app.py` | Entry point, all UI logic |
| `src/inference_atlas/mvp_planner.py` | LLM ranking engine (`rank_configs`) |
| `src/inference_atlas/data_loader.py` | Data access layer (catalog_v2, MVP catalogs, HF) |
| `src/inference_atlas/catalog_v2/sync.py` | Catalog sync pipeline |
| `src/inference_atlas/llm/router.py` | AI assistant router |
| `data/catalog_v2/pricing_catalog.json` | Bundled canonical catalog |
| `data/providers.json` | MVP planner provider configs |
| `data/capacity_table.json` | GPU throughput lookup table |
| `scripts/sync_catalog_v2.py` | CLI sync runner |
| `.github/workflows/daily-catalog-sync.yml` | CI sync schedule |
