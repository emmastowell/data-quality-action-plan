from server.repositories import insert, get_by_id, list_where, update_by_id, delete_by_id


def create_action(conn, asset_id, data: dict, user: str) -> dict:
    return insert(conn, "actions", {**data, "asset_id": asset_id, "created_by": user, "updated_by": user})


def list_actions(conn, asset_id):
    return list_where(conn, "actions", {"asset_id": asset_id})


def get_action(conn, id):
    return get_by_id(conn, "actions", id)


def update_action(conn, id, data: dict, user: str):
    return update_by_id(conn, "actions", id, {**data, "updated_by": user})


def delete_action(conn, id) -> bool:
    return delete_by_id(conn, "actions", id)
