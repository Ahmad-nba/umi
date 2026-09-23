from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import WorkflowError
from app.schemas.conversation import (
    ConversationCreate,
    ConversationMessage,
    ConversationRead,
    ConversationSubmitResponse,
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _read(conversation) -> dict:
    return {
        "id": conversation.id,
        "reporter_id": conversation.reporter_id,
        "feedback_id": conversation.feedback_id,
        "status": conversation.status,
        "turns": conversation.turns or [],
        "collected_fields": conversation.collected_fields or {},
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


def _error(exc: WorkflowError) -> HTTPException:
    code_to_status = {
        "conversation_not_found": status.HTTP_404_NOT_FOUND,
        "conversation_closed": status.HTTP_409_CONFLICT,
        "reporter_required": status.HTTP_422_UNPROCESSABLE_CONTENT,
        "message_required": status.HTTP_422_UNPROCESSABLE_CONTENT,
    }
    return HTTPException(
        status_code=code_to_status.get(exc.code, status.HTTP_409_CONFLICT),
        detail={"error": {"code": exc.code, "message": exc.message}},
    )


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate, db: Session = Depends(get_db)
) -> dict:
    conversation = ConversationService(db).create(
        reporter_name=payload.reporter_name,
        reporter_contact=payload.reporter_contact,
    )
    return _read(conversation)


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)) -> dict:
    conversation = ConversationService(db).get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _read(conversation)


@router.post("/{conversation_id}/messages", response_model=ConversationRead)
def add_message(
    conversation_id: int,
    payload: ConversationMessage,
    db: Session = Depends(get_db),
) -> dict:
    try:
        conversation = ConversationService(db).add_message(
            conversation_id, payload.content
        )
    except WorkflowError as exc:
        raise _error(exc) from exc
    return _read(conversation)


@router.post("/{conversation_id}/submit", response_model=ConversationSubmitResponse)
def submit_conversation(conversation_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        conversation, feedback = ConversationService(db).submit(conversation_id)
    except WorkflowError as exc:
        raise _error(exc) from exc
    return {"conversation": _read(conversation), "feedback_id": feedback.id}
