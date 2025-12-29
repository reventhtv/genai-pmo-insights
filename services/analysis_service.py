from services.llm_service import call_llm
from services.fallback_service import fallback_analysis


def analyze_update(text: str):
    """
    Orchestrates stakeholder update analysis using a hybrid AI approach.
    """
    prompt = f"""
You are a PMO AI assistant.

Analyze the stakeholder update below and return STRICT JSON only:
{{
  "subject": "...",
  "body": "...",
  "warnings": ["Delay", "Cost", "Morale", "Dependency", "Risk"],
  "risks": [
    {{
      "description": "...",
      "category": "Schedule | Cost | People | Quality | Risk",
      "severity": "Low | Medium | High"
    }}
  ]
}}

Stakeholder update:
{text}
"""

    result = call_llm(prompt)

    if result is None:
        return fallback_analysis()

    return result
