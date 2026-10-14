from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class DeliveryResult:
    delivered: bool
    error_type: str | None = None
    error_message: str | None = None


class SenderClient:
    def __init__(
        self,
        *,
        api_key: str,
        api_url: str,
        from_email: str,
        from_name: str,
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.api_url = api_url
        self.from_email = from_email
        self.from_name = from_name
        self.timeout = timeout

    def send_email(
        self,
        *,
        recipient: str,
        subject: str,
        body: str,
        html_body: str | None = None,
    ) -> DeliveryResult:
        payload = {
            "from": {"email": self.from_email, "name": self.from_name},
            "to": [{"email": recipient}],
            "subject": subject,
            "text": body,
        }
        if html_body is not None:
            payload["html"] = html_body
        try:
            response = httpx.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException:
            return DeliveryResult(False, "timeout", "Sender request timed out")
        except httpx.HTTPStatusError as exc:
            return DeliveryResult(
                False,
                "http_error",
                f"Sender returned HTTP {exc.response.status_code}",
            )
        except httpx.RequestError:
            return DeliveryResult(False, "connection_error", "Sender connection failed")
        except ValueError:
            return DeliveryResult(
                False, "invalid_response", "Sender response was invalid"
            )
        return DeliveryResult(True)
