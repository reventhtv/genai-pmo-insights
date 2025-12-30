from services.llm_service import call_llm
from services.fallback_service import fallback_analysis


# -----------------------------
# Risk Heat Calibration
# -----------------------------

def calculate_risk_heat(severity: str, attention: str) -> str:
    if severity == "High" and attention == "Immediate":
        return "High"
    if severity == "High" and attention == "Near-term":
        return "Medium"
    if severity == "Medium" and attention in ["Immediate", "Near-term"]:
        return "Medium"
    return "Low"


# -----------------------------
# Post-LLM Normalization (KEY FIX)
# -----------------------------

EARLY_STAGE_PHRASES = [
    "initial discussions",
    "ongoing",
    "pending",
    "no immediate impact",
    "at this stage",
    "monitoring",
    "no major risks"
]


def normalize_risk_based_on_text(risk: dict, stakeholder_text: str) -> dict:
    """
    Robust early-stage risk normalization.
    Guards against LLM over-escalation.
    """
    text = stakeholder_text.lower()

    early_indicators = [
        "initial",
        "ongoing",
        "pending",
        "monitor",
        "no immediate",
        "at this stage",
        "no major",
        "early"
    ]

    impact_indicators = [
        "uat at risk",
        "timeline impacted",
        "schedule rebaseline",
        "delay confirmed",
        "will impact",
        "now at risk"
    ]

    is_early = any(k in text for k in early_indicators)
    has_real_impact = any(k in text for k in impact_indicators)

    # Only downgrade if early-stage AND no real impact
    if is_early and not has_real_impact:
        risk["severity"] = "Medium"
        risk["attention_level"] = "Near-term"

    return risk


# -----------------------------
# Escalation Logic
# -----------------------------

ESCALATION_KEYWORDS_STRONG = [
    "uat at risk",
    "schedule rebaseline",
    "leadership attention",
    "timeline will be impacted",
    "requires escalation"
]


def build_escalation_summary(risks, stakeholder_text: str):
    escalations = []
    text = stakeholder_text.lower()

    strong_signal = any(k in text for k in ESCALATION_KEYWORDS_STRONG)

    for risk in risks:
        explicit_critical = (
            risk["severity"] == "High"
            and risk["attention_level"] == "Immediate"
        )

        if strong_signal or explicit_critical:
            escalations.append(
                f"- {risk['description']} "
                f"(Owner: {risk['suggested_owner']}, "
                f"Severity: {risk['severity']})"
            )

    return escalations


# -----------------------------
# Main Analysis Entry
# -----------------------------

def analyze_update(text: str):
    prompt = f"""
You are a PMO AI assistant.

Analyze the stakeholder update below and return STRICT JSON only.
Be conservative. Do NOT escalate early unless timeline impact is explicit.

Return JSON in this format:
{{
  "subject": "...",
  "body": "...",
  "warnings": [],
  "risks": [
    {{
      "description": "...",
      "category": "Schedule | Cost | People | Quality | Risk",
      "severity": "Low | Medium | High",
      "response_strategy": "Avoid | Mitigate | Transfer | Accept",
      "attention_level": "Immediate | Near-term | Monitor",
      "suggested_owner": "Program Manager | Engineering Manager | Vendor Manager"
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
    # Normalize risks BEFORE heat calc
    # -----------------------------
    normalized_risks = []
    for risk in result["risks"]:
        risk = normalize_risk_based_on_text(risk, text)
        risk["risk_heat"] = calculate_risk_heat(
            risk["severity"], risk["attention_level"]
        )
        normalized_risks.append(risk)

    result["risks"] = normalized_risks

    # -----------------------------
    # Build escalation summary
    # -----------------------------
    result["escalation_summary"] = build_escalation_summary(
        result["risks"], text
    )

    return result
