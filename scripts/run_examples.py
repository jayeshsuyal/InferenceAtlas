#!/usr/bin/env python3
"""Run all example scenarios and print recommendations.

This script loads JSON scenario files from examples/ and runs the recommendation
engine for each, displaying top-3 results with cost and utilization metrics.

Usage:
    python scripts/run_examples.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from inference_atlas import get_recommendations


def load_scenario(filepath: Path) -> dict:
    """Load scenario JSON file."""
    with open(filepath) as f:
        return json.load(f)


def run_scenario(scenario: dict) -> None:
    """Run recommendation engine for one scenario."""
    print(f"\n{'=' * 80}")
    print(f"Scenario: {scenario['name']}")
    print(f"{'=' * 80}")
    print(f"Description: {scenario['description']}")
    print(f"\nInputs:")
    print(f"  Model: {scenario['model']}")
    print(f"  Tokens/day: {scenario['tokens_per_day']:,}")
    print(f"  Traffic pattern: {scenario['traffic_pattern']}")
    print(f"  Latency requirement: {scenario['latency_requirement_ms']} ms" if scenario['latency_requirement_ms'] else "  Latency requirement: None")

    try:
        recommendations = get_recommendations(
            tokens_per_day=scenario['tokens_per_day'],
            pattern=scenario['traffic_pattern'],
            model_key=scenario['model'],
            latency_requirement_ms=scenario['latency_requirement_ms'],
            top_k=3,
        )

        print(f"\nTop 3 Recommendations:")
        print(f"{'-' * 80}")
        for rec in recommendations:
            print(f"\n{rec.rank}. {rec.platform} - {rec.option}")
            print(f"   Reasoning: {rec.reasoning}")
            print(f"   Monthly cost: ${rec.monthly_cost_usd:,.0f}")
            print(f"   Cost/1M tokens: ${rec.cost_per_million_tokens:.2f}")
            print(f"   Utilization: {rec.utilization_pct:.0f}%")
            print(f"   Idle waste: {rec.idle_waste_pct:.0f}%")

    except ValueError as exc:
        print(f"\n❌ Error: {exc}")


def main() -> None:
    """Run all example scenarios."""
    examples_dir = project_root / "examples"

    # Find all JSON files
    scenarios = sorted(examples_dir.glob("scenario_*.json"))

    if not scenarios:
        print("No scenario files found in examples/")
        sys.exit(1)

    print("InferenceAtlas Example Runner")
    print(f"Running {len(scenarios)} scenarios...\n")

    for scenario_file in scenarios:
        scenario = load_scenario(scenario_file)
        run_scenario(scenario)

    print(f"\n{'=' * 80}")
    print("All scenarios complete.")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
