def _asset(client):
    return client.post("/api/assets", json={"name": "Ship Register"}).json()["id"]


def test_create_action_with_assignee_and_due(client):
    aid = _asset(client)
    r = client.post(f"/api/assets/{aid}/actions", json={
        "title": "Add IMO uniqueness constraint", "remediation_type": "etl_fix",
        "priority": "high", "assignee_email": "eng@gov.uk", "due_date": "2026-09-30"})
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "todo" and r.json()["assignee_email"] == "eng@gov.uk"


def test_progress_and_complete_action(client):
    aid = _asset(client)
    aid2 = client.post(f"/api/assets/{aid}/actions", json={"title": "Backfill owners"}).json()["id"]
    assert client.patch(f"/api/actions/{aid2}", json={"status": "in_progress"}).json()["status"] == "in_progress"
    # 'complete' is the canonical terminal status
    assert client.patch(f"/api/actions/{aid2}", json={"status": "complete"}).json()["status"] == "complete"
    # 'done' is retained as a legacy alias and must still be accepted
    assert client.patch(f"/api/actions/{aid2}", json={"status": "done"}).json()["status"] == "done"
    assert client.delete(f"/api/actions/{aid2}").status_code == 200


def test_patch_unknown_action_returns_404(client):
    assert client.patch("/api/actions/00000000-0000-0000-0000-000000000000", json={"status": "done"}).status_code == 404


def test_delete_unknown_action_returns_404(client):
    assert client.delete("/api/actions/00000000-0000-0000-0000-000000000000").status_code == 404


def test_create_action_with_extended_fields(client):
    """New date and notes fields round-trip correctly and audit fields are surfaced."""
    aid = _asset(client)
    r = client.post(f"/api/assets/{aid}/actions", json={
        "title": "Automate renewal-status update",
        "description": "Trigger status update from survey workflow.",
        "remediation_type": "process",
        "priority": "high",
        "assignee_email": "ops.lead@mca.gov.uk",
        "start_date": "2026-04-01",
        "review_date": "2026-07-01",
        "completed_date": "2026-06-28",
        "success_criteria": "Renewal status updated within 24h of survey sign-off for ≥98% of cases.",
        "notes": "API integration delivered in Sprint 14.",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["start_date"] == "2026-04-01"
    assert body["review_date"] == "2026-07-01"
    assert body["completed_date"] == "2026-06-28"
    assert body["success_criteria"] == "Renewal status updated within 24h of survey sign-off for ≥98% of cases."
    assert body["notes"] == "API integration delivered in Sprint 14."
    # Audit fields are surfaced on the read model
    assert body["created_by"] == "tester@gov.uk"
    assert body["updated_by"] == "tester@gov.uk"


def test_action_status_complete_accepted(client):
    """'complete' is a valid action status value."""
    aid = _asset(client)
    aid2 = client.post(f"/api/assets/{aid}/actions", json={"title": "Fix uniqueness"}).json()["id"]
    r = client.patch(f"/api/actions/{aid2}", json={"status": "complete"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "complete"
