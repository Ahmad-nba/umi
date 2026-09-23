from __future__ import annotations

from pydantic import BaseModel, Field


class IssueRead(BaseModel):
    id: int
    feedback_id: int
    reference: str
    title: str
    summary: str
    category: str
    issue_type: str
    priority: str
    department: str
    handler_id: int | None = None
    status: str
    resolution: str | None = None
    created_at: str
    updated_at: str
    completed_at: str | None = None


class IssueCompleteRequest(BaseModel):
    resolution: str = Field(..., min_length=1)


class IssueConfirmRequest(BaseModel):
    confirmed: bool


class FeedbackIssueResponse(BaseModel):
    feedback_id: int
    issue: IssueRead
