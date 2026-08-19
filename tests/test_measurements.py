def _rule(client):
    aid = client.post("/api/assets", json={"name": "Ship Register"}).json()["id"]
    return client.post(f"/api/assets/{aid}/rules",
                       json={"name": "IMO unique", "dimension": "uniqueness"}).json()["id"]


def test_record_measurement_via_manual_provider(client):
    rid = _rule(client)
    r = client.post(f"/api/rules/{rid}/measurements",
                    json={"score": 97.2, "evidence_note": "dup scan", "sample_size": 5000})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["score"] == 97.2 and body["source"] == "manual" and body["method"] == "manual"


def test_list_measurements_is_time_ascending(client):
    rid = _rule(client)
    client.post(f"/api/rules/{rid}/measurements", json={"score": 90, "measured_at": "2026-01-01T00:00:00Z"})
    client.post(f"/api/rules/{rid}/measurements", json={"score": 95, "measured_at": "2026-06-01T00:00:00Z"})
    scores = [m["score"] for m in client.get(f"/api/rules/{rid}/measurements").json()]
    assert scores == [90, 95]


def test_measure_missing_rule_404(client):
    r = client.post("/api/rules/00000000-0000-0000-0000-000000000000/measurements", json={"score": 1})
    assert r.status_code == 404


def test_latest_by_rule_returns_newest(client, db_conn):
    from server.repositories.measurements import latest_by_rule
    rid = _rule(client)
    client.post(f"/api/rules/{rid}/measurements", json={"score": 90, "measured_at": "2026-01-01T00:00:00Z"})
    client.post(f"/api/rules/{rid}/measurements", json={"score": 95, "measured_at": "2026-06-01T00:00:00Z"})
    latest = latest_by_rule(db_conn, rid)
    assert latest is not None and float(latest["score"]) == 95
