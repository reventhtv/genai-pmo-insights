def fallback_analysis():
    """
    Deterministic fallback used when LLM is unavailable.
    Provides actionable risk guidance for PMO review.
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
                "severity": "High",
                "response_strategy": "Mitigate",
                "attention_level": "Immediate",
                "suggested_owner": "Program Manager"
            },
            {
                "description": "Team fatigue due to parallel deliverables",
                "category": "People",
                "severity": "Medium",
                "response_strategy": "Mitigate",
                "attention_level": "Near-term",
                "suggested_owner": "Engineering Manager"
            }
        ]
    }
