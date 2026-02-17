# AI Assistant

InferenceAtlas includes two AI-powered features: the **AI Suggest** panel and the **Ask IA AI** chat. Both are optional and require an API key. The app runs fully without AI.

---

## Feature Overview

| Feature | Location | What It Does |
|---|---|---|
| AI Suggest next steps | "AI Assistant" expander (top section) | Answers a one-shot question grounded in current catalog data |
| Ask IA AI chat | Bottom of the page (persistent) | Conversational interface for follow-up questions |

For Streamlit versions that do not support `st.chat_input`, the chat automatically falls back to a text input + Send button.

Both features use the same underlying pipeline: catalog context injection + LLM call.

---

## Required API Keys

Set at least one of these environment variables before running the app:

```bash
export OPENAI_API_KEY=sk-...
# or
export ANTHROPIC_API_KEY=sk-ant-...
```

If neither key is set:
- The "AI Suggest" button is disabled with a caption explaining the requirement
- The "Ask IA AI" chat responds with a static message: "AI is disabled. Set OPENAI_API_KEY or ANTHROPIC_API_KEY to use Ask IA AI."
- No error is shown; the app continues to function normally

---

## Model Routing

AI features use `LLMRouter` with a primary/fallback strategy:

| Priority | Provider | Model | Trigger |
|---|---|---|---|
| Primary | Anthropic | claude-opus-4-6 | First attempt |
| Fallback | OpenAI | gpt-5.2 | If primary fails or key absent |

If both fail, the error is shown in the UI.

**Configuration:** `LLMRouter(config=RouterConfig(primary_provider="opus_4_6", fallback_provider="gpt_5_2"))`

---

## Grounding Behavior

All AI responses are grounded in current catalog data. Grounding is enforced via the system prompt:

```
You are IA AI. Use ONLY the provided catalog context.
If data is missing, say "not available in current catalog".
Do not invent providers/SKUs/prices.
```

**What is injected into every prompt:**
- The selected workload type (`selected_workload`)
- The selected providers (`selected_global_providers`)
- Up to 40 catalog rows matching the current filters, sorted by unit price
- The current view mode (`page_mode`)
- The top ranked plan (if a recommendation has been run)

**What the AI is allowed to cite:**
- Providers, SKU names, and prices from the injected catalog context
- General reasoning about workload trade-offs

**What the AI should not do:**
- Invent providers, SKUs, or prices not in the context
- Claim to have real-time pricing data
- Make binding cost estimates outside catalog data

---

## Catalog Context Format

The catalog context passed to the AI looks like:

```
workload=llm
providers=anthropic,fireworks,openai
rows_total=47
units=1m_tokens
rows_sample_start
anthropic|claude-haiku-4-5|claude_haiku_4_5|per_token|0.25|1m_tokens|global|high|csv
fireworks|llama-v3p3-70b-instruct|llama_3_3_70b|per_token|0.9|1m_tokens|global|high|csv
openai|gpt-4o-mini|gpt_4o_mini|per_token|0.15|1m_tokens|global|high|api
rows_sample_end
```

Format per row: `provider|sku_name|model_key|billing_mode|unit_price_usd|unit_name|region|confidence|source_kind`

Up to 40 rows are included, sorted by `unit_price_usd`. If the filtered result exceeds 40 rows, only the 40 cheapest are included.

---

## Chat History

The **Ask IA AI** chat maintains conversation history in `st.session_state["ia_chat_history"]`. The last 6 messages are displayed and included in subsequent prompts.

History is scoped to the current browser session and is cleared on page refresh.

---

## No-Hallucination Guardrails

The AI prompt explicitly prohibits invented data. However, LLMs are probabilistic and can still produce inaccurate responses. Treat AI suggestions as directional guidance, not authoritative pricing.

**Always verify** specific prices against the catalog browser or provider websites before making infrastructure decisions.

---

## When AI Features Are Not Useful

- For browsing catalog data: use the **Browse Pricing Catalog** view directly
- For finding cheapest options: use **Optimize Workload** or the price-sorted catalog table
- For invoice analysis: use the **Invoice Analyzer** — it does exact catalog matching without LLM inference

AI features add value for: explaining trade-offs, suggesting which providers to consider, interpreting results, and answering open-ended "what should I do?" questions.
