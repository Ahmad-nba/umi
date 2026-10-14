from __future__ import annotations

import re

from app.notifications.sender_client import DeliveryResult, SenderClient
from app.notifications.templates import render_email


class EmailNotificationAdapter:
    channel = "email"

    def __init__(self, client: SenderClient):
        self.client = client

    def send(
        self,
        *,
        recipient: str,
        reporter_name: str,
        event_type: str,
        message: str,
        reference: str,
        feedback_id: int,
    ) -> DeliveryResult:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", recipient):
            return DeliveryResult(
                False, "invalid_recipient", "Reporter contact is not a valid email"
            )
        email = render_email(
            event_type=event_type,
            reporter_name=reporter_name,
            reference=reference,
            message=message,
            feedback_id=feedback_id,
        )
        return self.client.send_email(
            recipient=recipient,
            subject=email.subject,
            body=email.body,
            html_body=email.html_body,
        )
