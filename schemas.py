from typing import List
from pydantic import BaseModel


class Risk(BaseModel):
    description: str
    category: str
    severity: str  # Low | Medium | High


class AnalysisResult(BaseModel):
    subject: str
    body: str
    warnings: List[str]
    risks: List[Risk]
