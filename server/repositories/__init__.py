import uuid as _uuid_mod
from psycopg.rows import dict_row


def _cur(conn):
    return conn.cursor(row_factory=dict_row)


def _coerce(row):
    """Convert UUID objects to strings so psycopg3 native UUID type doesn't clash with str-typed models."""
    if row is None:
        return None
    return {k: str(v) if isinstance(v, _uuid_mod.UUID) else v for k, v in row.items()}


def insert(conn, table, values: dict) -> dict:
    cols = list(values)
    placeholders = ", ".join(["%s"] * len(cols))
    sql = f'INSERT INTO {table} ({", ".join(cols)}) VALUES ({placeholders}) RETURNING *'
    with _cur(conn) as cur:
        cur.execute(sql, tuple(values[c] for c in cols))
        return _coerce(cur.fetchone())


def get_by_id(conn, table, id):
    with _cur(conn) as cur:
        cur.execute(f"SELECT * FROM {table} WHERE id = %s", (id,))
        return _coerce(cur.fetchone())


# IMPORTANT: `order_by` is interpolated directly into SQL — it MUST be a hardcoded constant, never user input.
def list_where(conn, table, where: dict | None = None, order_by="created_at DESC"):
    where = where or {}
    clause = (" WHERE " + " AND ".join(f"{k} = %s" for k in where)) if where else ""
    with _cur(conn) as cur:
        cur.execute(f"SELECT * FROM {table}{clause} ORDER BY {order_by}", tuple(where.values()))
        return [_coerce(row) for row in cur.fetchall()]


def update_by_id(conn, table, id, values: dict):
    values = {k: v for k, v in values.items() if v is not None}
    if not values:
        return get_by_id(conn, table, id)
    sets = ", ".join(f"{k} = %s" for k in values) + ", updated_at = now()"
    with _cur(conn) as cur:
        cur.execute(f"UPDATE {table} SET {sets} WHERE id = %s RETURNING *",
                    tuple(values.values()) + (id,))
        return _coerce(cur.fetchone())


def delete_by_id(conn, table, id) -> bool:
    with _cur(conn) as cur:
        cur.execute(f"DELETE FROM {table} WHERE id = %s", (id,))
        return cur.rowcount > 0
