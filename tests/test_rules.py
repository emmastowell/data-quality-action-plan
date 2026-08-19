def _asset(client):
    return client.post("/api/assets", json={"name": "Ship Register"}).json()["id"]


def test_create_rule_with_dimension(client):
    aid = _asset(client)
    r = client.post(f"/api/assets/{aid}/rules",
                    json={"name": "IMO present", "dimension": "completeness", "target_threshold": 99.5})
    assert r.status_code == 201, r.text
    assert r.json()["dimension"] == "completeness" and r.json()["asset_id"] == aid


def test_duplicate_rule_name_conflicts(client):
    aid = _asset(client)
    body = {"name": "IMO valid", "dimension": "validity"}
    assert client.post(f"/api/assets/{aid}/rules", json=body).status_code == 201
    assert client.post(f"/api/assets/{aid}/rules", json=body).status_code == 409


def test_list_update_delete_rule(client):
    aid = _asset(client)
    rid = client.post(f"/api/assets/{aid}/rules",
                      json={"name": "Tonnage accurate", "dimension": "accuracy"}).json()["id"]
    assert len(client.get(f"/api/assets/{aid}/rules").json()) == 1
    assert client.patch(f"/api/rules/{rid}", json={"target_threshold": 98}).json()["target_threshold"] == 98
    assert client.delete(f"/api/rules/{rid}").status_code == 200
    assert client.get(f"/api/assets/{aid}/rules").json() == []


def test_patch_unknown_rule_returns_404(client):
    assert client.patch("/api/rules/00000000-0000-0000-0000-000000000000", json={"target_threshold": 50}).status_code == 404


def test_delete_unknown_rule_returns_404(client):
    assert client.delete("/api/rules/00000000-0000-0000-0000-000000000000").status_code == 404
