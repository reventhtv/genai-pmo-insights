import os
import json
from datetime import datetime


# -----------------------------
# Config
# -----------------------------

MEMORY_DIR = "memory"
DEFAULT_PROJECT_ID = "default"
MEMORY_VERSION = "1.3"  # confidence + decay

RESOLUTION_ABSENCE_THRESHOLD = 2  # after confidence reaches Low


# -----------------------------
# Helpers
# -----------------------------

def current_period():
    """Default logical period (ISO week)."""
    year, week, _ = datetime.utcnow().isocalendar()
    return f"{year}-W{week:02d}"


def normalize_period(period_id):
    if period_id and isinstance(period_id, str) and period_id.strip():
        return period_id.strip()
    return current_period()


def memory_file_path(project_id=DEFAULT_PROJECT_ID):
    return os.path.join(MEMORY_DIR, f"project_{project_id}.json")


def ensure_memory_dir():
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR)


# -----------------------------
# Load / Save
# -----------------------------

def load_memory(project_id=DEFAULT_PROJECT_ID):
    ensure_memory_dir()
    path = memory_file_path(project_id)

    # Fresh memory
    if not os.path.exists(path):
        return {
            "memory_version": MEMORY_VERSION,
            "project_id": project_id,
            "last_updated_period": None,
            "risks": {}
        }

    with open(path, "r") as f:
        memory = json.load(f)

    # -----------------------------
    # Backward Compatibility Layer
    # -----------------------------

    for risk in memory.get("risks", {}).values():

        # periods_seen introduced later
        if "periods_seen" not in risk:
            last_seen = risk.get("last_seen_period")
            risk["periods_seen"] = [last_seen] if last_seen else []

        # periods_open introduced later
        if "periods_open" not in risk:
            risk["periods_open"] = len(risk["periods_seen"])

        # confidence introduced in v1.3
        if "confidence" not in risk:
            risk["confidence"] = {
                "level": "High",
                "absence_count": 0,
                "last_confident_period": risk.get("last_seen_period")
            }

        # resolution structure normalization
        if "resolution" not in risk:
            risk["resolution"] = {
                "is_resolved": False,
                "resolved_period": None,
                "resolution_reason": None
            }

    memory["memory_version"] = MEMORY_VERSION
    return memory


def save_memory(memory, project_id=DEFAULT_PROJECT_ID):
    path = memory_file_path(project_id)
    with open(path, "w") as f:
        json.dump(memory, f, indent=2)


# -----------------------------
# Core Update Logic
# -----------------------------

def update_memory(analyzed_result, project_id=DEFAULT_PROJECT_ID, period_id=None):
    memory = load_memory(project_id)
    period = normalize_period(period_id)

    memory["last_updated_period"] = period
    risks_seen_this_period = set()

    for risk in analyzed_result.get("risks", []):
        risk_id = risk["risk_id"]
        risks_seen_this_period.add(risk_id)

        if risk_id not in memory["risks"]:
            memory["risks"][risk_id] = _create_new_risk_record(risk, period)
        else:
            _update_existing_risk(memory["risks"][risk_id], risk, period)

    _handle_missing_risks(memory["risks"], risks_seen_this_period, period)

    save_memory(memory, project_id)
    return memory


# -----------------------------
# Risk Record Handlers
# -----------------------------

def _create_new_risk_record(risk, period):
    return {
        "risk_id": risk["risk_id"],
        "category": risk["category"],

        "first_seen_period": period,
        "last_seen_period": period,
        "periods_seen": [period],
        "periods_open": 1,

        "heat_history": [risk["risk_heat"]],
        "attention_history": [risk["attention_level"]],

        "escalation_count": 0,
        "de_escalation_count": 0,
        "recurrence_count": 0,

        "current_status": "Stable",

        "confidence": {
            "level": "High",
            "absence_count": 0,
            "last_confident_period": period
        },

        "resolution": {
            "is_resolved": False,
            "resolved_period": None,
            "resolution_reason": None
        }
    }


def _update_existing_risk(record, risk, period):
    # Ignore duplicate updates in same period
    if period in record["periods_seen"]:
        return

    prev_heat = record["heat_history"][-1]
    curr_heat = risk["risk_heat"]

    record["periods_seen"].append(period)
    record["periods_open"] += 1
    record["last_seen_period"] = period
    record["heat_history"].append(curr_heat)
    record["attention_history"].append(risk["attention_level"])

    # Reset confidence on observation
    record["confidence"]["level"] = "High"
    record["confidence"]["absence_count"] = 0
    record["confidence"]["last_confident_period"] = period

    if _heat_rank(curr_heat) > _heat_rank(prev_heat):
        record["escalation_count"] += 1
        record["current_status"] = "Escalated"
    elif _heat_rank(curr_heat) < _heat_rank(prev_heat):
        record["de_escalation_count"] += 1
        record["current_status"] = "De-escalated"
    else:
        record["current_status"] = "Stable"

    # Recurrence handling
    if record["resolution"]["is_resolved"]:
        record["recurrence_count"] += 1
        record["resolution"]["is_resolved"] = False
        record["resolution"]["resolved_period"] = None
        record["resolution"]["resolution_reason"] = None
        record["current_status"] = "Recurring"


# -----------------------------
# Absence / Decay Logic (v1.3)
# -----------------------------

def _handle_missing_risks(risks, seen_ids, period):
    for risk_id, record in risks.items():

        if risk_id in seen_ids:
            continue

        if record["resolution"]["is_resolved"]:
            continue

        record["confidence"]["absence_count"] += 1
        absence = record["confidence"]["absence_count"]
        severity = record["heat_history"][-1]

        _apply_confidence_decay(record, severity, absence)

        # Resolution now confidence-based
        if (
            record["confidence"]["level"] == "Low"
            and absence >= RESOLUTION_ABSENCE_THRESHOLD
        ):
            record["resolution"]["is_resolved"] = True
            record["resolution"]["resolved_period"] = period
            record["resolution"]["resolution_reason"] = (
                "Confidence decayed after sustained absence"
            )
            record["current_status"] = "Resolved"


def _apply_confidence_decay(record, severity, absence):

    if severity == "High":
        if absence >= 5:
            record["confidence"]["level"] = "Low"
        elif absence >= 3:
            record["confidence"]["level"] = "Medium"

    elif severity == "Medium":
        if absence >= 4:
            record["confidence"]["level"] = "Low"
        elif absence >= 2:
            record["confidence"]["level"] = "Medium"

    else:  # Low severity
        if absence >= 3:
            record["confidence"]["level"] = "Low"
        elif absence >= 1:
            record["confidence"]["level"] = "Medium"


# -----------------------------
# Utilities
# -----------------------------

def _heat_rank(heat):
    return {"Low": 1, "Medium": 2, "High": 3}.get(heat, 0)
