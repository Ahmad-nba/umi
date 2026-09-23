from __future__ import annotations

from pydantic import BaseModel


class QAIssueSummary(BaseModel):
    id: int
    reference: str
    status: str
    priority: str
    department: str
    handler_id: int | None
    next_action: str


class QAEventRead(BaseModel):
    id: int
    issue_id: int
    event_type: str
    actor: str | None
    description: str
    metadata: dict | None
    created_at: str


class QADashboard(BaseModel):
    total_issues: int
    by_status: dict[str, int]
    issues: list[QAIssueSummary]


class QAIssueDetail(BaseModel):
    issue: QAIssueSummary
    events: list[QAEventRead]
    notification_count: int
