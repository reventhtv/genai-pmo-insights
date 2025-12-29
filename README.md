# genai-pmo-insights
GenAI-Powered PMO Insights Dashboard (GPMOID)

🧠 GenAI PMO Insights (GPMOID)

GenAI PMO Insights is a lightweight, privacy-first dashboard that converts raw stakeholder updates into actionable PMO signals — executive-ready communication, early warnings, and prioritized risks.

Unlike generic AI summarizers, this tool is designed around how PMOs actually operate: signal detection, risk management, predictability, and decision support.

✨ What This Tool Does

Given a plain-text stakeholder update, the system:

Generates an executive-ready email (subject + body)

Extracts early warning signals
(Delay, Cost, Morale, Dependency, Risk)

Identifies and structures project risks

Description

Category (Schedule, Cost, People, Quality, Risk)

Severity (Low / Medium / High)

Presents insights in a clear, review-ready dashboard

🧠 Why This Exists

In real projects:

Stakeholder updates are noisy and unstructured

Risks are discovered too late

PMOs spend time rewriting, not analyzing

This project explores how GenAI can assist PMOs by:

Surfacing weak signals early

Making risk discussions explicit

Supporting structured, repeatable decision-making

🏗️ Architecture Overview

This project uses a hybrid AI architecture designed for reliability and predictability.

Hybrid LLM Strategy

Primary path: Uses an LLM to analyze stakeholder updates

Fallback path: Deterministic, rule-based output when LLMs fail or are unavailable

This mirrors real enterprise expectations — AI systems must degrade gracefully.

High-Level Flow

User uploads a .txt stakeholder update

Analysis service invokes LLM (if available)

Structured insights are generated as JSON

Streamlit UI renders:

Email preview

Warning signals

Risk summary table
