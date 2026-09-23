from app.services.feedback_service import FeedbackService


def test_create_feedback_persists_reporter_and_feedback(db_session):
    service = FeedbackService(db_session)
    feedback = service.create_feedback(
        name="Ada",
        contact="ada@example.com",
        content="Student portal is broken",
        channel="form",
        context="Submission context",
    )

    assert feedback.id is not None
    assert feedback.reporter.name == "Ada"
    assert feedback.channel == "form"
    assert feedback.content == "Student portal is broken"


def test_create_feedback_reuses_reporter_for_same_contact(db_session):
    service = FeedbackService(db_session)

    first = service.create_feedback(
        name="Ada",
        contact="ada@example.com",
        content="First report",
    )
    second = service.create_feedback(
        name="Ada Updated",
        contact="ada@example.com",
        content="Second report",
    )

    assert first.reporter_id == second.reporter_id
    assert len(service.list_feedback()) == 2


def test_feedback_endpoints_list_and_return_not_found(client):
    assert client.get("/feedback").status_code == 200

    response = client.get("/feedback/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Feedback not found"


def test_feedback_endpoints_return_created_record(client):
    payload = {
        "name": "Grace",
        "contact": "grace@example.com",
        "content": "Marks missing",
        "channel": "form",
        "context": "Student portal",
    }
    response = client.post("/feedback", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Marks missing"
    assert data["reporter_id"] is not None


def test_feedback_endpoint_rejects_whitespace_only_fields(client):
    response = client.post(
        "/feedback",
        json={
            "name": "   ",
            "contact": "grace@example.com",
            "content": "Marks missing",
        },
    )

    assert response.status_code == 422


def test_feedback_endpoint_processes_feedback_with_local_fallback(client):
    create_response = client.post(
        "/feedback",
        json={
            "name": "Grace",
            "contact": "grace@example.com",
            "content": "My marks are missing from the student portal",
        },
    )
    feedback_id = create_response.json()["id"]

    response = client.post(f"/feedback/{feedback_id}/process")

    assert response.status_code == 200
    assert response.json()["status"] == "PROCESSED"
    assert response.json()["analysis"]["department"] == "Academic Affairs"
    assert client.get(f"/feedback/{feedback_id}").json()["status"] == "PROCESSED"


def test_feedback_endpoint_process_returns_not_found(client):
    response = client.post("/feedback/999/process")

    assert response.status_code == 404
    assert response.json()["detail"] == "Feedback not found"


def test_feedback_can_be_routed_to_an_assigned_issue(client):
    create_response = client.post(
        "/feedback",
        json={
            "name": "Grace",
            "contact": "grace@example.com",
            "content": "My marks are missing from the student portal",
        },
    )
    feedback_id = create_response.json()["id"]

    response = client.post(f"/feedback/{feedback_id}/route")

    assert response.status_code == 200
    issue = response.json()["issue"]
    assert issue["feedback_id"] == feedback_id
    assert issue["department"] == "Academic Affairs"
    assert issue["handler_id"] is not None
    assert issue["status"] == "ROUTED"
    assert client.get(f"/feedback/{feedback_id}").json()["status"] == "PROCESSED"
    assert (
        client.get(f"/issues/{issue['id']}").json()["reference"] == issue["reference"]
    )


def test_feedback_route_is_idempotent(client):
    create_response = client.post(
        "/feedback",
        json={
            "name": "Grace",
            "contact": "grace@example.com",
            "content": "The student portal is unavailable",
        },
    )
    feedback_id = create_response.json()["id"]

    first = client.post(f"/feedback/{feedback_id}/route").json()["issue"]
    second = client.post(f"/feedback/{feedback_id}/route").json()["issue"]

    assert second["id"] == first["id"]
    assert client.get("/issues").json()[-1]["id"] == first["id"]
