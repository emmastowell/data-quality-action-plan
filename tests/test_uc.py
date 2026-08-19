"""Tests for UC browse endpoints using the mock seam (no real Databricks needed)."""
import pytest
import server.uc as uc


class _FakeUC:
    def list_catalogs(self):
        return ["cat_a", "cat_b"]

    def list_schemas(self, catalog: str):
        return ["schema_x", "schema_y"]

    def list_tables(self, catalog: str, schema: str):
        return [
            {"name": "tbl_1", "full_name": f"{catalog}.{schema}.tbl_1", "table_type": None},
            {"name": "tbl_2", "full_name": f"{catalog}.{schema}.tbl_2", "table_type": None},
        ]


@pytest.fixture(autouse=True)
def fake_uc():
    """Inject a fake UC provider; restore to None after each test."""
    uc.set_uc_provider(_FakeUC())
    yield
    uc.set_uc_provider(None)


def test_list_catalogs(client):
    r = client.get("/api/uc/catalogs")
    assert r.status_code == 200
    assert r.json() == {"catalogs": ["cat_a", "cat_b"]}


def test_list_schemas(client):
    r = client.get("/api/uc/schemas?catalog=cat_a")
    assert r.status_code == 200
    assert r.json() == {"schemas": ["schema_x", "schema_y"]}


def test_list_schemas_missing_catalog_returns_400(client):
    r = client.get("/api/uc/schemas")
    assert r.status_code == 400


def test_list_tables(client):
    r = client.get("/api/uc/tables?catalog=cat_a&schema=schema_x")
    assert r.status_code == 200
    data = r.json()
    assert len(data["tables"]) == 2
    assert data["tables"][0]["full_name"] == "cat_a.schema_x.tbl_1"
    assert data["tables"][1]["name"] == "tbl_2"


def test_list_tables_missing_schema_returns_400(client):
    r = client.get("/api/uc/tables?catalog=cat_a")
    assert r.status_code == 400


def test_list_tables_missing_both_returns_400(client):
    r = client.get("/api/uc/tables")
    assert r.status_code == 400
