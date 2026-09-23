from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def run_demo() -> int:
    with TestClient(app) as client:
        feedback = client.post(
            "/feedback",
            json={
                "name": "Demo Reporter",
                "contact": "demo-reporter@example.com",
                "content": "My marks are missing from the student portal",
                "channel": "demo",
            },
        )
        feedback.raise_for_status()
        feedback_id = feedback.json()["id"]

        routed = client.post(f"/feedback/{feedback_id}/route")
        routed.raise_for_status()
        issue_id = routed.json()["issue"]["id"]

        actions = [
            (f"/issues/{issue_id}/acknowledge", None),
            (f"/issues/{issue_id}/start", None),
            (
                f"/issues/{issue_id}/complete",
                {"resolution": "Corrected the marks in the student portal."},
            ),
            (f"/issues/{issue_id}/confirm", {"confirmed": True}),
            (f"/issues/{issue_id}/close", None),
        ]
        for path, payload in actions:
            response = client.post(path, json=payload)
            response.raise_for_status()

        issue = client.get(f"/issues/{issue_id}")
        notifications = client.get(f"/issues/{issue_id}/notifications")
        issue.raise_for_status()
        notifications.raise_for_status()

        print(f"Demo issue: {issue.json()['reference']}")
        print(f"Final status: {issue.json()['status']}")
        print(f"Notifications: {len(notifications.json())}")
        return 0


if __name__ == "__main__":
    raise SystemExit(run_demo())
