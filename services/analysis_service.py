from services.llm_service import call_llm
from services.fallback_service import fallback_analysis


ESCALATION_KEYWORDS = [
    "leadership attention",
    "rebaseline",
    "approval not received",
    "will be impacted",
    "timeline will be impacted",
    "escalation may be required"
]


def build_escalation_summary(risks, stakeholder_text: str):
    """
    Builds escalation summary using:
    - Risk severity / attention
    - Explicit escalation language in stakeholder update
    """
    escalations = []
    text_lower = stakeholder_text.lower()

    keyword_triggered = any(
        keyword in text_lower for keyword in ESCALATION_KEYWORDS
    )

    for risk in risks:
        rule_triggered = (
            risk.get("severity") == "High"
            or risk.get("attention_level") == "Immediate"
        )

        if rule_triggered or keyword_triggered:
            escalations.append(
                f"- {risk['description']} "
                f"(Owner: {risk['suggested_owner']}, "
                f"Severity: {risk['severity']})"
            )

    return escalations


def analyze_update(text: str):
    """
    Orchestrates stakeholder update analysis using a hybrid AI approach.
    """
    prompt = f"""
You are a PMO AI assistant.

Analyze the stakeholder update below and return STRICT JSON only.

Your goal is not just to identify risks, but to provide
clear response guidance for PMO decision-making.

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

    result["escalation_summary"] = build_escalation_summary(
        result["risks"], text
    )

    return result
