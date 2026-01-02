import os
import json
from datetime import datetime


# -----------------------------
# Config
# -----------------------------

MEMORY_DIR = "memory"
DEFAULT_PROJECT_ID = "default"
MEMORY_VERSION = "1.2"  # explicit period support

RESOLUTION_ABSENCE_THRESHOLD = 2  # consecutive periods


# -----------------------------
# Helpers
# -----------------------------

def current_period():
    """
    Default logical period (ISO week).
    Example: 2026-W05
    """
    year, week, _ = datetime.utcnow().isocalendar()
    return f"{year}-W{week:02d}"


def normalize_period(period_id):
    """
    Option A:
    - Trust explicit period override
    - Guard against empty / invalid values
    """
    if period_id and isinstance(period_id, str) and period_id.strip():
        return period_id.strip()
    return current_period()


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
            "last_updated_period": None,
            "risks": {}
        }

    with open(path, "r") as f:
        return json.load(f)


def save_memory(memory, project_id=DEFAULT_PROJECT_ID):
    path = memory_file_path(project_id)
    with open(path, "w") as f:
        json.dump(memory, f, indent=2)


# -----------------------------
# Core Update Logic
# -----------------------------

def update_memory(analyzed_result, project_id=DEFAULT_PROJECT_ID, period_id=None):
    """
    Updates longitudinal memory.

    Option A:
    - period_id provided  -> trusted logical time (testing / replay)
    - period_id None      -> current ISO week (normal usage)
    """
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
        "periods_open": 1,
        "periods_seen": [period],

        "heat_history": [risk["risk_heat"]],
        "attention_history": [risk["attention_level"]],

        "escalation_count": 0,
        "de_escalation_count": 0,
        "recurrence_count": 0,

        "current_status": "Stable",

        "resolution": {
            "is_resolved": False,
            "resolved_period": None,
            "resolution_reason": None,
            "absence_count": 0
        }
    }


def _update_existing_risk(record, risk, period):
    # Ignore duplicate updates within same period
    if period in record["periods_seen"]:
        return

    prev_heat = record["heat_history"][-1]
    curr_heat = risk["risk_heat"]

    record["periods_seen"].append(period)
    record["periods_open"] += 1
    record["last_seen_period"] = period
    record["heat_history"].append(curr_heat)
    record["attention_history"].append(risk["attention_level"])

    record["resolution"]["absence_count"] = 0

    if _heat_rank(curr_heat) > _heat_rank(prev_heat):
        record["escalation_count"] += 1
        record["current_status"] = "Escalated"
    elif _heat_rank(curr_heat) < _heat_rank(prev_heat):
        record["de_escalation_count"] += 1
        record["current_status"] = "De-escalated"
    else:
        record["current_status"] = "Stable"

    if record["resolution"]["is_resolved"]:
        record["recurrence_count"] += 1
        record["resolution"]["is_resolved"] = False
        record["resolution"]["resolved_period"] = None
        record["resolution"]["resolution_reason"] = None
        record["current_status"] = "Recurring"


def _handle_missing_risks(risks, seen_ids, period):
    for risk_id, record in risks.items():
        if risk_id not in seen_ids and not record["resolution"]["is_resolved"]:
            if record["last_seen_period"] != period:
                record["resolution"]["absence_count"] += 1

            if record["resolution"]["absence_count"] >= RESOLUTION_ABSENCE_THRESHOLD:
                record["resolution"]["is_resolved"] = True
                record["resolution"]["resolved_period"] = period
                record["resolution"]["resolution_reason"] = "Not observed in recent periods"
                record["current_status"] = "Resolved"


# -----------------------------
# Utilities
# -----------------------------

def _heat_rank(heat):
    return {"Low": 1, "Medium": 2, "High": 3}.get(heat, 0)
