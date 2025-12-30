import streamlit as st

from services.analysis_service import analyze_update
from services.comparison_service import compare_updates


# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Multi-Update Comparison | GPMOID",
    layout="wide"
)

st.title("📊 Multi-Update Comparison")
st.caption(
    "Understand how risks, escalation, and priorities evolve across stakeholder updates."
)

# ---------------- Upload Section ----------------
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

            # ---- Step 1: Run v1 analysis on each update ----
            for file in uploaded_files:
                text = file.read().decode("utf-8")
                analysis = analyze_update(text)
                analyzed_updates.append(analysis)

            # ---- Step 2: Run v2 comparison ----
            comparison = compare_updates(analyzed_updates)

        # ---------------- Snapshot Comparison ----------------
        with st.expander("🔍 Snapshot: Previous vs Current", expanded=False):
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

        # ---------------- What Changed (Hero Section) ----------------
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

        # ---------------- Trend-Based Escalation ----------------
        if comparison["trend_escalation"]:
            st.subheader("🚨 Escalation (Trend-Based)")
            for item in comparison["trend_escalation"]:
                st.markdown(f"- {item}")

        # ---------------- Risk Comparison Table ----------------
        with st.expander("📊 Risk Comparison Details", expanded=False):
            st.dataframe(
                comparison["risk_comparison_table"],
                width="stretch"
            )

        # ---------------- Leadership Narrative ----------------
        st.subheader("🧭 Leadership Summary")
        st.write(comparison["leadership_summary"])
