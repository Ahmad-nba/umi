from __future__ import annotations

from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: int
    issue_id: int
    reporter_id: int
    channel: str
    event_type: str
    message: str
    status: str
    created_at: str
