"""Tests for asset_tables CRUD endpoints (pure Postgres, no UC needed)."""


def _create_asset(client, name="Test Asset"):
    r = client.post("/api/assets", json={"name": name, "criticality": "medium"})
    assert r.status_code == 201, r.json()
    return r.json()


def test_list_empty(client):
    asset = _create_asset(client)
    r = client.get(f"/api/assets/{asset['id']}/tables")
    assert r.status_code == 200
    assert r.json() == []


def test_create_and_list(client):
    asset = _create_asset(client)
    body = {"catalog_name": "my_cat", "schema_name": "my_schema", "table_name": "my_table"}
    r = client.post(f"/api/assets/{asset['id']}/tables", json=body)
    assert r.status_code == 201
    data = r.json()
    assert data["full_name"] == "my_cat.my_schema.my_table"
    assert data["asset_id"] == asset["id"]
    assert data["catalog_name"] == "my_cat"
    assert data["schema_name"] == "my_schema"
    assert data["table_name"] == "my_table"
    assert "id" in data
    assert "created_at" in data

    rows = client.get(f"/api/assets/{asset['id']}/tables").json()
    assert len(rows) == 1
    assert rows[0]["full_name"] == "my_cat.my_schema.my_table"


def test_create_two_tables_listed(client):
    asset = _create_asset(client)
    for tbl in ["table_a", "table_b"]:
        r = client.post(
            f"/api/assets/{asset['id']}/tables",
            json={"catalog_name": "c", "schema_name": "s", "table_name": tbl},
        )
        assert r.status_code == 201

    rows = client.get(f"/api/assets/{asset['id']}/tables").json()
    assert len(rows) == 2
    full_names = {row["full_name"] for row in rows}
    assert full_names == {"c.s.table_a", "c.s.table_b"}


def test_duplicate_returns_409(client):
    asset = _create_asset(client)
    body = {"catalog_name": "c", "schema_name": "s", "table_name": "t"}
    r1 = client.post(f"/api/assets/{asset['id']}/tables", json=body)
    assert r1.status_code == 201
    r2 = client.post(f"/api/assets/{asset['id']}/tables", json=body)
    assert r2.status_code == 409


def test_delete_removes_table(client):
    asset = _create_asset(client)
    r = client.post(
        f"/api/assets/{asset['id']}/tables",
        json={"catalog_name": "c", "schema_name": "s", "table_name": "t"},
    )
    tid = r.json()["id"]

    del_r = client.delete(f"/api/asset-tables/{tid}")
    assert del_r.status_code == 200
    assert del_r.json() == {"deleted": True}

    rows = client.get(f"/api/assets/{asset['id']}/tables").json()
    assert rows == []


def test_delete_missing_returns_404(client):
    r = client.delete("/api/asset-tables/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_nonexistent_asset_returns_422(client):
    r = client.post(
        "/api/assets/00000000-0000-0000-0000-000000000000/tables",
        json={"catalog_name": "c", "schema_name": "s", "table_name": "t"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_reference"
