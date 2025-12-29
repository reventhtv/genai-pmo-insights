from services.llm_service import call_llm
from services.fallback_service import fallback_analysis

def build_escalation_summary(risks):
    """
    Builds a short escalation summary for leadership review.
    """
    escalations = []

    for risk in risks:
        if (
            risk.get("severity") == "High"
            or risk.get("attention_level") == "Immediate"
        ):
            escalations.append(
                f"- {risk['description']} "
                f"(Owner: {risk['suggested_owner']})"
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
        return fallback_analysis()

    result["escalation_summary"] = build_escalation_summary(result["risks"])
    return result
