from server.repositories import insert, get_by_id, list_where, update_by_id, delete_by_id


def create_issue(conn, asset_id, data: dict, user: str) -> dict:
    return insert(conn, "issues", {**data, "asset_id": asset_id, "created_by": user, "updated_by": user})


def list_issues(conn, asset_id):
    return list_where(conn, "issues", {"asset_id": asset_id})


def get_issue(conn, id):
    return get_by_id(conn, "issues", id)


def update_issue(conn, id, data: dict, user: str):
    return update_by_id(conn, "issues", id, {**data, "updated_by": user})


def delete_issue(conn, id) -> bool:
    return delete_by_id(conn, "issues", id)
