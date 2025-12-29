def fallback_analysis():
    """
    Deterministic fallback used when LLM is unavailable or fails.
    Keeps output predictable and reviewable.
    """
    return {
        "subject": "Project Update: Key Risks and Dependencies",
        "body": (
            "The project is progressing, however early indicators suggest "
            "potential schedule risks due to external dependencies and "
            "increased workload on the team."
        ),
        "warnings": ["Delay", "Dependency", "Morale"],
        "risks": [
            {
                "description": "Dependency on external vendor approval",
                "category": "Schedule",
                "severity": "High"
            },
            {
                "description": "Team fatigue due to parallel deliverables",
                "category": "People",
                "severity": "Medium"
            }
        ]
    }
