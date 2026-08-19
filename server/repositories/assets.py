from server.repositories import insert, get_by_id, list_where, update_by_id


def create_asset(conn, data: dict, user: str) -> dict:
    return insert(conn, "data_assets", {**data, "created_by": user, "updated_by": user})


def get_asset(conn, id):
    return get_by_id(conn, "data_assets", id)


def list_assets(conn):
    return list_where(conn, "data_assets")


def update_asset(conn, id, data: dict, user: str):
    return update_by_id(conn, "data_assets", id, {**data, "updated_by": user})


def archive_asset(conn, id, user: str):
    return update_by_id(conn, "data_assets", id, {"status": "archived", "updated_by": user})
