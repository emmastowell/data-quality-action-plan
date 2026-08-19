def _asset(client):
    return client.post("/api/assets", json={"name": "Ship Register", "status": "active"}).json()["id"]


def test_journey_reflects_progress(client):
    aid = _asset(client)                       # step 1 done (asset exists)
    j = {i["step"]: i["done"] for i in client.get(f"/api/assets/{aid}/journey").json()}
    assert j[1] is True and j[2] is False      # no rules yet
    rid = client.post(f"/api/assets/{aid}/rules",
                      json={"name": "IMO", "dimension": "validity"}).json()["id"]
    client.post(f"/api/rules/{rid}/measurements", json={"score": 99})
    client.post(f"/api/assets/{aid}/actions", json={"title": "fix"})
    j = {i["step"]: i["done"] for i in client.get(f"/api/assets/{aid}/journey").json()}
    assert j[2] is True and j[3] is True and j[4] is True


def test_journey_step7_true(client):
    aid = _asset(client)
    rid = client.post(f"/api/assets/{aid}/rules",
                      json={"name": "R", "dimension": "completeness"}).json()["id"]
    client.post(f"/api/rules/{rid}/measurements", json={"score": 80})
    client.post(f"/api/rules/{rid}/measurements", json={"score": 90})
    j = {i["step"]: i["done"] for i in client.get(f"/api/assets/{aid}/journey").json()}
    assert j[7] is True


def test_export_csv(client):
    aid = _asset(client)
    client.post(f"/api/assets/{aid}/rules", json={"name": "IMO", "dimension": "validity", "target_threshold": 99})
    r = client.get(f"/api/assets/{aid}/export?format=csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "dimension" in r.text and "IMO" in r.text
