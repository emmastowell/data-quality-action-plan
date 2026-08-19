from server.bootstrap import maybe_bootstrap
from server.db import fetch_one


def test_bootstrap_skips_by_default(db_conn, monkeypatch):
    monkeypatch.delenv("RUN_SETUP_ON_START", raising=False)
    assert maybe_bootstrap(db_conn) == "skipped"


def test_bootstrap_creates_and_seeds(db_conn, monkeypatch):
    monkeypatch.setenv("RUN_SETUP_ON_START", "true")
    monkeypatch.setenv("SEED_ON_START", "true")
    assert maybe_bootstrap(db_conn) == "schema+seed"
    assert fetch_one(db_conn, "SELECT 1 FROM data_assets WHERE name='UK Ship Register'") is not None
