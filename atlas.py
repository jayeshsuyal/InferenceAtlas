#!/usr/bin/env python3
"""CLI for the MVP planner pipeline."""

from __future__ import annotations

import argparse

from inference_atlas import rank_configs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="InferenceAtlas MVP planner CLI")
    parser.add_argument("--tokens_day", type=float, required=True, help="Daily token volume")
    parser.add_argument("--peak_to_avg", type=float, default=2.5, help="Peak-to-average multiplier")
    parser.add_argument("--model", type=str, default="70b", help="Model size bucket (e.g., 7b, 13b, 34b, 70b)")
    parser.add_argument("--top_k", type=int, default=5, help="Number of ranked plans")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plans = rank_configs(
        tokens_per_day=args.tokens_day,
        model_bucket=args.model,
        peak_to_avg=args.peak_to_avg,
        top_k=args.top_k,
    )

    print("InferenceAtlas MVP Planner")
    print(
        f"tokens/day={args.tokens_day:,.0f} model_bucket={args.model} "
        f"peak_to_avg={args.peak_to_avg} top_k={args.top_k}"
    )
    print("-" * 120)
    print(
        f"{'rank':<5} {'provider':<14} {'billing':<18} {'gpu':<18} "
        f"{'gpus':<5} {'monthly_usd':<14} {'score':<12} {'why'}"
    )
    print("-" * 120)
    for plan in plans:
        gpu = plan.gpu_type or "-"
        print(
            f"{plan.rank:<5} {plan.provider_id:<14} {plan.billing_mode:<18} {gpu:<18} "
            f"{plan.gpu_count:<5} {plan.monthly_cost_usd:<14.2f} {plan.score:<12.2f} {plan.why}"
        )


if __name__ == "__main__":
    main()
