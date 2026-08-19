from server.repositories import insert, get_by_id, list_where, update_by_id, delete_by_id


def create_rule(conn, asset_id, data: dict, user: str) -> dict:
    return insert(conn, "quality_rules",
                  {**data, "asset_id": asset_id, "created_by": user, "updated_by": user})


def list_rules(conn, asset_id):
    return list_where(conn, "quality_rules", {"asset_id": asset_id}, order_by="dimension, name")


def get_rule(conn, id):
    return get_by_id(conn, "quality_rules", id)


def update_rule(conn, id, data: dict, user: str):
    return update_by_id(conn, "quality_rules", id, {**data, "updated_by": user})


def delete_rule(conn, id) -> bool:
    return delete_by_id(conn, "quality_rules", id)
