def _create_routed_issue(client):
    feedback_id = client.post(
        "/feedback",
        json={
            "name": "Workflow Tester",
            "contact": "workflow@example.com",
            "content": "Marks are missing from the student portal",
        },
    ).json()["id"]
    return client.post(f"/feedback/{feedback_id}/route").json()["issue"]


def test_phase5_workflow_reaches_closed_state(client):
    issue = _create_routed_issue(client)
    issue_id = issue["id"]

    assert (
        client.post(f"/issues/{issue_id}/acknowledge").json()["issue"]["status"]
        == "ACKNOWLEDGED"
    )
    assert client.post(f"/issues/{issue_id}/start").json()["issue"]["status"] == (
        "IN_PROGRESS"
    )
    completed = client.post(
        f"/issues/{issue_id}/complete",
        json={"resolution": "Corrected the marks in the student portal."},
    )
    assert completed.status_code == 200
    assert completed.json()["issue"]["status"] == "AWAITING_CONFIRMATION"
    assert completed.json()["issue"]["resolution"] == (
        "Corrected the marks in the student portal."
    )
    assert (
        client.post(f"/issues/{issue_id}/confirm", json={"confirmed": True}).json()[
            "issue"
        ]["status"]
        == "CONFIRMED"
    )
    assert client.post(f"/issues/{issue_id}/close").json()["issue"]["status"] == (
        "CLOSED"
    )


def test_phase5_failed_confirmation_reopens_work(client):
    issue_id = _create_routed_issue(client)["id"]
    client.post(f"/issues/{issue_id}/acknowledge")
    client.post(f"/issues/{issue_id}/start")
    client.post(f"/issues/{issue_id}/complete", json={"resolution": "Retry fix"})

    response = client.post(f"/issues/{issue_id}/confirm", json={"confirmed": False})

    assert response.status_code == 200
    assert response.json()["issue"]["status"] == "IN_PROGRESS"


def test_phase5_rejects_invalid_transition_and_payload(client):
    issue_id = _create_routed_issue(client)["id"]

    invalid_transition = client.post(f"/issues/{issue_id}/close")
    assert invalid_transition.status_code == 409
    assert invalid_transition.json()["detail"]["error"]["code"] == (
        "invalid_transition"
    )

    invalid_payload = client.post(
        f"/issues/{issue_id}/complete", json={"resolution": ""}
    )
    assert invalid_payload.status_code == 422
