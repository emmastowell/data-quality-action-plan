from server.db import fetch_all, fetch_one, execute

def test_execute_returning_and_fetch(db_conn):
    execute(db_conn, "CREATE TEMP TABLE t (id serial primary key, name text)")
    row = execute(db_conn, "INSERT INTO t (name) VALUES (%s) RETURNING id, name", ("alice",))
    assert row["name"] == "alice" and isinstance(row["id"], int)
    all_rows = fetch_all(db_conn, "SELECT name FROM t")
    assert all_rows == [{"name": "alice"}]
    one = fetch_one(db_conn, "SELECT name FROM t WHERE id = %s", (row["id"],))
    assert one == {"name": "alice"}
    assert fetch_one(db_conn, "SELECT name FROM t WHERE id = %s", (999,)) is None
