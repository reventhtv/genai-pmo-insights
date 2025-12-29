from typing import List
from pydantic import BaseModel


class Risk(BaseModel):
    description: str
    category: str
    severity: str  # Low | Medium | High
    response_strategy: str  # Avoid | Mitigate | Transfer | Accept
    attention_level: str    # Immediate | Near-term | Monitor
    suggested_owner: str    # PM | Program Manager | Engineering Manager | Vendor Manager


class AnalysisResult(BaseModel):
    subject: str
    body: str
    warnings: List[str]
    risks: List[Risk]
