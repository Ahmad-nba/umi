from app.services.feedback_service import FeedbackService


def test_phase2_feedback_persists_reporter_and_feedback(db_session):
    feedback = FeedbackService(db_session).create_feedback(
        name="Ada",
        contact="ada@example.com",
        content="Student portal is broken",
        channel="form",
        context="Submission context",
    )

    assert feedback.id is not None
    assert feedback.reporter.name == "Ada"
    assert feedback.reporter.contact == "ada@example.com"
    assert feedback.status == "RECEIVED"


def test_phase2_feedback_reuses_reporter_by_contact(db_session):
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


def test_phase2_feedback_api_validates_and_retrieves_records(client):
    response = client.post(
        "/feedback",
        json={
            "name": "  Grace  ",
            "contact": "grace@example.com",
            "content": "  Marks missing  ",
        },
    )

    assert response.status_code == 201
    feedback_id = response.json()["id"]
    assert response.json()["content"] == "Marks missing"
    assert client.get(f"/feedback/{feedback_id}").status_code == 200
    assert client.get("/feedback/999").status_code == 404

    invalid = client.post(
        "/feedback",
        json={
            "name": "   ",
            "contact": "grace@example.com",
            "content": "Marks missing",
        },
    )
    assert invalid.status_code == 422
