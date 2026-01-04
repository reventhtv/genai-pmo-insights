import streamlit as st
import json
import os

from services.analysis_service import analyze_update
from services.comparison_service import compare_updates


# -----------------------------
# Helpers (UI-only, deterministic)
# -----------------------------

def build_demo_weeks(start_year=2026, start_week=1, count=5):
    """
    Build consecutive ISO week labels for demo / replay.
    Example: 2026-W01, 2026-W02, ...
    """
    return [
        f"{start_year}-W{start_week + i:02d}"
        for i in range(count)
    ]


def load_current_memory(project_id="default"):
    path = os.path.join("memory", f"project_{project_id}.json")
    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)


def build_confidence_narrative(risk, current_period):
    confidence = risk.get("confidence", {}).get("level")
    resolution = risk.get("resolution", {})
    resolved_period = resolution.get("resolved_period")

    # Show resolved risks only once
    if resolution.get("is_resolved"):
        if resolved_period == current_period:
            return (
                "The risk is considered resolved following sustained absence "
                "and declining signals."
            )
        return None

    if confidence == "High":
        return (
            "Confidence remains high due to persistent or escalating signals "
            "across recent updates."
        )

    if confidence == "Medium":
        return (
            "Confidence is moderating as the risk shows signs of stabilization "
            "without recent escalation."
        )

    if confidence == "Low":
        return (
            "Confidence is declining as the risk has not been observed in "
            "recent updates."
        )

    return None


def build_confidence_trend(risk, recent_periods):
    """
    Reconstruct confidence trend for the last N periods (max 5),
    using deterministic replay rules aligned with memory v1.3.
    """
    periods_seen = set(risk.get("periods_seen", []))
    severity = risk.get("heat_history", ["Low"])[-1]

    trend = []
    absence = 0

    for period in recent_periods:
        if period in periods_seen:
            absence = 0
            level = "High"
        else:
            absence += 1
            # Severity-weighted decay (same philosophy as memory)
            if severity == "High":
                level = "Medium" if absence < 3 else "Low"
            elif severity == "Medium":
                level = "Medium" if absence < 2 else "Low"
            else:
                level = "Low"

        trend.append(level)

    return trend


def render_confidence_strip(trend):
    """
    Render confidence trend as a Streamlit-safe text strip.
    """
    return " → ".join(f"[{level}]" for level in trend)


# -----------------------------
# Session State Init
# -----------------------------

if "show_demo_hint" not in st.session_state:
    st.session_state.show_demo_hint = False

if "demo_weeks" not in st.session_state:
    st.session_state.demo_weeks = []

if "comparison" not in st.session_state:
    st.session_state.comparison = None


# -----------------------------
# Page Header
# -----------------------------

st.title("📊 Update Comparison")
st.caption(
    "Understand how risks, escalation and priorities evolve across stakeholder updates."
)

st.divider()


# -----------------------------
# Upload Section
# -----------------------------

uploaded_files = st.file_uploader(
    "Upload 2–5 stakeholder updates (.txt)",
    type=["txt"],
    accept_multiple_files=True
)

if uploaded_files:
    if len(uploaded_files) < 2:
        st.warning("Please upload at least two stakeholder updates.")
        st.stop()

    if len(uploaded_files) > 5:
        st.warning("Please upload a maximum of five updates.")
        st.stop()

    if st.button("Analyze Updates"):
        # ----------------------------------
        # Option A: Explicit demo weeks
        # ----------------------------------
        st.session_state.demo_weeks = build_demo_weeks(
            count=len(uploaded_files)
        )
        st.session_state.show_demo_hint = True

        analyzed_updates = []

        with st.spinner("Analyzing and comparing updates..."):
            for idx, file in enumerate(uploaded_files):
                text = file.read().decode("utf-8")
                period_id = st.session_state.demo_weeks[idx]

                analysis = analyze_update(
                    text,
                    period_id=period_id
                )

                analyzed_updates.append(analysis)

            st.session_state.comparison = compare_updates(analyzed_updates)


