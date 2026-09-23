from app.services.qa_service import QAService


def _create_issue(client):
    feedback_id = client.post(
        "/feedback",
        json={
            "name": "QA Manager",
            "contact": "qa-manager@example.com",
            "content": "Marks missing from portal",
        },
    ).json()["id"]
    return client.post(f"/feedback/{feedback_id}/route").json()["issue"]


def test_phase8_dashboard_summarizes_issue_status_and_next_action(client):
    issue = _create_issue(client)

    response = client.get("/qa/dashboard")

    assert response.status_code == 200
    assert response.json()["total_issues"] == 1
    assert response.json()["by_status"]["ROUTED"] == 1
    assert response.json()["issues"][0]["id"] == issue["id"]
    assert response.json()["issues"][0]["next_action"] == "Acknowledge issue"


def test_phase8_issue_detail_exposes_timeline_and_notifications(client, db_session):
    issue = _create_issue(client)

    detail = QAService(db_session).issue_detail(issue["id"])
    response = client.get(f"/qa/issues/{issue['id']}")

    assert response.status_code == 200
    assert detail is not None
    assert response.json()["issue"]["reference"] == issue["reference"]
    assert len(response.json()["events"]) == 3
    assert response.json()["notification_count"] == 1


def test_phase8_missing_issue_returns_not_found(client):
    response = client.get("/qa/issues/999")

    assert response.status_code == 404
