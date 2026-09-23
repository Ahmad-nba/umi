from app.core.enums import EventType
from app.models.event import Event
from app.models.handler import Handler
from app.models.issue import Issue
from app.services.routing_service import RoutingService


def test_phase4_routes_to_active_department_handler(db_session):
    handler = Handler(
        name="IT Support",
        department="IT",
        contact="it@umi.ac.ug",
        active=True,
    )
    db_session.add(handler)
    db_session.commit()

    assigned = RoutingService(db_session).route_issue("IT")

    assert assigned.id == handler.id
    assert assigned.department == "IT"


def test_phase4_feedback_becomes_assigned_issue_with_events(client, db_session):
    feedback_id = client.post(
        "/feedback",
        json={
            "name": "Grace",
            "contact": "grace@example.com",
            "content": "My marks are missing from the student portal",
        },
    ).json()["id"]

    response = client.post(f"/feedback/{feedback_id}/route")

    assert response.status_code == 200
    issue_data = response.json()["issue"]
    assert issue_data["feedback_id"] == feedback_id
    assert issue_data["department"] == "Academic Affairs"
    assert issue_data["handler_id"] is not None
    assert issue_data["status"] == "ROUTED"

    persisted_issue = db_session.query(Issue).filter_by(id=issue_data["id"]).one()
    events = (
        db_session.query(Event)
        .filter(Event.issue_id == persisted_issue.id)
        .order_by(Event.id)
        .all()
    )
    assert [event.event_type for event in events] == [
        EventType.FEEDBACK_CLASSIFIED.value,
        EventType.ISSUE_CREATED.value,
        EventType.ISSUE_ROUTED.value,
    ]


def test_phase4_route_is_idempotent_and_issue_is_retrievable(client):
    feedback_id = client.post(
        "/feedback",
        json={
            "name": "Grace",
            "contact": "grace@example.com",
            "content": "The student portal is unavailable",
        },
    ).json()["id"]

    first = client.post(f"/feedback/{feedback_id}/route").json()["issue"]
    second = client.post(f"/feedback/{feedback_id}/route").json()["issue"]

    assert second["id"] == first["id"]
    assert (
        client.get(f"/issues/{first['id']}").json()["reference"] == first["reference"]
    )
    assert len(client.get("/issues").json()) == 1
