import os
import psycopg
import pytest
from fastapi.testclient import TestClient

TEST_DB = os.environ.get("TEST_DATABASE_URL", "postgresql://localhost/dqap_test")


class _TxConn:
    """Proxy over one real connection: neutralise commit() so all work stays in
    a single transaction that the fixture rolls back. Everything else delegates."""
    def __init__(self, real):
        self._real = real
    def commit(self):
        pass
    def __getattr__(self, name):
        return getattr(self._real, name)


@pytest.fixture(scope="session")
def _created_schema():
    """Create all DB objects once per session from schema.sql."""
    from server.db import apply_schema
    with psycopg.connect(TEST_DB) as conn:
        apply_schema(conn)
        conn.commit()
    yield


_TABLES = ["raci_cells", "raci_roles", "asset_tables", "asset_step_status", "actions", "issues", "measurements", "quality_rules", "data_assets"]


@pytest.fixture
def db_conn(_created_schema):
    """A shared connection whose changes are rolled back after each test.

    Truncates all tables at the start of each test (within the transaction) so
    that committed seed data (e.g. from `setup.py --seed`) does not bleed into
    test assertions.  Because TRUNCATE is transactional in PostgreSQL, the
    rollback at teardown restores the seed data for E2E use.
    """
    real = psycopg.connect(TEST_DB, autocommit=False)
    tx = _TxConn(real)
    try:
        real.execute(f"TRUNCATE {', '.join(_TABLES)} CASCADE")
        yield tx
    finally:
        real.rollback()
        real.close()


@pytest.fixture
def client(db_conn):
    """FastAPI TestClient whose requests all use the test connection."""
    import server.db as db
    db.set_conn_provider(lambda: db_conn)
    try:
        from app import app
        with TestClient(app, headers={"X-Forwarded-Email": "tester@gov.uk"}) as c:
            yield c
    finally:
        db.set_conn_provider(None)
