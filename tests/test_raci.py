def test_seed_populates_default_roles_and_cells(client):
    m = client.get("/api/raci").json()
    assert len(m["roles"]) == 7
    assert len(m["activities"]) == 30
    # a known default cell: step 1, activity 0, Data steward = "R"
    role_by_name = {r["name"]: r["id"] for r in m["roles"]}
    steward = role_by_name["Data steward / Business SME"]
    assert m["cells"]["s1-0"][steward] == "R"


def test_add_role_appends_and_is_returned(client):
    r = client.post("/api/raci/roles", json={"name": "Records manager"})
    assert r.status_code == 201, r.text
    m = client.get("/api/raci").json()
    assert any(role["name"] == "Records manager" for role in m["roles"])


def test_add_duplicate_role_conflicts(client):
    client.post("/api/raci/roles", json={"name": "Dup role"})
    r = client.post("/api/raci/roles", json={"name": "Dup role"})
    assert r.status_code == 409


def test_delete_role_removes_it_and_its_cells(client):
    rid = client.post("/api/raci/roles", json={"name": "Temp role"}).json()["id"]
    client.put("/api/raci/cells", json={"activity_key": "s1-0", "role_id": rid, "value": "C"})
    assert client.delete(f"/api/raci/roles/{rid}").status_code == 200
    m = client.get("/api/raci").json()
    assert all(role["id"] != rid for role in m["roles"])
    assert rid not in m["cells"].get("s1-0", {})


def test_cell_upsert_inserts_then_updates(client):
    rid = client.post("/api/raci/roles", json={"name": "Cell role"}).json()["id"]
    client.put("/api/raci/cells", json={"activity_key": "s2-0", "role_id": rid, "value": "R"})
    assert client.get("/api/raci").json()["cells"]["s2-0"][rid] == "R"
    client.put("/api/raci/cells", json={"activity_key": "s2-0", "role_id": rid, "value": "A"})
    assert client.get("/api/raci").json()["cells"]["s2-0"][rid] == "A"


def test_cell_unknown_activity_key_rejected(client):
    rid = client.post("/api/raci/roles", json={"name": "Bad key role"}).json()["id"]
    r = client.put("/api/raci/cells", json={"activity_key": "s9-99", "role_id": rid, "value": "R"})
    assert r.status_code == 422


def test_delete_role_malformed_uuid_returns_404(client):
    r = client.delete("/api/raci/roles/not-a-uuid")
    assert r.status_code == 404


def test_put_cell_malformed_role_id_returns_422(client):
    r = client.put("/api/raci/cells", json={"activity_key": "s1-0", "role_id": "not-a-uuid", "value": "R"})
    assert r.status_code == 422


def test_add_role_blank_name_returns_422(client):
    r = client.post("/api/raci/roles", json={"name": "   "})
    assert r.status_code == 422


def test_clear_cell_removes_it_from_matrix(client):
    rid = client.post("/api/raci/roles", json={"name": "Clearable role"}).json()["id"]
    client.put("/api/raci/cells", json={"activity_key": "s3-0", "role_id": rid, "value": "I"})
    assert client.get("/api/raci").json()["cells"].get("s3-0", {}).get(rid) == "I"
    client.put("/api/raci/cells", json={"activity_key": "s3-0", "role_id": rid, "value": ""})
    assert rid not in client.get("/api/raci").json()["cells"].get("s3-0", {})


def test_rename_role_updates_name(client):
    rid = client.post("/api/raci/roles", json={"name": "Old name"}).json()["id"]
    r = client.patch(f"/api/raci/roles/{rid}", json={"name": "New name"})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "New name"
    m = client.get("/api/raci").json()
    assert any(role["id"] == rid and role["name"] == "New name" for role in m["roles"])


def test_rename_role_blank_returns_422(client):
    rid = client.post("/api/raci/roles", json={"name": "Renamable"}).json()["id"]
    assert client.patch(f"/api/raci/roles/{rid}", json={"name": "   "}).status_code == 422


def test_rename_role_duplicate_returns_409(client):
    client.post("/api/raci/roles", json={"name": "Existing role"})
    rid = client.post("/api/raci/roles", json={"name": "Another role"}).json()["id"]
    assert client.patch(f"/api/raci/roles/{rid}", json={"name": "Existing role"}).status_code == 409


def test_rename_role_missing_returns_404(client):
    r = client.patch("/api/raci/roles/00000000-0000-0000-0000-000000000000", json={"name": "X"})
    assert r.status_code == 404
