# GPUSelector

GPUSelector is an MVP LLM deployment optimizer that helps developers choose the right GPU platform using workload-driven recommendations and monthly cost estimates.

## Features

- Pricing + GPU catalog across multiple providers
- Traffic pattern modeling (`steady`, `business_hours`, `bursty`)
- Billing-aware monthly cost calculator
- Top-3 recommendation engine with brief reasoning
- Minimal Streamlit UI

## Project Structure

```text
gpuselector/
├── data/
│   ├── platforms.py
│   └── performance.py
├── core/
│   ├── utilization.py
│   ├── cost_calculator.py
│   └── recommender.py
├── ui/
│   └── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Quickstart

```bash
cd gpuselector
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run ui/app.py
```

## Inputs (MVP)

- Model: Llama-70B (hardcoded)
- Traffic: tokens/day
- Pattern: Steady, Business Hours, Bursty
- Latency requirement (optional)

## Cost Logic

- Autoscaling: `active_hours * hourly_rate`
- Dedicated/per-second/hourly/hourly-variable: `730 * hourly_rate`
- Per-token: `(monthly_tokens / 1_000_000) * price_per_m_tokens`

## Notes

- Pricing values are set to the user-provided verified dataset (Feb 2025).
- Recommendation quality is intended for initial planning and should be validated with provider-specific benchmarks.
