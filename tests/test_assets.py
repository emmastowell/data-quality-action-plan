def test_create_and_get_asset(client):
    r = client.post("/api/assets", json={"name": "UK Ship Register", "criticality": "high"})
    assert r.status_code == 201, r.text
    asset = r.json()
    assert asset["name"] == "UK Ship Register"
    assert asset["created_by"] == "tester@gov.uk"   # from X-Forwarded-Email
    got = client.get(f"/api/assets/{asset['id']}")
    assert got.status_code == 200 and got.json()["id"] == asset["id"]

def test_list_and_update_asset(client):
    aid = client.post("/api/assets", json={"name": "Seafarer CoC"}).json()["id"]
    assert any(a["id"] == aid for a in client.get("/api/assets").json())
    up = client.patch(f"/api/assets/{aid}", json={"status": "active", "owner_email": "owner@gov.uk"})
    assert up.status_code == 200 and up.json()["status"] == "active"

def test_get_missing_asset_404(client):
    r = client.get("/api/assets/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"

def test_archive_asset(client):
    aid = client.post("/api/assets", json={"name": "Temp"}).json()["id"]
    d = client.delete(f"/api/assets/{aid}")
    assert d.status_code == 200
    assert client.get(f"/api/assets/{aid}").json()["status"] == "archived"


def test_asset_defaults_to_critical_kind(client):
    aid = client.post("/api/assets", json={"name": "Kind Default"}).json()
    assert aid["kind"] == "critical"


def test_asset_kind_monitored_round_trips(client):
    a = client.post("/api/assets", json={"name": "Monitored A", "kind": "monitored"}).json()
    assert a["kind"] == "monitored"
    got = client.get(f"/api/assets/{a['id']}").json()
    assert got["kind"] == "monitored"


def test_asset_kind_patch_updates(client):
    a = client.post("/api/assets", json={"name": "Kind Patch"}).json()
    upd = client.patch(f"/api/assets/{a['id']}", json={"kind": "monitored"}).json()
    assert upd["kind"] == "monitored"