# -----------------------------
# Persistent UI Hint
# -----------------------------

if st.session_state.show_demo_hint:
    demo_weeks = st.session_state.demo_weeks
    st.info(
        f"🕒 Demo mode: Updates are analyzed as consecutive ISO weeks "
        f"({demo_weeks[0]} → {demo_weeks[-1]}), based on upload order."
    )


# -----------------------------
# Render Results (Persistent)
# -----------------------------

if st.session_state.comparison:
    comparison = st.session_state.comparison

    st.divider()

    # -----------------------------
    # Last Update Comparison
    # -----------------------------
    with st.expander("🔍 Last Update Comparison", expanded=False):
        prev = comparison["snapshot"]["previous"]
        curr = comparison["snapshot"]["current"]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Previous Update**")
            st.write(f"Escalation: {'🚨' if prev['escalation'] else '❌'}")
            st.write(f"Highest Risk Heat: {prev['highest_risk_heat']}")
            st.write(f"Top Risk: {prev['top_risk']}")

        with col2:
            st.markdown("**Current Update**")
            st.write(f"Escalation: {'🚨' if curr['escalation'] else '❌'}")
            st.write(f"Highest Risk Heat: {curr['highest_risk_heat']}")
            st.write(f"Top Risk: {curr['top_risk']}")

    st.divider()

    # -----------------------------
    # What Changed
    # -----------------------------
    st.subheader("📈 What Changed Since Last Update")

    changes = comparison["change_summary"]

    if (
        not changes["new"]
        and not changes["escalated"]
        and not changes["de_escalated"]
    ):
        st.write("No material changes detected.")
    else:
        for item in changes["new"]:
            st.markdown(f"🆕 New risk introduced: **{item}**")

        for item in changes["escalated"]:
            st.markdown(f"🔺 Risk escalated: **{item}**")

        for item in changes["de_escalated"]:
            st.markdown(f"🔻 Risk de-escalated: **{item}**")

    # -----------------------------
    # Trend-Based Escalation
    # -----------------------------
    if comparison["trend_escalation"]:
        st.divider()
        st.subheader("🚨 Escalation (Trend-Based)")
        for item in comparison["trend_escalation"]:
            st.markdown(f"- {item}")

    st.divider()

    # -----------------------------
    # Risk Comparison Table
    # -----------------------------
    with st.expander("📊 Risk Comparison Details", expanded=False):
        table = comparison["risk_comparison_table"]

        for row in table:
            row["Risk Trend"] = row.pop("trend")

            for key in list(row.keys()):
                if key.startswith("U"):
                    week_no = key.replace("U", "")
                    row[f"Week {week_no}"] = row.pop(key)

        st.dataframe(table, width="stretch")

    # -----------------------------
    # Risk Confidence Assessment + v1.4 Trends
    # -----------------------------
    st.divider()
    st.subheader("📌 Risk Confidence Assessment")

    memory = load_current_memory()
    risks = memory.get("risks", {})
    all_periods = st.session_state.demo_weeks[-5:]
    current_period = memory.get("last_updated_period")

    shown_any = False

    for risk in risks.values():
        narrative = build_confidence_narrative(risk, current_period)

        if narrative:
            shown_any = True
            risk_name = risk["risk_id"].replace("_", " ").title()
            st.markdown(f"**{risk_name}**")
            st.write(narrative)

            trend = build_confidence_trend(risk, all_periods)
            st.caption(
                "Confidence Trend (last "
                f"{len(all_periods)} periods):"
            )
            st.code(render_confidence_strip(trend), language="text")

    if not shown_any:
        st.write(
            "No active or recently resolved risks require confidence assessment."
        )

    st.divider()

    # -----------------------------
    # Leadership Narrative
    # -----------------------------
    st.subheader("🧭 Leadership Summary")
    st.write(comparison["leadership_summary"])
