"""
comparison_service.py

Implements v2 multi-update comparison logic for GPMOID.
This layer is deterministic, stateless, and UI-driven.
"""

from collections import defaultdict
from typing import List, Dict


# -----------------------------
# Helpers
# -----------------------------

def derive_risk_id(description: str, category: str) -> str:
    """
    Derives a stable risk_id from description + category.
    Simple heuristic for v2 (can be replaced with embeddings later).
    """
    text = f"{category} {description}".lower()

    if "vendor" in text or "external" in text:
        return "vendor_dependency"
    if "team" in text or "morale" in text or "capacity" in text:
        return "team_capacity"
    if "cost" in text or "budget" in text:
        return "cost_overrun"
    if "quality" in text:
        return "quality_risk"

    return category.lower().replace(" ", "_")


def heat_rank(heat: str) -> int:
    """Converts risk heat to comparable rank."""
    return {"Low": 1, "Medium": 2, "High": 3}.get(heat, 0)


# -----------------------------
# Normalization
# -----------------------------

def normalize_risks(analyzed_update: Dict) -> Dict:
    """
    Converts risk list into a dictionary keyed by risk_id.
    """
    normalized = {}

    for risk in analyzed_update.get("risks", []):
        risk_id = derive_risk_id(
            risk["description"], risk["category"]
        )

        normalized[risk_id] = {
            "display_name": risk["description"],
            "category": risk["category"],
            "severity": risk["severity"],
            "attention_level": risk["attention_level"],
            "risk_heat": risk["risk_heat"],
            "suggested_owner": risk["suggested_owner"],
        }

    return normalized


# -----------------------------
# Snapshot Comparison
# -----------------------------

def build_snapshot_comparison(previous: Dict, current: Dict) -> Dict:
    """
    Builds previous vs current snapshot.
    """
    def highest_heat(risks: Dict) -> str:
        if not risks:
            return "Low"
        return max(
            (r["risk_heat"] for r in risks.values()),
            key=heat_rank
        )

    def top_risk(risks: Dict) -> str:
        if not risks:
            return "None"
        return max(
            risks.values(),
            key=lambda r: heat_rank(r["risk_heat"])
        )["display_name"]

    return {
        "previous": {
            "escalation": bool(previous.get("escalation_summary")),
            "highest_risk_heat": highest_heat(previous["risks"]),
            "top_risk": top_risk(previous["risks"]),
        },
        "current": {
            "escalation": bool(current.get("escalation_summary")),
            "highest_risk_heat": highest_heat(current["risks"]),
            "top_risk": top_risk(current["risks"]),
        },
    }


# -----------------------------
# Change Detection
# -----------------------------

def detect_changes(previous: Dict, current: Dict) -> Dict:
    """
    Detects new, escalated, de-escalated, and unchanged risks.
    """
    changes = {
        "new": [],
        "escalated": [],
        "de_escalated": [],
        "unchanged": [],
    }

    prev_ids = set(previous.keys())
    curr_ids = set(current.keys())

    for risk_id in curr_ids - prev_ids:
        changes["new"].append(current[risk_id]["display_name"])

    for risk_id in curr_ids & prev_ids:
        prev_heat = heat_rank(previous[risk_id]["risk_heat"])
        curr_heat = heat_rank(current[risk_id]["risk_heat"])

        if curr_heat > prev_heat:
            changes["escalated"].append(
                f"{current[risk_id]['display_name']} "
                f"({previous[risk_id]['risk_heat']} → {current[risk_id]['risk_heat']})"
            )
        elif curr_heat < prev_heat:
            changes["de_escalated"].append(
                f"{current[risk_id]['display_name']} "
                f"({previous[risk_id]['risk_heat']} → {current[risk_id]['risk_heat']})"
            )
        else:
            changes["unchanged"].append(
                current[risk_id]["display_name"]
            )

    return changes


# -----------------------------
# Trend Escalation
# -----------------------------

def detect_trend_escalations(risk_history: Dict) -> List[str]:
    """
    Detects escalation based on repeated worsening.
    """
    escalations = []

    for risk_id, states in risk_history.items():
        if len(states) < 3:
            continue

        heat_trend = [heat_rank(s["risk_heat"]) for s in states[-3:]]

        if heat_trend[-1] > heat_trend[-2] and heat_trend[-2] >= heat_trend[-3]:
            escalations.append(
                f"{states[-1]['display_name']} escalated in recent updates"
            )

    return escalations


# -----------------------------
# Risk Comparison Table
# -----------------------------

def build_risk_comparison_table(
    normalized_updates: List[Dict]
) -> List[Dict]:
    """
    Builds a comparison table across updates.
    """
    table = defaultdict(dict)

    for idx, update in enumerate(normalized_updates):
        label = f"U{idx + 1}"
        for risk_id, risk in update.items():
            table[risk_id]["risk"] = risk["display_name"]
            table[risk_id][label] = risk["risk_heat"]

    rows = []
    for risk_id, values in table.items():
        heats = [
            heat_rank(v)
            for k, v in values.items()
            if k.startswith("U")
        ]

        trend = "Up" if heats[-1] > heats[0] else "Down" if heats[-1] < heats[0] else "Stable"

        values["trend"] = trend
        rows.append(values)

    return rows


# -----------------------------
# Leadership Narrative
# -----------------------------

def generate_leadership_summary(
    change_summary: Dict,
    trend_escalations: List[str]
) -> str:
    """
    Generates a concise leadership narrative.
    """
    lines = []

    if change_summary["escalated"]:
        lines.append(
            f"{len(change_summary['escalated'])} risk(s) have escalated since the last update."
        )

    if trend_escalations:
        lines.append(
            f"{len(trend_escalations)} risk(s) show sustained escalation trends."
        )

    if not lines:
        lines.append(
            "No material changes or escalation trends detected across updates."
        )

    return " ".join(lines)


# -----------------------------
# Main Entry Point
# -----------------------------

def compare_updates(analyzed_updates: List[Dict]) -> Dict:
    """
    Entry point for v2 comparison logic.
    """
    if len(analyzed_updates) < 2:
        raise ValueError("At least two analyzed updates are required")

    normalized = [
        normalize_risks(update) for update in analyzed_updates
    ]

    snapshot = build_snapshot_comparison(
        {"risks": normalized[-2], "escalation_summary": analyzed_updates[-2].get("escalation_summary")},
        {"risks": normalized[-1], "escalation_summary": analyzed_updates[-1].get("escalation_summary")},
    )

    change_summary = detect_changes(
        normalized[-2], normalized[-1]
    )

    # Build risk history for trend detection
    risk_history = defaultdict(list)
    for update in normalized:
        for risk_id, risk in update.items():
            risk_history[risk_id].append(risk)

    trend_escalation = detect_trend_escalations(risk_history)

    risk_table = build_risk_comparison_table(normalized)

    leadership_summary = generate_leadership_summary(
        change_summary, trend_escalation
    )

    return {
        "snapshot": snapshot,
        "change_summary": change_summary,
        "trend_escalation": trend_escalation,
        "risk_comparison_table": risk_table,
        "leadership_summary": leadership_summary,
    }
