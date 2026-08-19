from server.repositories import insert, list_where, delete_by_id


def create_asset_table(conn, asset_id: str, data: dict, user: str) -> dict:
    full_name = f"{data['catalog_name']}.{data['schema_name']}.{data['table_name']}"
    return insert(conn, "asset_tables", {
        "asset_id": asset_id,
        "catalog_name": data["catalog_name"],
        "schema_name": data["schema_name"],
        "table_name": data["table_name"],
        "full_name": full_name,
        "created_by": user,
    })


def list_asset_tables(conn, asset_id: str) -> list[dict]:
    return list_where(conn, "asset_tables", {"asset_id": asset_id})


def delete_asset_table(conn, table_id: str) -> bool:
    return delete_by_id(conn, "asset_tables", table_id)
