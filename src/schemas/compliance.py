"""Compliance schema for critic agent outputs."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class IssueSchema(BaseModel):
    """Schema for a single compliance issue."""
    
    type: str = Field(..., description="Issue type (lookahead, overfitting, data_leak, etc.)")
    severity: Literal['error', 'warning', 'info'] = Field(..., description="Issue severity level")
    detail: str = Field(..., description="Detailed description of the issue")
    location: Optional[str] = Field(None, description="Location in code/data where issue occurs")
    recommendation: Optional[str] = Field(None, description="Suggested fix or mitigation")


class ComplianceSchema(BaseModel):
    """Schema for compliance.json file from CriticAgent.
    
    Contains the critic's assessment of a factor run.
    """
    
    passed: bool = Field(..., description="Whether the run passed compliance checks")
    verdict: Literal['PASS', 'FAIL', 'CONDITIONAL'] = Field(
        ..., 
        description="Overall verdict (CONDITIONAL = passed with warnings)"
    )
    
    issues: List[IssueSchema] = Field(
        default_factory=list,
        description="List of identified issues"
    )
    
    recommendations: List[str] = Field(
        default_factory=list,
        description="General recommendations for improvement"
    )
    
    critique_summary: str = Field(..., description="Summary of the critique")
    
    lesson_id: Optional[int] = Field(
        None, 
        description="ID of lesson created from this critique"
    )
    
    reviewed_at: str = Field(..., description="Timestamp of review (ISO format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "passed": True,
                "verdict": "CONDITIONAL",
                "issues": [
                    {
                        "type": "high_turnover",
                        "severity": "warning",
                        "detail": "Monthly turnover of 120% exceeds recommended 100%",
                        "location": "portfolio construction",
                        "recommendation": "Consider reducing rebalance frequency"
                    }
                ],
                "recommendations": [
                    "Monitor turnover in live trading",
                    "Consider transaction cost sensitivity analysis"
                ],
                "critique_summary": "Factor shows good performance but high turnover may erode returns in practice.",
                "lesson_id": 42,
                "reviewed_at": "2023-11-20T12:45:30"
            }
        }
