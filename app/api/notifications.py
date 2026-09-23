from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.issue import Issue
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/issues", tags=["notifications"])


@router.get("/{issue_id}/notifications")
def list_notifications(issue_id: int, db: Session = Depends(get_db)) -> list[dict]:
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found"
        )
    items = NotificationService(db).list_notifications_for_issue(issue_id)
    return [
        {
            "id": item.id,
            "issue_id": item.issue_id,
            "reporter_id": item.reporter_id,
            "channel": item.channel,
            "event_type": item.event_type,
            "message": item.message,
            "status": item.status,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]
