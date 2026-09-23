def test_phase10_conversation_collects_messages(client):
    created = client.post(
        "/conversations",
        json={
            "reporter_name": "Conversation User",
            "reporter_contact": "conversation@example.com",
        },
    )
    assert created.status_code == 201
    conversation_id = created.json()["id"]
    assert created.json()["turns"] == []
    assert created.json()["status"] == "active"

    message = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "The portal rejects my submission."},
    )
    assert message.status_code == 200
    assert message.json()["turns"][0]["role"] == "user"
    assert message.json()["turns"][0]["content"] == (
        "The portal rejects my submission."
    )


def test_phase10_submission_creates_one_conversation_feedback(client):
    conversation_id = client.post(
        "/conversations",
        json={
            "reporter_name": "Conversation User",
            "reporter_contact": "conversation@example.com",
        },
    ).json()["id"]
    client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "The portal rejects my submission."},
    )

    first = client.post(f"/conversations/{conversation_id}/submit")
    second = client.post(f"/conversations/{conversation_id}/submit")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["feedback_id"] == second.json()["feedback_id"]
    assert first.json()["conversation"]["status"] == "submitted"
    feedback = client.get(f"/feedback/{first.json()['feedback_id']}").json()
    assert feedback["channel"] == "conversation"
    assert feedback["content"] == "The portal rejects my submission."


def test_phase10_rejects_closed_or_invalid_conversations(client):
    anonymous_id = client.post("/conversations", json={}).json()["id"]
    empty_submit = client.post(f"/conversations/{anonymous_id}/submit")
    assert empty_submit.status_code == 422
    assert empty_submit.json()["detail"]["error"]["code"] == "reporter_required"

    created = client.post(
        "/conversations",
        json={
            "reporter_name": "Conversation User",
            "reporter_contact": "closed@example.com",
        },
    ).json()
    conversation_id = created["id"]
    client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "A report"},
    )
    client.post(f"/conversations/{conversation_id}/submit")

    closed_message = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "Another message"},
    )
    assert closed_message.status_code == 409
    assert client.get("/conversations/999").status_code == 404
