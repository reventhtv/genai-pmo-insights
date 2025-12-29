import streamlit as st
import pandas as pd
from services.analysis_service import analyze_update


# ------------------ Page Config ------------------
st.set_page_config(
    page_title="GenAI PMO Insights",
    layout="wide"
)

st.title("🧠 GenAI PMO Insights")
st.caption(
    "Convert raw stakeholder updates into executive-ready communication, "
    "early warning signals, and structured risks."
)

# ------------------ File Upload ------------------
uploaded_file = st.file_uploader(
    "Upload stakeholder update (.txt)",
    type=["txt"]
)

if uploaded_file:
    raw_text = uploaded_file.read().decode("utf-8")

    st.subheader("📄 Stakeholder Update")
    st.text_area(
        label="",
        value=raw_text,
        height=220
    )

    # ------------------ Analyze ------------------
    if st.button("Analyze Update"):
        with st.spinner("Analyzing project signals..."):
            result = analyze_update(raw_text)

        # ------------------ Email Output ------------------
        st.subheader("✉️ Executive Email Preview")
        st.markdown(f"**Subject:** {result['subject']}")
        st.write(result["body"])

        # ------------------ Warnings ------------------
        st.subheader("⚠️ Early Warning Signals")
        if result["warnings"]:
            for w in result["warnings"]:
                st.markdown(f"- 🔶 {w}")
        else:
            st.write("No major warning signals detected.")

        # ------------------ Risks ------------------
        st.subheader("📊 Risk Summary")
        if result["risks"]:
            df = pd.DataFrame(result["risks"])
            st.dataframe(df, use_container_width=True)
        else:
            st.write("No explicit risks identified.")

        st.success("Analysis complete.")
