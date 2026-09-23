from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.qa import QADashboard, QAIssueDetail
from app.services.qa_service import QAService

router = APIRouter(prefix="/qa", tags=["qa"])


@router.get("/dashboard", response_model=QADashboard)
def dashboard(db: Session = Depends(get_db)) -> dict:
    return QAService(db).dashboard()


@router.get("/issues/{issue_id}", response_model=QAIssueDetail)
def issue_detail(issue_id: int, db: Session = Depends(get_db)) -> dict:
    detail = QAService(db).issue_detail(issue_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found"
        )
    return detail
