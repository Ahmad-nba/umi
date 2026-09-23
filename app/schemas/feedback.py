from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=255)
    contact: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    channel: str = Field(default="form", min_length=1, max_length=50)
    context: str | None = None


class FeedbackRead(BaseModel):
    id: int
    reporter_id: int
    channel: str
    content: str
    context: str | None = None
    submitted_at: str
    status: str
