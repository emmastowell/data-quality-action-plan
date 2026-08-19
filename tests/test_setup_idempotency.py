from server.db import apply_schema, fetch_one, execute
from setup import run_setup


def test_run_setup_is_idempotent(db_conn):
    run_setup(db_conn)              # first run
    execute(db_conn, "INSERT INTO data_assets (name) VALUES (%s)", ("keep-me",))
    run_setup(db_conn)              # second run must not error or wipe data
    row = fetch_one(db_conn, "SELECT count(*) AS n FROM data_assets WHERE name='keep-me'")
    assert row["n"] == 1


def test_run_setup_reset_wipes(db_conn):
    run_setup(db_conn)
    execute(db_conn, "INSERT INTO data_assets (name) VALUES (%s)", ("gone",))
    run_setup(db_conn, reset=True)
    row = fetch_one(db_conn, "SELECT count(*) AS n FROM data_assets")
    assert row["n"] == 0
