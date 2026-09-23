from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import WorkflowError
from app.schemas.issue import IssueCompleteRequest, IssueConfirmRequest
from app.schemas.workflow import WorkflowActionResponse
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/issues", tags=["workflow"])


def _issue_response(issue, message: str) -> dict:
    return {
        "ok": True,
        "message": message,
        "issue": {
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
        },
    }


@router.post("/{issue_id}/acknowledge", response_model=WorkflowActionResponse)
def acknowledge_issue(issue_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        issue = WorkflowService(db).acknowledge_issue(issue_id)
    except WorkflowError as exc:
        raise _workflow_http_error(exc) from exc
    return _issue_response(issue, "Issue acknowledged")


@router.post("/{issue_id}/start", response_model=WorkflowActionResponse)
def start_issue(issue_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        issue = WorkflowService(db).start_issue(issue_id)
    except WorkflowError as exc:
        raise _workflow_http_error(exc) from exc
    return _issue_response(issue, "Issue started")


@router.post("/{issue_id}/complete", response_model=WorkflowActionResponse)
def complete_issue(
    issue_id: int,
    body: IssueCompleteRequest,
    db: Session = Depends(get_db),
) -> dict:
    try:
        issue = WorkflowService(db).complete_issue(issue_id, body.resolution)
    except WorkflowError as exc:
        raise _workflow_http_error(exc) from exc
    return _issue_response(issue, "Issue completed")


@router.post("/{issue_id}/confirm", response_model=WorkflowActionResponse)
def confirm_issue(
    issue_id: int,
    body: IssueConfirmRequest,
    db: Session = Depends(get_db),
) -> dict:
    try:
        issue = WorkflowService(db).confirm_issue(issue_id, body.confirmed)
    except WorkflowError as exc:
        raise _workflow_http_error(exc) from exc
    return _issue_response(issue, "Issue confirmed")


@router.post("/{issue_id}/close", response_model=WorkflowActionResponse)
def close_issue(issue_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        issue = WorkflowService(db).close_issue(issue_id)
    except WorkflowError as exc:
        raise _workflow_http_error(exc) from exc
    return _issue_response(issue, "Issue closed")


def _workflow_http_error(exc: WorkflowError) -> HTTPException:
    code = (
        status.HTTP_404_NOT_FOUND
        if exc.code == "issue_not_found"
        else status.HTTP_409_CONFLICT
    )
    return HTTPException(
        status_code=code,
        detail={"error": {"code": exc.code, "message": exc.message}},
    )
