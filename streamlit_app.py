import streamlit as st
import pandas as pd
from services.analysis_service import analyze_update


# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="Single Update Analysis",
    layout="wide"
)


# -----------------------------
# Header
# -----------------------------
st.title("🧠 Single Update Analysis")
st.caption(
    "Escalation-aware PMO insights for a single stakeholder update."
)

st.divider()


# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload stakeholder update (.txt)",
    type=["txt"]
)

raw_text = ""

if uploaded_file:
    raw_text = uploaded_file.read().decode("utf-8")

    st.subheader("📄 Stakeholder Update")
    st.text_area(
        label="Stakeholder update content",
        value=raw_text,
        height=220,
        label_visibility="collapsed"
    )

    st.divider()

    # -----------------------------
    # Analysis Trigger
    # -----------------------------
    if st.button("Analyze Update"):
        with st.spinner("Analyzing project signals..."):
            result = analyze_update(raw_text)

        # -----------------------------
        # Escalation Summary
        # -----------------------------
        st.subheader("🚨 Escalation Summary")
        if result.get("escalation_summary"):
            for item in result["escalation_summary"]:
                st.markdown(item)
        else:
            st.write("No items require immediate escalation.")

        st.divider()

        # -----------------------------
        # Executive Email Preview
        # -----------------------------
        st.subheader("✉️ Executive Email Preview")
        st.markdown(f"**Subject:** {result['subject']}")
        st.write(result["body"])

        st.divider()

        # -----------------------------
        # Early Warning Signals
        # -----------------------------
        st.subheader("⚠️ Early Warning Signals")
        if result["warnings"]:
            for w in result["warnings"]:
                st.markdown(f"- 🔶 {w}")
        else:
            st.write("No early warning signals detected.")

        st.divider()

        # -----------------------------
        # Risk Heat Summary
        # -----------------------------
        st.subheader("🔥 Risk Heat Summary")

        df = pd.DataFrame(result["risks"])
        df = df[
            [
                "description",
                "category",
                "severity",
                "attention_level",
                "risk_heat",
                "response_strategy",
                "suggested_owner",
            ]
        ]

        st.dataframe(df, width="stretch")

        st.success("Analysis complete.")
