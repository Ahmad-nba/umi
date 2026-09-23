from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.issue import IssueRead


class WorkflowActionResponse(BaseModel):
    ok: bool = True
    message: str
    issue: IssueRead
