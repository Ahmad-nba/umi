from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.issue import IssueRead
from app.services.issue_service import IssueService

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("", response_model=list[IssueRead])
def list_issues(db: Session = Depends(get_db)) -> list[dict]:
    issues = IssueService(db).list_issues()
    return [
        {
            "id": issue.id,
            "feedback_id": issue.feedback_id,
            "reference": issue.reference,
            "title": issue.title,
            "summary": issue.summary,
            "category": issue.category,
            "issue_type": issue.issue_type,
            "priority": issue.priority,
            "department": issue.department,
            "handler_id": issue.handler_id,
            "status": issue.status,
            "resolution": issue.resolution,
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
            "completed_at": (
                issue.completed_at.isoformat() if issue.completed_at else None
            ),
        }
        for issue in issues
    ]


@router.get("/{issue_id}", response_model=IssueRead)
def get_issue(issue_id: int, db: Session = Depends(get_db)) -> dict:
    issue = IssueService(db).get_issue(issue_id)
    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found"
        )
    return {
        "id": issue.id,
        "feedback_id": issue.feedback_id,
        "reference": issue.reference,
        "title": issue.title,
        "summary": issue.summary,
        "category": issue.category,
        "issue_type": issue.issue_type,
        "priority": issue.priority,
        "department": issue.department,
        "handler_id": issue.handler_id,
        "status": issue.status,
        "resolution": issue.resolution,
        "created_at": issue.created_at.isoformat(),
        "updated_at": issue.updated_at.isoformat(),
        "completed_at": issue.completed_at.isoformat() if issue.completed_at else None,
    }
