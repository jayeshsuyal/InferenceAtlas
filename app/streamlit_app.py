"""Streamlit UI for InferenceAtlas LLM deployment recommendations."""

from __future__ import annotations

import streamlit as st

from inference_atlas import get_recommendations
from inference_atlas.data_loader import get_models
from inference_atlas.llm import LLMRouter, WorkloadSpec

st.set_page_config(page_title="InferenceAtlas", layout="centered")

st.title("InferenceAtlas: LLM Deployment Optimizer")
st.caption("Multi-GPU scaling + cost optimization for LLM deployments")

# Load model catalog
MODEL_REQUIREMENTS = get_models()

with st.expander("Or describe your workload in plain English"):
    user_text = st.text_area(
        "Describe your LLM deployment needs",
        placeholder=(
            "e.g., Chat app with 10k daily users, steady traffic, Llama 70B, "
            "need <200ms latency"
        ),
        height=100,
        key="ai_parse_input_text",
    )
    if st.button("Parse with AI"):
        try:
            router = LLMRouter()
            parsed = router.parse_workload(user_text)
            st.session_state["parsed_workload"] = {
                "tokens_per_day": parsed.tokens_per_day,
                "pattern": parsed.pattern,
                "model_key": parsed.model_key,
                "latency_requirement_ms": parsed.latency_requirement_ms,
            }
            st.success("Parsed successfully.")
            st.json(st.session_state["parsed_workload"])
        except Exception as exc:  # noqa: BLE001 - user-facing parser message
            st.error(f"Parsing failed: {exc}")

parsed_workload = st.session_state.get("parsed_workload", {})
pattern_to_label = {
    "steady": "Steady",
    "business_hours": "Business Hours",
    "bursty": "Bursty",
}
label_to_pattern = {
    "Steady": "steady",
    "Business Hours": "business_hours",
    "Bursty": "bursty",
}

with st.form("inputs"):
    model_items = list(MODEL_REQUIREMENTS.items())
    default_model_key = str(parsed_workload.get("model_key", "llama_70b"))
    default_index = next((i for i, (k, _) in enumerate(model_items) if k == default_model_key), 0)
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
        value=float(parsed_workload.get("tokens_per_day", 5_000_000.0)),
        step=100_000.0,
        help="Total generated+processed tokens per day.",
    )

    pattern_label = st.selectbox(
        "Traffic Pattern",
        ["Steady", "Business Hours", "Bursty"],
        index=["Steady", "Business Hours", "Bursty"].index(
            pattern_to_label.get(str(parsed_workload.get("pattern", "steady")), "Steady")
        ),
        help="Steady: 24/7 uniform load. Business Hours: 40hrs/week. Bursty: Irregular spikes.",
    )

    latency_requirement_ms = st.number_input(
        "Latency requirement (ms, optional)",
        min_value=0.0,
        value=float(parsed_workload.get("latency_requirement_ms") or 0.0),
        step=10.0,
        help="Set to 0 to ignore latency constraint. <300ms triggers strict latency penalties.",
    )

    submit = st.form_submit_button("Get Recommendations")

if submit:
    latency = latency_requirement_ms if latency_requirement_ms > 0 else None
    effective_workload = WorkloadSpec(
        tokens_per_day=float(tokens_per_day),
        pattern=label_to_pattern[pattern_label],
        model_key=model_key,
        latency_requirement_ms=latency,
    )
    st.session_state["last_workload"] = effective_workload

    try:
        recommendations = get_recommendations(
            tokens_per_day=effective_workload.tokens_per_day,
            pattern=effective_workload.pattern,
            model_key=effective_workload.model_key,
            latency_requirement_ms=effective_workload.latency_requirement_ms,
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
        if st.button("Explain this recommendation"):
            try:
                router = LLMRouter()
                top_rec = recommendations[0]
                summary = (
                    f"{top_rec.platform} - {top_rec.option}, "
                    f"${top_rec.monthly_cost_usd:.0f}/mo, "
                    f"{top_rec.utilization_pct:.0f}% util"
                )
                explanation = router.explain(summary, effective_workload)
                st.info(explanation)
            except Exception as exc:  # noqa: BLE001 - user-facing parser message
                st.error(f"Explanation failed: {exc}")
else:
    st.info("Enter workload details and click Get Recommendations.")
