import streamlit as st
import pandas as pd
from services.analysis_service import analyze_update


st.set_page_config(
    page_title="GenAI PMO Insights",
    layout="wide"
)

st.title("🧠 GenAI PMO Insights")
st.caption("Single stakeholder update analysis : Escalation aware PMO insights with risk prioritization.")

uploaded_file = st.file_uploader(
    "Upload stakeholder update (.txt)",
    type=["txt"]
)

if uploaded_file:
    raw_text = uploaded_file.read().decode("utf-8")

    st.subheader("📄 Stakeholder Update")
    st.text_area(
    label="Stakeholder update content",
    value=raw_text,
    height=220,
    label_visibility="collapsed"
    )


    if st.button("Analyze Update"):
        with st.spinner("Analyzing project signals..."):
            result = analyze_update(raw_text)

        # 🚨 Escalation Summary
        st.subheader("🚨 Escalation Summary")
        if result.get("escalation_summary"):
            for item in result["escalation_summary"]:
                st.markdown(item)
        else:
            st.write("No items require immediate escalation.")

        # ✉️ Executive Email
        st.subheader("✉️ Executive Email Preview")
        st.markdown(f"**Subject:** {result['subject']}")
        st.write(result["body"])

        # ⚠️ Warnings
        st.subheader("⚠️ Early Warning Signals")
        for w in result["warnings"]:
            st.markdown(f"- 🔶 {w}")

        # 📊 Risks with Heat
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
