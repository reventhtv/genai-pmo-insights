import streamlit as st

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
        with st.spinner("Analyzing and comparing updates..."):
            analyzed_updates = []

            # -----------------------------
            # Option A: Explicit demo weeks
            # -----------------------------
            demo_weeks = build_demo_weeks(
                count=len(uploaded_files)
            )

            # UI hint (explicit but lightweight)
            st.info(
                f"🕒 Demo mode: Updates are analyzed as consecutive ISO weeks "
                f"({demo_weeks[0]} → {demo_weeks[-1]}), based on upload order."
            )

            # -----------------------------
            # Step 1: Analyze each update
            # -----------------------------
            for idx, file in enumerate(uploaded_files):
                text = file.read().decode("utf-8")
                period_id = demo_weeks[idx]

                analysis = analyze_update(
                    text,
                    period_id=period_id
                )

                analyzed_updates.append(analysis)

            # -----------------------------
            # Step 2: Run comparison
            # -----------------------------
            comparison = compare_updates(analyzed_updates)

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

            # UX-friendly column names
            for row in table:
                row["Risk Trend"] = row.pop("trend")

                for key in list(row.keys()):
                    if key.startswith("U"):
                        week_no = key.replace("U", "")
                        row[f"Week {week_no}"] = row.pop(key)

            st.dataframe(table, width="stretch")

        st.divider()

        # -----------------------------
        # Leadership Narrative
        # -----------------------------
        st.subheader("🧭 Leadership Summary")
        st.write(comparison["leadership_summary"])
