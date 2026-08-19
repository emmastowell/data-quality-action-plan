from server.db import fetch_all, fetch_one, execute
from server.raci_content import (
    RACI_ACTIVITIES, RACI_DEFAULT_ROLES, RACI_DEFAULT_CELLS, ACTIVITY_KEYS,
)


def _seed_if_empty(conn) -> None:
    existing = fetch_one(conn, "SELECT count(*) AS n FROM raci_roles")
    if existing["n"] > 0:
        return
    # Insert roles with ON CONFLICT DO NOTHING so concurrent seeders don't
    # raise UniqueViolation → they both complete safely.
    for i, name in enumerate(RACI_DEFAULT_ROLES):
        execute(conn,
            "INSERT INTO raci_roles (name, sort_order) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
            (name, i))
    # Build name→id from the DB (covers rows a concurrent seeder inserted too).
    rows = fetch_all(conn, "SELECT id, name FROM raci_roles")
    name_to_id = {r["name"]: r["id"] for r in rows}
    for key, cells in RACI_DEFAULT_CELLS.items():
        for role_name, value in cells.items():
            if not value:
                continue
            execute(conn,
                "INSERT INTO raci_cells (activity_key, role_id, value) VALUES (%s, %s, %s)"
                " ON CONFLICT (activity_key, role_id) DO NOTHING",
                (key, name_to_id[role_name], value))


def get_matrix(conn) -> dict:
    _seed_if_empty(conn)
    roles = fetch_all(conn, "SELECT id, name, sort_order FROM raci_roles ORDER BY sort_order, name")
    cell_rows = fetch_all(conn, "SELECT activity_key, role_id, value FROM raci_cells")
    cells: dict[str, dict[str, str]] = {}
    for c in cell_rows:
        cells.setdefault(str(c["activity_key"]), {})[str(c["role_id"])] = c["value"]
    return {
        "roles": [{"id": str(r["id"]), "name": r["name"], "sort_order": r["sort_order"]} for r in roles],
        "activities": RACI_ACTIVITIES,
        "cells": cells,
    }


def add_role(conn, name: str, user: str) -> dict:
    top = fetch_one(conn, "SELECT coalesce(max(sort_order), -1) AS m FROM raci_roles")
    row = execute(conn,
        "INSERT INTO raci_roles (name, sort_order, created_by) VALUES (%s, %s, %s) RETURNING id, name, sort_order",
        (name, top["m"] + 1, user))
    return {"id": str(row["id"]), "name": row["name"], "sort_order": row["sort_order"]}


def rename_role(conn, role_id, name: str) -> dict | None:
    row = execute(conn,
        "UPDATE raci_roles SET name = %s WHERE id = %s RETURNING id, name, sort_order",
        (name, role_id))
    return {"id": str(row["id"]), "name": row["name"], "sort_order": row["sort_order"]} if row else None


def delete_role(conn, role_id) -> bool:
    row = execute(conn, "DELETE FROM raci_roles WHERE id = %s RETURNING id", (role_id,))
    return row is not None


def upsert_cell(conn, activity_key: str, role_id, value: str, user: str) -> None:
    # An empty value means "clear the cell" — delete rather than store blank rows.
    if value == "":
        execute(conn,
            "DELETE FROM raci_cells WHERE activity_key = %s AND role_id = %s",
            (activity_key, role_id))
    else:
        execute(conn, """
            INSERT INTO raci_cells (activity_key, role_id, value, updated_by)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (activity_key, role_id)
            DO UPDATE SET value = EXCLUDED.value, updated_by = EXCLUDED.updated_by, updated_at = now()
        """, (activity_key, role_id, value, user))
