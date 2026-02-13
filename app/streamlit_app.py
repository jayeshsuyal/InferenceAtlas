"""Streamlit UI for InferenceAtlas LLM deployment recommendations."""

from __future__ import annotations

import streamlit as st

from inference_atlas import get_recommendations
from inference_atlas.data_loader import get_models

st.set_page_config(page_title="InferenceAtlas", layout="centered")

st.title("InferenceAtlas: LLM Deployment Optimizer")
st.caption("Multi-GPU scaling + cost optimization for LLM deployments")

# Load model catalog
MODEL_REQUIREMENTS = get_models()

with st.form("inputs"):
    model_items = list(MODEL_REQUIREMENTS.items())
    default_index = next((i for i, (k, _) in enumerate(model_items) if k == "llama_70b"), 0)
    model_display_names = [v["display_name"] for _, v in model_items]
    model_key_by_display = {v["display_name"]: k for k, v in model_items}

    model_display_name = st.selectbox(
        "Model",
        options=model_display_names,
        index=default_index,
        help="Choose the LLM model you plan to deploy.",
    )
    model_key = model_key_by_display[model_display_name]

    tokens_per_day = st.number_input(
        "Traffic (tokens/day)",
        min_value=1.0,
        value=5_000_000.0,
        step=100_000.0,
        help="Total generated+processed tokens per day.",
    )

    pattern_label = st.selectbox(
        "Traffic Pattern",
        ["Steady", "Business Hours", "Bursty"],
        help="Steady: 24/7 uniform load. Business Hours: 40hrs/week. Bursty: Irregular spikes.",
    )

    latency_requirement_ms = st.number_input(
        "Latency requirement (ms, optional)",
        min_value=0.0,
        value=0.0,
        step=10.0,
        help="Set to 0 to ignore latency constraint. <300ms triggers strict latency penalties.",
    )

    submit = st.form_submit_button("Get Recommendations")

if submit:
    pattern_map = {
        "Steady": "steady",
        "Business Hours": "business_hours",
        "Bursty": "bursty",
    }
    latency = latency_requirement_ms if latency_requirement_ms > 0 else None

    try:
        recommendations = get_recommendations(
            tokens_per_day=tokens_per_day,
            pattern=pattern_map[pattern_label],
            model_key=model_key,
            latency_requirement_ms=latency,
            top_k=3,
        )
    except ValueError as exc:
        st.error(str(exc))
        recommendations = []

    if recommendations:
        st.subheader("Top 3 Recommendations")
        for rec in recommendations:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"### {rec.rank}. {rec.platform} - {rec.option}")
                    st.caption(rec.reasoning)

                with col2:
                    st.metric("Monthly Cost", f"${rec.monthly_cost_usd:,.0f}")
                    st.metric("Cost/1M Tokens", f"${rec.cost_per_million_tokens:.2f}")

                if rec.utilization_pct < 60:
                    util_label = "Low"
                elif rec.utilization_pct < 80:
                    util_label = "Moderate"
                else:
                    util_label = "High"
                st.progress(
                    min(max(rec.utilization_pct / 100, 0.0), 1.0),
                    text=f"{util_label} utilization: {rec.utilization_pct:.0f}%",
                )

                if rec.idle_waste_pct > 40:
                    potential_savings = rec.monthly_cost_usd * rec.idle_waste_pct / 100
                    st.warning(
                        f"{rec.idle_waste_pct:.0f}% idle capacity. "
                        f"Consider autoscaling to save about ${potential_savings:,.0f}/mo."
                    )

                st.divider()
else:
    st.info("Enter workload details and click Get Recommendations.")
