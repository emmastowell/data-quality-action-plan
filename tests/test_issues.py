def _asset(client):
    return client.post("/api/assets", json={"name": "Ship Register"}).json()["id"]


def test_create_issue_with_impact_tags(client):
    aid = _asset(client)
    r = client.post(f"/api/assets/{aid}/issues", json={
        "title": "Duplicate IMO numbers", "dimension": "uniqueness",
        "impact_tags": ["legal", "operational"], "severity": "high",
        "likelihood": "medium", "root_cause_category": "integration_etl"})
    assert r.status_code == 201, r.text
    assert r.json()["impact_tags"] == ["legal", "operational"]
    assert r.json()["status"] == "open"


def test_list_update_close_issue(client):
    aid = _asset(client)
    iid = client.post(f"/api/assets/{aid}/issues", json={"title": "Stale tonnage"}).json()["id"]
    assert len(client.get(f"/api/assets/{aid}/issues").json()) == 1
    up = client.patch(f"/api/issues/{iid}", json={"status": "resolved"})
    assert up.status_code == 200 and up.json()["status"] == "resolved"
    assert client.delete(f"/api/issues/{iid}").status_code == 200


def test_patch_unknown_issue_returns_404(client):
    assert client.patch("/api/issues/00000000-0000-0000-0000-000000000000", json={"status": "resolved"}).status_code == 404


def test_delete_unknown_issue_returns_404(client):
    assert client.delete("/api/issues/00000000-0000-0000-0000-000000000000").status_code == 404


def test_create_issue_with_extended_fields(client):
    """New DQAP fields round-trip correctly and audit fields are surfaced."""
    aid = _asset(client)
    r = client.post(f"/api/assets/{aid}/issues", json={
        "title": "Timeliness lag in regional offices",
        "description": "Status updates trail survey sign-off by two weeks.",
        "dimension": "timeliness",
        "severity": "high",
        "likelihood": "high",
        "root_cause_category": "process_gap",
        "reported_by": "survey.ops@mca.gov.uk",
        "assigned_to": "ops.lead@mca.gov.uk",
        "business_area": "Registry Operations",
        "priority": "high",
        "contributing_factors": "Manual handoff between survey team and clerical staff.",
        "root_cause_detail": "No API integration; staff must poll and update manually.",
        "status_date": "2026-06-30",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["reported_by"] == "survey.ops@mca.gov.uk"
    assert body["assigned_to"] == "ops.lead@mca.gov.uk"
    assert body["business_area"] == "Registry Operations"
    assert body["priority"] == "high"
    assert body["contributing_factors"] == "Manual handoff between survey team and clerical staff."
    assert body["root_cause_detail"] == "No API integration; staff must poll and update manually."
    assert body["status_date"] == "2026-06-30"
    # Audit fields are surfaced on the read model
    assert body["created_by"] == "tester@gov.uk"
    assert body["updated_by"] == "tester@gov.uk"


def test_issue_status_blocked_accepted(client):
    """'blocked' is a valid issue status value."""
    aid = _asset(client)
    iid = client.post(f"/api/assets/{aid}/issues", json={"title": "Blocked issue"}).json()["id"]
    r = client.patch(f"/api/issues/{iid}", json={"status": "blocked"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "blocked"
