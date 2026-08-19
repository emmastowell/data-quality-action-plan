def _seed_one(client):
    aid = client.post("/api/assets", json={"name": "Ship Register", "status": "active"}).json()["id"]
    rid = client.post(f"/api/assets/{aid}/rules",
                      json={"name": "IMO present", "dimension": "completeness", "target_threshold": 99}).json()["id"]
    client.post(f"/api/rules/{rid}/measurements", json={"score": 88, "measured_at": "2026-01-01T00:00:00Z"})
    client.post(f"/api/rules/{rid}/measurements", json={"score": 95, "measured_at": "2026-06-01T00:00:00Z"})
    return aid


def test_dashboard_uses_latest_scores(client):
    _seed_one(client)
    d = client.get("/api/dashboard").json()
    assert d["asset_count"] == 1 and d["active_asset_count"] == 1
    assert d["overall_score"] == 95                      # latest, not 88
    assert d["score_by_dimension"]["completeness"] == 95
    assert d["score_by_dimension"]["accuracy"] is None   # no rules
    assert d["assets_at_risk"][0]["failing_rules"] == 1  # 95 < 99 threshold


def test_dashboard_counts_issues_and_actions(client):
    aid = _seed_one(client)
    client.post(f"/api/assets/{aid}/issues", json={"title": "dupes", "status": "open"})
    client.post(f"/api/assets/{aid}/actions", json={"title": "fix", "status": "in_progress"})
    d = client.get("/api/dashboard").json()
    assert d["open_issue_count"] == 1 and d["actions_in_progress"] == 1


def test_dashboard_blocked_issue_included_in_open_count(client):
    """A 'blocked' issue must be included in open_issue_count (it is unresolved)."""
    aid = _seed_one(client)
    iid = client.post(f"/api/assets/{aid}/issues", json={"title": "blocked issue"}).json()["id"]
    # Resolved issue should NOT count
    client.post(f"/api/assets/{aid}/issues", json={"title": "resolved issue", "status": "resolved"})
    client.patch(f"/api/issues/{iid}", json={"status": "blocked"})
    d = client.get("/api/dashboard").json()
    # Only the blocked issue counts (resolved one excluded)
    assert d["open_issue_count"] == 1


def test_dashboard_splits_counts_by_kind(client):
    client.post("/api/assets", json={"name": "Crit 1", "kind": "critical", "status": "active"})
    client.post("/api/assets", json={"name": "Mon 1", "kind": "monitored", "status": "active"})
    client.post("/api/assets", json={"name": "Mon 2", "kind": "monitored", "status": "draft"})
    d = client.get("/api/dashboard").json()
    assert d["critical_asset_count"] == 1
    assert d["critical_active_count"] == 1
    assert d["monitored_asset_count"] == 2
    assert d["monitored_active_count"] == 1
