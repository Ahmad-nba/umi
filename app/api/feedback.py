from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import WorkflowError
from app.schemas.agent import FeedbackProcessResponse
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.schemas.issue import FeedbackIssueResponse
from app.services.feedback_service import FeedbackService
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=FeedbackRead)
def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)) -> dict:
    service = FeedbackService(db)
    feedback = service.create_feedback(
        name=payload.name,
        contact=payload.contact,
        content=payload.content,
        channel=payload.channel,
        context=payload.context,
    )
    return {
        "id": feedback.id,
        "reporter_id": feedback.reporter_id,
        "channel": feedback.channel,
        "content": feedback.content,
        "context": feedback.context,
        "submitted_at": feedback.submitted_at.isoformat(),
        "status": feedback.status,
    }


@router.get("", response_model=list[FeedbackRead])
def list_feedback(db: Session = Depends(get_db)) -> list[dict]:
    service = FeedbackService(db)
    items = service.list_feedback()
    return [
        {
            "id": item.id,
            "reporter_id": item.reporter_id,
            "channel": item.channel,
            "content": item.content,
            "context": item.context,
            "submitted_at": item.submitted_at.isoformat(),
            "status": item.status,
        }
        for item in items
    ]


@router.post("/{feedback_id}/process", response_model=FeedbackProcessResponse)
def process_feedback(feedback_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        feedback = WorkflowService(db).process_feedback(feedback_id)
    except WorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc

    return {
        "feedback_id": feedback_id,
        "status": "PROCESSED",
        "analysis": feedback,
    }


@router.post("/{feedback_id}/route", response_model=FeedbackIssueResponse)
def route_feedback(feedback_id: int, db: Session = Depends(get_db)) -> dict:
    service = WorkflowService(db)
    try:
        analysis = service.process_feedback(feedback_id)
        issue = service.create_and_route_issue(feedback_id, analysis)
    except WorkflowError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if exc.code == "feedback_not_found"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        raise HTTPException(status_code=status_code, detail=exc.message) from exc

    return {
        "feedback_id": feedback_id,
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


@router.get("/{feedback_id}", response_model=FeedbackRead)
def get_feedback(feedback_id: int, db: Session = Depends(get_db)) -> dict:
    service = FeedbackService(db)
    item = service.get_feedback(feedback_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
        )
    return {
        "id": item.id,
        "reporter_id": item.reporter_id,
        "channel": item.channel,
        "content": item.content,
        "context": item.context,
        "submitted_at": item.submitted_at.isoformat(),
        "status": item.status,
    }
