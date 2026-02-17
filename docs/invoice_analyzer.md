# Invoice Analyzer

The Invoice Analyzer is a **beta** feature that compares your current spending against the cheapest equivalent options in the InferenceAtlas catalog. It does not make purchasing recommendations — it surfaces where your effective unit price exceeds the market rate.

---

## Input CSV Schema

The analyzer requires a CSV file with these exact column names:

| Column | Type | Required | Description |
|---|---|---|---|
| `provider` | string | Yes | Provider name (e.g., `openai`, `anthropic`) |
| `workload_type` | string | Yes | Workload category (see aliases table) |
| `usage_qty` | float | Yes | Units consumed (must be > 0) |
| `usage_unit` | string | Yes | Unit of measure (must match catalog `unit_name`) |
| `amount_usd` | float | Yes | Total amount billed in USD (must be > 0) |

Additional columns are allowed and ignored.

**Example CSV:**
```csv
provider,workload_type,usage_qty,usage_unit,amount_usd
openai,llm,10000000,1m_tokens,150.00
anthropic,llm,5000000,1m_tokens,75.00
elevenlabs,text_to_speech,500000,1k_chars,80.00
deepgram,speech_to_text,1000,audio_hour,35.00
openai,image_generation,2000,image,80.00
```

---

## Workload Type Aliases

The `workload_type` column accepts these values (case-insensitive):

| Input value | Resolved to |
|---|---|
| `llm` | `llm` |
| `speech_to_text`, `transcription`, `stt` | `speech_to_text` |
| `text_to_speech`, `tts` | `text_to_speech` |
| `embeddings`, `embedding`, `rerank` | `embeddings` |
| `image_generation`, `image_gen` | `image_generation` |
| `vision` | `vision` |
| `video_generation` | `video_generation` |
| `moderation` | `moderation` |

Unrecognized values are passed through as-is. If no catalog rows match, that invoice line is skipped.

---

## Matching Logic

For each invoice line:

1. **Parse** `usage_qty` and `amount_usd` (skip lines with invalid values or zeros)
2. **Compute** effective unit price: `amount_usd / usage_qty`
3. **Find** catalog rows where `workload_type` matches AND `unit_name` matches `usage_unit`
4. **Get** the cheapest match: `min(unit_price_usd)` from the matching pool
5. **Compute** savings: `(effective_unit_price - cheapest_unit_price) × usage_qty`
6. **Skip** lines where savings ≤ 0 (you are already paying at or below market rate)

Results are sorted by `estimated_savings_usd` descending.

---

## Output Fields

Each suggestion row contains:

| Field | Description |
|---|---|
| `invoice_line` | Row number in uploaded CSV (starting from 2, header is 1) |
| `current_provider` | Provider from the invoice |
| `workload_type` | Resolved canonical workload type |
| `usage_qty` | Units consumed |
| `usage_unit` | Unit of measure |
| `amount_usd` | Amount billed |
| `effective_unit_price` | Your effective rate (`amount_usd / usage_qty`) |
| `best_provider` | Cheapest catalog provider for this workload + unit |
| `best_offering` | Cheapest catalog offering (SKU name) |
| `best_unit_price` | Cheapest unit price found in catalog |
| `estimated_savings_usd` | `(effective - best) × usage_qty` |
| `savings_pct` | `(savings / amount_usd) × 100` |
| `source_kind` | How the best offer's price was sourced (`provider_api`, `provider_csv`, `normalized_catalog`) |

The top 25 suggestions are shown in the UI. The full list is available via the download button.

---

## Summary Metrics

The UI shows two summary metrics:

- **Invoice Spend**: Total `amount_usd` across all valid invoice lines
- **Potential Savings**: Total `estimated_savings_usd` across all lines with positive savings

These are upper bounds on savings — actual savings depend on provider switching feasibility, volume discounts, and contractual commitments.

---

## Limitations

**Unit name matching is exact.** If your invoice uses `audio-hour` but the catalog uses `audio_hour`, no match is found. Check catalog unit names in the Browse Pricing Catalog view before uploading.

**No volume discount modeling.** Catalog prices are on-demand rates. Committed-use or volume discount pricing is not reflected.

**No multi-provider blending.** Each invoice line is matched independently. The analyzer does not suggest splitting workloads across providers.

**Savings are estimates only.** The effective unit price calculation assumes uniform pricing per unit within a billing period. Tiered pricing (e.g., OpenAI's batch discount tiers) is not modeled.

**Catalog freshness applies.** If the catalog is stale, the "best price" comparison may not reflect current market rates. Check the freshness indicator on the main page.

**Per-provider context is not available.** The analyzer does not know your contract terms, volume discounts, or committed-use credits.

---

## Common Issues

**"Invoice CSV missing required columns"** — Your CSV is missing one or more of: `provider`, `workload_type`, `usage_qty`, `usage_unit`, `amount_usd`.

**"No savings opportunities found"** — Either all your effective rates are already at or below catalog market rates, or no catalog rows matched your `workload_type` + `usage_unit` combinations. Check the Browse Catalog view to confirm your units exist in the catalog.

**Empty results for some lines** — Lines with `usage_qty <= 0` or `amount_usd <= 0` are silently skipped. Lines where no catalog match exists for the workload/unit pair are also skipped.
