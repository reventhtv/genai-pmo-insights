from services.llm_service import call_llm
from services.fallback_service import fallback_analysis


# -----------------------------
# Risk Heat Calibration (v1)
# -----------------------------

def calculate_risk_heat(severity: str, attention: str) -> str:
    """
    PMO-aligned risk heat calculation.
    Avoids early over-escalation.
    """
    if severity == "High" and attention == "Immediate":
        return "High"

    if severity == "High" and attention == "Near-term":
        return "Medium"

    if severity == "Medium" and attention in ["Immediate", "Near-term"]:
        return "Medium"

    return "Low"


# -----------------------------
# Escalation Logic (v1)
# -----------------------------

ESCALATION_KEYWORDS_STRONG = [
    "leadership attention",
    "schedule rebaseline",
    "uat at risk",
    "timeline will be impacted",
    "requires escalation",
    "approval not received and"
]

ESCALATION_KEYWORDS_WEAK = [
    "may be impacted",
    "risk that",
    "if approval is not received",
    "potential delay"
]


def build_escalation_summary(risks, stakeholder_text: str):
    """
    Builds escalation summary conservatively.
    Escalates only when signals are explicit and actionable.
    """
    escalations = []
    text = stakeholder_text.lower()

    strong_signal = any(k in text for k in ESCALATION_KEYWORDS_STRONG)
    weak_signal = any(k in text for k in ESCALATION_KEYWORDS_WEAK)

    for risk in risks:
        explicit_critical = (
            risk["severity"] == "High"
            and risk["attention_level"] == "Immediate"
        )

        # Escalate only on strong signals or explicit criticality
        if strong_signal or explicit_critical:
            escalations.append(
                f"- {risk['description']} "
                f"(Owner: {risk['suggested_owner']}, "
                f"Severity: {risk['severity']})"
            )

    # Weak signals alone do NOT trigger escalation
    return escalations


# -----------------------------
# Main Analysis Entry Point
# -----------------------------

def analyze_update(text: str):
    """
    Analyzes a single stakeholder update using a hybrid approach:
    - LLM when available
    - Deterministic fallback otherwise
    """
    prompt = f"""
You are a PMO AI assistant.

Analyze the stakeholder update below and return STRICT JSON only.

Your goal is to identify risks conservatively and realistically.
Do NOT escalate early unless timeline impact or leadership attention is explicit.

Return JSON in this exact format:
{{
  "subject": "...",
  "body": "...",
  "warnings": ["Delay", "Cost", "Morale", "Dependency", "Risk"],
  "risks": [
    {{
      "description": "...",
      "category": "Schedule | Cost | People | Quality | Risk",
      "severity": "Low | Medium | High",
      "response_strategy": "Avoid | Mitigate | Transfer | Accept",
      "attention_level": "Immediate | Near-term | Monitor",
      "suggested_owner": "PM | Program Manager | Engineering Manager | Vendor Manager"
    }}
  ]
}}

Stakeholder update:
{text}
"""

    result = call_llm(prompt)

    if result is None:
        result = fallback_analysis()

    # -----------------------------
    # Derive risk heat (calibrated)
    # -----------------------------
    for risk in result["risks"]:
        risk["risk_heat"] = calculate_risk_heat(
            risk["severity"], risk["attention_level"]
        )

    # -----------------------------
    # Build escalation summary
    # -----------------------------
    result["escalation_summary"] = build_escalation_summary(
        result["risks"], text
    )

    return result
