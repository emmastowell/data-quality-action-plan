"""Tests for warehouse SQL measurement endpoints and provider.

Uses set_sql_runner to inject a fake numeric result — no Databricks credentials needed.
"""
import pytest
from server.providers.warehouse import set_sql_runner


@pytest.fixture(autouse=True)
def reset_sql_runner():
    """Always reset the SQL runner mock after each test."""
    yield
    set_sql_runner(None)


def _asset(client, status="active"):
    return client.post("/api/assets", json={"name": "Measure Test Asset", "status": status}).json()["id"]


_rule_counter = [0]


def _rule(client, asset_id, *, sql=None, name=None):
    _rule_counter[0] += 1
    if name is None:
        name = f"Rule {_rule_counter[0]}"
    body = {"name": name, "dimension": "completeness"}
    if sql is not None:
        body["measurement_sql"] = sql
    return client.post(f"/api/assets/{asset_id}/rules", json=body).json()["id"]


# ─── POST /api/rules/{rule_id}/measure/run ────────────────────────────────────

def test_run_measure_returns_warehouse_measurement(client):
    set_sql_runner(lambda sql: 96.5)
    aid = _asset(client)
    rid = _rule(client, aid, sql="SELECT 96.5")
    r = client.post(f"/api/rules/{rid}/measure/run")
    assert r.status_code == 200, r.text
    body = r.json()
    assert float(body["score"]) == 96.5
    assert body["source"] == "warehouse"
    assert body["method"] == "automated"


def test_run_measure_persists_to_measurements(client):
    set_sql_runner(lambda sql: 96.5)
    aid = _asset(client)
    rid = _rule(client, aid, sql="SELECT 96.5")
    client.post(f"/api/rules/{rid}/measure/run")
    measurements = client.get(f"/api/rules/{rid}/measurements").json()
    assert len(measurements) == 1
    assert float(measurements[0]["score"]) == 96.5
    assert measurements[0]["source"] == "warehouse"


def test_run_measure_no_sql_returns_400(client):
    set_sql_runner(lambda sql: 99.0)
    aid = _asset(client)
    rid = _rule(client, aid)  # no measurement_sql
    r = client.post(f"/api/rules/{rid}/measure/run")
    assert r.status_code == 400


def test_run_measure_unknown_rule_returns_404(client):
    r = client.post("/api/rules/00000000-0000-0000-0000-000000000000/measure/run")
    assert r.status_code == 404


# ─── POST /api/assets/{asset_id}/measure/run-all ─────────────────────────────

def test_run_all_only_includes_rules_with_sql(client):
    """Rules without measurement_sql are skipped and absent from results."""
    set_sql_runner(lambda sql: 96.5)
    aid = _asset(client)
    rid_with_sql = _rule(client, aid, sql="SELECT 96.5")
    rid_no_sql = _rule(client, aid)  # no measurement_sql

    r = client.post(f"/api/assets/{aid}/measure/run-all")
    assert r.status_code == 200, r.text
    results = r.json()["results"]

    result_ids = [res["rule_id"] for res in results]
    assert rid_with_sql in result_ids
    assert rid_no_sql not in result_ids
    assert len(results) == 1
    assert float(results[0]["score"]) == 96.5


def test_run_all_rule_error_reported_not_500(client):
    """A failing rule contributes an {error} entry; the endpoint still returns 200."""
    from server.errors import AppError

    def bad_runner(sql):
        raise AppError("measure_failed", "SQL warehouse bombed", 502)

    set_sql_runner(bad_runner)
    aid = _asset(client)
    rid = _rule(client, aid, sql="SELECT bad")

    r = client.post(f"/api/assets/{aid}/measure/run-all")
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    assert len(results) == 1
    assert results[0]["rule_id"] == rid
    assert "error" in results[0]
    assert "score" not in results[0]


def test_run_all_empty_when_no_sql_rules(client):
    """Assets with no SQL rules return an empty results list."""
    aid = _asset(client)
    _rule(client, aid)  # no sql

    r = client.post(f"/api/assets/{aid}/measure/run-all")
    assert r.status_code == 200, r.text
    assert r.json()["results"] == []


# ─── Read-only SQL guard ──────────────────────────────────────────────────────

def test_unsafe_sql_rejected_at_run(client):
    """measurement_sql that is not a SELECT or WITH returns 400 unsafe_sql."""
    aid = _asset(client)
    rid = _rule(client, aid, sql="DROP TABLE quality_rules")
    r = client.post(f"/api/rules/{rid}/measure/run")
    assert r.status_code == 400, r.text
    assert r.json()["error"]["code"] == "unsafe_sql"


def test_unsafe_sql_reported_as_error_in_run_all(client):
    """run-all reports an unsafe rule as {error}, not 500, and does not execute it."""
    aid = _asset(client)
    rid = _rule(client, aid, sql="DELETE FROM data_assets")
    r = client.post(f"/api/assets/{aid}/measure/run-all")
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    assert len(results) == 1
    assert results[0]["rule_id"] == rid
    assert "error" in results[0]


# ─── run-all 404 on missing asset ────────────────────────────────────────────

def test_run_all_missing_asset_returns_404(client):
    r = client.post("/api/assets/00000000-0000-0000-0000-000000000000/measure/run-all")
    assert r.status_code == 404
