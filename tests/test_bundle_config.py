# tests/test_bundle_config.py
import pathlib
import yaml

_BUNDLE = pathlib.Path(__file__).resolve().parents[1] / "databricks.yml"


def _load():
    return yaml.safe_load(_BUNDLE.read_text())


def test_variables_declared():
    doc = _load()
    assert set(doc["variables"]) >= {
        "catalog", "metrics_schema", "warehouse_id",
        "lakebase_instance", "app_service_principal",
    }


def test_schema_resource_grants_sp():
    doc = _load()
    schemas = doc["resources"]["schemas"]
    schema = next(iter(schemas.values()))
    assert "${var.catalog}" in schema["catalog_name"]
    assert "${var.metrics_schema}" in schema["name"]
    grant = schema["grants"][0]
    assert "${var.app_service_principal}" in grant["principal"]
    assert set(grant["privileges"]) == {"USE_SCHEMA", "CREATE_TABLE"}


def test_job_has_two_chained_tasks_and_is_unpaused():
    doc = _load()
    job = doc["resources"]["jobs"]["dqap_measure_refresh"]
    assert "${var.app_service_principal}" in str(job["run_as"])
    tasks = {t["task_key"]: t for t in job["tasks"]}
    assert {"run_measures", "sync_to_uc"} <= set(tasks)
    depends = [d["task_key"] for d in tasks["sync_to_uc"].get("depends_on", [])]
    assert "run_measures" in depends
    assert job["schedule"]["pause_status"] == "UNPAUSED"


def test_variable_defaults():
    doc = _load()
    variables = doc["variables"]
    # Neutral, non-account-specific defaults ship with the accelerator.
    assert variables["catalog"]["default"] == "main"
    assert variables["metrics_schema"]["default"] == "dqap"
    assert variables["lakebase_instance"]["default"] == "dqap-accelerator"


def test_workspace_specific_vars_have_no_baked_in_default():
    # warehouse_id and app_service_principal are workspace/account-specific: they
    # must be REQUIRED (no default) so no customer inherits our identifiers.
    variables = _load()["variables"]
    assert "default" not in variables["warehouse_id"]
    assert "default" not in variables["app_service_principal"]


def test_sync_task_passes_catalog_and_schema():
    doc = _load()
    job = doc["resources"]["jobs"]["dqap_measure_refresh"]
    tasks = {t["task_key"]: t for t in job["tasks"]}
    params = tasks["sync_to_uc"]["spark_python_task"]["parameters"]
    joined = " ".join(params)
    assert "--catalog" in joined and "${var.catalog}" in joined
    assert "--schema" in joined and "${var.metrics_schema}" in joined
    assert "--lakebase-instance" in joined and "${var.lakebase_instance}" in joined
    assert "--pguser" in joined and "${var.app_service_principal}" in joined


def test_job_environment_includes_psycopg_pool_extra():
    """Regression: psycopg[binary] alone does NOT install psycopg_pool.
    server.db imports psycopg_pool at the top level, so the dependency must
    include the pool extra or both job tasks crash with ModuleNotFoundError."""
    doc = _load()
    deps = doc["resources"]["jobs"]["dqap_measure_refresh"]["environments"][0]["spec"]["dependencies"]
    psycopg_entries = [d for d in deps if str(d).startswith("psycopg[")]
    assert psycopg_entries, "No psycopg[...] entry found in job environment dependencies"
    assert all("pool" in entry for entry in psycopg_entries), (
        f"psycopg dependency is missing the 'pool' extra: {psycopg_entries}"
    )
