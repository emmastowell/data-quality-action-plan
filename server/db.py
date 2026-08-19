import os
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# When set, bypasses Lakebase and connects directly to a local Postgres instance.
# Usage: LOCAL_DATABASE_URL=postgresql://localhost/dqap_test uv run uvicorn app:app
_LOCAL_URL = os.environ.get("LOCAL_DATABASE_URL")

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _resolve_pg_params(w, instance_name):
    """Resolve (host, user, database) for the Lakebase connection.

    In the App runtime PGHOST/PGUSER are injected by the attached Database
    resource. In a Job runtime they are absent, so derive them from the SDK:
    host from the instance's read/write DNS, user from the caller identity.
    Env vars always win when present.
    """
    host = os.environ.get("PGHOST")
    if not host:
        inst = w.database.get_database_instance(name=instance_name)
        host = getattr(inst, "read_write_dns", None) or getattr(inst, "dns", None)
        if not host:
            raise RuntimeError(
                f"Could not resolve Lakebase host for instance {instance_name!r}; "
                "set PGHOST or check LAKEBASE_INSTANCE_NAME"
            )
    user = os.environ.get("PGUSER")
    if not user:
        user = w.current_user.me().user_name
    database = os.environ.get("PGDATABASE", "databricks_postgres")
    return host, user, database


def _build_pool() -> ConnectionPool:
    # Managed Lakebase Database Instance pattern.
    # The app service principal is granted a Postgres login role when the
    # Database resource is attached; the OAuth token generated below is used as
    # the connection password and is refreshed on every new connection (tokens
    # are short-lived, hence a modest max_lifetime on the pool).
    import uuid
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()

    # Instance name to mint credentials for. Prefer an explicit env var; fall
    # back to PGAPPNAME which Databricks injects with the resource name.
    instance_name = os.environ.get("LAKEBASE_INSTANCE_NAME") or os.environ.get("PGAPPNAME")
    if not instance_name:
        raise RuntimeError("Set LAKEBASE_INSTANCE_NAME (or run under an App that injects PGAPPNAME)")

    host, user, database = _resolve_pg_params(w, instance_name)

    class OAuthConnection(psycopg.Connection):
        @classmethod
        def connect(cls, conninfo="", **kwargs):
            cred = w.database.generate_database_credential(
                request_id=str(uuid.uuid4()),
                instance_names=[instance_name],
            )
            kwargs["password"] = cred.token
            return super().connect(conninfo, **kwargs)

    conninfo = (
        f"dbname={database} user={user} host={host} "
        f"port={os.environ.get('PGPORT', '5432')} "
        f"sslmode={os.environ.get('PGSSLMODE', 'require')}"
    )
    return ConnectionPool(
        conninfo=conninfo,
        connection_class=OAuthConnection,
        min_size=1, max_size=10, max_lifetime=2700, open=False,
    )


# Built lazily so importing this module never requires Databricks creds (tests override get_conn_ctx).
pool: ConnectionPool | None = None


def init_pool() -> ConnectionPool:
    global pool
    if pool is None:
        pool = _build_pool()
    return pool


# Tests set this to a callable returning a connection; read at call time so it
# works even though routes import get_conn_ctx by name.
_conn_provider = None


def set_conn_provider(fn):
    global _conn_provider
    _conn_provider = fn


@contextmanager
def get_conn_ctx():
    if _conn_provider is not None:
        # Tests override this; must stay first so test fixtures take precedence.
        yield _conn_provider()
    elif _LOCAL_URL:
        conn = psycopg.connect(_LOCAL_URL)
        try:
            yield conn
        finally:
            conn.close()
    else:
        with init_pool().connection() as conn:
            yield conn


def fetch_all(conn, sql, params=None) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(conn, sql, params=None):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(conn, sql, params=None):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


def apply_schema(conn) -> None:
    conn.execute(_SCHEMA_PATH.read_text())
