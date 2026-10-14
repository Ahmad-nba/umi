from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.enums import EventType


@dataclass(frozen=True)
class EmailMessage:
    subject: str
    body: str
    html_body: str | None = None


def render_email(
    *,
    event_type: str,
    reporter_name: str,
    reference: str,
    message: str,
    feedback_id: int,
) -> EmailMessage:
    settings = get_settings()
    frontend_base_url = settings.model_dump().get(
        "frontend_base_url", "http://localhost:3000"
    )
    track_url = f"{str(frontend_base_url).rstrip('/')}/reporter/feedback/{feedback_id}"
    greeting = f"Hello {reporter_name},"
    if event_type == EventType.ISSUE_ROUTED.value:
        subject = f"Your feedback is now with {message.split(' to ')[-1].rstrip('.') }"
        body = (
            f"{greeting}\n\nYour feedback {reference} has been routed for action.\n"
            f"\n{message}\n\nTrack your feedback: {track_url}"
        )
    elif event_type == EventType.TASK_COMPLETED.value:
        subject = f"Your feedback has been addressed — {reference}"
        body = f"{greeting}\n\n{message}\n\nTrack your feedback: {track_url}"
    elif event_type == EventType.CONFIRMATION_REQUESTED.value:
        subject = f"Please confirm your feedback resolution — {reference}"
        body = f"{greeting}\n\n{message}\n\nReview and respond: {track_url}"
    elif event_type == EventType.FEEDBACK_SUBMITTED.value:
        subject = f"We received your feedback — {reference}"
        body = (
            f"{greeting}\n\nWe have received your feedback.\n\n"
            f"Reference: {reference}\n\nTrack feedback: {track_url}"
        )
    else:
        subject = f"Update about your feedback — {reference}"
        body = f"{greeting}\n\n{message}\n\nTrack your feedback: {track_url}"
    return EmailMessage(subject=subject, body=body)
