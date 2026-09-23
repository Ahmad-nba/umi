from app.core.enums import EventType, IssueStatus
from app.models.event import Event


def test_phase7_complete_lifecycle_is_visible_through_public_api(client, db_session):
    feedback_id = client.post(
        "/feedback",
        json={
            "name": "Lifecycle Tester",
            "contact": "lifecycle@example.com",
            "content": "My marks are missing from the student portal",
        },
    ).json()["id"]
    issue_id = client.post(f"/feedback/{feedback_id}/route").json()["issue"]["id"]

    client.post(f"/issues/{issue_id}/acknowledge")
    client.post(f"/issues/{issue_id}/start")
    client.post(
        f"/issues/{issue_id}/complete",
        json={"resolution": "Updated the portal marks."},
    )
    client.post(f"/issues/{issue_id}/confirm", json={"confirmed": True})
    final_response = client.post(f"/issues/{issue_id}/close")

    assert final_response.status_code == 200
    assert final_response.json()["issue"]["status"] == IssueStatus.CLOSED.value
    assert client.get(f"/feedback/{feedback_id}").json()["status"] == "PROCESSED"
    assert client.get(f"/issues/{issue_id}").json()["status"] == "CLOSED"
    assert client.get(f"/issues/{issue_id}/notifications").status_code == 200

    event_types = [
        event.event_type
        for event in db_session.query(Event)
        .filter(Event.issue_id == issue_id)
        .order_by(Event.id)
        .all()
    ]
    assert EventType.ISSUE_ROUTED.value in event_types
    assert EventType.TASK_COMPLETED.value in event_types
    assert EventType.CONFIRMATION_REQUESTED.value in event_types
    assert EventType.ISSUE_CLOSED.value in event_types
