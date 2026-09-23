from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.core.enums import Department, Priority


class FeedbackAnalysis(BaseModel):
    summary: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    issue_type: str = Field(..., min_length=1, max_length=100)
    priority: Priority
    department: Department
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("summary")
    @classmethod
    def summary_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("summary cannot be blank")
        return value


class FeedbackProcessResponse(BaseModel):
    feedback_id: int
    status: str
    analysis: FeedbackAnalysis
