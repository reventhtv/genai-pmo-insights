🧠 GenAI PMO Insights (GPMOID)

A lightweight, privacy-first GenAI tool that turns raw stakeholder updates into actionable PMO insights — executive communication, early warnings, and structured risks.

Built for real PMOs, not AI demos.

What It Does

From a plain-text stakeholder update, the tool generates:

Executive-ready email (subject + body)

Early warning signals
(Delay, Cost, Morale, Dependency, Risk)

Structured risks with category and severity

Clear dashboard view for fast review

Why It Matters

PMOs don’t need summaries.
They need signals, risks, and clarity — early and consistently.

This project explores how GenAI can support:

Risk identification

Predictable decision-making

Better stakeholder communication

Architecture (Hybrid AI)

LLM-first for analysis

Deterministic fallback if LLM fails

Designed to degrade gracefully — enterprise-ready behavior.

Project Structure
genai-pmo-insights/
├── app.py                  # Streamlit UI
├── schemas.py              # Typed outputs
├── services/
│   ├── analysis_service.py
│   ├── llm_service.py
│   └── fallback_service.py
├── sample_inputs/
│   └── stakeholder_update.txt
└── requirements.txt

Privacy by Design

No database

No file storage

No user tracking

In-memory processing only

Tech Stack

Python

Streamlit

OpenAI API

Pydantic

Pandas

Run Locally
git clone https://github.com/<your-username>/genai-pmo-insights.git
cd genai-pmo-insights
pip install -r requirements.txt
export OPENAI_API_KEY="your_api_key"
streamlit run app.py

PMBOK Fit (Conceptual)

Risk Management

Stakeholder Communication

Schedule & Cost Signals

PMO Governance Support

Author

Built by a technical PM / TPM with an engineering background, focused on practical GenAI for delivery and governance.

License

MIT
