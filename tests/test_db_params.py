import pytest


class _FakeInstance:
    read_write_dns = "inst.example.database.azuredatabricks.net"


class _FakeMe:
    user_name = "sp-fallback-user"


class _FakeDB:
    def get_database_instance(self, name):
        assert name == "my-instance"
        return _FakeInstance()


class _FakeCurrentUser:
    def me(self):
        return _FakeMe()


class _FakeWorkspaceClient:
    database = _FakeDB()
    current_user = _FakeCurrentUser()


def test_resolve_pg_params_env_wins(monkeypatch):
    from server.db import _resolve_pg_params
    monkeypatch.setenv("PGHOST", "envhost")
    monkeypatch.setenv("PGUSER", "envuser")
    monkeypatch.setenv("PGDATABASE", "envdb")
    host, user, database = _resolve_pg_params(_FakeWorkspaceClient(), "my-instance")
    assert (host, user, database) == ("envhost", "envuser", "envdb")


def test_resolve_pg_params_sdk_fallback(monkeypatch):
    from server.db import _resolve_pg_params
    monkeypatch.delenv("PGHOST", raising=False)
    monkeypatch.delenv("PGUSER", raising=False)
    monkeypatch.delenv("PGDATABASE", raising=False)
    host, user, database = _resolve_pg_params(_FakeWorkspaceClient(), "my-instance")
    assert host == "inst.example.database.azuredatabricks.net"
    assert user == "sp-fallback-user"
    assert database == "databricks_postgres"  # default


def test_resolve_pg_params_no_host_raises(monkeypatch):
    from server.db import _resolve_pg_params

    class _NoHostInstance:
        read_write_dns = None
        dns = None

    class _NoHostDB:
        def get_database_instance(self, name):
            return _NoHostInstance()

    class _W:
        database = _NoHostDB()

    monkeypatch.delenv("PGHOST", raising=False)
    with pytest.raises(RuntimeError, match="host"):
        _resolve_pg_params(_W(), "my-instance")
