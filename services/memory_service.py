import os
import json
from datetime import datetime


# -----------------------------
# Config
# -----------------------------

MEMORY_DIR = "memory"
DEFAULT_PROJECT_ID = "default"
MEMORY_VERSION = "1.0"

RESOLUTION_ABSENCE_THRESHOLD = 2  # N consecutive updates


# -----------------------------
# Helpers
# -----------------------------

def current_week():
    return datetime.utcnow().strftime("%Y-W%U")


def memory_file_path(project_id=DEFAULT_PROJECT_ID):
    return os.path.join(MEMORY_DIR, f"project_{project_id}.json")


def ensure_memory_dir():
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR)


# -----------------------------
# Load / Initialize Memory
# -----------------------------

def load_memory(project_id=DEFAULT_PROJECT_ID):
    ensure_memory_dir()
    path = memory_file_path(project_id)

    if not os.path.exists(path):
        return {
            "memory_version": MEMORY_VERSION,
            "project_id": project_id,
            "last_updated_week": None,
            "risks": {}
        }

    with open(path, "r") as f:
        return json.load(f)


def save_memory(memory, project_id=DEFAULT_PROJECT_ID):
    memory["last_updated_week"] = current_week()
    path = memory_file_path(project_id)

    with open(path, "w") as f:
        json.dump(memory, f, indent=2)


# -----------------------------
# Core Update Logic
# -----------------------------

def update_memory(analyzed_result, project_id=DEFAULT_PROJECT_ID):
    """
    Updates longitudinal memory based on latest analyzed update.
    """
    memory = load_memory(project_id)
    risks_seen_this_week = set()

    for risk in analyzed_result.get("risks", []):
        risk_id = risk["risk_id"]
        risks_seen_this_week.add(risk_id)

        if risk_id not in memory["risks"]:
            # ---- First Seen ----
            memory["risks"][risk_id] = _create_new_risk_record(risk)
        else:
            # ---- Existing Risk ----
            _update_existing_risk(memory["risks"][risk_id], risk)

    # ---- Handle absence & resolution ----
    _handle_missing_risks(memory["risks"], risks_seen_this_week)

    save_memory(memory, project_id)
    return memory


# -----------------------------
# Risk Record Handlers
# -----------------------------

def _create_new_risk_record(risk):
    week = current_week()
    return {
        "risk_id": risk["risk_id"],
        "category": risk["category"],

        "first_seen_week": week,
        "last_seen_week": week,
        "weeks_open": 1,

        "heat_history": [risk["risk_heat"]],
        "attention_history": [risk["attention_level"]],

        "escalation_count": 0,
        "de_escalation_count": 0,
        "recurrence_count": 0,

        "current_status": "Stable",

        "resolution": {
            "is_resolved": False,
            "resolved_week": None,
            "resolution_reason": None,
            "absence_count": 0
        }
    }


def _update_existing_risk(record, risk):
    week = current_week()
    prev_heat = record["heat_history"][-1]
    curr_heat = risk["risk_heat"]

    record["last_seen_week"] = week
    record["weeks_open"] += 1
    record["heat_history"].append(curr_heat)
    record["attention_history"].append(risk["attention_level"])

    # Reset absence counter
    record["resolution"]["absence_count"] = 0

    # Escalation / De-escalation
    if _heat_rank(curr_heat) > _heat_rank(prev_heat):
        record["escalation_count"] += 1
        record["current_status"] = "Escalated"
    elif _heat_rank(curr_heat) < _heat_rank(prev_heat):
        record["de_escalation_count"] += 1
        record["current_status"] = "De-escalated"
    else:
        record["current_status"] = "Stable"

    # If it was previously resolved, this is recurrence
    if record["resolution"]["is_resolved"]:
        record["recurrence_count"] += 1
        record["resolution"]["is_resolved"] = False
        record["resolution"]["resolved_week"] = None
        record["resolution"]["resolution_reason"] = None
        record["current_status"] = "Recurring"


def _handle_missing_risks(risks, seen_ids):
    for risk_id, record in risks.items():
        if risk_id not in seen_ids and not record["resolution"]["is_resolved"]:
            record["resolution"]["absence_count"] += 1

            if record["resolution"]["absence_count"] >= RESOLUTION_ABSENCE_THRESHOLD:
                record["resolution"]["is_resolved"] = True
                record["resolution"]["resolved_week"] = current_week()
                record["resolution"]["resolution_reason"] = "Not observed in recent updates"
                record["current_status"] = "Resolved"


# -----------------------------
# Utilities
# -----------------------------

def _heat_rank(heat):
    return {"Low": 1, "Medium": 2, "High": 3}.get(heat, 0)
