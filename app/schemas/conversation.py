from __future__ import annotations

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    reporter_name: str | None = None
    reporter_contact: str | None = None


class ConversationMessage(BaseModel):
    content: str = Field(..., min_length=1)


class ConversationRead(BaseModel):
    id: int
    reporter_id: int | None = None
    feedback_id: int | None = None
    status: str
    turns: list[dict]
    collected_fields: dict
    created_at: str
    updated_at: str


class ConversationSubmitResponse(BaseModel):
    conversation: ConversationRead
    feedback_id: int
